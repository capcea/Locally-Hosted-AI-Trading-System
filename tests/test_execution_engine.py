"""Exact deterministic synthetic scenarios; no real broker connectivity claimed."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from packages.execution.contracts import (
    Command,
    OrderRequest,
    Quote,
    SimState,
    SimulationModel,
    SymbolSpec,
)
from packages.execution.engine import Engine
from packages.market.contracts import SessionCalendar

START = datetime(2024, 1, 2, tzinfo=UTC)
NAMESPACE = UUID("0d5fea91-8870-4fe6-9e69-fdc390ea606d")


def initial(mode: str = "HEDGING", **model: object) -> SimState:
    spec = SymbolSpec.model_validate(
        {
            "symbol": "EURUSD.test",
            "canonical_symbol": "EURUSD",
            "asset_class": "FOREX",
            "tick_size": "0.0001",
            "digits": 4,
            "contract_size": "100000",
            "min_volume": "0.01",
            "max_volume": "100",
            "volume_step": "0.01",
            "profit_currency": "USD",
            "order_types": ["MARKET", "LIMIT", "STOP"],
            "account_mode": mode,
            "oco_supported": True,
            "source": "SYNTHETIC_TEST_FIXTURE",
            "observed_at": START,
            "valid_until": START + timedelta(days=10),
            "calendar": SessionCalendar(
                source="Synthetic calendar", verified_until=START + timedelta(days=10)
            ),
        }
    )
    assumptions = SimulationModel.model_validate(
        {
            "assumption_source": "Explicit SYNTHETIC_TEST_FIXTURE assumptions",
            "commission_per_unit": "0",
            "liquidity_per_tick": "1",
            "synthetic_initial_balance": "25000",
            "account_currency": "USD",
            **model,
        }
    )
    return SimState(
        clock=START, spec=spec, model=assumptions, cash=assumptions.synthetic_initial_balance
    )


def apply(state: SimState, action: str, seconds: int = 0, **fields: object) -> SimState:
    command = Command.model_validate(
        {
            "key": f"{action}-{seconds}-test",
            "action": action,
            "at": START + timedelta(seconds=seconds),
            **fields,
        }
    )
    return Engine(state, NAMESPACE).apply(command)[0]


def tick(
    state: SimState, seconds: int, bid: str = "1.1000", ask: str = "1.1002", **fields: object
) -> SimState:
    at = START + timedelta(seconds=seconds)
    return apply(
        state,
        "TICK",
        seconds,
        quote=Quote.model_validate(
            {
                "symbol": state.spec.symbol,
                "event_time": at,
                "available_at": at,
                "sequence": seconds,
                "bid": bid,
                "ask": ask,
                **fields,
            }
        ),
    )


def submit(state: SimState, seconds: int = 0, **fields: object) -> SimState:
    return apply(
        state,
        "SUBMIT",
        seconds,
        order=OrderRequest.model_validate(
            {
                "side": "BUY",
                "order_type": "MARKET",
                "volume": "0.10",
                **fields,
            }
        ),
    )


def test_market_bid_ask_slippage_fee_and_seed_are_reproducible() -> None:
    state = tick(initial(commission_per_unit="2", slippage_ticks=2, seed=7), 0)
    first = submit(state)
    assert not first.fills and not state.orders
    executed = tick(first, 1)
    assert executed.fills[0].price == Decimal("1.1004")
    assert executed.fills[0].commission == Decimal("0.2")
    assert executed.cash == Decimal("24999.8")
    assert executed.model_dump() == tick(submit(state), 1).model_dump()
    assert list(executed.orders.values())[0].state == "FILLED"


@pytest.mark.parametrize(
    ("kind", "side", "price", "bid", "ask", "expected"),
    [
        ("LIMIT", "BUY", "1.0990", "1.0980", "1.0982", "1.0983"),
        ("LIMIT", "SELL", "1.1010", "1.1020", "1.1022", "1.1019"),
        ("STOP", "BUY", "1.1010", "1.1020", "1.1022", "1.1023"),
        ("STOP", "SELL", "1.0990", "1.0980", "1.0982", "1.0979"),
        ("MARKET", "SELL", None, "1.1000", "1.1005", "1.0999"),
    ],
)
def test_pending_activation_and_gap_side_prices(
    kind: str, side: str, price: str | None, bid: str, ask: str, expected: str
) -> None:
    state = tick(initial(slippage_ticks=1), 0)
    state = submit(state, order_type=kind, side=side, price=price)
    if kind != "MARKET":
        state = tick(state, 1)
        assert not state.fills
    state = tick(state, 2, bid, ask)
    assert state.fills[0].price == Decimal(expected)


def test_partial_fills_preserve_remaining_and_liquidity() -> None:
    state = submit(tick(initial(liquidity_per_tick="0.03"), 0))
    state = tick(state, 1)
    assert state.fills[0].volume == Decimal("0.03")
    assert list(state.orders.values())[0].state == "PARTIALLY_FILLED"
    state = tick(state, 2, ask_liquidity="0.07")
    assert sum(f.volume for f in state.fills) == Decimal("0.10")
    assert list(state.orders.values())[0].state == "FILLED"


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"volume": "0.015"}, "VOLUME_NOT_ON_SUPPORTED_GRID"),
        ({"volume": "101"}, "VOLUME_NOT_ON_SUPPORTED_GRID"),
        ({"stop_loss": "1.1003"}, "PROTECTION_DISTANCE_INVALID"),
        ({"take_profit": "1.1000"}, "PROTECTION_DISTANCE_INVALID"),
        ({"stop_loss": "1.09999"}, "PRICE_NOT_ON_TICK_GRID"),
    ],
)
def test_rejection_is_journalled(overrides: dict[str, object], reason: str) -> None:
    state = submit(tick(initial(), 0), 0, **overrides)
    order = list(state.orders.values())[0]
    assert order.state == "REJECTED" and order.rejection_reason == reason and not state.fills


def test_stop_loss_uses_adverse_gap_and_tp_uses_available_bid() -> None:
    state = submit(tick(initial(slippage_ticks=1), 0), stop_loss="1.0990", take_profit="1.1020")
    state = tick(state, 1)
    gap = tick(state, 2, "1.0950", "1.0955")
    assert gap.fills[-1].price == Decimal("1.0949")
    assert gap.fills[-1].reason == "STOP_LOSS_GAP" and gap.fills[-1].realized_pnl < 0
    profit = tick(state, 2, "1.1030", "1.1035")
    assert profit.fills[-1].price == Decimal("1.1029")
    assert profit.fills[-1].reason == "TAKE_PROFIT"


def test_cancellation_expiration_and_oco() -> None:
    state = submit(tick(initial(), 0), order_type="LIMIT", price="1.0990")
    identifier = list(state.orders.values())[0].id
    cancelled = apply(state, "CANCEL", target_id=identifier)
    assert cancelled.orders[str(identifier)].state == "CANCELLED"
    state = submit(
        tick(initial(), 0),
        order_type="LIMIT",
        price="1.0990",
        expires_at=START + timedelta(seconds=1),
    )
    assert list(tick(state, 1).orders.values())[0].state == "EXPIRED"
    state = submit(tick(initial(), 0), order_type="STOP", price="1.1010", oco_group="breakout")
    state = submit(state, 1, order_type="STOP", side="SELL", price="1.0990", oco_group="breakout")
    state = tick(state, 2, "1.1020", "1.1022")
    assert sorted(o.state for o in state.orders.values()) == ["CANCELLED", "FILLED"]


def test_netting_reduces_position_while_hedging_retains_both() -> None:
    for mode, expected in (("NETTING", 1), ("HEDGING", 2)):
        state = tick(submit(tick(initial(mode), 0)), 1)
        state = submit(state, 2, side="SELL", volume="0.04")
        state = tick(state, 3)
        assert len(state.positions) == expected
        assert sum(p.volume for p in state.positions.values()) == Decimal(
            "0.06" if mode == "NETTING" else "0.14"
        )


def test_modify_partial_close_and_same_quote_liquidity_budget() -> None:
    state = tick(submit(tick(initial(liquidity_per_tick="0.10"), 0)), 1)
    identifier = list(state.positions.values())[0].id
    state = apply(
        state, "MODIFY", 1, target_id=identifier, stop_loss="1.0990", take_profit="1.1020"
    )
    assert state.positions[str(identifier)].stop_loss == Decimal("1.0990")
    state = apply(state, "CLOSE", 1, target_id=identifier, volume="0.04")
    assert state.positions[str(identifier)].volume == Decimal("0.06")
    state.bid_remaining = Decimal("0.01")
    with pytest.raises(ValueError, match="LIQUIDITY_EXHAUSTED"):
        apply(state, "CLOSE", 1, target_id=identifier, volume="0.02")


def test_unknown_cannot_be_resubmitted_until_real_simulated_truth_reconciliation() -> None:
    state = apply(tick(initial(), 0), "FAULT", fault="AFTER_SUBMIT")
    state = submit(state)
    assert list(state.orders.values())[0].state == "UNKNOWN" and not state.fills
    with pytest.raises(ValueError, match="RECONCILE_UNKNOWN"):
        submit(state, 1)
    state = apply(state, "RECONCILE", 1)
    assert state.incident is None
    state = tick(state, 2)
    assert len(state.fills) == 1
    missing = submit(apply(tick(initial(), 0), "FAULT", fault="DELAY_ACK"))
    missing.broker_truth.clear()
    missing = apply(missing, "RECONCILE", 1)
    assert missing.incident == "BROKER_TRUTH_MISSING"
    assert list(missing.orders.values())[0].state == "UNKNOWN"


@pytest.mark.parametrize("fault", ["BEFORE_SUBMIT", "REJECT_NEXT"])
def test_known_failures_are_not_unknown(fault: str) -> None:
    state = submit(apply(tick(initial(), 0), "FAULT", fault=fault))
    assert list(state.orders.values())[0].state == "REJECTED" and not state.fills


def test_latency_staleness_calendar_mismatch_and_duplicate_quotes() -> None:
    state = submit(tick(initial(latency_ms=2000), 0))
    assert not tick(state, 1).fills and tick(state, 2).fills
    stale = submit(tick(initial(), 0), 31)
    assert list(stale.orders.values())[0].rejection_reason == "QUOTE_STALE_OR_UNAVAILABLE"
    state = tick(initial(), 0)
    with pytest.raises(ValueError, match="DUPLICATE_OR_OUT_OF_ORDER"):
        tick(state, 0)
    with pytest.raises(ValueError, match="MISMATCH"):
        tick(state, 1, symbol="OTHER")
    state.spec.calendar = None
    assert list(submit(state).orders.values())[0].state == "REJECTED"
    state = tick(initial(), 0)
    state.spec.valid_until = START + timedelta(seconds=1)
    assert list(submit(state, 2).orders.values())[0].rejection_reason == "SYMBOL_SPEC_STALE"


def test_funding_only_charges_actual_holding_interval_in_supplied_model() -> None:
    state = tick(submit(tick(initial(swap_per_unit_per_day="-2"), 0)), 1)
    state = apply(state, "SWAP", 86401)
    assert state.swap == Decimal("-0.2")
    assert state.cash == Decimal("24999.8")
    with pytest.raises(ValueError, match="NOT_SUPPLIED"):
        apply(initial(), "SWAP", 1)


def test_float_amounts_and_future_quotes_are_refused() -> None:
    with pytest.raises(ValidationError):
        OrderRequest(side="BUY", order_type="MARKET", volume=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Quote(
            symbol="EURUSD",
            event_time=START,
            available_at=START - timedelta(seconds=1),
            sequence=0,
            bid=Decimal("1"),
            ask=Decimal("2"),
        )
