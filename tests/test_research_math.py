"""Causal/financial/statistical oracles; no measured historical profitability claims."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from packages.research.contracts import Parameters, StrategyName
from packages.research.statistics import deflated_sharpe, folds, metrics, purged_cv, robustness
from packages.research.strategies import NAMES, definition, signal

START = datetime(2024, 1, 2, tzinfo=UTC)


def history(prices: list[int]) -> list[dict[str, str]]:
    return [
        {
            "at": (START + timedelta(minutes=i)).isoformat(),
            "close": str(v),
            "high": str(v + 1),
            "low": str(v - 1),
        }
        for i, v in enumerate(prices)
    ]


@pytest.mark.parametrize("name", NAMES)
def test_trusted_benchmarks_have_immutable_definition_and_explicit_warmup(
    name: StrategyName,
) -> None:
    assert definition(name)["digest"] == definition(name)["digest"]
    assert definition(name)["paper_eligible"] is False
    assert signal(name, history([100, 101]), Parameters(), START + timedelta(minutes=2)) == 0


@pytest.mark.parametrize("name", NAMES)
def test_future_observation_cannot_be_passed_to_signal(name: StrategyName) -> None:
    with pytest.raises(ValueError, match="FUTURE"):
        signal(name, history(list(range(100, 130))), Parameters(), START + timedelta(minutes=10))


@given(st.lists(st.integers(min_value=50, max_value=150), min_size=25, max_size=50))
def test_ema_prefix_is_independent_of_later_prices(prices: list[int]) -> None:
    prefix = history(prices[:25])
    at = START + timedelta(minutes=24)
    assert signal("EMA_TREND", prefix, Parameters(), at) == signal(
        "EMA_TREND", history(prices)[:25], Parameters(), at
    )


def test_donchian_uses_prior_window_not_current_high() -> None:
    h = history([100] * 20 + [110])
    h[-1]["high"] = "999"
    assert signal("DONCHIAN", h, Parameters(), START + timedelta(minutes=20)) == 1


def test_long_only_control_cannot_emit_short() -> None:
    assert (
        signal(
            "EMA_TREND",
            history(list(range(130, 100, -1))),
            Parameters(direction="LONG_ONLY"),
            START + timedelta(minutes=30),
        )
        == 0
    )


def test_chronological_folds_purge_horizons_and_embargo() -> None:
    result = folds(list(map(float, range(200))), 60, 160, 200, 2, 10, 5)
    for fold in result:
        assert max(fold["train"]) + 10 < min(fold["test"]) - 5
        assert not set(fold["train"]) & set(fold["test"])
    with pytest.raises(ValueError, match="CHRONOLOGICAL"):
        folds([1, 2, 3], 3, 2, 4, 2, 0, 0)


def test_overlapping_labels_are_purged_and_embargoed() -> None:
    result = purged_cv([0, 10, 20, 30, 40], [15, 25, 35, 45, 55], [2], 5)
    assert result == {"train": [0], "test": [2]}


def test_metrics_exact_profit_drawdown_and_small_sample_refusal() -> None:
    curve = [
        {"equity": "100", "at": "2024-01-01T00:00:00Z", "timestamp": 0},
        {"equity": "110", "at": "2024-01-02T00:00:00Z", "timestamp": 86400},
        {"equity": "99", "at": "2024-01-03T00:00:00Z", "timestamp": 172800},
    ]
    result = metrics(
        curve,
        [{"net": "10", "holding_seconds": 10}, {"net": "-11", "holding_seconds": 20}],
        100,
        7,
        100,
    )
    assert result["net_profit"] == -1 and result["max_drawdown"] == 11
    assert result["max_drawdown_fraction"] == pytest.approx(0.1)
    assert result["profit_factor"] == pytest.approx(10 / 11)
    assert result["expectancy"] == -0.5 and result["win_rate"] == 0.5
    assert result["sharpe"] is None and result["sortino"] is None and result["calmar"] is None
    assert result["uncertainty"]["bootstrap_mean_95"] is None


def test_empty_trade_ratios_are_unknown_not_infinite_profit() -> None:
    result = metrics([{"equity": "100", "at": "2024-01-01", "timestamp": 0}], [], 100, 1, 100)
    assert result["profit_factor"] is None and result["win_rate"] is None


def test_resampling_is_seeded_and_changes_with_input() -> None:
    series = list(map(float, [-3, -2, -1, 0, 1, 2, 3, 4, 5, 6]))
    assert robustness(series, 10, 100) == robustness(series, 10, 100)
    assert robustness(series, 10, 100) != robustness([x + 1 for x in series], 10, 100)


def test_deflated_sharpe_penalizes_more_trials_and_invalid_samples() -> None:
    low = deflated_sharpe(0.15, 0.002, 10, 1250, -3, 10)
    high = deflated_sharpe(0.15, 0.002, 100, 1250, -3, 10)
    assert low["value"] > high["value"]
    assert high["benchmark_per_period"] == pytest.approx(0.1132, abs=0.0001)
    assert deflated_sharpe(0.1, 0.002, 1, 1250, 0, 3)["value"] is None
    assert deflated_sharpe(0.1, 0.002, 10, 5, 0, 3)["value"] is None


def test_bounded_parameter_contract_rejects_float_sizing() -> None:
    with pytest.raises(ValueError):
        Parameters.model_validate({"volume": 0.1})
    with pytest.raises(ValueError):
        Parameters(fast=30, slow=10)
    assert Parameters(volume=Decimal(".01")).volume == Decimal(".01")
