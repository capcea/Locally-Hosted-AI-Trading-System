"""Conservative decisions from complete canonical Phase5 artifacts, never chart samples."""

from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from packages.campaigns.contracts import EvaluationDecision, ResearchObjective


def evaluate(
    objective: ResearchObjective, result: dict[str, Any], evidence: UUID
) -> EvaluationDecision:
    observations: list[dict[str, Any]] = []
    unknown = [
        "Independent trial count is UNKNOWN; correlated attempts are not independent evidence.",
        "Parameter sensitivity and server-matched comparison require separate evidence.",
        "Prior data exposure outside this registry is UNKNOWN.",
    ]
    reasons = []
    insufficient = False
    rejected = False
    uncertain = False
    trials = result.get("trials", [])
    if not trials or len(trials) > 24:
        insufficient = True
        reasons.append("NO_BOUNDED_CANONICAL_TRIAL_EVIDENCE")
    for trial in trials[:24]:
        metrics = trial.get("metrics")
        if not isinstance(metrics, dict) or trial.get("risk_validated") is not True:
            insufficient = True
            reasons.append("SCREEN_OR_UNVALIDATED_RISK_RESULT")
            continue
        names = (
            "net_profit",
            "max_drawdown",
            "max_drawdown_fraction",
            "trade_count",
            "daily_return_observations",
            "ratios_reason",
            "uncertainty",
        )
        observations.append(
            {
                "ordinal": trial.get("ordinal"),
                "parameters": trial.get("parameters"),
                "cost_multiplier": trial.get("cost_multiplier"),
                "metrics": {name: metrics.get(name) for name in names},
                "transaction_costs": trial.get("transaction_costs"),
                "walk_forward": trial.get("walk_forward"),
            }
        )
        required = ("trade_count", "net_profit", "max_drawdown_fraction")
        if any(metrics.get(name) is None for name in required):
            insufficient = True
            reasons.append("CANONICAL_METRIC_MISSING")
            continue
        if metrics["trade_count"] < objective.evaluation.minimum_trades:
            insufficient = True
            reasons.append("INSUFFICIENT_TRADE_SAMPLE")
        if Decimal(str(metrics["net_profit"])) <= 0:
            rejected = True
            reasons.append("NONPOSITIVE_NET_AFTER_MODELED_COSTS")
        if Decimal(str(metrics["max_drawdown_fraction"])) > Decimal(
            objective.evaluation.maximum_drawdown_fraction
        ):
            rejected = True
            reasons.append("DECLARED_RESEARCH_DRAWDOWN_CRITERION_EXCEEDED")
        interval = metrics.get("uncertainty", {}).get("block_bootstrap_mean_95")
        if not interval or interval[0] <= 0:
            uncertain = True
            reasons.append("EXPLORATORY_UNCERTAINTY_NOT_RESOLVED")
        if not trial.get("transaction_costs"):
            insufficient = True
            reasons.append("COST_EVIDENCE_MISSING")
        if (metrics.get("daily_return_observations") or 0) < 30:
            uncertain = True
            reasons.append("TEMPORAL_SAMPLE_TOO_SHORT_FOR_RATIOS")
    if any(
        d.get("coverage_pct") != "100" and Decimal(str(d.get("coverage_pct") or 0)) < 100
        for d in result.get("datasets", [])
    ) or not result.get("datasets"):
        insufficient = True
        reasons.append("DATA_COVERAGE_INCOMPLETE_OR_UNKNOWN")
    if len(objective.template.cost_multipliers) < 2:
        uncertain = True
        reasons.append("COST_STRESS_NOT_TESTED")
    if objective.template.phase != "VALIDATION":
        uncertain = True
        reasons.append("IN_SAMPLE_ONLY_NOT_INDEPENDENT_OOS")
    if objective.template.validation_mode != "WALK_FORWARD":
        uncertain = True
        reasons.append("CHRONOLOGICAL_STABILITY_NOT_ESTABLISHED")
    if objective.mode == "SYNTHETIC_FIXTURE" or any(
        d.get("provenance") == "SYNTHETIC_TEST_FIXTURE" for d in result.get("datasets", [])
    ):
        uncertain = True
        reasons.append("SYNTHETIC_FIXTURE_CANNOT_ESTABLISH_REAL_RESEARCH_CANDIDACY")
    decision: Literal[
        "INSUFFICIENT_EVIDENCE", "REJECTED", "NEEDS_MORE_VALIDATION", "RESEARCH_CANDIDATE"
    ] = (
        "INSUFFICIENT_EVIDENCE"
        if insufficient
        else "REJECTED"
        if rejected
        else "NEEDS_MORE_VALIDATION"
        if uncertain
        else "RESEARCH_CANDIDATE"
    )
    reasons.append("RESEARCH_ONLY_NO_PAPER_OR_TRADING_AUTHORITY")
    return EvaluationDecision(
        decision=decision,
        reasons=list(dict.fromkeys(reasons)),
        observations=observations,
        unknown=unknown,
        evidence_id=evidence,
        source=objective.mode,
    )
