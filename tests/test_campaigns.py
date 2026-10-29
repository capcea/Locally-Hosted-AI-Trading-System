"""Strict finite research protocols; statistical unknowns and no execution authority."""

from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError
from test_execution_engine import START, initial
from test_risk_math import financial

from packages.campaigns.contracts import ParameterCandidate, ResearchObjective
from packages.campaigns.evaluation import evaluate
from packages.research.strategies import definition


def spec() -> dict[str, Any]:
    state = initial()
    plan = {
        "key": "synthetic-native-campaign",
        "name": "Synthetic native fixture",
        "source_account_id": str(uuid4()),
        "strategy": "EMA_TREND",
        "strategy_digest": definition("EMA_TREND")["digest"],
        "datasets": [
            {
                "dataset_id": str(uuid4()),
                "manifest_sha256": "a" * 64,
                "symbol": state.spec.model_dump(mode="json"),
                "context": {
                    "financial": financial().model_dump(mode="json"),
                    "owner_acknowledged_synthetic_assumptions": True,
                },
            }
        ],
        "parameters": [{}],
        "chronology": {
            k: (START + timedelta(days=n)).isoformat()
            for n, k in enumerate(
                ["start", "discovery_end", "calibration_end", "validation_end", "end"]
            )
        },
        "phase": "DISCOVERY",
        "engine": "EVENT",
        "assumptions": state.model.model_dump(mode="json"),
        "acknowledged_clone_policy_to_isolated_accounts": True,
        "acknowledged_research_only": True,
        "acknowledged_cost_and_bar_assumptions": True,
    }
    return {
        "title": "Synthetic objective",
        "objective": "Test a bounded synthetic hypothesis.",
        "mode": "SYNTHETIC_FIXTURE",
        "template": plan,
        "search_space": [{}],
        "acknowledged_owner_handoffs": True,
        "acknowledged_no_promotion": True,
    }


@pytest.mark.parametrize(
    "patch",
    [
        {"source_code": "import os"},
        {"docker_socket": "/var/run/docker.sock"},
        {"mode": "LIVE"},
        {"schema_version": True},
        {"acknowledged_owner_handoffs": 1},
        {"budgets": {"active_experiments": True}},
        {"budgets": {"experiments": 13}},
        {"budgets": {"candidate_proposals": 9}},
        {"budgets": {"iterations": 3}},
        {"budgets": {"active_experiments": 2}},
        {"budgets": {"runtime_seconds": 0}},
        {"search_space": [{"unknown_parameter": 3}]},
        {"search_space": [{"fast": True}]},
        {"search_space": [{"fast": "2"}]},
        {"search_space": [{"volume": 0.01}]},
    ],
)
def test_refuses_unbounded_unknown_source_or_invalid_parameter_types(patch: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        ResearchObjective.model_validate({**spec(), **patch})


def test_final_holdout_and_adaptive_validation_are_forbidden() -> None:
    body = spec()
    body["template"]["phase"] = "FINAL_HOLDOUT"
    with pytest.raises(ValidationError, match="HOLDOUT"):
        ResearchObjective.model_validate(body)
    body["template"]["phase"] = "VALIDATION"
    with pytest.raises(ValidationError, match="NO_ADAPTIVE"):
        ResearchObjective.model_validate(body)
    body["budgets"] = {"iterations": 1}
    assert ResearchObjective.model_validate(body).template.phase == "VALIDATION"


def test_phase5_trial_fold_and_purge_quotas_are_not_bypassed() -> None:
    body = spec()
    body["template"]["chronology"]["purge_seconds"] = 1
    with pytest.raises(ValidationError, match="PURGE"):
        ResearchObjective.model_validate(body)
    body = spec()
    body["template"].update(parameters=[{}, {}])
    with pytest.raises(ValidationError, match="ONE_PARAMETER"):
        ResearchObjective.model_validate(body)


def test_model_payload_cannot_name_other_datasets_accounts_code_or_execution() -> None:
    payload = {
        "strategy": "EMA_TREND",
        "strategy_digest": definition("EMA_TREND")["digest"],
        "parameters": {},
        "source": "AI_GATEWAY",
    }
    for name in ("dataset_id", "account_id", "source_code", "holdout_release_id", "broker_order"):
        with pytest.raises(ValidationError):
            ParameterCandidate.model_validate({**payload, name: "untrusted injection"})


def canonical(trades: int = 40, net: str = "100") -> dict[str, Any]:
    return {
        "datasets": [{"coverage_pct": "100"}],
        "trials": [
            {
                "risk_validated": True,
                "metrics": {
                    "trade_count": trades,
                    "net_profit": net,
                    "max_drawdown": "2",
                    "max_drawdown_fraction": 0.001,
                    "daily_return_observations": 40,
                    "uncertainty": {"block_bootstrap_mean_95": [1, 4]},
                },
                "transaction_costs": {"commission": "1"},
            }
        ],
    }


def test_fixture_never_becomes_real_candidate_and_sampled_charts_are_not_evidence() -> None:
    objective = ResearchObjective.model_validate(spec())
    accepted = evaluate(objective, canonical(), uuid4())
    assert accepted.decision == "NEEDS_MORE_VALIDATION"
    assert not accepted.paper_eligible and not accepted.trading_authority
    missing = evaluate(objective, {"equity": [{"equity": "999999"}]}, uuid4())
    assert missing.decision == "INSUFFICIENT_EVIDENCE"
    assert evaluate(objective, canonical(trades=2), uuid4()).decision == "INSUFFICIENT_EVIDENCE"
    assert evaluate(objective, canonical(net="-1"), uuid4()).decision == "REJECTED"
    assert any("Independent trial" in s for s in accepted.unknown)


def test_real_gateway_mode_cannot_turn_synthetic_market_evidence_into_a_research_candidate() -> (
    None
):
    body = spec()
    body["mode"] = "AI_GATEWAY"
    body["budgets"] = {"iterations": 1}
    body["template"].update(
        phase="VALIDATION", validation_mode="WALK_FORWARD", cost_multipliers=["1", "2"]
    )
    result = canonical()
    result["datasets"][0]["provenance"] = "SYNTHETIC_TEST_FIXTURE"
    decision = evaluate(ResearchObjective.model_validate(body), result, uuid4())
    assert decision.decision == "NEEDS_MORE_VALIDATION"
    assert "SYNTHETIC_FIXTURE_CANNOT_ESTABLISH_REAL_RESEARCH_CANDIDACY" in decision.reasons
    assert not decision.paper_eligible and not decision.trading_authority
