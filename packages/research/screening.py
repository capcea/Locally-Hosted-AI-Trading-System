"""Arrow-vectorized exploratory accounting; one-observation execution lag, never authority."""

import hashlib
from collections.abc import Callable
from datetime import timedelta
from decimal import Decimal
from typing import Any

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.compute as pc  # type: ignore[import-untyped]

from packages.research.contracts import ExperimentInput
from packages.research.data import phase_range
from packages.research.strategies import signal
from packages.risk.sizing import payoff_multiplier


def screen(
    plan: ExperimentInput, datasets: list[dict[str, Any]], heartbeat: Callable[[int], None]
) -> dict[str, Any]:
    trials: list[dict[str, Any]] = []
    ordinal = 0
    start, end = phase_range(plan)
    for parameters in plan.parameters:
        for stress in plan.cost_multipliers:
            pnl = Decimal(0)
            observations = 0
            signals = []
            for dataset in datasets:
                if dataset["pin"].role != "EXECUTION":
                    continue
                if dataset["pin"].symbol.profit_currency != plan.assumptions.account_currency:
                    raise ValueError("SCREEN_CROSS_CURRENCY_REQUIRES_EVENT_ENGINE")
                if any(d["pin"].role == "CONFIRMATION" for d in datasets):
                    raise ValueError("CONFIRMATION_STREAMS_REQUIRE_EVENT_ENGINE")
                rows = sorted(dataset["rows"], key=lambda r: (r.available_at, r.sequence))
                history = []
                positions = []
                changes = []
                costs = []
                funding = []
                holding = 0
                pending: tuple[int, Any] | None = None
                opened = None
                previous = Decimal(0)
                for i, row in enumerate(rows):
                    at = row.available_at
                    close = row.close if row.close is not None else (row.bid + row.ask) / 2
                    multiplier = payoff_multiplier(
                        dataset["pin"].symbol, dataset["pin"].context.financial, at
                    )
                    if (
                        not dataset["pin"].symbol.observed_at
                        <= at
                        <= dataset["pin"].symbol.valid_until
                    ):
                        raise ValueError("SYMBOL_SPEC_STALE")
                    positions.append(float(holding))
                    changes.append(float(close - previous) if i else 0.0)
                    seconds = (at - rows[i - 1].available_at).total_seconds() if i else 0.0
                    rate = plan.assumptions.swap_per_unit_per_day or Decimal(0)
                    funding.append(float(abs(holding) * parameters.volume * rate) * seconds / 86400)
                    spread = (
                        row.ask - row.bid
                        if row.bid is not None and row.ask is not None
                        else plan.bar_spread
                    )
                    if spread is None:
                        raise ValueError("SCREEN_SPREAD_UNVERIFIED")
                    cost = (
                        spread * stress * multiplier / 2
                        + plan.assumptions.commission_per_unit * stress
                        + dataset["pin"].symbol.tick_size
                        * plan.assumptions.slippage_ticks
                        * stress
                        * multiplier
                    )
                    turnover = 0
                    # The previous observation's decision can execute only
                    # now, after marking old exposure.
                    delay = timedelta(
                        milliseconds=plan.assumptions.latency_ms
                        + plan.assumptions.latency_jitter_ms
                    )
                    if pending is not None and at >= pending[1] + delay:
                        next_holding = pending[0]
                        turnover = abs(next_holding - holding)
                        holding = next_holding
                        opened = at if holding else None
                        pending = None
                    costs.append(float(turnover * parameters.volume * cost))
                    history.append(
                        {
                            "at": at.isoformat(),
                            "close": str(close),
                            "high": str(row.high or close),
                            "low": str(row.low or close),
                        }
                    )
                    raw = signal(plan.strategy, history, parameters, at) if start <= at < end else 0
                    keep = (
                        int.from_bytes(
                            hashlib.sha256(
                                f"{plan.seed}:{dataset['dataset_id']}:{row.sequence}".encode()
                            ).digest()[:8],
                            "big",
                        )
                        % 100
                        < parameters.random_keep_pct
                    )
                    if pending is None:
                        if holding and (
                            raw
                            and raw != holding
                            or opened is not None
                            and (at - opened).total_seconds() >= parameters.max_hold_seconds
                        ):
                            pending = (0, at)
                        elif not holding and raw and keep:
                            pending = (raw, at)
                    signals.append(
                        {
                            "dataset": dataset["dataset_id"],
                            "at": at.isoformat(),
                            "raw_direction": raw,
                            "random_entry_allowed": keep,
                            "next_observation_intent": pending[0] if pending else None,
                        }
                    )
                    observations += 1
                    previous = close
                    if i % 50 == 0:
                        heartbeat(
                            min(
                                95,
                                ordinal
                                * 100
                                // (len(plan.parameters) * len(plan.cost_multipliers)),
                            )
                        )
                gross = pc.multiply(
                    pc.multiply(pa.array(positions), pa.array(changes)),
                    float(parameters.volume * multiplier),
                )
                approximate = (
                    pc.sum(pc.add(pc.subtract(gross, pa.array(costs)), pa.array(funding))).as_py()
                    or 0.0
                )
                if holding:
                    if (
                        end - rows[-1].available_at
                    ).total_seconds() > plan.assumptions.max_quote_age_seconds:
                        raise ValueError("TERMINAL_SCREEN_QUOTE_STALE")
                    approximate -= abs(holding) * float(parameters.volume * cost)
                pnl += Decimal(str(approximate))
            trials.append(
                {
                    "ordinal": ordinal,
                    "parameters": parameters.model_dump(mode="json"),
                    "cost_multiplier": str(stress),
                    "approximate_net": str(pnl),
                    "observations": observations,
                    "signals": signals,
                    "risk_validated": False,
                    "paper_eligible": False,
                    "source": "SIMULATED",
                    "unknown_funding_cost": plan.assumptions.swap_per_unit_per_day is None,
                    "warning": "Exploratory Arrow mark-to-close model with one-observation lag and maximum declared latency; no SL/TP, pending-order, liquidity, calendar or risk certification. Event validation mandatory.",
                }
            )
            ordinal += 1
    trials.sort(key=lambda t: Decimal(t["approximate_net"]), reverse=True)
    return {
        "engine": "ARROW_VECTORIZED_SCREEN",
        "trials": trials,
        "paper_eligible": False,
        "source": "SIMULATED",
    }
