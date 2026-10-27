"""Reviewed fixed registry: causal deterministic benchmark signals, never imported strategy code."""

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from packages.research.contracts import Parameters, StrategyName

D = Decimal
NAMES: tuple[StrategyName, ...] = (
    "EMA_TREND",
    "MA_CROSS",
    "DONCHIAN",
    "BOLLINGER",
    "RSI",
    "ATR_BREAKOUT",
    "OPENING_RANGE",
    "SESSION_MOMENTUM",
)
VERSION = "1.0.0"


def definition(name: StrategyName) -> dict[str, Any]:
    body = {
        "id": name,
        "version": VERSION,
        "source_digest": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "implementation": "reviewed-fixed-registry-v1",
        "asset_classes": ["FOREX", "METAL", "INDEX", "CRYPTO"],
        "data_types": ["TICK", "BAR"],
        "automated": True,
        "execution_style": "INTRADAY_BENCHMARK",
        "timeframes": ["TICK", "M1", "M5", "M15", "H1", "H4", "D1"],
        "parameters": Parameters.model_json_schema(),
        "entry": name + ": causal completed-observation feature, next eligible execution event",
        "exit": (
            "opposite signal, explicit maximum holding time, mandatory SL/TP or "
            "end-of-run liquidation"
        ),
        "sizing": "explicit volume request bounded by actual Phase4 RiskGateway",
        "session": "UTC minutes constrained further by verified symbol/policy calendar",
        "quality": "VALID immutable dataset, explicit warmup; unknown tick coverage stays unknown",
        "assumptions": (
            "Experimental benchmark; no profitability or external tradability certification"
        ),
        "source": "SIMULATED",
        "paper_eligible": False,
    }
    body["digest"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return body


def ema(values: list[Decimal], period: int) -> Decimal:
    value = values[0]
    weight = D(2) / D(period + 1)
    for item in values[1:]:
        value += weight * (item - value)
    return value


def signal(name: StrategyName, history: list[dict[str, Any]], p: Parameters, at: datetime) -> int:
    """Caller supplies only already visible complete observations, never a future frame."""
    if any(datetime.fromisoformat(str(row["at"])) > at for row in history):
        raise ValueError("FUTURE_OBSERVATION_IN_FEATURE_WINDOW")
    if name not in NAMES:
        raise ValueError("UNREGISTERED_STRATEGY")
    minute = at.hour * 60 + at.minute
    if not p.session_open <= minute < p.session_close:
        return 0
    if len(history) < max(p.slow, p.lookback + 1):
        return 0
    values = [D(str(r["close"])) for r in history]
    last = values[-1]
    previous = values[-p.lookback - 1 : -1]
    direction = 0
    if name == "EMA_TREND":
        level = ema(values, p.slow)
        direction = (
            1
            if last > level and level > ema(values[:-1], p.slow)
            else -1
            if last < level and level < ema(values[:-1], p.slow)
            else 0
        )
    elif name == "MA_CROSS":
        fast = sum(values[-p.fast :]) / p.fast
        slow = sum(values[-p.slow :]) / p.slow
        old_fast = sum(values[-p.fast - 1 : -1]) / p.fast
        old_slow = sum(values[-p.slow - 1 : -1]) / p.slow
        direction = (
            1
            if fast > slow and old_fast <= old_slow
            else -1
            if fast < slow and old_fast >= old_slow
            else 0
        )
    elif name == "DONCHIAN":
        highs = [D(str(r["high"])) for r in history[-p.lookback - 1 : -1]]
        lows = [D(str(r["low"])) for r in history[-p.lookback - 1 : -1]]
        direction = 1 if last > max(highs) else -1 if last < min(lows) else 0
    elif name == "BOLLINGER":
        average = sum(previous, D(0)) / len(previous)
        std = (sum(((x - average) ** 2 for x in previous), D(0)) / len(previous)).sqrt()
        direction = (
            1
            if last < average - p.threshold * std
            else -1
            if last > average + p.threshold * std
            else 0
        )
    elif name == "RSI":
        diffs = [values[i] - values[i - 1] for i in range(len(values) - p.lookback, len(values))]
        up, down = sum(max(D(0), x) for x in diffs), sum(max(D(0), -x) for x in diffs)
        rsi = D(50) if up + down == 0 else D(100) * up / (up + down)
        level = min(D(49), p.threshold * 10)
        direction = 1 if rsi < level else -1 if rsi > 100 - level else 0
    elif name == "ATR_BREAKOUT":
        prior = history[-p.lookback - 1 : -1]
        tr = [
            max(
                D(str(r["high"])) - D(str(r["low"])),
                abs(D(str(r["high"])) - values[len(values) - p.lookback - 2 + i])
                if len(values) > p.lookback + 1
                else D(0),
                abs(D(str(r["low"])) - values[len(values) - p.lookback - 2 + i])
                if len(values) > p.lookback + 1
                else D(0),
            )
            for i, r in enumerate(prior)
        ]
        atr = sum(tr, D(0)) / len(tr)
        direction = (
            1
            if last > values[-2] + p.threshold * atr
            else -1
            if last < values[-2] - p.threshold * atr
            else 0
        )
    else:
        today = [r for r in history if datetime.fromisoformat(str(r["at"])).date() == at.date()]
        opening = [
            r
            for r in today
            if p.session_open
            <= datetime.fromisoformat(str(r["at"])).hour * 60
            + datetime.fromisoformat(str(r["at"])).minute
            < p.session_open + p.opening_minutes
        ]
        if not opening or minute < p.session_open + p.opening_minutes:
            return 0
        if name == "OPENING_RANGE":
            direction = (
                1
                if last > max(D(str(r["high"])) for r in opening)
                else -1
                if last < min(D(str(r["low"])) for r in opening)
                else 0
            )
        else:
            first = D(str(opening[0]["close"]))
            direction = 1 if last > first else -1 if last < first else 0
    if (
        direction > 0
        and p.direction == "SHORT_ONLY"
        or direction < 0
        and p.direction == "LONG_ONLY"
    ):
        return 0
    return direction


def observed_regime(history: list[dict[str, Any]], p: Parameters, tick: Decimal) -> str:
    values = [D(str(r["close"])) for r in history]
    if len(values) < p.slow:
        return "WARMUP"
    level = ema(values[:-1], p.slow)
    trend = "UP" if values[-1] > level else "DOWN" if values[-1] < level else "FLAT"
    changes = [
        abs(b - a)
        for a, b in zip(values[-p.lookback - 1 : -1], values[-p.lookback :], strict=False)
    ]
    volatility = (
        "HIGH_VOL"
        if changes and sum(changes, D(0)) / len(changes) > p.threshold * tick
        else "LOW_VOL"
    )
    return trend + "/" + volatility
