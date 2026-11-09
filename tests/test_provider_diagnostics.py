"""Only synthetic HTTP responses; no real key, provider request or paid inference."""

import json
import secrets

import httpx
import pytest
from test_openrouter import adapter

from packages.ai.diagnostics import safe_provider_diagnostic
from packages.ai.providers import ProviderFailure


@pytest.mark.parametrize("status", [302, 400, 401, 402, 403, 404, 408, 422, 429, 502, 503])
def test_status_and_stage_survive_without_headers_response_body_or_model_content(
    status: int,
) -> None:
    secret = secrets.token_hex(24)
    obj = adapter(
        lambda request: httpx.Response(
            status,
            headers={"Location": "https://example.invalid/"},
            json={"error": {"message": secret, "metadata": {"raw": secret}}},
        )
    )
    try:
        with pytest.raises(ProviderFailure) as caught:
            obj.describe("fixture/model")
        assert caught.value.diagnostic == {"http_status": status, "operation": "MODEL_METADATA"}
        sanitized = secret not in json.dumps(caught.value.diagnostic) + str(caught.value)
        assert sanitized, "Provider diagnostics must never retain raw response content"
        assert caught.value.retryable == (status in {429, 503})
        assert caught.value.ambiguous == (status >= 500 and status != 503)
    finally:
        obj.close()


@pytest.mark.parametrize("operation", ["MODEL_CATALOG", "COMPLETION"])
def test_http_operation_classification_distinguishes_metadata_from_generation(
    operation: str,
) -> None:
    obj = adapter(lambda request: httpx.Response(400, json={"error": "SYNTHETIC_REFUSAL"}))
    try:
        with pytest.raises(ProviderFailure) as caught:
            if operation == "MODEL_CATALOG":
                obj.discover()
            else:
                obj.complete({}, max_bytes=1024, max_seconds=5, progress=lambda _: None)
        assert caught.value.code == "AI_PROVIDER_REQUEST_REFUSED"
        assert caught.value.diagnostic == {"http_status": 400, "operation": operation}
    finally:
        obj.close()


@pytest.mark.parametrize(
    "value",
    [
        None,
        {},
        {"http_status": True, "operation": "COMPLETION"},
        {"http_status": "400", "operation": "COMPLETION"},
        {"http_status": 600, "operation": "COMPLETION"},
        {"http_status": 404, "operation": "arbitrary provider text"},
    ],
)
def test_invalid_diagnostics_cannot_be_reinterpreted_as_provider_facts(value: object) -> None:
    assert safe_provider_diagnostic(value) is None


def test_safe_diagnostic_strips_every_extra_field() -> None:
    assert safe_provider_diagnostic(
        {"http_status": 404, "operation": "MODEL_METADATA", "message": "private fixture"}
    ) == {"http_status": 404, "operation": "MODEL_METADATA"}
