"""Actual default password policy keeps inference isolated and never fabricates MFA."""

from typing import cast
from uuid import uuid4

import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from test_ai_integration import AI
from test_ai_integration import ai as ai
from test_phase1_integration import ORIGIN

pytestmark = pytest.mark.isolated_services


def test_password_policy_keeps_existing_enrollment_and_real_worker_path(ai: AI) -> None:
    app = cast(FastAPI, ai.owner.client.app)
    app.state.settings = ai.owner.config.model_copy(update={"auth_mode": "PASSWORD"})
    reply = ai.owner.client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"username": "fixture-owner", "password": ai.owner.password},
    )
    assert (
        reply.status_code == 200
        and reply.json()["state"] == "FULL"
        and reply.json()["auth_mode"] == "PASSWORD"
    )
    engine = create_engine(ai.owner.admin_url)
    try:
        with engine.connect() as db:
            assert db.scalar(text("SELECT mfa_secret IS NOT NULL FROM users")) is True
            assert (
                db.scalar(
                    text("SELECT mfa_at IS NULL FROM login_sessions WHERE auth_policy='PASSWORD'")
                )
                is True
            )
    finally:
        engine.dispose()
    ai.setup()
    job = ai.job("/requests", ai.question())
    engine = create_engine(ai.owner.admin_url)
    try:
        legacy = uuid4()
        with engine.begin() as db:
            # Model the pre-migration request format without creating another executable job.
            db.execute(
                text(
                    "INSERT INTO ai_requests "
                    "(id,owner_id,key,digest,kind,role,specification,"
                    "expires_at,retain_until,created_at) "
                    "SELECT :legacy,owner_id,:key,digest,kind,role,"
                    "CAST(specification AS jsonb)-'auth_policy',expires_at,retain_until,created_at "
                    "FROM ai_requests WHERE id=:id"
                ),
                {"legacy": legacy, "key": uuid4().hex, "id": job["id"]},
            )
        with ai.worker.store.engine.connect() as db:
            assert (
                db.scalar(
                    text("SELECT authorized FROM ai_request_authority WHERE request_id=:id"),
                    {"id": job["id"]},
                )
                is True
            )
            assert (
                db.scalar(
                    text("SELECT authorized FROM ai_request_authority WHERE request_id=:id"),
                    {"id": legacy},
                )
                is False
            )
    finally:
        engine.dispose()
    result = ai.finish(job)
    assert result["state"] == "SUCCEEDED", result["error"]
    assert result["metadata"]["trading_authority"] is False
    assert ai.owner.client.get("/api/v1/safety").json()["executor_capability"] == "DENY_ALL"


def test_strategy_lab_research_document_uses_actual_registry_and_real_fixture_transport(
    ai: AI,
) -> None:
    from uuid import UUID

    from apps.api.ai.context import ContextScope, assemble
    from packages.ai.contracts import ContextReference
    from packages.ai.prompts import digest
    from packages.research.strategies import NAMES, definition

    ai.setup()
    question = ai.question()
    question["references"] = [{"kind": "documentation", "id": "strategy-lab-v1"}]
    job = ai.job("/requests", question)
    result = ai.finish(job)
    assert result["state"] == "SUCCEEDED", result["error"]
    assert result["output"]["verified"] is False
    app = cast(FastAPI, ai.owner.client.app)
    me = ai.owner.client.get("/api/v1/auth/me").json()
    with app.state.store.session() as db:
        context = assemble(
            ContextScope(db, UUID(me["user"]["id"])),
            [ContextReference(kind="documentation", id="strategy-lab-v1")],
            ai.worker.config,
        )
    assert context[0]["untrusted_content"] is True
    assert {item["id"] for item in context[0]["reviewed_baselines"]} == set(NAMES)
    assert all(
        item["version"] == definition(item["id"])["version"]
        for item in context[0]["reviewed_baselines"]
    )
    assert context[0]["registry_sha256"] == digest([definition(name) for name in NAMES])
