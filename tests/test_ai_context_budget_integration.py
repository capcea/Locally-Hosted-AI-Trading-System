"""Real disposable services/worker + deterministic HTTP fixture; no paid model requests."""

import json
import logging
from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from sqlalchemy import func, select
from test_ai_integration import AI
from test_ai_integration import ai as ai
from test_ai_standing_integration import consent, plain

from apps.api.ai.context import ContextScope, assemble
from packages.ai.contracts import ContextReference
from packages.ai.models import AIRequest
from packages.ai.prompts import canonical, messages
from testing.ai_fixture import NAME

pytestmark = pytest.mark.isolated_services


def configured_4096(ai: AI) -> tuple[str, str]:
    ai.setup()
    connection = ai.owner.client.get("/api/v1/ai/connections").json()[0]["id"]
    registered = ai.post(
        "/models", {"connection_id": connection, "name": NAME, "context_ceiling": 4096}
    )
    assert registered.status_code == 201
    model = registered.json()["id"]
    probe = ai.finish(ai.job(f"/models/{model}/probe", {"key": uuid4().hex}))
    assert probe["state"] == "SUCCEEDED", probe["error"]
    assert probe["output"]["context_tokens"] == 4096
    assert ai.post("/routes", {"role": "RESEARCH", "model_id": model}).status_code == 201
    authorization = consent(ai, connection)
    return model, authorization["id"]


def test_short_romanian_research_with_approved_default_context_is_processed(
    ai: AI, caplog: pytest.LogCaptureFixture
) -> None:
    # Synthetic provider is separately probed at exactly4096; never invent capacity.
    _, authorization = configured_4096(ai)
    caplog.set_level(logging.INFO, logger="research.requests")
    for document, question in [
        ("strategy-lab-v1", "Propune o strategie pentru XAUUSD."),
        (
            "strategy-lab-v1",
            "Propune o ipoteză testabilă pentru XAUUSD pe M5, cu riscuri și dovezi lipsă.",
        ),
        ("research-limits-v1", "Ce dovezi lipsesc pentru această ipoteză?"),
    ]:
        body = plain(
            ai,
            authorization,
            question=question,
            parameters={"context_tokens": 4096, "output_tokens": 768},
            references=[{"kind": "documentation", "id": document}],
        )
        response = ai.post("/requests", body)
        app = cast(FastAPI, ai.owner.client.app)
        owner = ai.owner.client.get("/api/v1/auth/me").json()["user"]["id"]
        with app.state.store.session() as db:
            context = assemble(
                ContextScope(db, UUID(owner)),
                [ContextReference(kind="documentation", id=document)],
                ai.config,
            )
        prompt = messages("RESEARCH", question, context)
        diagnostic = {
            "http_status": response.status_code,
            "question_bytes": len(question.encode()),
            "serialized_prompt_bytes": len(canonical(prompt).encode()),
            "reserved_output": 768,
            "requested_context": 4096,
        }
        assert response.status_code == 202, diagnostic
        result = ai.finish(response.json())
        assert result["state"] == "SUCCEEDED", result["error"]
        assert result["output"]["verified"] is False
        assert ai.owner.client.get("/api/v1/safety").json()["executor_capability"] == "DENY_ALL"
    budgets = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "research.requests" and '"event":"ai.context_budget"' in record.message
    ]
    assert len(budgets) == 3
    for budget in budgets:
        assert budget["required_context_upper_bound"] <= budget["effective_context_tokens"] == 4096
        assert budget["schema_bytes"] > 0
        assert budget["output_tokens"] == 768
        assert budget["request_id"]
        assert all(
            isinstance(value, int)
            for key, value in budget.items()
            if key not in {"event", "request_id", "method"}
        )
        assert not {"question", "prompt", "context", "key", "owner_id", "session"} & budget.keys()


def test_real_overflow_is_422_before_enqueue_and_corrected_submission_can_recover(ai: AI) -> None:
    _, authorization = configured_4096(ai)
    body = plain(
        ai,
        authorization,
        question="a" * 1200,
        parameters={"context_tokens": 4096, "output_tokens": 768},
        references=[{"kind": "documentation", "id": "strategy-lab-v1"}],
    )
    seen = ai.fixture.seen
    rejected = ai.post("/requests", body)
    assert rejected.status_code == 422
    assert rejected.json() == {"detail": "AI_CONTEXT_BUDGET_EXCEEDED"}
    sizes = json.loads(rejected.headers["X-AI-Context-Budget"])
    assert all(type(value) is int for value in sizes.values())
    assert sizes["required_context_upper_bound"] > sizes["effective_context_tokens"] == 4096
    assert sizes["question_bytes"] == 1200
    assert sizes["input_upper_bound"] == sizes["message_content_bytes"] + sizes["schema_bytes"]
    assert sizes["required_context_upper_bound"] == sizes["input_upper_bound"] + 768 + 512
    assert rejected.headers["X-Request-ID"]
    assert ai.fixture.seen == seen
    app = cast(FastAPI, ai.owner.client.app)
    with app.state.store.session() as db:
        assert (
            db.scalar(
                select(func.count()).select_from(AIRequest).where(AIRequest.key == body["key"])
            )
            == 0
        )
    # No key is reserved by a deterministic 422. A corrected request can be edited and submitted.
    body["question"] = "Propune o strategie pentru XAUUSD."
    accepted = ai.post("/requests", body)
    assert accepted.status_code == 202
    repeated = ai.post("/requests", body)
    assert repeated.status_code == 202
    assert repeated.json()["id"] == accepted.json()["id"]
    assert ai.finish(accepted.json())["state"] == "SUCCEEDED"
    body["key"] = uuid4().hex
    body["parameters"] = {"context_tokens": 8192, "output_tokens": 768}
    unverified = ai.post("/requests", body)
    assert unverified.status_code == 422
    assert unverified.json()["detail"] == "AI_CONTEXT_BUDGET_UNVERIFIED"
    sizes = json.loads(unverified.headers["X-AI-Context-Budget"])
    assert sizes["verified_context_tokens"] == sizes["registered_context_tokens"] == 4096


def test_dynamic_modes_revision_preview_and_actual_worker_compatibility(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    from packages.ai.models import AIModel

    old, authorization = configured_4096(ai)
    seen = ai.fixture.seen
    revised = ai.post(f"/models/{old}/context-revisions", {"context_ceiling": 32768})
    assert revised.status_code == 201
    new = revised.json()["id"]
    assert new != old and revised.json()["verification_required"]
    assert ai.fixture.seen == seen  # Registration is never an automatic paid probe.
    model_rows = ai.owner.client.get("/api/v1/ai/models").json()
    assert next(row for row in model_rows if row["id"] == new)["verification_current"] is False
    assert next(row for row in model_rows if row["id"] == old)["verification_current"] is True
    assert ai.post("/routes", {"role": "RESEARCH", "model_id": new}).status_code == 409
    app = cast(FastAPI, ai.owner.client.app)
    with app.state.store.session() as db:
        assert db.get(AIModel, UUID(old)).context_ceiling == 4096
    # New metadata plus a fresh actual synthetic HTTP probe; no old proof is upgraded.
    ai.fixture.context_length = 32768
    result = ai.finish(
        ai.job(
            f"/models/{new}/probe", {"key": uuid4().hex, "standing_authorization_id": authorization}
        )
    )
    assert result["state"] == "SUCCEEDED" and result["output"]["context_tokens"] == 32768
    for role in ["RESEARCH", "CRITIC", "CODING", "LIGHTWEIGHT"]:
        assert ai.post("/routes", {"role": role, "model_id": new}).status_code == 201
        for mode, tier in [
            ("AUTO", 4096),
            ("RAPID", 4096),
            ("STANDARD", 16384),
            ("COMPLEX", 32768),
        ]:
            body = plain(
                ai,
                authorization,
                role=role,
                context_mode=mode,
                question="Ce dovezi lipsesc?",
                parameters={"output_tokens": 768},
            )
            before = ai.fixture.seen
            preview = ai.post("/requests/preview", body)
            assert preview.status_code == 200
            assert preview.json()["budget"]["selected_context_tokens"] == tier
            assert preview.json()["provider_request_sent"] is False
            assert ai.fixture.seen == before
            job = ai.finish(ai.job("/requests", body))
            assert job["state"] == "SUCCEEDED", job["error"]
            assert job["metadata"]["parameters"]["context_tokens"] == tier
    # AUTO has real assembled larger inputs, never a UI-only estimate.
    for question, tier in [
        ("Ce dovezi? " + "î" * 2000, 16384),
        ("Ce dovezi? " + "🧪" * 3900, 32768),
    ]:
        body = plain(
            ai,
            authorization,
            context_mode="AUTO",
            question=question,
            parameters={"output_tokens": 768},
        )
        preview = ai.post("/requests/preview", body)
        assert preview.status_code == 200
        assert preview.json()["budget"]["selected_context_tokens"] == tier
        assert (
            ai.finish(ai.job("/requests", body))["metadata"]["parameters"]["context_tokens"] == tier
        )
    # Omitted mode/omitted numeric ceiling is AUTO; provenance must describe the actual allocator.
    default_body = plain(
        ai, authorization, question="Ce dovezi lipsesc?", parameters={"output_tokens": 768}
    )
    default_job = ai.job("/requests", default_body)
    with app.state.store.session() as db:
        assert db.get(AIRequest, UUID(default_job["id"])).specification["context_mode"] == "AUTO"
    assert ai.finish(default_job)["metadata"]["parameters"]["context_tokens"] == 4096
    # Lower verified fallback prevents an enlarged manual request.
    assert (
        ai.post("/routes", {"role": "RESEARCH", "model_id": new, "fallback_ids": [old]}).status_code
        == 201
    )
    refused = ai.post(
        "/requests", plain(ai, authorization, context_mode="COMPLEX", allow_fallback=True)
    )
    assert refused.status_code == 422 and refused.json()["detail"] == "AI_CONTEXT_BUDGET_UNVERIFIED"
    from datetime import timedelta

    from packages.persistence.models import utcnow

    with monkeypatch.context() as clock:
        clock.setattr("packages.ai.registry.utcnow", lambda: utcnow() + timedelta(days=30))
        assert (
            ai.post("/requests/preview", plain(ai, authorization, context_mode="AUTO")).status_code
            == 409
        )
    # Revocation remains independent of context mode.
    assert ai.post("/standing-authorization/revoke", {}).status_code == 200
    assert (
        ai.post("/requests/preview", plain(ai, authorization, context_mode="AUTO")).status_code
        == 409
    )


def test_cloud_auto_reserves_selected_tier_and_standing_cap_still_refuses_32k(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    from decimal import Decimal

    from test_openrouter_integration import enable

    from packages.ai.cloud import reservation_amount
    from packages.ai.models import AICloudReservation

    connection, old, calls = enable(ai, monkeypatch, context_length=32768, request_limit="0.04")
    # Explicit fixture-owner cap; the installed owner's caps are never changed.
    authorization = consent(ai, connection, request_usd="0.04")["id"]
    revised = ai.post(f"/models/{old}/context-revisions", {"context_ceiling": 32768}).json()["id"]
    assert not calls
    job = ai.job(
        f"/models/{revised}/probe", {"key": uuid4().hex, "standing_authorization_id": authorization}
    )
    assert ai.finish(job)["output"]["context_tokens"] == 32768
    assert ai.post("/routes", {"role": "RESEARCH", "model_id": revised}).status_code == 201
    body = plain(
        ai,
        authorization,
        context_mode="AUTO",
        question="Ce dovezi lipsesc?",
        parameters={"output_tokens": 768},
    )
    before = len(calls)
    preview = ai.post("/requests/preview", body)
    assert preview.status_code == 200 and len(calls) == before
    assert preview.json()["budget"]["selected_context_tokens"] == 4096
    assert preview.json()["financial"]["reservation_usd"] == "0.00716800"
    accepted = ai.job("/requests", body)
    app = cast(FastAPI, ai.owner.client.app)
    with app.state.store.session() as db:
        row = db.get(AIRequest, UUID(accepted["id"]))
        reservation = db.get(AICloudReservation, UUID(accepted["id"]))
        assert reservation.amount == Decimal("0.00716800")
        assert reservation.amount == reservation_amount(
            row.specification["cloud"], "INFER", 4096, 768
        )
    assert ai.finish(accepted)["state"] == "SUCCEEDED"
    smaller = consent(ai, connection, request_usd="0.01")["id"]
    denied = ai.post(
        "/requests", plain(ai, smaller, context_mode="COMPLEX", parameters={"output_tokens": 768})
    )
    assert denied.status_code == 409 and denied.json()["detail"] == "AI_CLOUD_BUDGET_EXCEEDED"
    assert len(calls) == before + 1
