"""Standing consent against disposable PostgreSQL/Redis; provider HTTP is synthetic only."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import DBAPIError
from test_ai_integration import AI
from test_ai_integration import ai as ai
from test_openrouter_integration import enable, verify

from apps.api.main import create_app
from packages.ai.models import AICloudReservation, AIRequest, AIStandingAuthorization
from packages.ai.worker import Worker
from packages.persistence.models import utcnow

pytestmark = pytest.mark.isolated_services
PREFIX = "/api/v1/ai"


def consent(ai: AI, connection: str, **updates: Any) -> dict[str, Any]:
    body = {
        "connection_ids": [connection],
        "roles": ["RESEARCH", "CRITIC", "CODING", "LIGHTWEIGHT"],
        "data_categories": ["documentation", "strategy"],
        "operations": ["INFER", "PROBE", "DISCOVER"],
        "request_usd": "0.02",
        "daily_usd": "0.50",
        "monthly_usd": "5",
        **updates,
    }
    response = ai.post("/standing-authorization", body)
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json()["authorization"])


def plain(ai: AI, identifier: str, **updates: Any) -> dict[str, Any]:
    body = ai.question(standing_authorization_id=identifier, **updates)
    body.pop("processing_acknowledged")
    body.pop("retain_structured_output")
    return body


def age_mfa(ai: AI) -> None:
    engine = create_engine(ai.owner.admin_url)
    try:
        with engine.begin() as db:
            db.execute(
                text("UPDATE login_sessions SET mfa_at=:old"),
                {"old": utcnow() - timedelta(minutes=6)},
            )
    finally:
        engine.dispose()


def ready(ai: AI) -> dict[str, Any]:
    return cast(dict[str, Any], ai.owner.client.get(PREFIX + "/inference-readiness").json())


def test_new_install_activation_exact_scope_and_no_checkbox_requests(ai: AI) -> None:
    assert ai.owner.client.get(PREFIX + "/standing-authorization").json() == {"authorization": None}
    assert ready(ai)["reason"] == "AI_STANDING_AUTHORIZATION_REQUIRED"
    assert ai.post("/requests", plain(ai, str(uuid4()))).status_code == 409
    ai.setup()
    connection = ai.owner.client.get(PREFIX + "/connections").json()[0]["id"]
    auth = consent(ai, connection)
    assert auth["active"] and auth["policy"]["trading_authority"] is False
    assert auth["policy"]["generated_code_execution"] is False
    job = ai.job("/requests", plain(ai, auth["id"]))
    assert ai.finish(job)["state"] == "SUCCEEDED"
    assert ready(ai)["ready"] is True
    repeat = ai.job("/requests", plain(ai, auth["id"], role="CRITIC"))
    assert ai.finish(repeat)["state"] == "SUCCEEDED"
    # Replacing legacy booleans with true never creates a standing grant.
    denied = ai.post(
        "/requests", plain(ai, str(uuid4()), allow_remote=True, cloud_cost_acknowledged=True)
    )
    assert denied.status_code == 409
    engine = create_engine(ai.owner.admin_url)
    try:
        with engine.connect() as db:
            assert (
                db.scalar(
                    text(
                        "SELECT count(*) FROM audit_events WHERE event_type='ai.standing_activated'"
                    )
                )
                == 1
            )
    finally:
        engine.dispose()


def test_standing_survives_stale_mfa_and_restart_but_changes_require_recent_mfa(ai: AI) -> None:
    ai.setup()
    connection = ai.owner.client.get(PREFIX + "/connections").json()[0]["id"]
    auth = consent(ai, connection)
    age_mfa(ai)
    assert (
        ai.post(
            "/standing-authorization",
            {
                k: v
                for k, v in auth["policy"].items()
                if k
                not in {
                    "grants",
                    "trading_authority",
                    "generated_code_execution",
                    "processing",
                    "retention",
                }
            },
        ).status_code
        == 403
    )
    assert ai.post("/standing-authorization/revoke", {}).status_code == 403
    job = ai.job("/requests", plain(ai, auth["id"]))
    ai.worker.close()
    ai.worker = Worker(ai.config)
    config = cast(FastAPI, ai.owner.client.app).state.ai_config
    with TestClient(create_app(ai.owner.config, config)) as restarted:
        restarted.cookies.update(ai.owner.client.cookies)
        saved = restarted.get(PREFIX + "/standing-authorization").json()["authorization"]
        assert saved["id"] == auth["id"] and saved["policy"] == auth["policy"]
    assert ai.finish(job)["state"] == "SUCCEEDED"
    # A valid full login is still required; standing consent is not a replacement session.
    queued = ai.job("/requests", plain(ai, auth["id"]))
    count = ai.fixture.seen
    assert ai.owner.post("/api/v1/auth/sessions/revoke-all", {}).status_code == 204
    assert ai.owner.client.get(PREFIX + "/inference-readiness").status_code == 401
    assert ai.worker.once()
    assert ai.fixture.seen == count
    engine = create_engine(ai.owner.admin_url)
    try:
        with engine.connect() as db:
            assert (
                db.scalar(
                    text("SELECT state FROM ai_jobs WHERE request_id=:id"), {"id": queued["id"]}
                )
                == "FAILED"
            )
    finally:
        engine.dispose()


def test_revocation_blocks_new_and_queued_work_without_revival(ai: AI) -> None:
    ai.setup()
    connection = ai.owner.client.get(PREFIX + "/connections").json()[0]["id"]
    auth = consent(ai, connection)
    queued = ai.job("/requests", plain(ai, auth["id"]))
    count = ai.fixture.seen
    revoked = ai.post("/standing-authorization/revoke", {})
    assert revoked.status_code == 200 and not revoked.json()["authorization"]["active"]
    assert ai.post("/requests", plain(ai, auth["id"])).status_code == 409
    assert ready(ai)["reason"] == "AI_STANDING_AUTHORIZATION_REQUIRED"
    assert (
        ai.post(
            "/requests", ai.question(allow_remote=True, cloud_cost_acknowledged=True)
        ).status_code
        == 409
    )
    replacement = consent(ai, connection)
    assert replacement["id"] != auth["id"]
    assert ai.finish(queued)["state"] == "FAILED"
    assert ai.fixture.seen == count


def test_standing_owner_csrf_account_and_data_isolation(ai: AI) -> None:
    ai.setup()
    connection = ai.owner.client.get(PREFIX + "/connections").json()[0]["id"]
    auth = consent(ai, connection)
    viewer, _ = ai.owner.peer("standing-viewer", "VIEWER")
    try:
        assert (
            ai.owner.post(PREFIX + "/standing-authorization/revoke", {}, viewer).status_code == 403
        )
        assert viewer.get(PREFIX + "/standing-authorization").json()["authorization"] is None
        assert ai.owner.post(PREFIX + "/requests", plain(ai, auth["id"]), viewer).status_code == 403
        assert (
            ai.owner.client.post(PREFIX + "/standing-authorization/revoke", json={}).status_code
            == 403
        )
    finally:
        cast(FastAPI, viewer.app).state.store.engine.dispose()
        viewer.close()
    assert (
        ai.post(
            "/requests", plain(ai, auth["id"], references=[{"kind": "dataset", "id": str(uuid4())}])
        ).status_code
        == 409
    )
    # Even permitting a category does not grant access to another owner's record or final holdout.
    broader = consent(ai, connection, data_categories=["dataset", "documentation"])
    assert (
        ai.post(
            "/requests",
            plain(ai, broader["id"], references=[{"kind": "dataset", "id": str(uuid4())}]),
        ).status_code
        == 404
    )
    body = {
        "connection_ids": [str(uuid4())],
        "roles": ["RESEARCH"],
        "data_categories": ["documentation"],
        "operations": ["INFER"],
        "request_usd": "0.01",
        "daily_usd": "0.50",
        "monthly_usd": "5",
    }
    assert ai.post("/standing-authorization", body).status_code == 409


def test_cloud_standing_probe_research_and_critic_without_per_request_flags(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    connection, model, calls = enable(ai, monkeypatch)
    auth = consent(ai, connection)
    probe = ai.job(
        f"/models/{model}/probe", {"key": uuid4().hex, "standing_authorization_id": auth["id"]}
    )
    assert ai.finish(probe)["state"] == "SUCCEEDED"
    for role in ["RESEARCH", "CRITIC"]:
        assert ai.post("/routes", {"role": role, "model_id": model}).status_code == 201
        result = ai.finish(ai.job("/requests", plain(ai, auth["id"], role=role)))
        assert result["state"] == "SUCCEEDED", result["error"]
        assert result["metadata"]["trading_authority"] is False
    assert len(calls) == 3
    budget = ready(ai)["budget"]
    assert budget["available"] and budget["monthly_reserved_usd"] != "0"
    assert budget["basis"] == "CONSERVATIVE_RESERVATIONS_NOT_PROVIDER_BILLING"


def test_standing_atomic_daily_reservations_and_idempotency(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    connection, model, _ = enable(ai, monkeypatch)
    verify(ai, model)
    # Probe already reserved 0.008448; one 0.011264 analysis fits 0.02, two do not.
    auth = consent(ai, connection, daily_usd="0.02", monthly_usd="1")
    bodies = [plain(ai, auth["id"]) for _ in range(2)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda body: ai.post("/requests", body), bodies))
    assert sorted(r.status_code for r in replies) == [202, 409]
    index = next(i for i, r in enumerate(replies) if r.status_code == 202)
    again = ai.post("/requests", bodies[index])
    assert again.status_code == 202
    assert again.json()["id"] == replies[index].json()["id"]
    assert ready(ai)["reason"] == "AI_CLOUD_BUDGET_EXCEEDED"
    engine = create_engine(ai.owner.admin_url)
    try:
        with engine.connect() as db:
            assert db.scalar(select(func.count()).select_from(AICloudReservation)) == 2
    finally:
        engine.dispose()


def test_monthly_budget_counts_prior_days_and_reauthorization_does_not_reset(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    connection, model, _ = enable(ai, monkeypatch)
    verify(ai, model)
    auth = consent(ai, connection, daily_usd="0.02", monthly_usd="0.02")
    # Historical fixture reservation: same month, earlier day; never provider billing.
    engine = create_engine(ai.owner.admin_url)
    historical = utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    try:
        with engine.begin() as connection_db:
            owner = connection_db.scalar(
                text("SELECT owner_id FROM ai_cloud_authorizations LIMIT 1")
            )
            cloud_id = connection_db.scalar(text("SELECT id FROM ai_cloud_authorizations LIMIT 1"))
        from sqlalchemy.orm import Session

        with Session(engine) as db, db.begin():
            request = AIRequest(
                owner_id=owner,
                key=uuid4().hex,
                digest="0" * 64,
                kind="DISCOVER",
                role="LIGHTWEIGHT",
                specification={"source": "SYNTHETIC_TEST_FIXTURE"},
                expires_at=historical,
                retain_until=historical,
                created_at=historical,
            )
            db.add(request)
            db.flush()
            db.add(
                AICloudReservation(
                    request_id=request.id,
                    owner_id=owner,
                    authorization_id=cloud_id,
                    amount=Decimal("0.015"),
                    created_at=historical,
                )
            )
    finally:
        engine.dispose()
    # Fixed day avoids wall-clock sleeps and month-end ambiguity on every calendar day.
    monkeypatch.setattr("packages.ai.cloud.utcnow", lambda: utcnow().replace(day=15))
    state = ready(ai)
    assert Decimal(state["budget"]["daily_reserved_usd"]) < Decimal("0.02")
    assert Decimal(state["budget"]["monthly_reserved_usd"]) > Decimal("0.02")
    assert state["reason"] == "AI_CLOUD_BUDGET_EXCEEDED"
    # A manually approved legacy model probe cannot bypass the active monthly cap either.
    legacy_probe = ai.post(
        f"/models/{model}/probe", {"key": uuid4().hex, "cloud_cost_acknowledged": True}
    )
    assert (
        legacy_probe.status_code == 409
        and legacy_probe.json()["detail"] == "AI_CLOUD_BUDGET_EXCEEDED"
    )
    renewed = consent(ai, connection, operations=["INFER"], daily_usd="0.02", monthly_usd="0.02")
    assert renewed["id"] != auth["id"]
    assert ai.post("/requests", plain(ai, renewed["id"])).status_code == 409


def test_cloud_policy_change_never_expands_standing_scope(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    connection, model, _ = enable(ai, monkeypatch)
    verify(ai, model)
    auth = consent(ai, connection)
    old = ai.owner.client.get(PREFIX + "/cloud-policy").json()["authorization"]["policy"]
    assert ai.post("/endpoints/openrouter", {**old, "daily_usd": "0.45"}).status_code == 201
    verify(ai, model)
    rejected = ai.post("/requests", plain(ai, auth["id"]))
    assert rejected.status_code == 409 and rejected.json()["detail"] == "AI_STANDING_SCOPE_CHANGED"


def test_worker_availability_requires_real_recent_heartbeat_and_recovers(ai: AI) -> None:
    ai.setup()
    connection = ai.owner.client.get(PREFIX + "/connections").json()[0]["id"]
    consent(ai, connection)
    ai.worker.queue.set("ai:worker-heartbeat", str(utcnow().timestamp() - 60), ex=20)
    assert ready(ai)["reason"] == "AI_WORKER_UNAVAILABLE"
    ai.worker.once()
    assert ready(ai)["ready"]


def test_standing_records_immutable_and_worker_cannot_activate_or_revoke(ai: AI) -> None:
    ai.setup()
    connection = ai.owner.client.get(PREFIX + "/connections").json()[0]["id"]
    auth = consent(ai, connection)
    with ai.worker.store.engine.connect() as db:
        assert (
            db.scalar(
                text(
                    "SELECT has_table_privilege(current_user,"
                    "'ai_standing_authorizations','INSERT,UPDATE,DELETE')"
                )
            )
            is False
        )
    with cast(FastAPI, ai.owner.client.app).state.store.session() as db:
        with pytest.raises(DBAPIError):
            db.execute(
                text("UPDATE ai_standing_authorizations SET active=false WHERE id=:id"),
                {"id": UUID(auth["id"])},
            )
        db.rollback()
    # Separate financial execution boundary remains DENY_ALL.
    assert ai.owner.client.get("/api/v1/safety").json()["executor_capability"] == "DENY_ALL"


def test_running_revocation_cannot_publish_an_answer(ai: AI) -> None:
    ai.setup()
    connection = ai.owner.client.get(PREFIX + "/connections").json()[0]["id"]
    auth = consent(ai, connection)
    job = ai.job("/requests", plain(ai, auth["id"]))
    ai.fixture.behavior = "blocked"
    ai.fixture.entered.clear()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(ai.worker.once)
        assert ai.fixture.entered.wait(5)
        assert ai.post("/standing-authorization/revoke", {}).status_code == 200
        ai.fixture.release.set()
        assert future.result(timeout=10)
    observed = ai.owner.client.get(PREFIX + "/requests/" + job["id"]).json()
    assert observed["state"] == "CANCELLED" and observed["output"] is None


def test_standing_does_not_unlock_final_holdout(ai: AI) -> None:
    from test_research_integration import prepared

    ai.setup()
    plan = prepared(ai.owner)
    dataset = plan["datasets"][0]["dataset_id"]
    connection = ai.owner.client.get(PREFIX + "/connections").json()[0]["id"]
    auth = consent(ai, connection, data_categories=["dataset"])
    assert (
        ai.owner.post(
            "/api/v1/research/holdouts",
            {
                "dataset_id": dataset,
                "reason": "Synthetic standing holdout protection",
                "acknowledged_prior_exposure_unknown": True,
            },
        ).status_code
        == 201
    )
    refused = ai.post(
        "/requests", plain(ai, auth["id"], references=[{"kind": "dataset", "id": dataset}])
    )
    assert refused.status_code == 404


def test_standing_authorization_survives_actual_postgres_container_restart() -> None:
    from test_phase1_integration import close_system, create_system, isolated_config

    from packages.ai.settings import Endpoint, GatewaySettings

    isolated = isolated_config()
    database = "p1_standing_persist_" + isolated.run_id
    system = create_system(database, create=isolated.stage == "write")
    try:
        if isolated.stage == "write":
            system.bootstrap()
            system.secret, system.recovery = system.enroll()
            cast(FastAPI, system.client.app).state.ai_config = GatewaySettings(
                endpoints=[
                    Endpoint(
                        id="persist",
                        label="Synthetic persistence fixture",
                        url="http://127.0.0.1:19095",
                        transport="LOOPBACK",
                        private_only_attested=True,
                    )
                ]
            )
            connection = system.post(
                PREFIX + "/connections",
                {
                    "name": "SYNTHETIC_PERSISTENCE_FIXTURE",
                    "endpoint_id": "persist",
                    "provider": "OLLAMA_NATIVE",
                    "policy": {"rights_confirmed": True, "approved_processing": True},
                },
            )
            assert connection.status_code == 201
            response = system.post(
                PREFIX + "/standing-authorization",
                {
                    "connection_ids": [connection.json()["id"]],
                    "roles": ["RESEARCH"],
                    "data_categories": ["documentation"],
                    "operations": ["INFER"],
                    "request_usd": "0.010000",
                    "daily_usd": "0.50",
                    "monthly_usd": "5",
                },
            )
            assert response.status_code == 201
        # The harness stops/starts the actual database container before the verify stage.
        with cast(FastAPI, system.client.app).state.store.session() as db:
            rows = list(db.scalars(select(AIStandingAuthorization)))
            assert len(rows) == 1
            saved = rows[0]
            assert saved.active is True and saved.revision == 1
            assert saved.policy["request_usd"] == "0.010000"
            assert saved.policy["grants"][0]["endpoint_id"] == "persist"
            assert saved.policy["roles"] == ["RESEARCH"]
    finally:
        close_system(system, drop=isolated.stage == "verify")
