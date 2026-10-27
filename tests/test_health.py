import asyncio
import json
from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from apps.api.health import check_service
from packages.domain.contracts import ServiceHealth, ServiceStatus


def test_liveness_is_independent_of_external_dependencies(client: TestClient) -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["mode"] == "SIMULATED"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"]


def test_readiness_fails_closed_on_missing_configuration(client: TestClient) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert all(service["status"] == "NOT_CONFIGURED" for service in response.json())


def test_readiness_requires_every_dependency(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    services = [
        ServiceHealth(id=name, name=name, status=ServiceStatus.HEALTHY, detail="test")
        for name in ("postgres", "redis", "storage")
    ]
    probe = AsyncMock(return_value=services)
    monkeypatch.setattr("apps.api.main.infrastructure_health", probe)
    assert client.get("/health/ready").status_code == 200
    services[2] = services[2].model_copy(update={"status": ServiceStatus.UNAVAILABLE})
    assert client.get("/health/ready").status_code == 503


def test_dependency_errors_do_not_disclose_credentials() -> None:
    probe = AsyncMock(side_effect=RuntimeError("connection failed: password=do-not-leak"))
    result = asyncio.run(check_service("postgres", "Postgres", True, probe))
    assert result.status == ServiceStatus.UNAVAILABLE
    assert "do-not-leak" not in result.model_dump_json()


def test_missing_configuration_does_not_attempt_a_connection() -> None:
    probe = AsyncMock()
    result = asyncio.run(check_service("postgres", "Postgres", False, probe))
    assert result.status == ServiceStatus.NOT_CONFIGURED
    probe.assert_not_called()


def test_structured_logs_exclude_query_values(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    messages: list[str] = []
    monkeypatch.setattr("apps.api.main.logger.info", messages.append)
    response = client.get("/health/live?token=secret-not-for-logs")
    assert len(messages) == 1
    event = json.loads(messages[0])
    assert event["request_id"] == response.headers["x-request-id"]
    assert event["event"] == "http_request"
    assert "secret-not-for-logs" not in messages[0]


@pytest.mark.parametrize("sqlstate", ["40P01", "57014", "not-a-safe-driver-code"])
def test_database_failures_are_correlated_without_logging_exception_data(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, sqlstate: str
) -> None:
    messages: list[str] = []
    monkeypatch.setattr("apps.api.main.logger.error", messages.append)

    class DriverFailure(Exception):
        sqlstate: str

    driver = DriverFailure("sensitive-driver-fixture")
    driver.sqlstate = sqlstate

    @cast(FastAPI, client.app).get("/test-storage-error")
    def fail() -> None:
        raise OperationalError("sensitive-statement-fixture", {"private": "fixture"}, driver)

    response = client.get("/test-storage-error?token=private-query-fixture")
    assert response.status_code == 503
    assert response.json() == {"detail": "Persistent service unavailable; no change accepted"}
    assert response.headers["x-error-category"] == "PERSISTENCE_TRANSACTION_FAILED"
    assert len(messages) == 1
    assert json.loads(messages[0]) == {
        "event": "persistence_failure",
        "category": "PERSISTENCE_TRANSACTION_FAILED",
        "request_id": response.headers["x-request-id"],
        "sqlstate": sqlstate if sqlstate in {"40P01", "57014"} else None,
    }
    for private in (
        "sensitive-driver-fixture",
        "sensitive-statement-fixture",
        "private-query-fixture",
    ):
        assert private not in response.text + messages[0]


def test_overview_labels_reference_values_and_unimplemented_features(client: TestClient) -> None:
    response = client.get("/api/v1/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["reference_profile"]["equity"] == "25000.00"
    assert data["reference_profile"]["enforced"] is False
    assert data["reference_profile"]["provenance"] == "CONFIGURATION_EXAMPLE"
    assert data["performance_data_available"] is False
    assert data["trading_data_available"] is False
    assert data["timestamp"].endswith("Z")
    brokers = [service for service in data["services"] if service["id"] in ("mt5", "ctrader")]
    assert all(service["status"] == "PENDING_IMPLEMENTATION" for service in brokers)
    assert len(data["roadmap"]) == 11
