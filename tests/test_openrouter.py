"""No external network or paid inference. Public-provider boundaries use explicit fixtures."""

import ipaddress
import json
import secrets
import socket
from typing import Any

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from packages.ai.cloud_contracts import OPENROUTER_URL, CloudPolicy, CredentialInput
from packages.ai.contracts import Generation
from packages.ai.providers import Adapter, ProviderFailure
from packages.ai.settings import Endpoint, GatewaySettings
from services.ai_egress.proxy import destinations, pinned_address


def policy(**patch: Any) -> CloudPolicy:
    return CloudPolicy.model_validate(
        {
            "upstream_provider": "fixture-provider",
            "acknowledged_public_cloud": True,
            "acknowledged_upstream_processing": True,
            "acknowledged_cost": True,
            "acknowledged_provider_policy_limits": True,
            **patch,
        }
    )


def endpoint() -> Endpoint:
    return GatewaySettings(openrouter_enabled=True).endpoint("openrouter")


def test_public_opt_in_is_separate_and_private_is_still_default() -> None:
    assert not GatewaySettings().openrouter_enabled
    assert GatewaySettings().endpoints == []
    assert endpoint().url == OPENROUTER_URL and not endpoint().private_only_attested
    with pytest.raises(ValidationError):
        GatewaySettings(endpoints=[endpoint()])
    for patch in (
        {"url": "https://example.com/api/v1"},
        {"url": OPENROUTER_URL + "/"},
        {"url": "https://openrouter.ai.evil.invalid/api/v1"},
        {"private_only_attested": True},
        {"ca_file": "/run/secrets/ai-custom"},
        {"url": "http://openrouter.ai/api/v1"},
    ):
        with pytest.raises(ValidationError):
            Endpoint.model_validate({**endpoint().model_dump(), **patch})
    for field in (
        "acknowledged_public_cloud",
        "acknowledged_upstream_processing",
        "acknowledged_cost",
        "acknowledged_provider_policy_limits",
    ):
        with pytest.raises(ValidationError):
            policy(**{field: False})
    with pytest.raises(ValidationError):
        policy(daily_usd="5.1")
    with pytest.raises(ValidationError):
        policy(request_usd="0.9")


@pytest.mark.parametrize(
    "address",
    ["127.0.0.1", "10.0.0.1", "169.254.169.254", "100.64.0.1", "::1", "224.0.0.1", "192.0.2.1"],
)
def test_cloud_dns_refuses_any_nonpublic_answer(
    address: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **kw: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443)),
        ],
    )
    with pytest.raises(ValueError, match="DNS_ADDRESS_REFUSED"):
        pinned_address("openrouter.ai", 443)


def test_proxy_accepts_only_exact_public_host_and_pins_validated_ip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = [{"host": "openrouter.ai", "port": 443, "cloud_policy": "openrouter-public-v1"}]
    assert destinations(json.dumps(raw)) == frozenset({("openrouter.ai", 443)})
    for patch in (
        {"host": "example.com"},
        {"host": "openrouter.ai."},
        {"port": 8443},
        {"cloud_policy": "private"},
    ):
        with pytest.raises(ValueError):
            destinations(json.dumps([{**raw[0], **patch}]))
    calls = []

    def resolve(*a: Any, **kw: Any) -> Any:
        calls.append(a)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))]

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    assert ipaddress.ip_address(pinned_address("openrouter.ai", 443)).is_global
    assert len(calls) == 1


def fixture(request: httpx.Request) -> httpx.Response:
    assert request.url.scheme == "https" and request.url.host == "openrouter.ai"
    assert request.headers["authorization"].startswith("Bearer ")
    if request.method == "GET":
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
    assert body["provider"] == policy().routing()
    assert body["model"] == "fixture/model"
    text = json.dumps({"probe": "ok"})
    content = (
        "data: "
        + json.dumps(
            {
                "choices": [{"delta": {"content": text}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 4},
            }
        )
        + "\n\ndata: [DONE]\n\n"
    )
    return httpx.Response(200, content=content)


def adapter(handler: Any = fixture) -> Adapter:
    obj = Adapter(
        endpoint(),
        "OPENROUTER",
        proxy="http://127.0.0.1:18888",
        bearer_token=secrets.token_hex(24),
        cloud_policy=policy(),
    )
    headers = dict(obj.client.headers)
    obj.client.close()
    obj.client = httpx.Client(
        base_url="https://openrouter.ai",
        headers=headers,
        transport=httpx.MockTransport(handler),
        follow_redirects=False,
    )
    return obj


def test_compatible_adapter_exact_paths_routing_one_paid_probe_and_no_tools() -> None:
    calls = []

    def record(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        return fixture(request)

    obj = adapter(record)
    try:
        measured = obj.probe("fixture/model", 8192)
        assert measured["structured_outputs"] == "VERIFIED"
        assert measured["tool_calling"] == "UNVERIFIED_NOT_REQUESTED"
        assert len([c for c in calls if c[0] == "POST"]) == 1
        assert ("POST", "/api/v1/chat/completions") in calls
        assert all(not p.startswith("/v1/") and "/api/tags" not in p for _, p in calls)
        with pytest.raises(ProviderFailure, match="EXACT_MODEL_ID"):
            obj.identity("../secrets")
    finally:
        obj.close()


@pytest.mark.parametrize("status", [301, 302, 307, 401, 402, 429, 503])
def test_refusals_never_follow_redirects_or_echo_provider_secrets(status: int) -> None:
    secret = secrets.token_hex(24)
    obj = adapter(
        lambda r: httpx.Response(
            status, headers={"Location": "https://example.com/"}, json={"error": secret}
        )
    )
    try:
        with pytest.raises(ProviderFailure) as error:
            obj.discover()
        assert secret not in str(error.value)
    finally:
        obj.close()


def test_cloud_credentials_are_write_only_and_not_in_bodies() -> None:
    token = secrets.token_hex(24)
    assert token not in repr(CredentialInput(api_key=SecretStr(token)))
    assert CredentialInput.model_json_schema()["properties"]["api_key"]["writeOnly"] is True
    obj = adapter()
    try:
        body = obj.body(
            "fixture/model",
            [{"role": "user", "content": "Synthetic input only"}],
            {"type": "object"},
            Generation(),
        )
        assert "Authorization" not in json.dumps(body)
        assert body["provider"]["zdr"] is True
        assert body["provider"]["allow_fallbacks"] is False
    finally:
        obj.close()


def test_provider_cannot_reflect_configured_credential_back_into_catalog() -> None:
    def reflect(request: httpx.Request) -> httpx.Response:
        token = request.headers["authorization"].removeprefix("Bearer ")
        return httpx.Response(200, json={"data": [{"id": token}]})

    obj = adapter(reflect)
    try:
        with pytest.raises(ProviderFailure, match="SECRET_REFLECTION_REFUSED"):
            obj.discover()
    finally:
        obj.close()


def test_operator_setup_preserves_private_destinations_and_secret_lines(tmp_path: Any) -> None:
    from scripts.configure_openrouter import apply, private_config, proposal

    original = (
        "AI_WORKER_DATABASE_URL=private-retained-value\n"
        "AI_ENDPOINTS='[]'\n"
        'AI_EGRESS_DESTINATIONS=\'[{"ip":"192.0.2.1","port":443}]\'\n'
    )
    updated = proposal(original)
    assert "private-retained-value" in updated and "AI_ENDPOINTS='[]'" in updated
    assert "192.0.2.1" in updated and "openrouter.ai" in updated
    assert proposal(updated) == updated
    path = tmp_path / ".env.ai"
    path.write_text(original)
    path.chmod(0o600)
    apply(path, original, updated)
    assert private_config(path) == updated
    assert path.stat().st_mode & 0o777 == 0o600
    link = tmp_path / "symlink"
    link.symlink_to(path)
    with pytest.raises(ValueError):
        private_config(link)
