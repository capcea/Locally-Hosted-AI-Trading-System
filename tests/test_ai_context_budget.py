"""Capacity accounting boundaries, without a guessed tokenizer or a larger model window."""

from typing import Any, cast

from apps.api.ai.budget import measure, refusal
from packages.ai.contracts import Generation
from packages.ai.prompts import canonical


def measured(text: str, capacity: int = 4096, verified: int = 4096) -> dict[str, int]:
    models: list[dict[str, Any]] = [
        {"context_ceiling": capacity, "capabilities": {"context_tokens": verified}}
    ]
    return measure(
        [{"role": "user", "content": text}],
        {},
        Generation(context_tokens=capacity, output_tokens=768),
        models,
        question=text,
        context=[],
        storage_limit=12000,
    )


def test_counts_romanian_utf8_content_and_schema_not_transport_escaping() -> None:
    text = 'Ce dovezi lipsesc? „Încă o ipoteză”\n"costuri"'
    result = measured(text)
    assert result["question_bytes"] == result["message_content_bytes"] == len(text.encode())
    assert result["schema_bytes"] == len(canonical({}).encode()) == 2
    assert result["prompt_json_bytes"] > result["message_content_bytes"]
    assert result["required_context_upper_bound"] == len(text.encode()) + 2 + 512 + 768
    assert result["storage_input_bytes"] > result["prompt_json_bytes"]
    assert refusal(result) is None


def test_exact_capacity_is_accepted_and_one_more_byte_is_refused() -> None:
    assert measured("a" * 2814)["required_context_upper_bound"] == 4096
    assert refusal(measured("a" * 2814)) is None
    assert refusal(measured("a" * 2815)) == "AI_CONTEXT_BUDGET_EXCEEDED"


def test_registration_cannot_expand_verified_capacity_or_fallback_capacity() -> None:
    assert refusal(measured("short", capacity=8192)) == "AI_CONTEXT_BUDGET_UNVERIFIED"
    result = measured("short")
    result["registered_context_tokens"] = 2048
    assert refusal(result) == "AI_CONTEXT_BUDGET_UNVERIFIED"
    result = measure(
        [{"role": "user", "content": "short"}],
        {},
        Generation(context_tokens=4096),
        [
            {"context_ceiling": 8192, "capabilities": {"context_tokens": 8192}},
            {"context_ceiling": 4096, "capabilities": {"context_tokens": 2048}},
        ],
        question="short",
        context=[],
        storage_limit=12000,
    )
    assert result["effective_context_tokens"] == 2048
    assert refusal(result) == "AI_CONTEXT_BUDGET_UNVERIFIED"


def test_missing_or_invalid_verification_never_invents_capacity() -> None:
    for value in [None, True, "4096", -1]:
        result = measure(
            [],
            {},
            Generation(),
            [{"context_ceiling": 4096, "capabilities": {"context_tokens": value}}],
            question="",
            context=[],
            storage_limit=12000,
        )
        assert result["verified_context_tokens"] == 0
        assert refusal(result) == "AI_CONTEXT_BUDGET_UNVERIFIED"


def test_auto_chooses_smallest_tier_and_honors_verified_fallback() -> None:
    from apps.api.ai.budget import allocate

    base = measured("short", capacity=32768, verified=32768)
    for required, expected in [
        (4096, 4096),
        (4097, 16384),
        (16384, 16384),
        (16385, 32768),
        (32768, 32768),
    ]:
        result, error = allocate(
            {**base, "required_context_upper_bound": required}, "AUTO", [4096, 16384, 32768]
        )
        assert error is None and result["selected_context_tokens"] == expected
        assert result["remaining_context_tokens"] == expected - required
    for required, verified in [(32769, 32768), (5000, 4096), (17000, 16384)]:
        result, error = allocate(
            {**base, "required_context_upper_bound": required, "verified_context_tokens": verified},
            "AUTO",
            [4096, 16384, 32768],
        )
        assert error == "AI_CONTEXT_BUDGET_EXCEEDED"
        assert result["effective_context_tokens"] <= verified


def test_all_explicit_modes_large_schema_and_future_config_are_bounded() -> None:
    from apps.api.ai.budget import allocate
    from packages.ai.contracts import ContextMode

    base = measured("Întrebare română", capacity=32768, verified=32768)
    for mode, expected in [("RAPID", 4096), ("STANDARD", 16384), ("COMPLEX", 32768)]:
        result, error = allocate(base, cast(ContextMode, mode), [4096, 16384, 32768])
        assert error is None and result["selected_context_tokens"] == expected
    _, error = allocate({**base, "verified_context_tokens": 4096}, "COMPLEX", [4096, 16384, 32768])
    assert error == "AI_CONTEXT_BUDGET_UNVERIFIED"
    large = measure(
        [{"role": "user", "content": "Întrebare"}],
        {"description": "s" * 16000},
        Generation(),
        [{"context_ceiling": 32768, "capabilities": {"context_tokens": 32768}}],
        question="Întrebare",
        context=[],
        storage_limit=65536,
    )
    assert allocate(large, "AUTO", [4096, 16384, 32768])[0]["selected_context_tokens"] == 32768
    future = {
        **base,
        "required_context_upper_bound": 40000,
        "registered_context_tokens": 131072,
        "verified_context_tokens": 131072,
    }
    assert allocate(future, "AUTO", [4096, 16384, 32768])[1] is not None
    assert (
        allocate(future, "AUTO", [4096, 16384, 32768, 131072])[0]["selected_context_tokens"]
        == 131072
    )


def test_ai_request_json_is_bounded_for_length_and_chunked_transport() -> None:
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient

    from apps.api.ai.limits import AIJSONLimit

    app = FastAPI()
    app.add_middleware(AIJSONLimit)

    @app.post("/api/v1/ai/bounded")
    async def bounded(request: Request) -> dict[str, int]:
        return {"bytes": len(await request.body())}

    with TestClient(app) as client:
        assert client.post("/api/v1/ai/bounded", content=b"x" * 65536).json() == {"bytes": 65536}
        assert client.post("/api/v1/ai/bounded", content=b"x" * 65537).status_code == 413
        assert (
            client.post(
                "/api/v1/ai/bounded", content=iter([b"x" * 40000, b"x" * 40000])
            ).status_code
            == 413
        )


def test_context_tier_configuration_is_bounded_and_explicit() -> None:
    import pytest
    from pydantic import ValidationError

    from packages.ai.settings import GatewaySettings

    assert GatewaySettings().context_tiers == [4096, 16384, 32768]
    assert GatewaySettings(context_tiers=[4096, 16384, 32768, 131072]).context_tiers[-1] == 131072
    for tiers in [[], [32768, 4096], [4096, 4096], [4096, 131073]]:
        with pytest.raises(ValidationError):
            GatewaySettings(context_tiers=tiers)
