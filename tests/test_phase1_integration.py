"""Phase 1 acceptance against native disposable PostgreSQL, never ambient databases."""

import base64
import hashlib
import os
import secrets
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import psycopg
import pyotp
import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import sql
from pydantic import SecretStr
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ProgrammingError

from apps.api.config import Settings
from apps.api.identity.dependencies import COOKIE, Principal
from apps.api.main import create_app
from scripts.integration_services import IsolatedServices
from scripts.provision_runtime import provision_runtime

pytestmark = pytest.mark.isolated_services
ORIGIN = "http://testserver"


@dataclass(repr=False)
class System:
    admin_url: str
    runtime_url: str
    config: Settings
    client: TestClient
    password: str = field(default_factory=lambda: secrets.token_urlsafe(24))
    secret: str = ""
    recovery: list[str] = field(default_factory=list)

    def csrf(self, client: TestClient | None = None) -> dict[str, str]:
        client = client or self.client
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        return {"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]}

    def post(self, path: str, data: dict[str, Any], client: TestClient | None = None) -> Any:
        target = client or self.client
        return target.post(path, json=data, headers=self.csrf(target))

    def enroll(self, client: TestClient | None = None) -> tuple[str, list[str]]:
        target = client or self.client
        started = self.post("/api/v1/auth/mfa/enroll", {}, target)
        assert started.status_code == 200
        secret = started.json()["secret"]
        confirmed = self.post(
            "/api/v1/auth/mfa/confirm", {"code": pyotp.TOTP(secret).now()}, target
        )
        assert confirmed.status_code == 200
        assert confirmed.json()["session"]["state"] == "FULL"
        return secret, confirmed.json()["recovery_codes"]

    def bootstrap(self) -> None:
        token = self.config.auth_bootstrap_token
        assert token is not None
        response = self.client.post(
            "/api/v1/auth/bootstrap",
            headers={"Origin": ORIGIN},
            json={
                "username": "fixture-owner",
                "display_name": "Synthetic test owner",
                "password": self.password,
                "bootstrap_token": token.get_secret_value(),
            },
        )
        assert response.status_code == 201
        assert response.json()["state"] == "ENROLLMENT"

    def account(
        self, name: str = "Synthetic account", client: TestClient | None = None
    ) -> dict[str, Any]:
        response = self.post(
            "/api/v1/records/accounts",
            {
                "kind": "accounts",
                "name": name,
                "currency": "USD",
                "initial_capital": "25000.12345678",
                "source": "SYNTHETIC_TEST_FIXTURE",
            },
            client,
        )
        assert response.status_code == 201
        return dict(response.json())

    def peer(self, username: str, role: str) -> tuple[TestClient, str]:
        password = secrets.token_urlsafe(24)
        result = self.post(
            "/api/v1/auth/users",
            {
                "username": username,
                "display_name": "Fixture peer",
                "password": password,
                "role": role,
            },
        )
        assert result.status_code == 201
        peer = TestClient(create_app(self.config))
        response = peer.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={"username": username, "password": password},
        )
        assert response.status_code == 200
        self.enroll(peer)
        return peer, result.json()["id"]


def isolated_config() -> IsolatedServices:
    name = os.environ.get("PHASE0_TEST_CONFIG")
    if not name:
        pytest.fail("BLOCKED: run via make integration-services")
    return IsolatedServices.model_validate_json(Path(name).read_bytes())


def admin_connection(url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(
        make_url(url)
        .set(drivername="postgresql", database="postgres")
        .render_as_string(hide_password=False),
        autocommit=True,
    )


def create_system(database: str, *, create: bool = True) -> System:
    isolated = isolated_config()
    if create:
        with admin_connection(isolated.database_url) as connection:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    admin_url = (
        make_url(isolated.database_url).set(database=database).render_as_string(hide_password=False)
    )
    config = Config("alembic.ini")
    config.attributes["database_url"] = admin_url
    if create:
        command.upgrade(config, "head")
    runtime_url = provision_runtime(admin_url, isolated.storage_password.get_secret_value())
    encryption = base64.urlsafe_b64encode(
        hashlib.sha256(isolated.storage_password.get_secret_value().encode()).digest()
    ).decode()
    settings = Settings(
        _env_file=None,
        app_environment="test",
        database_url=SecretStr(runtime_url),
        auth_encryption_key=SecretStr(encryption),
        auth_bootstrap_token=isolated.storage_password,
        auth_origins=[ORIGIN],
        auth_cookie_secure=False,
    )
    client = TestClient(create_app(settings))
    return System(admin_url, runtime_url, settings, client)


def close_system(system: System, *, drop: bool = True) -> None:
    cast(FastAPI, system.client.app).state.store.engine.dispose()
    system.client.close()
    if drop:
        with admin_connection(system.admin_url) as connection:
            database = make_url(system.admin_url).database
            assert database is not None and database.startswith("p1_")
            connection.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database))
            )


@pytest.fixture
def system() -> Iterator[System]:
    instance = create_system(f"p1_{uuid4().hex}")
    try:
        yield instance
    finally:
        close_system(instance)


@pytest.fixture
def owner(system: System) -> System:
    system.bootstrap()
    system.secret, system.recovery = system.enroll()
    return system


def test_bootstrap_is_single_use_and_mfa_is_mandatory(system: System) -> None:
    assert system.client.get("/api/v1/auth/status").json()["initialized"] is False
    system.bootstrap()
    assert system.client.get("/api/v1/records/accounts").status_code == 403
    token = system.config.auth_bootstrap_token
    assert token is not None
    response = system.client.post(
        "/api/v1/auth/bootstrap",
        headers={"Origin": ORIGIN},
        json={
            "username": "second-owner",
            "display_name": "Fixture",
            "password": system.password,
            "bootstrap_token": token.get_secret_value(),
        },
    )
    assert response.status_code == 409
    system.enroll()
    assert system.client.get("/api/v1/records/accounts").status_code == 200


def test_mfa_replay_login_logout_and_session_rotation(owner: System) -> None:
    old = owner.client.cookies.get(COOKIE)
    assert owner.post("/api/v1/auth/logout", {}).status_code == 204
    assert owner.client.get("/api/v1/auth/me").status_code == 401
    login = owner.client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"username": "fixture-owner", "password": owner.password},
    )
    assert login.status_code == 200 and login.json()["state"] == "MFA"
    pending = owner.client.cookies.get(COOKIE)
    assert pending != old
    assert (
        owner.post("/api/v1/auth/mfa/verify", {"code": pyotp.TOTP(owner.secret).now()}).status_code
        == 401
    )
    code = pyotp.TOTP(owner.secret).at(datetime.now(UTC) + timedelta(seconds=30))
    assert owner.post("/api/v1/auth/mfa/verify", {"code": code}).status_code == 200
    assert owner.client.cookies.get(COOKIE) != pending
    cookie = owner.client.cookies.get(COOKIE)
    assert cookie is not None
    with create_engine(owner.admin_url).connect() as connection:
        stored = (
            connection.execute(
                text("SELECT token_hash FROM login_sessions WHERE revoked_at IS NULL")
            )
            .scalars()
            .all()
        )
        assert cookie not in stored
    assert owner.client.get("/api/v1/audit/verify").json()["valid"] is True


def test_recovery_revokes_sessions_and_requires_new_enrollment(owner: System) -> None:
    owner.client.cookies.clear()
    response = owner.client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"username": "fixture-owner", "password": owner.password},
    )
    assert response.status_code == 200
    recovery = owner.post("/api/v1/auth/mfa/recover", {"code": owner.recovery[0]})
    assert recovery.status_code == 200 and recovery.json()["state"] == "ENROLLMENT"
    assert owner.client.get("/api/v1/records/accounts").status_code == 403
    owner.enroll()
    assert owner.client.get("/api/v1/records/accounts").status_code == 200
    owner.client.cookies.clear()
    assert (
        owner.client.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={"username": "fixture-owner", "password": owner.password},
        ).status_code
        == 200
    )
    assert owner.post("/api/v1/auth/mfa/recover", {"code": owner.recovery[0]}).status_code == 401


def test_session_expiry_and_global_revocation(owner: System) -> None:
    assert owner.post("/api/v1/auth/sessions/revoke-all", {}).status_code == 204
    assert owner.client.get("/api/v1/auth/me").status_code == 401
    owner.client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"username": "fixture-owner", "password": owner.password},
    )
    with create_engine(owner.admin_url).begin() as connection:
        connection.execute(
            text("UPDATE login_sessions SET expires_at = :expired"),
            {"expired": datetime.now(UTC) - timedelta(seconds=1)},
        )
    assert owner.client.get("/api/v1/auth/me").status_code == 401


def test_csrf_origin_and_bruteforce_are_enforced(owner: System) -> None:
    payload = {"kind": "accounts", "name": "Rejected", "currency": "USD", "initial_capital": "1"}
    assert owner.client.post("/api/v1/records/accounts", json=payload).status_code == 403
    headers = owner.csrf()
    headers["Origin"] = "https://attacker.invalid"
    assert (
        owner.client.post("/api/v1/records/accounts", json=payload, headers=headers).status_code
        == 403
    )
    assert owner.client.get("/api/v1/records/accounts").json()["total"] == 0
    results = [
        owner.client.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={"username": "unknown-fixture", "password": "wrong"},
        ).status_code
        for _ in range(11)
    ]
    assert results[:10] == [401] * 10 and results[10] == 429


def test_cross_user_account_references_and_role_denial(owner: System) -> None:
    account = owner.account()
    peer, _ = owner.peer("other-operator", "OPERATOR")
    try:
        assert peer.get(f"/api/v1/records/accounts/{account['id']}").status_code == 404
        assert peer.get("/api/v1/records/accounts").json()["total"] == 0
        denied = owner.post(
            "/api/v1/records/brokers",
            {"kind": "brokers", "name": "Denied", "account_id": account["id"], "adapter": "MT5"},
            peer,
        )
        assert denied.status_code == 404
        assert peer.get("/api/v1/auth/users").status_code == 403
        assert owner.account("Peer-owned fixture", peer)["owner_id"] != account["owner_id"]
    finally:
        cast(FastAPI, peer.app).state.store.engine.dispose()
        peer.close()
    viewer, _ = owner.peer("other-viewer", "VIEWER")
    try:
        assert owner.post("/api/v1/records/accounts", account["data"], viewer).status_code == 403
    finally:
        cast(FastAPI, viewer.app).state.store.engine.dispose()
        viewer.close()


def test_concurrent_revisions_and_transactional_audit(
    owner: System, monkeypatch: pytest.MonkeyPatch
) -> None:
    account = owner.account()
    headers, cookie = owner.csrf(), owner.client.cookies.get(COOKIE)

    def mutate(name: str) -> int:
        with TestClient(create_app(owner.config)) as client:
            client.cookies.set(COOKIE, cookie or "")
            response = client.put(
                f"/api/v1/records/accounts/{account['id']}?expected_revision=1",
                json={**account["data"], "name": name},
                headers=headers,
            )
            cast(FastAPI, client.app).state.store.engine.dispose()
            return int(response.status_code)

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(mutate, ["First fixture", "Second fixture"])) == [200, 409]
    assert owner.client.get("/api/v1/audit/verify").json()["valid"] is True

    def failed_audit(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Injected audit failure")

    monkeypatch.setattr(Principal, "audit", failed_audit)
    with pytest.raises(RuntimeError, match="Injected audit failure"):
        owner.post("/api/v1/records/accounts", {**account["data"], "name": "Must roll back"})
    assert owner.client.get("/api/v1/records/accounts").json()["total"] == 1


def test_runtime_cannot_rewrite_audit_and_chain_detects_admin_tampering(owner: System) -> None:
    owner.account()
    engine = create_engine(owner.runtime_url)
    try:
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
                ).scalar()
                is False
            )
        for statement in (
            "UPDATE audit_events SET digest = 'bad'",
            "DELETE FROM audit_events",
            "TRUNCATE audit_events",
        ):
            with pytest.raises(ProgrammingError), engine.begin() as connection:
                connection.execute(text(statement))
    finally:
        engine.dispose()
    admin = create_engine(owner.admin_url)
    with admin.begin() as connection:
        connection.execute(text("ALTER TABLE audit_events DISABLE TRIGGER USER"))
        connection.execute(
            text("UPDATE audit_events SET digest = :digest WHERE sequence = 1"),
            {"digest": "f" * 64},
        )
        connection.execute(text("ALTER TABLE audit_events ENABLE TRIGGER USER"))
    assert owner.client.get("/api/v1/audit/verify").json()["valid"] is False
    admin.dispose()


def test_policy_versions_dates_scope_and_disabled_execution(owner: System) -> None:
    account = owner.account()
    assert (
        owner.client.get(f"/api/v1/accounts/{account['id']}/policy-eligibility").json()[
            "policy_eligible"
        ]
        is False
    )
    firm = owner.client.get("/api/v1/records/firms").json()["items"][0]
    program = owner.post(
        "/api/v1/records/programs",
        {
            "kind": "programs",
            "name": "Synthetic program",
            "firm_id": firm["id"],
            "phase": "test",
            "platform": "test",
        },
    ).json()
    linked = owner.post(
        "/api/v1/records/accounts",
        {**account["data"], "name": "Policy fixture", "program_id": program["id"]},
    ).json()
    now = datetime.now(UTC)
    data = {
        "kind": "policies",
        "name": "Synthetic policy, not actual firm rules",
        "source": "SYNTHETIC_TEST_FIXTURE",
        "program_id": program["id"],
        "account_id": linked["id"],
        "version": 1,
        "source_references": ["https://example.invalid/synthetic-policy"],
        "document_digest": "a" * 64,
        "effective_at": (now - timedelta(days=1)).isoformat(),
        "expires_at": (now + timedelta(days=1)).isoformat(),
    }
    policy = owner.post("/api/v1/records/policies", data)
    assert policy.status_code == 201
    endpoint = f"/api/v1/accounts/{linked['id']}/policy-eligibility"
    assert owner.client.get(endpoint).json()["policy_eligible"] is False
    verification = owner.post(
        f"/api/v1/policies/{policy.json()['id']}/verify",
        {"decision": "VERIFIED", "source_review_acknowledged": True, "expected_revision": 1},
    )
    assert verification.status_code == 200
    attestation = verification.json()["policy_attestation"]
    assert attestation["verified_at"] is not None and attestation["verified_by"] is not None
    assert attestation["account_revision"] == linked["revision"]
    assert owner.client.get(endpoint).json() == {
        "policy_eligible": True,
        "trading_authorized": False,
        "reasons": ["EXECUTION_DISABLED"],
    }
    changed = owner.client.put(
        f"/api/v1/records/accounts/{linked['id']}?expected_revision=1",
        headers=owner.csrf(),
        json={**linked["data"], "name": "Changed account configuration"},
    )
    assert changed.status_code == 200
    assert "POLICY_SCOPE_CHANGED" in owner.client.get(endpoint).json()["reasons"]
    assert owner.client.get(endpoint).json()["policy_eligible"] is False
    assert (
        owner.post(
            f"/api/v1/policies/{policy.json()['id']}/verify",
            {"decision": "VERIFIED", "source_review_acknowledged": True, "expected_revision": 2},
        ).status_code
        == 409
    )
    expired = owner.post(
        "/api/v1/records/policies",
        {**data, "version": 2, "expires_at": (now - timedelta(hours=1)).isoformat()},
    )
    assert expired.status_code == 201
    assert owner.client.get(endpoint).json()["policy_eligible"] is False
    assert (
        owner.post(
            f"/api/v1/policies/{expired.json()['id']}/verify",
            {"decision": "VERIFIED", "source_review_acknowledged": True, "expected_revision": 1},
        ).status_code
        == 409
    )
    for path in ("/api/v1/orders", "/api/v1/live/activate"):
        assert owner.post(path, {}).status_code == 403


def test_phase1_account_policy_risk_and_audit_survive_service_restart() -> None:
    isolated = isolated_config()
    database = f"p1_{isolated.run_id}"
    instance = create_system(database, create=isolated.stage == "write")
    # Deterministic disposable fixture credential so a fresh client can log in after restart.
    instance.password = hashlib.sha256((isolated.run_id + "fixture-password").encode()).hexdigest()
    try:
        if isolated.stage == "write":
            instance.bootstrap()
            instance.enroll()
            account = instance.account("Persistent fixture")
            response = instance.post(
                "/api/v1/records/risk-profiles",
                {
                    "kind": "risk-profiles",
                    "name": "Persistent risk fixture",
                    "account_id": account["id"],
                    "per_trade_pct": "0.25",
                    "daily_loss_pct": "1",
                    "total_loss_pct": "3",
                    "aggregate_risk_pct": "1",
                },
            )
            assert response.status_code == 201
            firm = instance.client.get("/api/v1/records/firms").json()["items"][0]
            program = instance.post(
                "/api/v1/records/programs",
                {
                    "kind": "programs",
                    "name": "Persistent program",
                    "firm_id": firm["id"],
                    "phase": "Synthetic phase",
                    "platform": "Synthetic platform",
                },
            ).json()
            scoped = instance.post(
                "/api/v1/records/accounts",
                {
                    **account["data"],
                    "name": "Persistent policy account",
                    "program_id": program["id"],
                },
            ).json()
            now = datetime.now(UTC)
            policy = instance.post(
                "/api/v1/records/policies",
                {
                    "kind": "policies",
                    "name": "Persistent synthetic policy",
                    "source": "SYNTHETIC_TEST_FIXTURE",
                    "program_id": program["id"],
                    "account_id": scoped["id"],
                    "version": 1,
                    "source_references": ["https://example.invalid/persistent-fixture"],
                    "document_digest": "b" * 64,
                    "effective_at": now.isoformat(),
                    "expires_at": (now + timedelta(days=1)).isoformat(),
                },
            )
            assert policy.status_code == 201
        else:
            # Inspect persisted native rows with a new connection after Docker stop/start.
            engine = create_engine(instance.runtime_url)
            with engine.connect() as connection:
                assert connection.execute(
                    text(
                        "SELECT initial_capital FROM trading_accounts "
                        "WHERE name = 'Persistent fixture'"
                    )
                ).scalar() == Decimal("25000.12345678")
                assert (
                    str(
                        connection.execute(text("SELECT per_trade_pct FROM risk_profiles")).scalar()
                    )
                    == "0.2500"
                )
                assert (
                    connection.execute(
                        text("SELECT count(*) FROM users WHERE mfa_secret IS NOT NULL")
                    ).scalar()
                    == 1
                )
                assert (
                    connection.execute(text("SELECT count(*) FROM audit_events")).scalar() or 0
                ) >= 5
                assert (
                    connection.execute(text("SELECT document_digest FROM firm_policies")).scalar()
                    == "b" * 64
                )
                encrypted = connection.execute(
                    text("SELECT mfa_secret FROM users WHERE username = 'fixture-owner'")
                ).scalar_one()
            engine.dispose()
            from apps.api.identity.crypto import decrypt_secret

            key = instance.config.auth_encryption_key
            assert key is not None
            secret = decrypt_secret(key.get_secret_value(), encrypted)
            login = instance.client.post(
                "/api/v1/auth/login",
                headers={"Origin": ORIGIN},
                json={
                    "username": "fixture-owner",
                    "password": instance.password,
                },
            )
            assert login.status_code == 200
            code = pyotp.TOTP(secret).at(datetime.now(UTC) + timedelta(seconds=30))
            assert instance.post("/api/v1/auth/mfa/verify", {"code": code}).status_code == 200
            assert instance.client.get("/api/v1/audit/verify").json()["valid"] is True
            assert instance.client.get("/api/v1/records/accounts").json()["total"] == 2
            assert instance.client.get("/api/v1/records/policies").json()["total"] == 1
    finally:
        close_system(instance, drop=isolated.stage == "verify")


def test_all_metadata_entities_and_immutable_strategy_version(owner: System) -> None:
    account = owner.account()

    def create(kind: str, **fields: Any) -> dict[str, Any]:
        response = owner.post(
            f"/api/v1/records/{kind}",
            {
                "kind": kind,
                "name": f"Synthetic {kind}",
                "source": "SYNTHETIC_TEST_FIXTURE",
                **fields,
            },
        )
        assert response.status_code == 201
        result = dict(response.json())
        assert owner.client.get(f"/api/v1/records/{kind}/{result['id']}").status_code == 200
        return result

    venue = create("venues", venue_type="CUSTOM")
    create("instruments", venue_id=venue["id"], symbol="SYNTHETIC", asset_class="OTHER")
    create("brokers", account_id=account["id"], adapter="CUSTOM")
    strategy = create(
        "strategies", account_id=account["id"], hypothesis="Synthetic hypothesis; no execution"
    )
    version = create(
        "strategy-versions", strategy_id=strategy["id"], version=1, artifact_digest="c" * 64
    )
    create(
        "experiments", strategy_version_id=version["id"], research_question="Metadata only; not run"
    )
    approval = create("approvals", account_id=account["id"], strategy_version_id=version["id"])
    other_account = owner.account("Different account in the same partition")
    assert (
        owner.post(
            "/api/v1/records/approvals",
            {
                "kind": "approvals",
                "name": "Mismatched account approval",
                "account_id": other_account["id"],
                "strategy_version_id": version["id"],
            },
        ).status_code
        == 409
    )
    incident = create("incidents", account_id=account["id"], severity="INFO")
    assert (
        owner.client.put(
            f"/api/v1/records/incidents/{incident['id']}?expected_revision=1",
            json={**incident["data"], "status": "RESOLVED"},
            headers=owner.csrf(),
        ).status_code
        == 200
    )
    assert (
        owner.post(
            f"/api/v1/approvals/{approval['id']}/review",
            {
                "decision": "REVIEWED",
                "expected_revision": 1,
            },
        ).status_code
        == 200
    )
    assert (
        owner.client.put(
            f"/api/v1/records/strategy-versions/{version['id']}?expected_revision=1",
            json=version["data"],
            headers=owner.csrf(),
        ).status_code
        == 409
    )
    engine = create_engine(owner.runtime_url)
    try:
        with pytest.raises(ProgrammingError), engine.begin() as connection:
            connection.execute(
                text("UPDATE strategy_versions SET artifact_digest = :digest"), {"digest": "d" * 64}
            )
    finally:
        engine.dispose()
    assert (
        owner.post(
            "/api/v1/records/brokers",
            {
                "kind": "brokers",
                "name": "Denied credentials",
                "account_id": account["id"],
                "adapter": "MT5",
                "broker_password": "must not be accepted",
            },
        ).status_code
        == 422
    )
    assert (
        owner.post(
            f"/api/v1/approvals/{approval['id']}/review",
            {
                "decision": "LIVE_APPROVED",
                "expected_revision": 2,
            },
        ).status_code
        == 422
    )


def test_role_changes_and_disabling_users_revoke_sessions(owner: System) -> None:
    peer, user_id = owner.peer("role-fixture", "OPERATOR")
    try:
        account = owner.account("Owned before demotion", peer)
        response = owner.client.patch(
            f"/api/v1/auth/users/{user_id}",
            headers=owner.csrf(),
            json={"role": "VIEWER", "active": False},
        )
        assert response.status_code == 200
        assert peer.get(f"/api/v1/records/accounts/{account['id']}").status_code == 401
    finally:
        cast(FastAPI, peer.app).state.store.engine.dispose()
        peer.close()


def test_password_change_revokes_existing_sessions_and_redacts_validation(owner: System) -> None:
    new_password = secrets.token_urlsafe(24)
    response = owner.post(
        "/api/v1/auth/password", {"current_password": owner.password, "new_password": new_password}
    )
    assert response.status_code == 204
    assert owner.client.get("/api/v1/auth/me").status_code == 401
    wrong = owner.client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"username": "fixture-owner", "password": owner.password},
    )
    assert wrong.status_code == 401
    accepted = owner.client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"username": "fixture-owner", "password": new_password},
    )
    assert accepted.status_code == 200
    assert (
        "HttpOnly" in accepted.headers["set-cookie"]
        and "SameSite=strict" in accepted.headers["set-cookie"]
    )
    invalid = owner.client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"username": "!", "password": new_password},
    )
    assert invalid.status_code == 422 and new_password not in invalid.text


def test_identity_refuses_superuser_database_identity(owner: System) -> None:
    config = owner.config.model_copy(update={"database_url": SecretStr(owner.admin_url)})
    with TestClient(create_app(config)) as client:
        assert client.get("/api/v1/auth/status").status_code == 503
        cast(FastAPI, client.app).state.store.engine.dispose()


def test_enrollment_expiry_and_recent_mfa_are_enforced(system: System) -> None:
    system.bootstrap()
    pending = system.post("/api/v1/auth/mfa/enroll", {}).json()["secret"]
    engine = create_engine(system.admin_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE users SET pending_mfa_expires = :expired"),
                {"expired": datetime.now(UTC) - timedelta(seconds=1)},
            )
        assert (
            system.post("/api/v1/auth/mfa/confirm", {"code": pyotp.TOTP(pending).now()}).status_code
            == 409
        )
        system.secret, system.recovery = system.enroll()
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE login_sessions SET mfa_at = :old WHERE state = 'FULL'"),
                {"old": datetime.now(UTC) - timedelta(minutes=6)},
            )
        body = {
            "username": "new-viewer",
            "display_name": "Viewer",
            "role": "VIEWER",
            "password": secrets.token_urlsafe(24),
        }
        assert system.post("/api/v1/auth/users", body).status_code == 403
        code = pyotp.TOTP(system.secret).at(datetime.now(UTC) + timedelta(seconds=30))
        assert (
            system.post(
                "/api/v1/auth/reauthenticate", {"password": system.password, "code": code}
            ).status_code
            == 200
        )
        assert system.post("/api/v1/auth/users", body).status_code == 201
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE login_sessions SET idle_expires_at = :expired"),
                {"expired": datetime.now(UTC) - timedelta(seconds=1)},
            )
        assert system.client.get("/api/v1/auth/me").status_code == 401
    finally:
        engine.dispose()


def test_concurrent_bootstrap_creates_exactly_one_owner(system: System) -> None:
    token = system.config.auth_bootstrap_token
    assert token is not None

    def attempt(number: int) -> int:
        with TestClient(create_app(system.config)) as client:
            return int(
                client.post(
                    "/api/v1/auth/bootstrap",
                    headers={"Origin": ORIGIN},
                    json={
                        "username": f"owner-{number}",
                        "display_name": "Concurrent fixture",
                        "password": system.password,
                        "bootstrap_token": token.get_secret_value(),
                    },
                ).status_code
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, range(2))) == [201, 409]
    engine = create_engine(system.admin_url)
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM users WHERE role = 'OWNER'")) == 1
            assert (
                connection.scalar(
                    text(
                        "SELECT count(*) FROM audit_events WHERE event_type = 'owner.bootstrapped'"
                    )
                )
                == 1
            )
    finally:
        engine.dispose()


def test_public_source_metadata_rejects_secret_bearing_urls(owner: System) -> None:
    for url in (
        "https://user:private@example.invalid/doc",
        "https://example.invalid/doc?token=private",
        "https://example.invalid/doc#private",
    ):
        response = owner.post(
            "/api/v1/records/firms", {"kind": "firms", "name": "Synthetic", "website": url}
        )
        assert response.status_code == 422 and "private" not in response.text
    assert owner.client.get("/api/v1/records/firms").json()["total"] == 3
