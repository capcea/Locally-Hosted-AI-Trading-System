"""Expanding chronological training, purged labels, embargo and independent OOS accounts."""

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from packages.research.contracts import ExperimentInput
from packages.research.engine import event_trial
from packages.research.models import ResearchRun
from packages.research.statistics import folds


def evaluate(
    db: Session,
    research: ResearchRun,
    plan: ExperimentInput,
    datasets: list[dict[str, Any]],
    attempt: int,
    key: str,
    heartbeat: Callable[[int], None],
) -> dict[str, Any]:
    c = plan.chronology
    times = sorted({row.available_at.timestamp() for d in datasets for row in d["rows"]})
    windows = folds(
        times,
        c.calibration_end.timestamp(),
        c.validation_end.timestamp(),
        c.end.timestamp(),
        c.walk_forward_folds,
        c.purge_seconds,
        c.embargo_seconds,
    )
    ordinal = 0
    out = []
    descriptions = []
    for index, window in enumerate(windows):
        training_end = datetime.fromtimestamp(window["train_end"], UTC)
        train_results = []
        for parameters in plan.parameters:
            for stress in plan.cost_multipliers:
                trial = event_trial(
                    db,
                    research,
                    plan,
                    datasets,
                    parameters,
                    stress,
                    attempt,
                    ordinal,
                    key,
                    heartbeat,
                    (c.start, training_end),
                )
                ordinal += 1
                train_results.append(
                    (Decimal(str(trial["metrics"]["net_profit"])), parameters, stress, trial)
                )
        # Select using training net P&L only, deterministic stable parameter order for ties.
        best = max(range(len(train_results)), key=lambda i: train_results[i][0])
        score, parameters, stress, train = train_results[best]
        start = datetime.fromtimestamp(window["test_start"], UTC)
        end = datetime.fromtimestamp(window["test_end"], UTC)
        test = event_trial(
            db,
            research,
            plan,
            datasets,
            parameters,
            stress,
            attempt,
            ordinal,
            key,
            heartbeat,
            (start, end),
        )
        ordinal += 1
        description = {
            "fold": index,
            "train_start": c.start.isoformat(),
            "train_end": training_end.isoformat(),
            "oos_start": start.isoformat(),
            "oos_end": end.isoformat(),
            "selected_parameters": parameters.model_dump(mode="json"),
            "selected_cost_multiplier": str(stress),
            "training_net": str(score),
            "training_candidate_metrics": [r[3]["metrics"] for r in train_results],
            "oos_metrics": test["metrics"],
            "purge_seconds": c.purge_seconds,
            "embargo_seconds": c.embargo_seconds,
            "selection_rule": "maximum training net P&L; OOS never selects parameters",
        }
        test["walk_forward"] = [description]
        out.append(test)
        descriptions.append(description)
    return {
        "engine": "EVENT_JOURNAL_RISK_GATEWAY",
        "trials": out,
        "walk_forward": descriptions,
        "source": "SIMULATED",
        "paper_eligible": False,
    }
