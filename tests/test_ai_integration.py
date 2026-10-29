"""Actual isolated PostgreSQL/Redis and synthetic HTTP; never real model acceptance."""

import base64
import hashlib
import os
import subprocess
import sys
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from redis.exceptions import NoPermissionError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from test_market_integration import configure_market
from test_phase1_integration import (
    System,
    close_system,
    create_system,
    isolated_config,
)

from apps.api.main import create_app
from packages.ai.settings import Endpoint, GatewaySettings
from packages.ai.worker import Worker
from packages.persistence.models import utcnow
from scripts.provision_ai import provision_database, provision_queue
from testing.ai_fixture import NAME, Fixture, running_fixture

pytestmark = pytest.mark.isolated_services
PREFIX = "/api/v1/ai"


@dataclass
class AI:
    owner: System
    worker: Worker
    fixture: Fixture
    config: GatewaySettings

    def post(self, path: str, body: dict[str, Any]) -> Any:
        return self.owner.post(PREFIX + path, body)

    def job(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        response = self.post(path, body)
        assert response.status_code == 202
        return cast(dict[str, Any], response.json())

    def finish(self, job: dict[str, Any]) -> dict[str, Any]:
        assert self.worker.once()
        response = self.owner.client.get(PREFIX + "/requests/" + job["id"])
        assert response.status_code == 200
        return cast(dict[str, Any], response.json())

    def setup(self) -> str:
        response = self.post(
            "/connections",
            {
                "name": "SYNTHETIC_HTTP_FIXTURE",
                "endpoint_id": "fixture",
                "provider": "OLLAMA_NATIVE",
                "policy": {"rights_confirmed": True, "approved_processing": True},
            },
        )
        assert response.status_code == 201
        connection = response.json()["id"]
        discovered = self.finish(
            self.job(f"/connections/{connection}/discover", {"key": uuid4().hex})
        )
        assert discovered["state"] == "SUCCEEDED", discovered["error"]
        response = self.post(
            "/models", {"connection_id": connection, "name": NAME, "context_ceiling": 8192}
        )
        assert response.status_code == 201
        model = str(response.json()["id"])
        before = self.post("/routes", {"role": "RESEARCH", "model_id": model})
        assert before.status_code == 409
        probed = self.finish(self.job(f"/models/{model}/probe", {"key": uuid4().hex}))
        assert probed["state"] == "SUCCEEDED", probed["error"]
        for role in ("RESEARCH", "CODING", "CRITIC", "LIGHTWEIGHT"):
            assert self.post("/routes", {"role": role, "model_id": model}).status_code == 201
        return model

    def question(self, **updates: Any) -> dict[str, Any]:
        return {
            "key": uuid4().hex,
            "question": "Ce dovezi lipsesc pentru această ipoteză?",
            "role": "RESEARCH",
            "parameters": {"context_tokens": 8192},
            "references": [{"kind": "documentation", "id": "research-limits-v1"}],
            "processing_acknowledged": True,
            "retain_structured_output": True,
            **updates,
        }


@pytest.fixture
def ai() -> Iterator[AI]:
    isolated = isolated_config()
    system = create_system(f"p1_ai_{uuid4().hex}")
    configure_market(system, "ai-context-" + uuid4().hex)
    password = hashlib.sha256(
        ("ai-worker:" + isolated.storage_password.get_secret_value()).encode()
    ).hexdigest()
    database = provision_database(system.admin_url, password)
    queue_admin = isolated.redis_url
    provision_queue(queue_admin, "ai_worker", password)
    provision_queue(queue_admin, "ai_api", password)
    key = base64.urlsafe_b64encode(
        hashlib.sha256(("ai-content:" + password).encode()).digest()
    ).decode()
    with running_fixture() as fixture:
        common = GatewaySettings(
            endpoints=[
                Endpoint(
                    id="fixture",
                    label="Synthetic HTTP fixture",
                    url=fixture.url,
                    transport="LOOPBACK",
                    private_only_attested=True,
                )
            ],
            data_key=SecretStr(key),
            database_url=SecretStr(database),
            redis_url=SecretStr(f"redis://ai_worker:{password}@127.0.0.1:{isolated.redis_port}/0"),
        )
        api_config = common.model_copy(
            update={
                "database_url": None,
                "redis_url": SecretStr(
                    f"redis://ai_api:{password}@127.0.0.1:{isolated.redis_port}/0"
                ),
            }
        )
        old_client = system.client
        cast(FastAPI, old_client.app).state.store.engine.dispose()
        old_client.close()
        system.client = TestClient(create_app(system.config, api_config))
        system.bootstrap()
        system.secret, system.recovery = system.enroll()
        worker = Worker(common)
        try:
            yield AI(system, worker, fixture, common)
        finally:
            worker.close()
            close_system(system)


def test_registry_real_roundtrip_idempotency_and_scoped_worker(ai: AI) -> None:
    endpoints = ai.owner.client.get(PREFIX + "/endpoints")
    assert endpoints.status_code == 200
    assert endpoints.json() == [
        {"id": "fixture", "label": "Synthetic HTTP fixture", "transport": "LOOPBACK"}
    ]
    ai.setup()
    body = ai.question()
    job = ai.job("/requests", body)
    assert ai.job("/requests", body)["id"] == job["id"]
    assert ai.post("/requests", {**body, "question": "Different payload"}).status_code == 409
    result = ai.finish(job)
    assert result["state"] == "SUCCEEDED", result["error"]
    assert result["output"]["verified"] is False
    assert result["metadata"]["trading_authority"] is False
    assert "PRIVATE_REASONING" not in str(result)
    assert ai.owner.client.get(PREFIX + "/requests/" + job["id"] + "/wait").status_code == 200
    with ai.worker.store.engine.connect() as db:
        assert db.scalar(text("SELECT has_table_privilege(current_user,'users','SELECT')")) is False
        assert (
            db.scalar(
                text("SELECT has_table_privilege(current_user,'risk_profile_versions','UPDATE')")
            )
            is False
        )
        assert (
            db.scalar(
                text("SELECT has_table_privilege(current_user,'research_experiments','SELECT')")
            )
            is False
        )
        assert (
            db.scalar(
                text("SELECT count(*) FROM ai_artifacts WHERE request_id=:id"), {"id": job["id"]}
            )
            == 1
        )
    with pytest.raises(NoPermissionError):
        ai.worker.queue.get("research:forbidden")
    with pytest.raises(NoPermissionError):
        ai.worker.queue.config_get("*")
    for forbidden in (
        "SELECT password_hash FROM users",
        "SELECT * FROM risk_profile_versions",
        "UPDATE ai_connections SET enabled=false",
    ):
        with ai.worker.store.engine.connect() as db, pytest.raises(DBAPIError):
            db.execute(text(forbidden))
    assert ai.owner.client.get("/api/v1/audit/verify").json()["valid"]


def test_cancel_queued_running_and_reject_malformed_outputs(ai: AI) -> None:
    ai.setup()
    queued = ai.job("/requests", ai.question())
    requested = ai.post(f"/requests/{queued['id']}/cancel", {})
    assert requested.status_code == 202 and requested.json()["state"] == "QUEUED"
    assert ai.finish(queued)["state"] == "CANCELLED"
    running = ai.job("/requests", ai.question())
    ai.fixture.behavior = "blocked"
    ai.fixture.entered.clear()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(ai.worker.once)
        assert ai.fixture.entered.wait(5)
        response = ai.post(f"/requests/{running['id']}/cancel", {})
        assert response.status_code == 202 and response.json()["state"] == "RUNNING"
        ai.fixture.release.set()
        assert future.result(timeout=10)
    assert ai.owner.client.get(PREFIX + "/requests/" + running["id"]).json()["state"] == "CANCELLED"
    for behavior in ("invalid", "invented", "tool", "unknown"):
        ai.fixture.behavior = behavior
        result = ai.finish(ai.job("/requests", ai.question()))
        assert result["state"] == ("UNKNOWN" if behavior == "unknown" else "FAILED")
        assert result["output"] is None


def test_revocation_privacy_erasure_and_lease_fencing(ai: AI) -> None:
    ai.setup()
    job = ai.job("/requests", ai.question())
    engine = create_engine(ai.owner.admin_url)
    try:
        with engine.begin() as db:
            db.execute(
                text(
                    "UPDATE ai_jobs SET state='RUNNING',attempts=1,worker_token=:token,"
                    "dispatched_at=:old,lease_until=:old WHERE request_id=:id"
                ),
                {"id": job["id"], "token": uuid4(), "old": utcnow() - timedelta(seconds=60)},
            )
        count = ai.fixture.seen
        assert ai.finish(job)["state"] == "UNKNOWN"
        assert ai.fixture.seen == count
        completed = ai.finish(ai.job("/requests", ai.question()))
        assert completed["state"] == "SUCCEEDED"
        response = ai.owner.client.delete(
            PREFIX + f"/requests/{completed['id']}/content", headers=ai.owner.csrf()
        )
        assert response.status_code == 204
        assert ai.owner.client.get(PREFIX + "/requests/" + completed["id"]).json()["output"] is None
        revoked = ai.job("/requests", ai.question())
        assert ai.owner.post("/api/v1/auth/sessions/revoke-all", {}).status_code == 204
        assert ai.worker.once()
        with engine.connect() as db:
            assert (
                db.scalar(
                    text("SELECT state FROM ai_jobs WHERE request_id=:id"), {"id": revoked["id"]}
                )
                == "FAILED"
            )
    finally:
        engine.dispose()


def test_role_csrf_and_context_isolation(ai: AI) -> None:
    ai.setup()
    viewer, _ = ai.owner.peer("ai-viewer", "VIEWER")
    try:
        response = ai.owner.post(PREFIX + "/requests", ai.question(), viewer)
        assert response.status_code == 403
        assert ai.owner.client.post(PREFIX + "/requests", json=ai.question()).status_code == 403
        job = ai.job("/requests", ai.question())
        assert viewer.get(PREFIX + "/requests/" + job["id"]).status_code == 404
        for reference in (
            {"kind": "dataset", "id": str(uuid4())},
            {"kind": "documentation", "id": "../../secrets"},
        ):
            assert ai.post("/requests", ai.question(references=[reference])).status_code in {
                404,
                422,
            }
    finally:
        cast(FastAPI, viewer.app).state.store.engine.dispose()
        viewer.close()


def test_owner_quota_and_no_automatic_remote_fallback(ai: AI) -> None:
    ai.setup()
    app = cast(FastAPI, ai.owner.client.app)
    app.state.ai_config = app.state.ai_config.model_copy(update={"hourly_role_limit": 1})
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(ai.post, "/requests", ai.question()) for _ in range(2)]
        assert sorted(f.result(timeout=10).status_code for f in futures) == [202, 429]


def test_holdout_seal_refuses_active_disclosure_and_invalidates_cached_context(ai: AI) -> None:
    from test_research_integration import prepared

    ai.setup()
    plan = prepared(ai.owner)
    dataset = plan["datasets"][0]["dataset_id"]
    cached = ai.finish(
        ai.job("/requests", ai.question(references=[{"kind": "dataset", "id": dataset}]))
    )
    assert cached["state"] == "SUCCEEDED"
    running = ai.job("/requests", ai.question(references=[{"kind": "dataset", "id": dataset}]))
    ai.fixture.behavior = "blocked"
    ai.fixture.entered.clear()
    seal_body = {
        "dataset_id": dataset,
        "reason": "Synthetic final holdout fixture",
        "acknowledged_prior_exposure_unknown": True,
    }
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(ai.worker.once)
        assert ai.fixture.entered.wait(5)
        busy = ai.owner.post("/api/v1/research/holdouts", seal_body)
        assert busy.status_code == 409
        assert busy.json()["detail"] == "AI_CONTEXT_BUSY_CANCEL_OR_WAIT_BEFORE_SEALING"
        ai.fixture.release.set()
        assert future.result(timeout=10)
    queued = ai.job("/requests", ai.question(references=[{"kind": "dataset", "id": dataset}]))
    assert ai.owner.post("/api/v1/research/holdouts", seal_body).status_code == 201
    assert ai.finish(queued)["state"] == "CANCELLED"
    for ref in ({"kind": "dataset", "id": dataset}, {"kind": "ai_artifact", "id": cached["id"]}):
        response = ai.post("/requests", ai.question(references=[ref]))
        assert response.status_code == 404
    hidden = ai.owner.client.get(PREFIX + "/requests/" + running["id"]).json()
    assert hidden["context_available"] is False and hidden["output"] is None


def test_actual_worker_sigkill_after_dispatch_is_unknown_and_not_repeated(ai: AI) -> None:
    ai.setup()
    job = ai.job("/requests", ai.question())
    ai.fixture.behavior = "blocked"
    ai.fixture.entered.clear()
    assert ai.config.database_url and ai.config.redis_url and ai.config.data_key
    environment = {k: v for k, v in os.environ.items() if k in {"PATH", "LANG", "TMPDIR"}}
    environment.update(
        {
            "AI_DATABASE_URL": ai.config.database_url.get_secret_value(),
            "AI_REDIS_URL": ai.config.redis_url.get_secret_value(),
            "AI_DATA_KEY": ai.config.data_key.get_secret_value(),
            "AI_ENDPOINTS": "[" + ai.config.endpoints[0].model_dump_json() + "]",
        }
    )
    process = subprocess.Popen(  # noqa: S603 -- fixed worker; minimal env; no shell
        [sys.executable, "-m", "scripts.ai_worker", "--once"],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        assert ai.fixture.entered.wait(5)
        process.kill()
        assert process.wait(timeout=5) != 0
        seen = ai.fixture.seen
        ai.fixture.release.set()
        engine = create_engine(ai.owner.admin_url)
        try:
            # Advance only the disposable lease fixture, avoiding a wall-clock sleep.
            with engine.begin() as db:
                db.execute(
                    text("UPDATE ai_jobs SET lease_until=:old WHERE request_id=:id"),
                    {"old": utcnow() - timedelta(seconds=1), "id": job["id"]},
                )
            assert ai.finish(job)["state"] == "UNKNOWN"
            assert ai.fixture.seen == seen
        finally:
            engine.dispose()
    finally:
        ai.fixture.release.set()
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def test_invalid_ai_config_or_key_reuse_disables_ai_without_unmounting_safety(
    ai: AI, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AI_DATA_KEY", "invalid-synthetic-configuration")
    for ai_config in (
        None,
        ai.config.model_copy(update={"data_key": ai.owner.config.auth_encryption_key}),
    ):
        app = create_app(ai.owner.config, ai_config)
        with TestClient(app) as client:
            client.cookies.update(ai.owner.client.cookies)
            assert client.get("/api/v1/auth/me").json()["state"] == "FULL"
            assert client.get("/api/v1/safety").json()["executor_capability"] == "DENY_ALL"
            status = client.get(PREFIX + "/status")
            assert status.status_code == 200 and status.json()["configured"] is False
            assert status.json()["configuration_error"] == "AI_CONFIGURATION_INVALID"
