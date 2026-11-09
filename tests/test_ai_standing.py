"""Standing policy rejects authority expansion and unlimited/ambiguous budgets."""

from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from packages.ai.standing_contracts import StandingInput


def policy() -> dict[str, Any]:
    return {
        "connection_ids": [str(uuid4())],
        "roles": ["RESEARCH"],
        "data_categories": ["documentation"],
        "operations": ["INFER"],
        "request_usd": "0.01",
        "daily_usd": "0.50",
        "monthly_usd": "5",
    }


@pytest.mark.parametrize(
    "updates",
    [
        {"monthly_usd": "0.10"},
        {"monthly_usd": "999"},
        {"daily_usd": "6"},
        {"request_usd": "0.11"},
        {"request_usd": "0.00"},
        {"monthly_usd": "NaN"},
        {"operations": ["BROKER_ORDER"]},
        {"data_categories": ["holdout"]},
        {"roles": ["RESEARCH", "RESEARCH"]},
        {"trading_authority": True},
        {"endpoint_url": "https://unapproved.example"},
    ],
)
def test_invalid_standing_scope_and_budget(updates: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        StandingInput.model_validate({**policy(), **updates})


def test_standing_policy_preserves_exact_decimal_strings_and_explicit_scope() -> None:
    value = StandingInput.model_validate({**policy(), "request_usd": "0.010000"})
    assert value.request_usd == "0.010000" and value.operations == ["INFER"]
