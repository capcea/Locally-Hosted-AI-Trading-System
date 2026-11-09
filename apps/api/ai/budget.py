"""Content-only conservative capacity accounting. No tokenizer or prompt logging."""

from typing import Any

from packages.ai.contracts import ContextMode, Generation
from packages.ai.prompts import canonical

FRAMING_TOKENS = 512


def measure(
    messages: list[dict[str, str]],
    schema: dict[str, Any],
    parameters: Generation,
    models: list[dict[str, Any]],
    *,
    question: str,
    context: list[dict[str, Any]],
    storage_limit: int,
) -> dict[str, int]:
    def limit(value: Any) -> int:
        return value if type(value) is int and value >= 0 else 0

    registered = min((limit(m.get("context_ceiling")) for m in models), default=0)
    verified = min(
        (limit(m.get("capabilities", {}).get("context_tokens")) for m in models), default=0
    )
    content_bytes = sum(len(m["content"].encode("utf-8")) for m in messages)
    schema_bytes = len(canonical(schema).encode("utf-8"))
    # Keep the existing conservative one-byte-per-token bound, but do not count HTTP/JSON
    # escaping as model input. Structured-output schema DOES consume input capacity.
    return {
        "question_bytes": len(question.encode("utf-8")),
        "context_bytes": len(canonical(context).encode("utf-8")),
        "system_bytes": sum(len(m["content"].encode()) for m in messages if m["role"] == "system"),
        "user_bytes": sum(len(m["content"].encode()) for m in messages if m["role"] == "user"),
        "prompt_json_bytes": len(canonical(messages).encode("utf-8")),
        "message_content_bytes": content_bytes,
        "schema_bytes": schema_bytes,
        "input_upper_bound": content_bytes + schema_bytes,
        "framing_tokens": FRAMING_TOKENS,
        "output_tokens": parameters.output_tokens,
        "requested_context_tokens": parameters.context_tokens,
        "registered_context_tokens": registered,
        "verified_context_tokens": verified,
        "effective_context_tokens": min(parameters.context_tokens, registered, verified),
        "required_context_upper_bound": content_bytes
        + schema_bytes
        + FRAMING_TOKENS
        + parameters.output_tokens,
        "storage_input_bytes": len(canonical({"messages": messages}).encode("utf-8")),
        "storage_limit_bytes": storage_limit,
    }


def refusal(budget: dict[str, int]) -> str | None:
    if budget["requested_context_tokens"] > min(
        budget["registered_context_tokens"], budget["verified_context_tokens"]
    ):
        return "AI_CONTEXT_BUDGET_UNVERIFIED"
    if budget["required_context_upper_bound"] > budget["effective_context_tokens"]:
        return "AI_CONTEXT_BUDGET_EXCEEDED"
    return None


def allocate(
    budget: dict[str, int], mode: ContextMode | None, tiers: list[int]
) -> tuple[dict[str, int], str | None]:
    """Choose capacity, never authority. None preserves an explicit legacy numeric request."""
    result = dict(budget)
    ceiling = min(
        budget["registered_context_tokens"], budget["verified_context_tokens"], max(tiers)
    )
    required = budget["required_context_upper_bound"]
    selected = budget["requested_context_tokens"]
    failure = None
    if mode == "AUTO":
        possible = [tier for tier in tiers if required <= tier <= ceiling]
        if not possible:
            # Diagnostics describe the maximum usable budget; no request will be enqueued.
            selected = max((tier for tier in tiers if tier <= ceiling), default=ceiling)
            failure = "AI_CONTEXT_BUDGET_EXCEEDED"
        else:
            selected = min(possible)
    elif mode:
        selected = {"RAPID": 4096, "STANDARD": 16384, "COMPLEX": 32768}[mode]
        if selected not in tiers:
            failure = "AI_CONTEXT_TIER_UNAVAILABLE"
    result.update(
        selected_context_tokens=selected,
        requested_context_tokens=selected,
        effective_context_tokens=min(selected, ceiling),
        platform_context_ceiling=max(tiers),
        minimum_fitting_tier=next((tier for tier in tiers if tier >= required), 0),
        remaining_context_tokens=max(0, min(selected, ceiling) - required),
    )
    failure = failure or refusal(result)
    if selected > max(tiers):
        failure = "AI_CONTEXT_TIER_UNAVAILABLE"
    return result, failure
