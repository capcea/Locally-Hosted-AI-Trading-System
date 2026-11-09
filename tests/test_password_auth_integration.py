"""New product default: real password/session auth without TOTP or forged MFA assertions."""

from collections.abc import Iterator
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from test_phase1_integration import ORIGIN, System, close_system, create_system

from apps.api.main import create_app

pytestmark = pytest.mark.isolated_services


@pytest.fixture
def password_system() -> Iterator[System]:
    system = create_system("p1_password_" + uuid4().hex)
    cast(FastAPI, system.client.app).state.store.engine.dispose()
    system.client.close()
    system.config = system.config.model_copy(update={"auth_mode": "PASSWORD"})
    system.client = TestClient(create_app(system.config))
    try:
        yield system
    finally:
        close_system(system)


def bootstrap(system: System) -> dict[str, Any]:
    token = system.config.auth_bootstrap_token
    assert token is not None
    reply = system.client.post(
        "/api/v1/auth/bootstrap",
        headers={"Origin": ORIGIN},
        json={
            "username": "password-owner",
            "display_name": "Password-only fixture",
            "password": system.password,
            "bootstrap_token": token.get_secret_value(),
        },
    )
    assert reply.status_code == 201
    assert reply.json()["state"] == "FULL" and reply.json()["auth_mode"] == "PASSWORD"
    return cast(dict[str, Any], reply.json())


def test_password_bootstrap_login_no_totp_and_honest_audit(password_system: System) -> None:
    system = password_system
    first = bootstrap(system)
    assert system.client.get("/api/v1/auth/status").json()["auth_mode"] == "PASSWORD"
    account = system.account()
    assert account["data"]["name"] == "Synthetic account"
    assert system.post("/api/v1/auth/mfa/enroll", {}).status_code == 409
    engine = create_engine(system.admin_url)
    try:
        with engine.connect() as db:
            assert db.scalar(text("SELECT mfa_secret FROM users")) is None
            assert db.scalar(text("SELECT mfa_at FROM login_sessions")) is None
            assert db.scalar(text("SELECT bool_or(mfa_verified) FROM audit_events")) is False
    finally:
        engine.dispose()
    assert system.post("/api/v1/auth/logout", {}).status_code == 204
    reply = system.client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"username": "password-owner", "password": system.password},
    )
    assert reply.status_code == 200 and reply.json()["state"] == "FULL"
    assert reply.json()["session_id"] != first["session_id"]
    assert system.client.get("/api/v1/records/accounts").status_code == 200
    # Explicitly restoring the legacy policy must not inherit password-only session authority.
    app = cast(FastAPI, system.client.app)
    app.state.settings = system.config.model_copy(update={"auth_mode": "TOTP"})
    refused = system.client.get("/api/v1/auth/me")
    assert refused.status_code == 401 and refused.headers["X-Auth-Error"] == "SESSION_EXPIRED"


def test_password_reauth_rotates_csrf_and_invalid_password_keeps_session(
    password_system: System,
) -> None:
    system = password_system
    before = bootstrap(system)
    bad = system.post("/api/v1/auth/reauthenticate", {"password": "incorrect password"})
    assert bad.status_code == 401 and bad.headers["X-Auth-Error"] == "REAUTH_INVALID"
    assert system.client.get("/api/v1/auth/me").json()["session_id"] == before["session_id"]
    reply = system.post("/api/v1/auth/reauthenticate", {"password": system.password})
    assert reply.status_code == 200 and reply.json()["state"] == "FULL"
    assert reply.json()["session_id"] != before["session_id"]
    assert reply.json()["csrf_token"] != before["csrf_token"]
    assert (
        system.client.post(
            "/api/v1/auth/sessions/revoke-all",
            headers={"Origin": ORIGIN, "X-CSRF-Token": before["csrf_token"]},
            json={},
        ).status_code
        == 403
    )
    assert system.post("/api/v1/auth/sessions/revoke-all", {}).status_code == 204
    assert system.client.get("/api/v1/auth/me").status_code == 401


def test_password_session_keeps_owner_roles_csrf_and_execution_denial(
    password_system: System,
) -> None:
    system = password_system
    bootstrap(system)
    assert system.client.post("/api/v1/auth/users", json={}).status_code == 403
    user = system.post(
        "/api/v1/auth/users",
        {
            "username": "password-viewer",
            "display_name": "Viewer fixture",
            "password": system.password,
            "role": "VIEWER",
        },
    )
    assert user.status_code == 201
    viewer = TestClient(cast(FastAPI, system.client.app))
    response = viewer.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"username": "password-viewer", "password": system.password},
    )
    assert response.status_code == 200 and response.json()["state"] == "FULL"
    try:
        assert (
            system.post(
                "/api/v1/auth/users",
                {
                    "username": "blocked-user",
                    "display_name": "Blocked",
                    "password": system.password,
                    "role": "VIEWER",
                },
                viewer,
            ).status_code
            == 403
        )
    finally:
        viewer.close()
    assert system.client.get("/api/v1/safety").json()["executor_capability"] == "DENY_ALL"
