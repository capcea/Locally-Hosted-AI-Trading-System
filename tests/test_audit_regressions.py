"""Regression reproductions for findings in the 2026-10-25 audit."""

from collections.abc import Callable
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from packages.domain.contracts import SafetyState
from scripts.smoke_demo import smoke


def install_http_mock(
    monkeypatch: pytest.MonkeyPatch, handler: Callable[[httpx.Request], httpx.Response]
) -> None:
    original_client = httpx.Client

    def make_client(*args: Any, **kwargs: Any) -> httpx.Client:
        return original_client(*args, **kwargs, transport=httpx.MockTransport(handler))

    monkeypatch.setattr("scripts.smoke_demo.httpx.Client", make_client)


def test_untrusted_host_is_rejected(client: TestClient) -> None:
    assert client.get("/api/v1/overview", headers={"host": "attacker.invalid"}).status_code == 400


def test_smoke_never_targets_external_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(500)

    install_http_mock(monkeypatch, handler)
    with pytest.raises(ValueError, match="loopback"):
        smoke("https://broker.example.invalid", False)
    assert requests == []


def test_smoke_fails_on_server_error_readiness(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    overview = client.get("/api/v1/overview").json()

    def handler(request: httpx.Request) -> httpx.Response:
        match request.url.path:
            case "/health/live":
                return httpx.Response(
                    200, json={"mode": "SIMULATED", "version": "0.1.0", "status": "ok"}
                )
            case "/api/v1/safety":
                return httpx.Response(200, json=SafetyState().model_dump(mode="json"))
            case "/api/v1/overview":
                return httpx.Response(200, json=overview)
            case "/health/ready":
                return httpx.Response(500, json={"detail": "unhandled error"})
            case _:
                return httpx.Response(403, json={"detail": "disabled"})

    install_http_mock(monkeypatch, handler)
    with pytest.raises((RuntimeError, httpx.HTTPStatusError), match="readiness|500"):
        smoke("http://127.0.0.1:18000", False)


@pytest.mark.parametrize("payload", [{}, {"mode": "LIVE"}, {"mode": "SIMULATED"}])
def test_smoke_never_posts_without_complete_safe_contract(
    monkeypatch: pytest.MonkeyPatch, payload: dict[str, str]
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/health/live":
            return httpx.Response(
                200, json={"status": "ok", "mode": "SIMULATED", "version": "0.1.0"}
            )
        return httpx.Response(200, json=payload)

    install_http_mock(monkeypatch, handler)
    with pytest.raises(RuntimeError, match="safety"):
        smoke("http://127.0.0.1:18000", False)
    assert all(request.method == "GET" for request in requests)


def test_smoke_accepts_honest_degraded_local_app(
    monkeypatch: pytest.MonkeyPatch, client: TestClient, capsys: pytest.CaptureFixture[str]
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        response = client.request(request.method, request.url.path)
        return httpx.Response(response.status_code, json=response.json())

    install_http_mock(monkeypatch, handler)
    smoke("http://127.0.0.1:18000", False)
    assert "readiness: 503" in capsys.readouterr().out
    with pytest.raises(RuntimeError, match="readiness failed"):
        smoke("http://127.0.0.1:18000", True)
