"""Actual disposable identity/CSRF/cloud metadata flow. No provider calls or real users."""

from datetime import timedelta
from http.cookies import SimpleCookie
from typing import cast
from uuid import UUID

import pyotp
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, update
from starlette.types import Message, Receive, Scope, Send
from test_phase1_integration import ORIGIN, System
from test_phase1_integration import owner as owner
from test_phase1_integration import system as system

from apps.api.identity.crypto import token_digest
from apps.api.identity.dependencies import COOKIE
from packages.ai.settings import GatewaySettings
from packages.persistence.models import LoginSession, utcnow

pytestmark = pytest.mark.isolated_services
CLOUD = {
    "upstream_provider": "synthetic-fixture",
    "acknowledged_public_cloud": True,
    "acknowledged_upstream_processing": True,
    "acknowledged_cost": True,
    "acknowledged_provider_policy_limits": True,
}


def test_rotated_session_is_committed_before_cookie_headers_are_sent(owner: System) -> None:
    """Observe database visibility at ASGI response.start, before dependency cleanup."""
    previous = owner.client.get("/api/v1/auth/me").json()
    prior_cookie = owner.client.cookies.get(COOKIE)
    visible: list[bool] = []
    engine = create_engine(owner.admin_url)
    app = cast(FastAPI, owner.client.app)

    async def measured(scope: Scope, receive: Receive, send: Send) -> None:
        async def inspect(message: Message) -> None:
            if message["type"] == "http.response.start" and message["status"] == 200:
                for key, value in message.get("headers", []):
                    if key.lower() == b"set-cookie":
                        cookie = SimpleCookie()
                        cookie.load(value.decode())
                        if COOKIE in cookie:
                            with engine.connect() as db:
                                visible.append(
                                    db.scalar(
                                        select(LoginSession.id).where(
                                            LoginSession.token_hash
                                            == token_digest(cookie[COOKIE].value)
                                        )
                                    )
                                    is not None
                                )
            await send(message)

        await app(scope, receive, inspect)

    client = TestClient(measured)
    try:
        assert prior_cookie is not None
        client.cookies.set(COOKIE, prior_cookie)
        response = client.post(
            "/api/v1/auth/reauthenticate",
            headers={
                "Origin": ORIGIN,
                "X-CSRF-Token": previous["csrf_token"],
            },
            json={
                "password": owner.password,
                "code": pyotp.TOTP(owner.secret).at(utcnow() + timedelta(seconds=30)),
            },
        )
        assert response.status_code == 200
        assert visible == [True], (
            "New session must be committed before the browser can use its cookie"
        )
    finally:
        client.close()
        engine.dispose()


def age(owner: System, field: str) -> None:
    session = owner.client.get("/api/v1/auth/me").json()
    assert field in {"mfa_at", "idle_expires_at", "expires_at"}
    engine = create_engine(owner.admin_url)
    try:
        with engine.begin() as db:
            db.execute(
                update(LoginSession)
                .where(LoginSession.id == UUID(session["session_id"]))
                .values({field: utcnow() - timedelta(minutes=6)})
            )
    finally:
        engine.dispose()


def test_invalid_step_up_keeps_session_and_recent_refusal_precedes_cloud_creation(
    owner: System,
) -> None:
    cast(FastAPI, owner.client.app).state.ai_config = GatewaySettings(openrouter_enabled=True)
    before = owner.client.get("/api/v1/auth/me").json()
    age(owner, "mfa_at")
    refused = owner.post("/api/v1/ai/endpoints/openrouter", CLOUD)
    assert refused.status_code == 403
    assert refused.headers["X-Auth-Error"] == "MFA_RECENT_REQUIRED"
    assert refused.json()["detail"] == "Recent MFA verification required"
    invalid = owner.post(
        "/api/v1/auth/reauthenticate", {"password": owner.password, "code": "bad-code"}
    )
    assert invalid.status_code == 401 and invalid.headers["X-Auth-Error"] == "MFA_INVALID"
    me = owner.client.get("/api/v1/auth/me")
    assert me.status_code == 200 and me.json()["state"] == "FULL"
    unchanged = before["session_id"] == me.json()["session_id"]
    assert unchanged
    assert owner.client.get("/api/v1/ai/cloud-policy").json()["authorization"] is None


def test_step_up_rotates_cookie_csrf_revokes_old_session_and_authorizes_cloud(
    owner: System,
) -> None:
    cast(FastAPI, owner.client.app).state.ai_config = GatewaySettings(openrouter_enabled=True)
    old = owner.client.get("/api/v1/auth/me").json()
    old_cookie = owner.client.cookies.get(COOKIE)
    age(owner, "mfa_at")
    code = pyotp.TOTP(owner.secret).at(utcnow() + timedelta(seconds=30))
    stepped = owner.post("/api/v1/auth/reauthenticate", {"password": owner.password, "code": code})
    assert stepped.status_code == 200
    new = stepped.json()
    changed = (
        new["session_id"] != old["session_id"]
        and new["csrf_token"] != old["csrf_token"]
        and owner.client.cookies.get(COOKIE) != old_cookie
    )
    assert changed, "Step-up must rotate session, cookie and CSRF"
    flags = {
        flag: flag in stepped.headers.get("set-cookie", "").lower()
        for flag in ("httponly", "samesite=strict", "path=/")
    }
    assert all(flags.values())
    expired = TestClient(cast(FastAPI, owner.client.app))
    try:
        assert old_cookie is not None
        expired.cookies.set(COOKIE, old_cookie)
        assert expired.get("/api/v1/auth/me").status_code == 401
    finally:
        expired.close()
    wrong_csrf = owner.client.post(
        "/api/v1/ai/endpoints/openrouter",
        json=CLOUD,
        headers={"Origin": ORIGIN, "X-CSRF-Token": old["csrf_token"]},
    )
    assert wrong_csrf.status_code == 403 and wrong_csrf.headers["X-Auth-Error"] == "CSRF_FAILED"
    assert owner.client.get("/api/v1/auth/me").status_code == 200
    assert owner.post("/api/v1/ai/endpoints/openrouter", CLOUD).status_code == 201
    assert owner.client.get("/api/v1/audit/verify").json()["valid"]


@pytest.mark.parametrize("field", ["idle_expires_at", "expires_at"])
def test_expired_session_requires_password_then_mfa_without_reusing_cookie(
    owner: System, field: str
) -> None:
    old = owner.client.get("/api/v1/auth/me").json()
    age(owner, field)
    me = owner.client.get("/api/v1/auth/me")
    assert me.status_code == 401 and me.headers["X-Auth-Error"] == "SESSION_EXPIRED"
    rejected = owner.client.post(
        "/api/v1/auth/reauthenticate",
        json={"password": owner.password, "code": "bad-code"},
        headers={"Origin": ORIGIN, "X-CSRF-Token": old["csrf_token"]},
    )
    assert rejected.status_code == 401 and rejected.headers["X-Auth-Error"] == "SESSION_EXPIRED"
    login = owner.client.post(
        "/api/v1/auth/login",
        json={"username": "fixture-owner", "password": owner.password},
        headers={"Origin": ORIGIN},
    )
    assert login.status_code == 200 and login.json()["state"] == "MFA"
    assert owner.client.get("/api/v1/records/accounts").status_code == 403
    invalid = owner.post("/api/v1/auth/mfa/verify", {"code": "bad-code"})
    assert invalid.status_code == 401 and invalid.headers["X-Auth-Error"] == "MFA_INVALID"
    assert owner.client.get("/api/v1/auth/me").json()["state"] == "MFA"
    valid = owner.post(
        "/api/v1/auth/mfa/verify",
        {"code": pyotp.TOTP(owner.secret).at(utcnow() + timedelta(seconds=30))},
    )
    assert valid.status_code == 200 and valid.json()["state"] == "FULL"
    assert owner.client.get("/api/v1/records/accounts").status_code == 200


def test_bad_codes_are_rate_limited_without_logging_out_or_enrolling_again(owner: System) -> None:
    results = [
        owner.post(
            "/api/v1/auth/reauthenticate", {"password": owner.password, "code": "bad-code"}
        ).status_code
        for _ in range(11)
    ]
    assert 401 in results and results[-1] == 429
    assert owner.client.get("/api/v1/auth/me").json()["state"] == "FULL"
    assert owner.post("/api/v1/auth/mfa/enroll", {}).status_code == 409


@pytest.mark.parametrize("role", ["VIEWER", "OPERATOR"])
def test_step_up_does_not_grant_owner_role_or_cross_owner_cloud_policy(
    owner: System, role: str
) -> None:
    cast(FastAPI, owner.client.app).state.ai_config = GatewaySettings(openrouter_enabled=True)
    created = owner.post(
        "/api/v1/auth/users",
        {
            "username": "limited-peer",
            "display_name": "Peer",
            "password": owner.password,
            "role": role,
        },
    )
    assert created.status_code == 201
    peer = TestClient(cast(FastAPI, owner.client.app))
    try:
        assert (
            peer.post(
                "/api/v1/auth/login",
                json={"username": "limited-peer", "password": owner.password},
                headers={"Origin": ORIGIN},
            ).status_code
            == 200
        )
        owner.enroll(peer)
        denied = owner.post("/api/v1/ai/endpoints/openrouter", CLOUD, peer)
        assert denied.status_code == 403 and denied.headers["X-Auth-Error"] == "ROLE_REQUIRED"
        assert peer.get("/api/v1/ai/cloud-policy").json()["authorization"] is None
    finally:
        peer.close()


def test_wrong_origin_and_csrf_do_not_expire_valid_session(owner: System) -> None:
    for headers in (
        {"Origin": ORIGIN, "X-CSRF-Token": "stale"},
        {**owner.csrf(), "Origin": "http://localhost:5173"},
    ):
        denied = owner.client.post(
            "/api/v1/auth/reauthenticate",
            json={"password": owner.password, "code": "bad-code"},
            headers=headers,
        )
        assert denied.status_code == 403
        assert owner.client.get("/api/v1/auth/me").status_code == 200
