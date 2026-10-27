from typing import Any

import pytest
from fastapi.testclient import TestClient
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from apps.api.config import Settings
from packages.domain.contracts import SafetyState
from packages.domain.safety import ExecutionDisabledError, deny_order_submission
from workers.safety import require_research_execution


@pytest.mark.parametrize("environment", ["LIVE", "DEMO", "live", "", "UNKNOWN"])
def test_non_simulated_environment_cannot_start(environment: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, broker_environment=environment)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", ["true", "1", "yes", "on", "True"])
@pytest.mark.parametrize("name", ["LIVE_TRADING_ENABLED", "WORKER_EXECUTION_ENABLED"])
def test_environment_cannot_enable_execution(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError, match="cannot be enabled"):
        Settings(_env_file=None)


@given(st.text().filter(lambda value: value != "DENY_ALL"))
def test_any_other_executor_capability_is_rejected(capability: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, executor_capability=capability)  # type: ignore[arg-type]


def test_executor_and_worker_refuse_even_if_configuration_validation_is_bypassed() -> None:
    unsafe = Settings.model_construct(live_trading_enabled=True, worker_execution_enabled=True)
    with pytest.raises(ExecutionDisabledError):
        deny_order_submission()
    with pytest.raises(ExecutionDisabledError):
        require_research_execution(unsafe)


@pytest.mark.parametrize("endpoint", ["/api/v1/orders", "/api/v1/live/activate"])
def test_execution_endpoints_deny_unconditionally(client: TestClient, endpoint: str) -> None:
    response = client.post(endpoint, json={"mode": "LIVE", "approved": True, "owner": True})
    assert response.status_code == 403
    assert "DISABLED" in response.text or "NOT_IMPLEMENTED" in response.text


def test_safety_contract_is_frozen_and_rejects_enabled_flags() -> None:
    state = SafetyState()
    with pytest.raises(ValidationError):
        state.mode = "SIMULATED"  # type: ignore[misc]  # Deliberate mutation for runtime test.
    with pytest.raises(ValidationError):
        SafetyState(live_trading_enabled=True)  # type: ignore[arg-type]


def test_missing_auth_cannot_be_bypassed_via_other_methods(client: TestClient) -> None:
    for method in ("PUT", "PATCH", "DELETE"):
        response = client.request(method, "/api/v1/safety", json={"mode": "LIVE"})
        assert response.status_code == 405


def test_unknown_sensitive_routes_are_not_present(client: TestClient) -> None:
    for endpoint in ("/api/v1/credentials", "/api/v1/settings", "/api/v1/strategies/promote"):
        assert client.post(endpoint).status_code == 404


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://localhost",
        "http://user:secret@host",
        "http://host?token=secret",
    ],
)
def test_invalid_health_url_rejected(url: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, object_store_url=url)


def test_secret_configuration_is_redacted() -> None:
    fields: dict[str, Any] = {"database_url": "postgresql://user:secret-not-for-logs@localhost/db"}
    settings = Settings(_env_file=None, **fields)
    assert "secret-not-for-logs" not in repr(settings)
