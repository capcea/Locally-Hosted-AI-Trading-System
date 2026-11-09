"""Synthetic routing metadata only: never a provider switch, privacy bypass or real completion."""

import json

import httpx
import pytest
from test_openrouter import adapter, fixture

from packages.ai.providers import ProviderFailure

REQUIRED = ["temperature", "top_p", "response_format", "structured_outputs"]


def row(**patch: object) -> dict[str, object]:
    return {
        "model_id": "fixture/model",
        "tag": "fixture-provider",
        "supported_parameters": [*REQUIRED, "max_tokens"],
        **patch,
    }


@pytest.mark.parametrize(
    ("data", "code"),
    [
        ([], "AI_APPROVED_UPSTREAM_NOT_ZDR"),
        ([row(tag="another-provider")], "AI_APPROVED_UPSTREAM_NOT_ZDR"),
        ([row(model_id="another/model")], "AI_APPROVED_UPSTREAM_NOT_ZDR"),
        ([row(supported_parameters=["max_tokens"])], "AI_APPROVED_PARAMETERS_UNAVAILABLE"),
        ([row(supported_parameters=[*REQUIRED])], "AI_APPROVED_PARAMETERS_UNAVAILABLE"),
        ([row(supported_parameters="not a list")], "AI_APPROVED_PARAMETERS_UNAVAILABLE"),
        ({"unexpected": []}, "AI_PROVIDER_METADATA_INVALID"),
    ],
)
def test_ineligible_or_unknown_metadata_stops_before_completion(data: object, code: str) -> None:
    posts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            posts.append(request.url.path)
        if request.url.path == "/api/v1/endpoints/zdr":
            return httpx.Response(200, json={"data": data})
        return fixture(request)

    obj = adapter(handler)
    try:
        with pytest.raises(ProviderFailure, match=code):
            obj.probe("fixture/model", 8192)
        assert not posts
        assert obj.cloud_policy is not None
        assert obj.cloud_policy.routing()["only"] == ["fixture-provider"]
        assert obj.cloud_policy.routing()["zdr"] is True
        assert obj.cloud_policy.routing()["allow_fallbacks"] is False
    finally:
        obj.close()


@pytest.mark.parametrize("output_limit_key", ["max_tokens", "max_completion_tokens"])
def test_token_parameter_is_measured_and_keeps_exact_approved_output_limit(
    output_limit_key: str,
) -> None:
    calls: list[str] = []
    bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.method)
        if request.url.path == "/api/v1/endpoints/zdr":
            return httpx.Response(
                200, json={"data": [row(supported_parameters=[*REQUIRED, output_limit_key])]}
            )
        if request.method == "POST":
            bodies.append(json.loads(request.content))
        return fixture(request)

    obj = adapter(handler)
    try:
        result = obj.probe("fixture/model", 8192, progress=lambda _: calls.append("AUTH_RECHECK"))
        assert result["structured_outputs"] == "VERIFIED"
        assert len(bodies) == 1 and bodies[0][output_limit_key] == 64
        assert ("max_tokens" in bodies[0]) != ("max_completion_tokens" in bodies[0])
        assert (
            calls.count("GET") == 2
        )  # One model read + one ZDR read, cached only in this adapter.
        assert calls.index("AUTH_RECHECK") < calls.index("POST")
        assert obj.cloud_policy is not None
        assert bodies[0]["provider"] == obj.cloud_policy.routing()
    finally:
        obj.close()


def test_usage_limit_is_still_enforced_for_completion_token_alias() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/endpoints/zdr":
            return httpx.Response(
                200, json={"data": [row(supported_parameters=[*REQUIRED, "max_completion_tokens"])]}
            )
        if request.method == "POST":
            response = fixture(request)
            return httpx.Response(
                200,
                content=response.content.replace(
                    b'"completion_tokens": 4', b'"completion_tokens": 65'
                ),
            )
        return fixture(request)

    obj = adapter(handler)
    try:
        with pytest.raises(ProviderFailure, match="AI_PROVIDER_OUTPUT_TOKEN_LIMIT"):
            obj.probe("fixture/model", 8192)
    finally:
        obj.close()
