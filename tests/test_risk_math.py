"""Exact financial/DST oracles and adversarial properties; no real broker observations."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Literal, cast

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError
from test_execution_engine import START, initial, tick

from packages.execution.contracts import OrderRequest, Quote
from packages.execution.engine import session_open
from packages.risk.clock import period_start, reset_instant
from packages.risk.contracts import (
    Decision,
    EquityValues,
    FinancialTerms,
    FXQuote,
    Limits,
    PolicyTerms,
)
from packages.risk.ledger import drawdown_state
from packages.risk.sizing import loss_conversion, size

D = Decimal


def financial(**updates: object) -> FinancialTerms:
    return FinancialTerms.model_validate(
        {
            "payoff": "LINEAR_CONTRACT",
            "base_currency": "EUR",
            "quote_currency": "USD",
            "tick_value_profit_currency": "10",
            "margin_per_unit": "1000",
            "correlation_group": "USD_FOREX",
            "execution_style": "MANUAL",
            "source_reference": "Explicit synthetic fixture, not verified broker specifications",
            "verified_at": START,
            "valid_until": START + timedelta(days=10),
            **updates,
        }
    )


def policy(**updates: object) -> PolicyTerms:
    return PolicyTerms.model_validate(
        {
            "currency": "USD",
            "timezone": "UTC",
            "reset_fold": "EARLIER",
            "daily_loss_pct": "1",
            "total_loss_pct": "3",
            "daily_reference": "BALANCE",
            "daily_amount_basis": "INITIAL",
            "total_mode": "STATIC",
            "trailing_amount_basis": "INITIAL",
            "include_floating": True,
            "allow_overnight": False,
            "allow_weekend": False,
            "automation_permitted": False,
            "max_position_seconds": 3600,
            "permitted_instruments": ["EURUSD"],
            "prohibited_styles": [],
            "news_required": False,
            "news_scope": "NEW_ENTRIES",
            **updates,
        }
    )


def equity(balance: str = "25000", unrealized: str = "0") -> EquityValues:
    return EquityValues(
        balance=D(balance),
        equity=D(balance) + D(unrealized),
        realized_pnl=D(balance) - D("25000"),
        unrealized_pnl=D(unrealized),
        commissions=D(0),
        funding=D(0),
        open_risk=D(0),
        pending_risk=D(0),
        reserved_risk=D(0),
        margin_used=D(0),
        position_count=0,
        groups={},
    )


def order(**updates: object) -> OrderRequest:
    return OrderRequest.model_validate(
        {
            "side": "BUY",
            "order_type": "MARKET",
            "volume": "0.1",
            "stop_loss": "1.0990",
            "take_profit": "1.1030",
            **updates,
        }
    )


def sizing(budget: Decimal | None = None, *, auto_size: bool = False) -> Decision:
    state = tick(initial(), 0)
    state.spec.stop_distance = D(0)
    assert state.quote
    return size(
        state.spec,
        financial(),
        state.quote,
        order(),
        START,
        "USD",
        budget if budget is not None else D("62.5"),
        D("25000"),
        D("3.5"),
        2,
        auto_size=auto_size,
    )


def test_exact_side_aware_cost_and_step_oracle() -> None:
    result = sizing()
    assert result.decision == "ALLOW"
    # .0012 stop distance + .0004 entry/exit slip, 100000 units, 7 round-trip fee.
    assert result.risk_per_unit == D("167")
    assert result.estimated_risk == D("16.7")
    assert result.maximum_volume == D("0.37")
    assert result.estimated_margin == D("100")


@pytest.mark.parametrize("amount", ["0", "0.01", "1.66999999"])
def test_minimum_legal_volume_is_refused_instead_of_rounding_up(amount: str) -> None:
    result = sizing(D(amount), auto_size=True)
    assert result.decision != "ALLOW"
    assert result.approved_volume == 0


def test_exact_cross_currency_liability_uses_ask_and_reverse_bid() -> None:
    fx = FXQuote(
        base="USD",
        quote="JPY",
        bid=D("150"),
        ask=D("150.1"),
        observed_at=START,
        available_at=START,
        valid_until=START + timedelta(seconds=60),
        source_reference="Synthetic USDJPY quote",
    )
    assert loss_conversion("USD", "JPY", [fx], START) == D("150.1")
    assert loss_conversion("JPY", "USD", [fx], START) * D("150") == D(1)
    assert loss_conversion("USD", "JPY", [fx], START, liability=False) == D("150")
    with pytest.raises(ValueError, match="MISSING_OR_STALE"):
        loss_conversion("JPY", "USD", [fx], START + timedelta(seconds=31))
    with pytest.raises(ValueError, match="MISSING_OR_STALE"):
        loss_conversion("EUR", "JPY", [fx], START)


def test_jpy_sizing_uses_reported_contract_and_currency_conversion() -> None:
    state = initial()
    state.spec.symbol = "USDJPY.test"
    state.spec.canonical_symbol = "USDJPY"
    state.spec.tick_size, state.spec.digits = D(".001"), 3
    state.spec.profit_currency = "JPY"
    state.spec.stop_distance = D(".005")
    fx = {
        "base": "USD",
        "quote": "JPY",
        "bid": "150",
        "ask": "150.1",
        "observed_at": START,
        "available_at": START,
        "valid_until": START + timedelta(seconds=30),
        "source_reference": "Synthetic USDJPY quote",
    }
    terms = financial(
        base_currency="USD", quote_currency="JPY", tick_value_profit_currency="100", fx=[fx]
    )
    quote = Quote(
        symbol=state.spec.symbol,
        bid=D("150"),
        ask=D("150.002"),
        event_time=START,
        available_at=START,
        sequence=0,
    )
    result = size(
        state.spec,
        terms,
        quote,
        order(stop_loss="149.900", take_profit="151.000"),
        START,
        "USD",
        D("62.5"),
        D("25000"),
        D(0),
        0,
    )
    assert result.decision == "ALLOW"
    assert result.risk_per_unit == D("68")  # .102 *100000 JPY /150 USDJPY bid.
    assert result.maximum_volume == D(".91")


@pytest.mark.parametrize(
    "asset,symbol,contract,tick_size,entry,stop,take,tick_value",
    [
        ("METAL", "XAUUSD", "100", ".01", "2000.02", "1995", "2010", "1"),
        ("METAL", "XAGUSD", "5000", ".001", "25.002", "24.9", "25.5", "5"),
        ("INDEX", "INDEX.test", "1", ".1", "5000.2", "4990", "5020", ".1"),
        ("CRYPTO", "BTCUSD", "1", ".01", "50000.02", "49000", "51000", ".01"),
    ],
)
def test_explicit_linear_payoffs_for_metal_index_and_crypto(
    asset: str,
    symbol: str,
    contract: str,
    tick_size: str,
    entry: str,
    stop: str,
    take: str,
    tick_value: str,
) -> None:
    state = initial()
    state.spec.asset_class = cast(Literal["FOREX", "METAL", "INDEX", "CRYPTO", "OTHER"], asset)
    state.spec.symbol = state.spec.canonical_symbol = symbol
    state.spec.contract_size, state.spec.tick_size = D(contract), D(tick_size)
    exponent = D(tick_size).as_tuple().exponent
    assert isinstance(exponent, int)
    state.spec.digits = max(0, -exponent)
    state.spec.stop_distance = D(0)
    quote = Quote(
        symbol=symbol,
        bid=D(entry) - D(tick_size),
        ask=D(entry),
        event_time=START,
        available_at=START,
        sequence=0,
    )
    result = size(
        state.spec,
        financial(tick_value_profit_currency=tick_value),
        quote,
        order(volume=".01", stop_loss=stop, take_profit=take),
        START,
        "USD",
        D("62.5"),
        D("25000"),
        D(0),
        0,
    )
    assert result.decision == "ALLOW"
    assert result.estimated_risk == (D(entry) - D(stop)) * D(contract) * D(".01")


@pytest.mark.parametrize(
    "updates,reason",
    [
        ({"payoff": "INVERSE"}, "UNSUPPORTED"),
        ({"payoff": "UNVERIFIED"}, "UNSUPPORTED"),
        ({"tick_value_profit_currency": "9"}, "CONTRADICTORY_TICK"),
        ({"quote_currency": "EUR"}, "CURRENCY_MISMATCH"),
        ({"margin_per_unit": None}, "MARGIN"),
        ({"base_currency": None}, "CURRENCIES_REQUIRED"),
        (
            {"valid_until": START - timedelta(seconds=1), "verified_at": START - timedelta(days=1)},
            "STALE",
        ),
    ],
)
def test_unknown_contradictory_payoffs_fail_closed(updates: dict[str, object], reason: str) -> None:
    state = tick(initial(), 0)
    state.spec.stop_distance = D(0)
    assert state.quote is not None
    result = size(
        state.spec,
        financial(**updates),
        state.quote,
        order(),
        START,
        "USD",
        D("62.5"),
        D("25000"),
        D(0),
        0,
    )
    assert result.decision == "INDETERMINATE"
    assert any(reason in value for value in result.reasons)


@given(st.integers(min_value=1, max_value=100000))
@settings(max_examples=100)
def test_sized_volume_never_exceeds_declared_worst_case_risk_budget(cents: int) -> None:
    budget = D(cents) / 100
    result = sizing(budget, auto_size=True)
    if result.decision == "ALLOW":
        assert result.approved_volume % D(".01") == 0
        assert result.approved_volume >= D(".01")
        # Independent exact cost oracle, no repeated rounding implementation.
        assert result.approved_volume * D("167") <= budget
        assert result.estimated_risk <= budget
        assert result.estimated_margin <= D("25000")


def test_static_trailing_floating_and_committed_loss_references() -> None:
    first = drawdown_state({}, equity(), D("25000"), START, policy())
    loss = drawdown_state(first, equity("25000", "-251"), D("25000"), START, policy())
    assert loss["policy_daily_headroom"] == "-1"
    assert loss["policy_total_headroom"] == "499"
    balance_only = drawdown_state(
        first, equity("25000", "-251"), D("25000"), START, policy(include_floating=False)
    )
    assert balance_only["policy_daily_headroom"] == "250"
    high = drawdown_state(
        first, equity("26000"), D("25000"), START, policy(total_mode="TRAILING_BALANCE")
    )
    trailing = drawdown_state(
        high, equity("25200"), D("25000"), START, policy(total_mode="TRAILING_BALANCE")
    )
    assert trailing["policy_total_headroom"] == "-50"
    static = drawdown_state(first, equity("25200"), D("25000"), START, policy())
    assert static["policy_total_headroom"] == "950"


def test_dst_reset_uses_explicit_fold_and_refuses_nonexistent_reset() -> None:
    early = policy(timezone="Europe/Bucharest", reset_minute=210, reset_fold="EARLIER")
    late = policy(timezone="Europe/Bucharest", reset_minute=210, reset_fold="LATER")
    assert reset_instant(date(2024, 10, 27), early) == datetime(2024, 10, 27, 0, 30, tzinfo=UTC)
    assert reset_instant(date(2024, 10, 27), late) == datetime(2024, 10, 27, 1, 30, tzinfo=UTC)
    with pytest.raises(ValueError, match="NONEXISTENT"):
        reset_instant(date(2024, 3, 31), early)
    midnight = policy(timezone="Europe/Bucharest")
    day1 = period_start(datetime(2024, 3, 31, 12, tzinfo=UTC), midnight)
    day2 = period_start(datetime(2024, 4, 1, 12, tzinfo=UTC), midnight)
    assert day2 - day1 == timedelta(hours=23)


def test_holiday_market_closure_uses_date_values() -> None:
    state = initial()
    assert state.spec.calendar is not None
    state.spec.calendar.holidays = [START.date()]
    assert not session_open(state)


@pytest.mark.parametrize("value", [float(".25"), True, "NaN", "Infinity"])
def test_risk_percentages_reject_nonexact_or_nonfinite_values(value: object) -> None:
    with pytest.raises(ValidationError):
        Limits.model_validate({"per_trade_pct": value})


def test_fill_revalidation_consumes_entry_slippage_buffer_without_counting_it_twice() -> None:
    state = tick(initial(), 0)
    state.spec.stop_distance = D(0)
    assert state.quote is not None
    approved = sizing()
    within = size(
        state.spec,
        financial(),
        state.quote,
        order(),
        START,
        "USD",
        approved.estimated_risk,
        D("25000"),
        D("3.5"),
        2,
        execution_price=D("1.1004"),
    )
    assert within.decision == "ALLOW"
    assert within.estimated_risk == approved.estimated_risk
    beyond = size(
        state.spec,
        financial(),
        state.quote,
        order(),
        START,
        "USD",
        approved.estimated_risk,
        D("25000"),
        D("3.5"),
        2,
        execution_price=D("1.1005"),
    )
    assert beyond.decision == "DENY"


def test_trailing_equity_uses_floating_high_water_and_never_resets_on_loss() -> None:
    terms = policy(total_mode="TRAILING_EQUITY")
    high = drawdown_state({}, equity("25000", "1000"), D("25000"), START, terms)
    later = drawdown_state(high, equity("25000", "200"), D("25000"), START, terms)
    assert later["high_equity"] == "26000"
    assert later["policy_total_headroom"] == "-50"


def test_daily_reset_refuses_unknown_overnight_equity_reference() -> None:
    terms = policy(daily_reference="EQUITY", allow_overnight=True)
    before = drawdown_state({}, equity(), D("25000"), START, terms)
    held = equity("25000", "-10")
    held.position_count = 1
    with pytest.raises(ValueError, match="DAILY_RESET_REFERENCE_MISSING"):
        drawdown_state(before, held, D("25000"), START + timedelta(days=1, seconds=1), terms)
    exact = drawdown_state(before, held, D("25000"), START + timedelta(days=1), terms)
    assert exact["day_equity"] == "24990"


def test_future_and_conflicting_fx_paths_are_not_selected_optimistically() -> None:
    def fx(base: str, quote: str, rate: str) -> FXQuote:
        return FXQuote(
            base=base,
            quote=quote,
            bid=D(rate),
            ask=D(rate),
            observed_at=START,
            available_at=START,
            valid_until=START + timedelta(seconds=30),
            source_reference="Explicit synthetic currency rate",
        )

    quotes = [fx("USD", "JPY", "150"), fx("USD", "EUR", ".9"), fx("EUR", "JPY", "170")]
    with pytest.raises(ValueError, match="CONTRADICTORY_FX_PATHS"):
        loss_conversion("USD", "JPY", quotes, START)
    future = fx("USD", "JPY", "150")
    future.available_at = START + timedelta(seconds=1)
    with pytest.raises(ValueError, match="MISSING_OR_STALE"):
        loss_conversion("USD", "JPY", [future], START)


def test_reopened_netting_position_gets_a_new_duration_reference() -> None:
    from test_execution_engine import apply, submit

    from packages.risk.ledger import position_opened_at

    state = tick(submit(tick(initial("NETTING"), 0)), 1)
    position = next(iter(state.positions.values()))
    state = apply(state, "CLOSE", 1, target_id=position.id, volume=".1")
    assert position_opened_at(state, position.id) is None
    state = tick(submit(state, 2), 3)
    assert position_opened_at(state, position.id) == START + timedelta(seconds=3)


def test_strictest_scopes_cannot_disable_required_calendar_or_relax_caps() -> None:
    from packages.risk.models import ProfileBinding
    from packages.risk.policy import strictest

    broad = ProfileBinding(limits=Limits().model_dump(mode="json"))
    tight = ProfileBinding(
        limits=Limits(
            per_trade_pct=D(".1"), headroom_buffer_pct=D(".2"), requires_economic_calendar=True
        ).model_dump(mode="json")
    )
    result = strictest([broad, tight])
    assert result.per_trade_pct == D(".1") and result.headroom_buffer_pct == D(".2")
    assert result.requires_economic_calendar
