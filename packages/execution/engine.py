"""Pure event-driven broker model. No SDK, network, wall clock or external credential access."""

import hashlib
from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, Decimal, localcontext
from uuid import UUID, uuid5
from zoneinfo import ZoneInfo

from packages.execution.contracts import (
    Command,
    EngineEvent,
    Fill,
    OrderRequest,
    Position,
    Quote,
    SimOrder,
    SimState,
)

ACTIVE = {"ACKNOWLEDGED", "PARTIALLY_FILLED"}
ZERO = Decimal(0)


def rounded(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000000000001"), rounding=ROUND_HALF_EVEN)


def session_open(state: SimState) -> bool:
    calendar = state.spec.calendar
    if calendar is None or calendar.verified_until < state.clock:
        return False
    local = state.clock.astimezone(ZoneInfo(calendar.timezone))
    minute = local.hour * 60 + local.minute
    return (
        local.weekday() in calendar.weekdays
        and local.date() not in calendar.holidays
        and calendar.opens <= minute < calendar.closes
    )


def validate_spec(state: SimState, allow_conversion: bool = False) -> None:
    if not state.spec.observed_at <= state.clock <= state.spec.valid_until:
        raise ValueError("SYMBOL_SPEC_STALE")
    if state.spec.profit_currency != state.model.account_currency and not allow_conversion:
        raise ValueError("CURRENCY_CONVERSION_NOT_MODELLED")


def fresh_quote(state: SimState) -> Quote:
    quote = state.quote
    if (
        quote is None
        or quote.available_at > state.clock
        or state.clock - quote.event_time > timedelta(seconds=state.model.max_quote_age_seconds)
    ):
        raise ValueError("QUOTE_STALE_OR_UNAVAILABLE")
    return quote


def volume_ok(state: SimState, volume: Decimal) -> bool:
    spec = state.spec
    return spec.min_volume <= volume <= spec.max_volume and volume % spec.volume_step == 0


def prices_ok(state: SimState, request: OrderRequest, reference: Decimal) -> None:
    for price in (request.price, request.stop_loss, request.take_profit):
        if price is not None and price % state.spec.tick_size:
            raise ValueError("PRICE_NOT_ON_TICK_GRID")
    distance = state.spec.stop_distance
    for price, below in (
        (request.stop_loss, request.side == "BUY"),
        (request.take_profit, request.side == "SELL"),
    ):
        if price is not None and (
            (price >= reference if below else price <= reference)
            or (distance is not None and abs(reference - price) < distance)
        ):
            raise ValueError("PROTECTION_DISTANCE_INVALID")


def advance_clock(state: SimState, at: datetime) -> tuple[SimState, list[EngineEvent]]:
    """Advance the one synthetic funding clock, reusable before risk assessment and execution."""
    if at < state.clock:
        raise ValueError("COMMAND_TIME_REVERSED")
    result = state.model_copy(deep=True)
    previous_clock = result.clock
    result.clock = at
    events: list[EngineEvent] = []
    with localcontext() as context:
        context.prec = 60
        if result.model.swap_per_unit_per_day is not None and at > previous_clock:
            delta = at - previous_clock
            micros = (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds
            held = sum((position.volume for position in result.positions.values()), ZERO)
            funding = rounded(
                held * result.model.swap_per_unit_per_day * Decimal(micros) / Decimal(86400000000)
            )
            result.swap = rounded(result.swap + funding)
            result.cash = rounded(result.cash + funding)
            result.swap_through = at
            if funding:
                events.append(
                    EngineEvent(
                        kind="SWAP_ACCRUAL",
                        timestamp=at,
                        source_sequence=result.quote.sequence if result.quote else 0,
                        payload={
                            "amount": str(funding),
                            "elapsed_microseconds": micros,
                            "model": result.model.assumption_source,
                        },
                    )
                )
    return result, events


class Engine:
    def __init__(
        self,
        state: SimState,
        namespace: UUID,
        entry_guard: Callable[[SimState, SimOrder, Decimal, Decimal], str | None] | None = None,
        profit_converter: Callable[[Decimal, datetime], Decimal] | None = None,
        pnl_multiplier: Decimal | None = None,
    ) -> None:
        self.state = state.model_copy(deep=True)
        self.namespace = namespace
        self.events: list[EngineEvent] = []
        self.entry_guard = entry_guard
        self.profit_converter = profit_converter
        self.pnl_multiplier = pnl_multiplier or state.spec.contract_size

    def event(self, kind: str, order: SimOrder | None = None, **payload: object) -> None:
        self.events.append(
            EngineEvent(
                kind=kind,
                order_id=order.id if order else None,
                timestamp=self.state.clock,
                source_sequence=self.state.quote.sequence if self.state.quote else 0,
                payload=payload,
            )
        )

    def transition(self, order: SimOrder, state: str, reason: str | None = None) -> None:
        old = order.state
        # State assignments are revalidated, including the closed Literal state set.
        order.state = SimOrder.model_validate({**order.model_dump(), "state": state}).state
        order.rejection_reason = reason
        self.event(
            "ORDER_STATE",
            order,
            before=old,
            after=state,
            reason=reason,
            broker_order_id=order.broker_order_id,
        )

    def reject(self, order: SimOrder, reason: str) -> None:
        self.transition(order, "REJECTED", reason)

    def submit(self, command: Command) -> None:
        state = self.state
        if command.order is None:
            raise ValueError("ORDER_REQUIRED")
        if len(state.orders) >= 200 or len(state.fills) >= 2000:
            raise ValueError("SIMULATION_CAPACITY_REACHED")
        if any(order.state == "UNKNOWN" for order in state.orders.values()):
            raise ValueError("RECONCILE_UNKNOWN_BEFORE_SUBMIT")
        request = command.order
        order_id = uuid5(self.namespace, command.key)
        if str(order_id) in state.orders:
            raise ValueError("DUPLICATE_COMMAND_REQUIRES_JOURNAL_LOOKUP")
        jitter = int.from_bytes(
            hashlib.sha256(f"{state.model.seed}:{command.key}".encode()).digest()[:4], "big"
        )
        delay = state.model.latency_ms + jitter % (state.model.latency_jitter_ms + 1)
        order = SimOrder(
            id=order_id,
            idempotency_key=command.key,
            request=request,
            state="CREATED",
            created_at=state.clock,
            eligible_at=state.clock + timedelta(milliseconds=delay),
        )
        state.orders[str(order.id)] = order
        self.event("ORDER_CREATED", order, request=request.model_dump(mode="json"))
        try:
            validate_spec(state, self.profit_converter is not None)
            quote = fresh_quote(state)
            if not session_open(state):
                raise ValueError("MARKET_CLOSED_OR_CALENDAR_UNVERIFIED")
            if request.order_type not in state.spec.order_types:
                raise ValueError("ORDER_TYPE_UNSUPPORTED")
            if not volume_ok(state, request.volume):
                raise ValueError("VOLUME_NOT_ON_SUPPORTED_GRID")
            if request.oco_group and not state.spec.oco_supported:
                raise ValueError("OCO_UNSUPPORTED")
            if request.expires_at and request.expires_at <= state.clock:
                raise ValueError("EXPIRATION_INVALID")
            prices_ok(
                state, request, request.price or (quote.ask if request.side == "BUY" else quote.bid)
            )
            if (
                request.order_type == "LIMIT"
                and request.price is not None
                and (
                    request.price >= quote.ask
                    if request.side == "BUY"
                    else request.price <= quote.bid
                )
            ):
                raise ValueError("LIMIT_MUST_START_PASSIVE")
            if (
                request.order_type == "STOP"
                and request.price is not None
                and (
                    request.price <= quote.ask
                    if request.side == "BUY"
                    else request.price >= quote.bid
                )
            ):
                raise ValueError("STOP_MUST_START_PENDING")
        except ValueError as error:
            self.reject(order, str(error))
            return
        self.transition(order, "VALIDATED")
        self.transition(order, "SUBMIT_PENDING")
        if state.connection != "CONNECTED" or state.fault == "BEFORE_SUBMIT":
            state.connection, state.fault = "DISCONNECTED", "NONE"
            self.reject(order, "NOT_SENT_CONNECTION_LOST")
            return
        order.broker_order_id = "SIM-" + str(order.id)
        self.transition(order, "SUBMITTED")
        if state.fault == "REJECT_NEXT":
            state.fault = "NONE"
            state.broker_truth[str(order.id)] = "REJECTED"
            self.reject(order, "SYNTHETIC_BROKER_REJECTION")
            return
        state.broker_truth[str(order.id)] = "ACKNOWLEDGED"
        if state.fault in {"AFTER_SUBMIT", "DELAY_ACK"}:
            state.fault = "NONE"
            state.connection = "DISCONNECTED"
            state.incident = "SIMULATED_SUBMIT_BEFORE_ACK_UNCERTAINTY"
            self.transition(order, "UNKNOWN", "RECONCILIATION_REQUIRED")
            self.event("INCIDENT", order, code=state.incident)
            return
        self.transition(order, "ACKNOWLEDGED")
        # Orders cannot reuse an old quote's liquidity; fills occur only on subsequent TICK events.

    def add_fill(
        self,
        position: Position,
        order: SimOrder | None,
        side: str,
        volume: Decimal,
        price: Decimal,
        pnl: Decimal,
        reason: str,
    ) -> None:
        state = self.state
        if self.profit_converter is not None:
            pnl = self.profit_converter(pnl, state.clock)
        fee = rounded(volume * state.model.commission_per_unit)
        deal_id = "SIM-" + str(uuid5(self.namespace, f"deal:{len(state.fills)}"))
        fill = Fill(
            deal_id=deal_id,
            order_id=order.id if order else None,
            position_id=position.id,
            side="BUY" if side == "BUY" else "SELL",
            volume=volume,
            price=price,
            commission=fee,
            realized_pnl=rounded(pnl),
            timestamp=state.clock,
            sequence=state.quote.sequence if state.quote else 0,
            reason=reason,
        )
        state.fills.append(fill)
        state.cash = rounded(state.cash + pnl - fee)
        state.fees = rounded(state.fees + fee)
        position.realized_pnl = rounded(position.realized_pnl + pnl)
        self.event("FILL", order, **fill.model_dump(mode="json"))

    def fill_order(self, order: SimOrder, volume: Decimal, price: Decimal) -> None:
        state, request = self.state, order.request
        identifier = (
            uuid5(self.namespace, "net-position")
            if state.spec.account_mode == "NETTING"
            else order.id
        )
        position = state.positions.get(str(identifier))
        pnl = ZERO
        if position is None or position.volume == 0:
            position = Position(
                id=identifier,
                symbol=state.spec.symbol,
                side=request.side,
                volume=volume,
                entry_price=price,
                stop_loss=request.stop_loss,
                take_profit=request.take_profit,
            )
            state.positions[str(identifier)] = position
        elif position.side == request.side:
            position.entry_price = rounded(
                (position.entry_price * position.volume + price * volume)
                / (position.volume + volume)
            )
            position.volume += volume
            # Explicit last-fill protection policy for the one netting position.
            position.stop_loss, position.take_profit = request.stop_loss, request.take_profit
        else:
            closing = min(position.volume, volume)
            pnl = (price - position.entry_price) * closing * self.pnl_multiplier
            if position.side == "SELL":
                pnl = -pnl
            remaining = position.volume - volume
            position.volume = abs(remaining)
            if remaining < 0:
                position.side, position.entry_price = request.side, price
                position.stop_loss, position.take_profit = request.stop_loss, request.take_profit
        self.add_fill(position, order, request.side, volume, price, pnl, "ORDER")
        old = order.filled_volume
        order.filled_volume += volume
        order.average_price = rounded(
            (order.average_price * old + price * volume) / order.filled_volume
        )
        self.transition(
            order, "FILLED" if order.filled_volume == request.volume else "PARTIALLY_FILLED"
        )
        state.broker_truth[str(order.id)] = order.state
        if request.oco_group:
            for sibling in state.orders.values():
                if (
                    sibling.id != order.id
                    and sibling.request.oco_group == request.oco_group
                    and sibling.state in ACTIVE
                ):
                    self.transition(sibling, "CANCELLED", "SYNTHETIC_OCO_PEER_FILL")
                    state.broker_truth[str(sibling.id)] = "CANCELLED"

    def close(self, position: Position, volume: Decimal, price: Decimal, reason: str) -> None:
        if volume <= 0 or volume > position.volume or volume % self.state.spec.volume_step:
            raise ValueError("INVALID_CLOSE_VOLUME")
        pnl = (price - position.entry_price) * volume * self.pnl_multiplier
        if position.side == "SELL":
            pnl = -pnl
        side = "SELL" if position.side == "BUY" else "BUY"
        position.volume -= volume
        self.add_fill(position, None, side, volume, price, pnl, reason)

    def tick(self, quote: Quote) -> None:
        state = self.state
        if quote.symbol != state.spec.symbol or quote.available_at != state.clock:
            raise ValueError("QUOTE_ACCOUNT_SYMBOL_OR_CLOCK_MISMATCH")
        if state.quote and (quote.available_at, quote.sequence) <= (
            state.quote.available_at,
            state.quote.sequence,
        ):
            raise ValueError("DUPLICATE_OR_OUT_OF_ORDER_QUOTE")
        if state.quote and quote.event_time < state.quote.event_time:
            raise ValueError("OUT_OF_ORDER_QUOTE_EVENT_TIME")
        if quote.bid % state.spec.tick_size or quote.ask % state.spec.tick_size:
            raise ValueError("QUOTE_OFF_TICK_GRID")
        state.quote = quote
        state.bid_remaining, state.ask_remaining = ZERO, ZERO
        self.event("QUOTE", bid=str(quote.bid), ask=str(quote.ask), sequence=quote.sequence)
        for order in state.orders.values():
            if (
                order.state in ACTIVE
                and order.request.expires_at
                and order.request.expires_at <= state.clock
            ):
                self.transition(order, "EXPIRED")
                state.broker_truth[str(order.id)] = "EXPIRED"
        if state.connection != "CONNECTED" or not session_open(state):
            return
        validate_spec(state, self.profit_converter is not None)
        fresh_quote(state)
        slip = state.spec.tick_size * state.model.slippage_ticks
        bid_left = (
            quote.bid_liquidity
            if quote.bid_liquidity is not None
            else state.model.liquidity_per_tick
        )
        ask_left = (
            quote.ask_liquidity
            if quote.ask_liquidity is not None
            else state.model.liquidity_per_tick
        )
        # Protection precedes new entries. Gaps use the available quote side.
        for position in state.positions.values():
            if position.volume == 0:
                continue
            price = quote.bid if position.side == "BUY" else quote.ask
            stop = position.stop_loss
            take = position.take_profit
            stopped = stop is not None and (
                price <= stop if position.side == "BUY" else price >= stop
            )
            taken = take is not None and (
                price >= take if position.side == "BUY" else price <= take
            )
            if stopped or taken:
                available = bid_left if position.side == "BUY" else ask_left
                volume = (
                    min(position.volume, available) / state.spec.volume_step
                ).to_integral_value(rounding=ROUND_DOWN) * state.spec.volume_step
                if volume:
                    execution = (
                        max(state.spec.tick_size, price - slip)
                        if position.side == "BUY"
                        else price + slip
                    )
                    if taken and take is not None:
                        execution = (
                            max(take, execution) if position.side == "BUY" else min(take, execution)
                        )
                    self.close(
                        position, volume, execution, "STOP_LOSS_GAP" if stopped else "TAKE_PROFIT"
                    )
                    if position.side == "BUY":
                        bid_left -= volume
                    else:
                        ask_left -= volume
        for order in sorted(state.orders.values(), key=lambda o: (o.created_at, str(o.id))):
            if order.state not in ACTIVE or order.eligible_at > state.clock:
                continue
            request = order.request
            price = quote.ask if request.side == "BUY" else quote.bid
            active = request.order_type == "MARKET" or order.activated
            if request.price is not None:
                active |= (
                    (price <= request.price if request.side == "BUY" else price >= request.price)
                    if request.order_type == "LIMIT"
                    else (
                        price >= request.price if request.side == "BUY" else price <= request.price
                    )
                )
            if not active:
                continue
            if request.order_type == "STOP" and not order.activated:
                order.activated = True
                self.event("PENDING_ACTIVATED", order)
            available = ask_left if request.side == "BUY" else bid_left
            volume = (
                min(request.volume - order.filled_volume, available) / state.spec.volume_step
            ).to_integral_value(rounding=ROUND_DOWN) * state.spec.volume_step
            if not volume:
                continue
            price = (
                price + slip if request.side == "BUY" else max(state.spec.tick_size, price - slip)
            )
            if request.order_type == "LIMIT" and request.price is not None:
                price = (
                    min(price, request.price)
                    if request.side == "BUY"
                    else max(price, request.price)
                )
            try:
                prices_ok(state, request, price)
            except ValueError:
                self.reject(order, "PROTECTION_INVALID_AT_FILL")
                state.broker_truth[str(order.id)] = "REJECTED"
                continue
            if self.entry_guard is not None:
                refusal = self.entry_guard(state, order, volume, price)
                if refusal:
                    self.reject(order, refusal)
                    state.broker_truth[str(order.id)] = "REJECTED"
                    continue
            self.fill_order(order, volume, price)
            if request.side == "BUY":
                ask_left -= volume
            else:
                bid_left -= volume
        state.bid_remaining, state.ask_remaining = bid_left, ask_left

    def apply(self, command: Command) -> tuple[SimState, list[EngineEvent]]:
        self.state, clock_events = advance_clock(self.state, command.at)
        self.events.extend(clock_events)
        state = self.state
        with localcontext() as context:
            context.prec = 60
            if command.action == "SUBMIT":
                self.submit(command)
            elif command.action == "TICK":
                if command.quote is None:
                    raise ValueError("QUOTE_REQUIRED")
                self.tick(command.quote)
            elif command.action == "FAULT":
                if command.fault is None:
                    raise ValueError("FAULT_REQUIRED")
                state.fault = command.fault
                if command.fault == "NONE":
                    state.connection = "CONNECTED"
                self.event("FAULT_CONFIGURATION", code=command.fault)
            elif command.action == "RECONCILE":
                for order in state.orders.values():
                    if order.state == "UNKNOWN":
                        truth = state.broker_truth.get(str(order.id))
                        if truth is None:
                            state.incident = "BROKER_TRUTH_MISSING"
                            self.event("INCIDENT", order, code=state.incident)
                            continue
                        self.transition(order, truth, "SIMULATED_AUTHORITATIVE_RECONCILIATION")
                if not any(o.state == "UNKNOWN" for o in state.orders.values()):
                    state.incident = None
                    state.connection = "CONNECTED"
                self.event("RECONCILIATION", unresolved=state.incident is not None)
            elif command.action == "CANCEL":
                cancelling = state.orders.get(str(command.target_id))
                if (
                    cancelling is None
                    or cancelling.state not in ACTIVE
                    or state.connection != "CONNECTED"
                ):
                    raise ValueError("ORDER_NOT_CANCELLABLE_RECONCILE_IF_UNKNOWN")
                self.transition(cancelling, "CANCELLED")
                state.broker_truth[str(cancelling.id)] = "CANCELLED"
            elif command.action in {"MODIFY", "CLOSE"}:
                if state.connection != "CONNECTED" or state.incident:
                    raise ValueError("RECONCILIATION_REQUIRED")
                position = state.positions.get(str(command.target_id))
                if position is None or position.volume <= 0:
                    raise ValueError("OPEN_POSITION_REQUIRED")
                validate_spec(state, self.profit_converter is not None)
                quote = fresh_quote(state)
                if not session_open(state):
                    raise ValueError("MARKET_CLOSED")
                price = quote.bid if position.side == "BUY" else quote.ask
                if state.spec.freeze_distance is not None:
                    for protection in (position.stop_loss, position.take_profit):
                        if (
                            protection is not None
                            and abs(price - protection) < state.spec.freeze_distance
                        ):
                            raise ValueError("POSITION_FROZEN")
                if command.action == "MODIFY":
                    request = OrderRequest(
                        side=position.side,
                        order_type="MARKET",
                        volume=position.volume,
                        stop_loss=command.stop_loss,
                        take_profit=command.take_profit,
                    )
                    prices_ok(state, request, price)
                    position.stop_loss, position.take_profit = (
                        command.stop_loss,
                        command.take_profit,
                    )
                    self.event("POSITION_MODIFIED", position=position.model_dump(mode="json"))
                else:
                    if command.volume is None:
                        raise ValueError("CLOSE_VOLUME_REQUIRED")
                    available = (
                        state.bid_remaining if position.side == "BUY" else state.ask_remaining
                    )
                    if command.volume > available:
                        raise ValueError("CLOSE_LIQUIDITY_EXHAUSTED_WAIT_FOR_NEXT_TICK")
                    slip = state.spec.tick_size * state.model.slippage_ticks
                    execution = (
                        max(state.spec.tick_size, price - slip)
                        if position.side == "BUY"
                        else price + slip
                    )
                    self.close(position, command.volume, execution, "MANUAL_SIMULATED_CLOSE")
                    if position.side == "BUY":
                        state.bid_remaining -= command.volume
                    else:
                        state.ask_remaining -= command.volume
            elif command.action == "SWAP":
                if state.model.swap_per_unit_per_day is None:
                    raise ValueError("SWAP_MODEL_NOT_SUPPLIED")
                self.event("SWAP_MODEL_CHECKPOINT", cumulative=str(state.swap))
        if len(state.fills) > 2000:
            raise ValueError("SIMULATION_FILL_CAPACITY_REACHED")
        return state, self.events
