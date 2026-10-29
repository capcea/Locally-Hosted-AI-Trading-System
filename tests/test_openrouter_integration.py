"""Real PG/Redis/MinIO and inference worker, synthetic provider HTTP transport. No paid requests."""

import json
import secrets
from concurrent.futures import ThreadPoolExecutor
from typing import Any, cast
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from test_ai_integration import AI
from test_ai_integration import ai as ai

from packages.ai.models import AICloudReservation, AIConnectionSecret
from packages.ai.providers import Adapter, create_provider
from packages.ai.settings import GatewaySettings
from testing.ai_fixture import structured

pytestmark = pytest.mark.isolated_services


def enable(
    ai: AI,
    monkeypatch: pytest.MonkeyPatch,
    *,
    daily: str = "0.50",
    statuses: list[int] | None = None,
) -> tuple[str, str, list[dict[str, Any]]]:
    app = cast(FastAPI, ai.owner.client.app)
    old = app.state.ai_config
    config = GatewaySettings(
        **{
            **ai.config.model_dump(),
            "openrouter_enabled": True,
            "egress_proxy": "http://127.0.0.1:18888",
        }
    )
    app.state.ai_config = config.model_copy(
        update={"database_url": None, "redis_url": old.redis_url}
    )
    ai.worker.config = config
    calls: list[dict[str, Any]] = []
    token = secrets.token_hex(32)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "openrouter.ai" and request.url.scheme == "https"
        assert request.headers["authorization"] == "Bearer " + token
        if request.method == "GET":
            if request.url.path == "/api/v1/models":
                return httpx.Response(200, json={"data": [{"id": "fixture/model"}]})
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "fixture/model",
                        "endpoints": [{"tag": "fixture-provider", "context_length": 8192}],
                    }
                },
            )
        body = json.loads(request.content)
        assert token not in json.dumps(body)
        assert body["provider"]["only"] == ["fixture-provider"]
        assert body["provider"]["zdr"] and not body["provider"]["allow_fallbacks"]
        calls.append(body)
        if statuses:
            code = statuses.pop(0)
            if code:
                return httpx.Response(code, json={"error": "Synthetic provider refusal"})
        properties = body["response_format"]["json_schema"]["schema"]["properties"]
        output = {"probe": "ok"} if "probe" in properties else structured(properties)
        content = (
            "data: "
            + json.dumps(
                {
                    "choices": [
                        {"delta": {"content": json.dumps(output)}, "finish_reason": "stop"}
                    ],
                    "usage": {"prompt_tokens": 12, "completion_tokens": 4},
                }
            )
            + "\n\ndata: [DONE]\n\n"
        )
        return httpx.Response(200, content=content)

    def provider(*args: Any, **kwargs: Any) -> Any:
        adapter = create_provider(*args, **kwargs)
        assert isinstance(adapter, Adapter)
        if args[1] == "OPENROUTER":
            headers = dict(adapter.client.headers)
            adapter.client.close()
            adapter.client = httpx.Client(
                base_url="https://openrouter.ai",
                headers=headers,
                transport=httpx.MockTransport(handler),
                follow_redirects=False,
            )
        return adapter

    monkeypatch.setattr("packages.ai.worker.create_provider", provider)
    policy = {
        "upstream_provider": "fixture-provider",
        "request_usd": "0.02",
        "daily_usd": daily,
        "acknowledged_public_cloud": True,
        "acknowledged_upstream_processing": True,
        "acknowledged_cost": True,
        "acknowledged_provider_policy_limits": True,
    }
    assert ai.post("/endpoints/openrouter", policy).status_code == 201
    connection = ai.post(
        "/connections",
        {
            "name": "SYNTHETIC_OPENROUTER_TRANSPORT",
            "endpoint_id": "openrouter",
            "provider": "OPENROUTER",
            "policy": {
                "rights_confirmed": True,
                "approved_processing": True,
                "remote_processing": True,
                "cloud_processing_acknowledged": True,
            },
        },
    )
    assert connection.status_code == 201, connection.text
    connection_id = connection.json()["id"]
    stored = ai.post(f"/connections/{connection_id}/credential", {"api_key": token})
    assert stored.status_code == 200 and token not in stored.text
    model = ai.post(
        "/models",
        {"connection_id": connection_id, "name": "fixture/model", "context_ceiling": 8192},
    )
    assert model.status_code == 201
    return connection_id, model.json()["id"], calls


def verify(ai: AI, model: str) -> None:
    probe = ai.job(f"/models/{model}/probe", {"key": uuid4().hex, "cloud_cost_acknowledged": True})
    result = ai.finish(probe)
    assert result["state"] == "SUCCEEDED", result["error"]
    for role in ("RESEARCH", "CRITIC"):
        assert ai.post("/routes", {"role": role, "model_id": model}).status_code == 201


def test_cloud_setup_empty_prerequisites_explicit_operator_owner_and_protocol(ai: AI) -> None:
    assert ai.owner.client.get("/api/v1/ai/connections").json() == []
    cloud = ai.owner.client.get("/api/v1/ai/cloud-policy").json()
    assert not cloud["operator_enabled"] and cloud["authorization"] is None
    denied = ai.post(
        "/endpoints/openrouter",
        {
            "upstream_provider": "fixture",
            "acknowledged_public_cloud": True,
            "acknowledged_upstream_processing": True,
            "acknowledged_cost": True,
            "acknowledged_provider_policy_limits": True,
        },
    )
    assert denied.status_code == 409
    body = {
        "name": "No implicit cloud",
        "endpoint_id": "fixture",
        "provider": "OPENROUTER",
        "policy": {
            "rights_confirmed": True,
            "approved_processing": True,
            "remote_processing": True,
        },
    }
    assert ai.post("/connections", body).status_code == 409
    assert ai.post("/endpoints/openrouter", {"url": "https://example.com"}).status_code == 422


def test_cloud_verified_research_critic_secret_isolation_and_real_durable_results(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    connection, model, calls = enable(ai, monkeypatch)
    # A model record never grants routing authority, and a paid probe requires separate approval.
    assert ai.post("/routes", {"role": "RESEARCH", "model_id": model}).status_code == 409
    assert ai.post(f"/models/{model}/probe", {"key": uuid4().hex}).status_code == 409
    verify(ai, model)
    for role in ("RESEARCH", "CRITIC"):
        job = ai.job(
            "/requests", ai.question(role=role, allow_remote=True, cloud_cost_acknowledged=True)
        )
        result = ai.finish(job)
        assert result["state"] == "SUCCEEDED", result["error"]
        assert result["metadata"]["provider"] == "OPENROUTER"
        assert result["metadata"]["trading_authority"] is False
    assert len(calls) == 3  # One probe and two actual worker/fixture completions, no extra probes.
    engine = create_engine(ai.owner.runtime_url)
    with Session(engine) as db:
        secret = db.get(AIConnectionSecret, UUID(connection))
        assert secret and secret.ciphertext.startswith("gAAAA")
        plain = ai.config.cipher().decrypt(secret.ciphertext.encode()).decode()
        assert plain not in secret.ciphertext
        assert plain not in ai.owner.client.get("/api/v1/ai/connections").text
        assert plain not in ai.owner.client.get("/api/v1/ai/requests").text
        assert plain not in ai.owner.client.get("/api/v1/audit").text
        assert len(db.scalars(select(AICloudReservation)).all()) == 3
    with ai.worker.store.session() as db:
        assert db.scalar(text("SELECT has_table_privilege(current_user,'users','SELECT')")) is False
        assert (
            db.scalar(text("SELECT has_table_privilege(current_user,'campaign_runtime','SELECT')"))
            is False
        )
        assert (
            db.scalar(
                text("SELECT has_table_privilege(current_user,'ai_cloud_reservations','INSERT')")
            )
            is False
        )
    viewer, _ = ai.owner.peer("cloud-viewer", "VIEWER")
    assert viewer.get("/api/v1/ai/cloud-policy").json()["authorization"] is None
    assert (
        ai.owner.post(
            "/api/v1/ai/connections/" + connection + "/credential",
            {"api_key": secrets.token_hex(32)},
            viewer,
        ).status_code
        == 403
    )
    assert (
        ai.owner.client.post(
            "/api/v1/ai/connections/" + connection + "/credential",
            json={"api_key": secrets.token_hex(32)},
        ).status_code
        == 403
    )
    engine.dispose()


def test_cloud_atomic_budget_reservations_and_idempotent_submit(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, model, _ = enable(ai, monkeypatch, daily="0.025")
    verify(ai, model)
    bodies = [ai.question(allow_remote=True, cloud_cost_acknowledged=True) for _ in range(2)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda b: ai.post("/requests", b), bodies))
    assert sorted(r.status_code for r in responses) == [202, 409]
    accepted = next((r, b) for r, b in zip(responses, bodies, strict=True) if r.status_code == 202)
    assert ai.post("/requests", accepted[1]).json()["id"] == accepted[0].json()["id"]
    rows = ai.owner.client.get("/api/v1/ai/cloud-policy").json()["billing_reservations"]
    assert len(rows) == 2  # Probe plus exactly one inference; rejected duplicate spend rolls back.


def test_credential_rotation_revokes_verification_and_pending_request(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    connection, model, calls = enable(ai, monkeypatch)
    verify(ai, model)
    job = ai.job("/requests", ai.question(allow_remote=True, cloud_cost_acknowledged=True))
    calls.clear()
    assert (
        ai.post(
            f"/connections/{connection}/credential", {"api_key": secrets.token_hex(32)}
        ).status_code
        == 200
    )
    rows = ai.owner.client.get("/api/v1/ai/models").json()
    assert not next(m for m in rows if m["id"] == model)["verification_current"]
    result = ai.finish(job)
    assert result["state"] == "CANCELLED" and result["output"] is None
    assert not calls
    assert (
        ai.post(
            "/requests", ai.question(allow_remote=True, cloud_cost_acknowledged=True)
        ).status_code
        == 409
    )


def test_cloud_missing_per_request_consent_and_account_scope_are_refused(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    connection, model, _ = enable(ai, monkeypatch)
    verify(ai, model)
    assert ai.post("/requests", ai.question(allow_remote=True)).status_code == 409
    assert ai.post("/requests", ai.question(cloud_cost_acknowledged=True)).status_code == 409
    peer, _ = ai.owner.peer("other-cloud-reader", "OPERATOR")
    assert (
        ai.owner.post(
            "/api/v1/ai/connections/" + connection + "/credential",
            {"api_key": secrets.token_hex(32)},
            peer,
        ).status_code
        == 403
    )
    assert peer.get("/api/v1/ai/connections").json() == []


def test_cloud_refusal_is_not_automatically_retried_and_owner_can_recover_explicitly(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    statuses: list[int] = []
    _, model, calls = enable(ai, monkeypatch, statuses=statuses)
    verify(ai, model)
    calls.clear()
    statuses.extend([429, 0])
    body = ai.question(allow_remote=True, cloud_cost_acknowledged=True)
    job = ai.job("/requests", body)
    failed = ai.finish(job)
    assert failed["state"] == "FAILED" and failed["output"] is None
    assert failed["attempts"] == 1 and failed["error"] == "AI_PROVIDER_BUSY"
    assert not ai.worker.once()  # No automatic paid retry.
    assert ai.post("/requests", body).json()["id"] == job["id"]
    assert len(calls) == 1
    replacement = ai.job("/requests", ai.question(allow_remote=True, cloud_cost_acknowledged=True))
    assert ai.finish(replacement)["state"] == "SUCCEEDED"
    assert len(calls) == 2


def test_new_cloud_authorization_revokes_old_probe_and_queued_request(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, model, calls = enable(ai, monkeypatch)
    verify(ai, model)
    job = ai.job("/requests", ai.question(allow_remote=True, cloud_cost_acknowledged=True))
    calls.clear()
    policy = ai.owner.client.get("/api/v1/ai/cloud-policy").json()["authorization"]["policy"]
    updated = ai.post(
        "/endpoints/openrouter", {**policy, "upstream_provider": "different-reviewed-provider"}
    )
    assert updated.status_code == 201
    assert not next(m for m in ai.owner.client.get("/api/v1/ai/models").json() if m["id"] == model)[
        "verification_current"
    ]
    assert ai.finish(job)["state"] == "CANCELLED"
    assert not calls
