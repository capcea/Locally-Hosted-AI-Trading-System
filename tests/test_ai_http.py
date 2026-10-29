"""Real HTTP contract tests against an explicitly synthetic protocol fixture."""

import json

import pytest
from pydantic import ValidationError

from packages.ai.contracts import OUTPUTS, Generation, Provider
from packages.ai.prompts import validate_output
from packages.ai.providers import Adapter, ProviderFailure
from packages.ai.settings import Endpoint
from testing.ai_fixture import NAME, running_fixture


@pytest.mark.parametrize("protocol", ["OLLAMA_NATIVE", "OLLAMA_OPENAI", "PRIVATE_OPENAI"])
def test_actual_http_discovery_probe_streaming_and_reasoning_removal(protocol: Provider) -> None:
    with running_fixture() as fixture:
        endpoint = Endpoint(
            id="fixture",
            label="Synthetic HTTP fixture",
            url=fixture.url,
            transport="LOOPBACK",
            private_only_attested=True,
        )
        adapter = Adapter(endpoint, protocol)
        try:
            assert adapter.discover()[0]["name"] == NAME
            capabilities = adapter.probe(NAME, 8192)
            assert capabilities["structured_outputs"] == "VERIFIED"
            assert capabilities["tool_calling"] == "VERIFIED_INERT_SUGGESTIONS_ONLY"
            assert capabilities["gpu_availability"] == "UNKNOWN"
            partials: list[str] = []
            result = adapter.complete(
                adapter.body(NAME, [], OUTPUTS["RESEARCH"].model_json_schema(), Generation()),
                max_bytes=12000,
                max_seconds=5,
                progress=partials.append,
            )
            assert len(partials) == 2
            assert "PRIVATE_REASONING" not in result.content
            assert result.input_tokens == 30 and result.output_tokens == 40
            assert (
                validate_output("RESEARCH", result.content, set()).model_dump()["verified"] is False
            )
        finally:
            adapter.close()


@pytest.mark.parametrize(
    "behavior,code,retry,ambiguous",
    [
        ("busy", "AI_PROVIDER_BUSY", True, False),
        ("unknown", "AI_PROVIDER_COMPLETION_UNKNOWN", False, True),
        ("tool", "AI_TOOL_SUGGESTION_REFUSED", False, False),
        ("incomplete", "AI_PROVIDER_INCOMPLETE", False, True),
    ],
)
def test_transport_failures_are_classified_without_unsafe_retry(
    behavior: str,
    code: str,
    retry: bool,
    ambiguous: bool,
) -> None:
    with running_fixture() as fixture:
        fixture.behavior = behavior
        adapter = Adapter(
            Endpoint(
                id="fixture",
                label="Fixture",
                url=fixture.url,
                transport="LOOPBACK",
                private_only_attested=True,
            ),
            "OLLAMA_NATIVE",
        )
        try:
            with pytest.raises(ProviderFailure) as failure:
                adapter.complete(
                    adapter.body(NAME, [], OUTPUTS["RESEARCH"].model_json_schema(), Generation()),
                    max_bytes=12000,
                    max_seconds=5,
                    progress=lambda _: None,
                )
            assert (failure.value.code, failure.value.retryable, failure.value.ambiguous) == (
                code,
                retry,
                ambiguous,
            )
        finally:
            adapter.close()


@pytest.mark.parametrize("role", list(OUTPUTS))
def test_outputs_are_inert_strict_and_require_real_references(role: str) -> None:
    from testing.ai_fixture import structured

    payload = structured(OUTPUTS[role].model_json_schema()["properties"])
    assert validate_output(role, json.dumps(payload), set())
    payload["evidence_refs"] = ["invented"]
    with pytest.raises(ValueError, match="AI_HALLUCINATED_REFERENCE"):
        validate_output(role, json.dumps(payload), set())
    payload["evidence_refs"] = []
    payload["execute"] = True
    with pytest.raises(ValueError, match="AI_OUTPUT_SCHEMA_INVALID"):
        validate_output(role, json.dumps(payload), set())


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254:11434",
        "http://localhost:11434",
        "http://127.0.0.1:5432",
        "http://127.0.0.1:11434/path",
        "http://user@127.0.0.1:11434",
        "http://0.0.0.0:11434",
        "http://127.0.0.1:11434?token=x",
        "http://[::ffff:169.254.169.254]:11434",
    ],
)
def test_endpoint_refuses_ssrf_targets(url: str) -> None:
    with pytest.raises(ValidationError):
        Endpoint(
            id="fixture", label="Fixture", url=url, transport="LOOPBACK", private_only_attested=True
        )


@pytest.mark.parametrize("value", [0, 1, True, "false", None])
def test_output_authority_is_exact_json_false_not_literal_coercion(value: object) -> None:
    from testing.ai_fixture import structured

    payload = structured(OUTPUTS["CODING"].model_json_schema()["properties"])
    payload["executable"] = value
    with pytest.raises(ValueError, match="AI_OUTPUT_SCHEMA_INVALID"):
        validate_output("CODING", json.dumps(payload), set())


def test_duplicate_output_fields_are_refused() -> None:
    from testing.ai_fixture import structured

    payload = structured(OUTPUTS["LIGHTWEIGHT"].model_json_schema()["properties"])
    duplicate = json.dumps(payload)[:-1] + ',"verified":false}'
    with pytest.raises(ValueError, match="AI_OUTPUT_SCHEMA_INVALID"):
        validate_output("LIGHTWEIGHT", duplicate, set())
