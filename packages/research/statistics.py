"""Explicit descriptive/uncertainty statistics; floats never authorize money or execution."""

import math
import random
from datetime import date
from statistics import NormalDist, mean, stdev
from typing import Any


def deflated_sharpe(
    sr: float, variance_trials: float, trials: int, observations: int, skew: float, kurtosis: float
) -> dict[str, Any]:
    if trials < 2 or observations < 30 or variance_trials <= 0:
        return {"value": None, "reason": "INSUFFICIENT_INDEPENDENT_TRIAL_MODEL"}
    normal = NormalDist()
    benchmark = math.sqrt(variance_trials) * (
        (1 - 0.5772156649015329) * normal.inv_cdf(1 - 1 / trials)
        + 0.5772156649015329 * normal.inv_cdf(1 - 1 / (trials * math.e))
    )
    denominator = 1 - skew * sr + (kurtosis - 1) * sr * sr / 4
    if denominator <= 0 or not all(math.isfinite(x) for x in (sr, benchmark, denominator)):
        return {"value": None, "reason": "INVALID_DSR_MOMENTS"}
    return {
        "value": normal.cdf(
            (sr - benchmark) * math.sqrt(observations - 1) / math.sqrt(denominator)
        ),
        "benchmark_per_period": benchmark,
        "assumption": (
            "declared independent-trial count/variance; non-excess kurtosis; no "
            "autocorrelation correction"
        ),
    }


def folds(
    times: list[float],
    calibration: float,
    validation: float,
    end: float,
    count: int,
    purge: int,
    embargo: int,
) -> list[dict[str, Any]]:
    if not times or not min(times) < calibration < validation < end or purge < 0 or embargo < 0:
        raise ValueError("INVALID_CHRONOLOGICAL_SPLIT")
    result = []
    width = (validation - calibration) / count
    for number in range(count):
        boundary = calibration + width * number
        train = [i for i, t in enumerate(times) if t + purge < boundary]
        test = [i for i, t in enumerate(times) if boundary + embargo <= t < boundary + width]
        if not train or not test:
            raise ValueError("FOLD_EMPTY_AFTER_PURGE_OR_EMBARGO")
        result.append(
            {
                "train": train,
                "test": test,
                "train_end": boundary - purge,
                "test_start": boundary + embargo,
                "test_end": boundary + width,
            }
        )
    return result


def purged_cv(
    starts: list[float], ends: list[float], test_indices: list[int], embargo: float
) -> dict[str, list[int]]:
    if (
        len(starts) != len(ends)
        or not test_indices
        or any(b < a for a, b in zip(starts, ends, strict=True))
    ):
        raise ValueError("INVALID_LABEL_INTERVALS")
    lower = min(starts[i] for i in test_indices)
    upper = max(ends[i] for i in test_indices)
    train = [
        i
        for i, (a, b) in enumerate(zip(starts, ends, strict=True))
        if i not in test_indices and (b < lower or a > upper + embargo)
    ]
    return {"train": train, "test": test_indices}


def robustness(values: list[float], seed: int, samples: int, block: int = 5) -> dict[str, Any]:
    if len(values) < 10:
        return {
            "bootstrap_mean_95": None,
            "block_bootstrap_mean_95": None,
            "monte_carlo": None,
            "reason": "FEWER_THAN_10_TRADES",
        }
    rng = random.Random(seed)  # noqa: S311 - reproducible statistical resampling, not security
    size = len(values)
    block = min(block, size)
    iid = []
    blocked = []
    drawdowns = []
    for _ in range(samples):
        iid.append(mean(rng.choices(values, k=size)))
        path: list[float] = []
        while len(path) < size:
            begin = rng.randrange(size)
            path.extend(values[(begin + j) % size] for j in range(block))
        blocked.append(mean(path[:size]))
        shuffled = list(values)
        rng.shuffle(shuffled)
        total = peak = worst = 0.0
        for x in shuffled:
            total += x
            peak = max(peak, total)
            worst = max(worst, peak - total)
        drawdowns.append(worst)

    def interval(items: list[float]) -> list[float]:
        ordered = sorted(items)
        return [ordered[int((samples - 1) * 0.025)], ordered[int((samples - 1) * 0.975)]]

    return {
        "bootstrap_mean_95": interval(iid),
        "block_bootstrap_mean_95": interval(blocked),
        "block_length": block,
        "monte_carlo": {
            "permuted_trade_drawdown_95": interval(drawdowns),
            "samples": samples,
            "does_not_model_new_returns": True,
        },
        "warning": (
            "Percentile intervals are exploratory; stationarity/dependence and sample "
            "adequacy are not certified."
        ),
    }


def metrics(
    equity: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    initial: float,
    seed: int,
    samples: int,
) -> dict[str, Any]:
    if initial <= 0 or not equity:
        raise ValueError("MISSING_EQUITY_OR_CAPITAL")
    amounts = [float(p["equity"]) for p in equity]
    times = [float(p["timestamp"]) for p in equity]
    gains = [float(t["net"]) for t in trades]
    wins = [x for x in gains if x > 0]
    losses = [x for x in gains if x < 0]
    peak = initial
    max_dd = max_dd_pct = underwater = 0.0
    last_peak = times[0]
    consecutive = longest = 0
    for value, at in zip(amounts, times, strict=True):
        if value >= peak:
            peak = value
            last_peak = at
        else:
            underwater = max(underwater, at - last_peak)
        max_dd = max(max_dd, peak - value)
        max_dd_pct = max(max_dd_pct, (peak - value) / peak if peak > 0 else 0)
    for value in gains:
        consecutive = consecutive + 1 if value < 0 else 0
        longest = max(longest, consecutive)
    # One executable account mark per UTC day, including the initial capital reference.
    daily: dict[str, float] = {}
    for point in equity:
        daily[str(point["at"])[:10]] = float(point["equity"])
    previous = initial
    returns: list[float] = []
    for value in daily.values():
        if previous <= 0:
            returns = []
            break
        returns.append(value / previous - 1)
        previous = value
    sd = stdev(returns) if len(returns) > 1 else 0
    downside = math.sqrt(sum(min(0, x) ** 2 for x in returns) / len(returns)) if returns else 0
    dates = [date.fromisoformat(day) for day in daily]
    regular = all((b - a).days == 1 for a, b in zip(dates, dates[1:], strict=False))
    sufficient = len(returns) >= 30 and regular
    duration = max(0, times[-1] - times[0])
    annualized = None
    if duration >= 365.25 * 86400 and amounts[-1] > 0:
        annualized = (amounts[-1] / initial) ** (365.25 * 86400 / duration) - 1
    return {
        "net_profit": amounts[-1] - initial,
        "net_return": amounts[-1] / initial - 1,
        "max_drawdown": max_dd,
        "max_drawdown_fraction": max_dd_pct,
        "profit_factor": sum(wins) / -sum(losses) if losses else None,
        "expectancy": mean(gains) if gains else None,
        "win_rate": len(wins) / len(gains) if gains else None,
        "average_winner": mean(wins) if wins else None,
        "average_loser": mean(losses) if losses else None,
        "risk_reward_distribution": [t.get("realized_r") for t in trades],
        "sharpe": mean(returns) / sd * math.sqrt(365.25) if sufficient and sd else None,
        "sortino": mean(returns) / downside * math.sqrt(365.25)
        if sufficient and downside
        else None,
        "calmar": annualized / max_dd_pct
        if sufficient and annualized is not None and max_dd_pct > 0
        else None,
        "annualized_volatility": sd * math.sqrt(365.25) if sufficient and sd else None,
        "recovery_factor": (amounts[-1] - initial) / max_dd if max_dd else None,
        "maximum_consecutive_losses": longest,
        "time_underwater_seconds": underwater,
        "trade_count": len(trades),
        "holding_seconds": [t["holding_seconds"] for t in trades],
        "daily_return_observations": len(returns),
        "ratios_reason": None
        if sufficient
        else "FEWER_THAN_30_DAILY_OBSERVATIONS"
        if len(returns) < 30
        else "IRREGULAR_CALENDAR_DAILY_OBSERVATIONS",
        "annualization_convention": (
            "365.25 calendar days; ratios withheld for missing UTC days; no forward-filled prices"
        ),
        "daily_returns": returns,
        "uncertainty": robustness(gains, seed, samples),
        "source": "SIMULATED",
        "paper_eligible": False,
    }
