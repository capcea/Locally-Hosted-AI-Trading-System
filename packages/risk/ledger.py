"""Account-serialized projections of actual durable synthetic positions and cash deltas."""

import hashlib
from datetime import UTC, datetime
from decimal import ROUND_FLOOR, Decimal, localcontext
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.domain.serialization import canonical
from packages.execution.contracts import OrderRequest, SimState
from packages.execution.engine import ACTIVE, advance_clock, session_open, validate_spec
from packages.execution.models import SimulationRun
from packages.persistence.models import Incident, TradingAccount
from packages.risk.clock import period_start
from packages.risk.contracts import Context, EquityValues, PolicyTerms
from packages.risk.models import (
    AccountControl,
    Reservation,
    RiskAuthorization,
    RiskLedger,
    RunContext,
)
from packages.risk.sizing import ZERO, ceil_money, loss_conversion, payoff_multiplier


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def ledger_money(value: Decimal) -> Decimal:
    with localcontext() as precision:
        precision.prec = 80
        return value.quantize(Decimal("0.000000000001"), rounding=ROUND_FLOOR)


def lock_account(db: Session, account_id: UUID) -> TradingAccount:
    account = db.scalar(
        select(TradingAccount).where(TradingAccount.id == account_id).with_for_update()
    )
    if account is None:
        raise ValueError("ACCOUNT_NOT_FOUND")
    return account


def context_for(db: Session, run: SimulationRun) -> tuple[RunContext, Context]:
    context = db.scalar(
        select(RunContext)
        .where(RunContext.run_id == run.id)
        .order_by(RunContext.version.desc())
        .limit(1)
    )
    if context is None:
        raise ValueError("RISK_CONTEXT_MISSING")
    state = SimState.model_validate(run.state)
    if context.spec_digest != digest(state.spec.model_dump(mode="json")):
        raise ValueError("SYMBOL_SPEC_BINDING_CHANGED")
    return context, Context.model_validate(context.body)


def incident(db: Session, account: TradingAccount, reason: str) -> None:
    name = "SIMULATED RISK: " + reason[:95]
    existing = db.scalar(
        select(Incident.id).where(
            Incident.account_id == account.id, Incident.status == "OPEN", Incident.name == name
        )
    )
    if existing is None:
        db.add(
            Incident(
                owner_id=account.owner_id,
                account_id=account.id,
                name=name,
                severity="CRITICAL",
                status="OPEN",
                source="SYNTHETIC_TEST_FIXTURE",
            )
        )


def position_opened_at(state: SimState, position_id: UUID) -> datetime | None:
    signed_volume = ZERO
    opened = None
    for fill in state.fills:
        if fill.position_id != position_id:
            continue
        before = signed_volume
        signed_volume += fill.volume if fill.side == "BUY" else -fill.volume
        if signed_volume == 0:
            opened = None
        elif before == 0 or before * signed_volume < 0:
            opened = fill.timestamp
    return opened


def request_risk(
    state: SimState,
    context: Context,
    request: OrderRequest,
    volume: Decimal,
    reference: Decimal,
    at: datetime,
) -> Decimal:
    if request.stop_loss is None:
        raise ValueError("MISSING_PROTECTIVE_STOP")
    multiplier = payoff_multiplier(state.spec, context.financial, at)
    fx = loss_conversion(
        state.spec.profit_currency, state.model.account_currency, context.financial.fx, at
    )
    distance = max(
        ZERO,
        reference - request.stop_loss if request.side == "BUY" else request.stop_loss - reference,
    )
    return ceil_money(
        volume
        * (
            (distance + state.spec.tick_size * Decimal(state.model.slippage_ticks + 2))
            * multiplier
            * fx
            + state.model.commission_per_unit * 2
            + context.financial.funding_buffer_per_unit
        )
    )


def project(
    db: Session,
    account: TradingAccount,
    at: datetime,
    overrides: dict[UUID, SimState] | None = None,
) -> tuple[EquityValues, list[str]]:
    balance, unrealized, realized, commissions, funding = (
        account.initial_capital,
        ZERO,
        ZERO,
        ZERO,
        ZERO,
    )
    opened, pending, margin, count = ZERO, ZERO, ZERO, 0
    groups: dict[str, Decimal] = {}
    strategies: dict[str, Decimal] = {}
    reasons: list[str] = []
    runs = db.scalars(
        select(SimulationRun)
        .where(SimulationRun.account_id == account.id)
        .order_by(SimulationRun.id)
    )
    with localcontext() as precision:
        precision.prec = 80
        for run in runs:
            from packages.execution.journal import verify

            if not verify(db, run):
                raise ValueError("EXECUTION_JOURNAL_INTEGRITY_FAILURE")
            state = (
                overrides[run.id]
                if overrides and run.id in overrides
                else (SimState.model_validate(run.state))
            )
            if state.model.synthetic_initial_balance != account.initial_capital:
                reasons.append("RUN_INITIAL_BALANCE_MISMATCH")
            if state.clock > at:
                raise ValueError("ACCOUNT_EXPOSURE_CLOCK_REVERSED")
            state, _ = advance_clock(state, at)
            balance += state.cash - state.model.synthetic_initial_balance
            commissions += state.fees
            funding += state.swap
            realized += sum((fill.realized_pnl for fill in state.fills), ZERO)
            positions = [p for p in state.positions.values() if p.volume > 0]
            orders = [o for o in state.orders.values() if o.state in ACTIVE | {"UNKNOWN"}]
            if not positions and not orders:
                continue
            try:
                _, context = context_for(db, run)
                quote = state.quote
                if (
                    quote is None
                    or quote.available_at > at
                    or (at - quote.event_time).total_seconds() > state.model.max_quote_age_seconds
                ):
                    raise ValueError("ACCOUNT_EXPOSURE_QUOTE_STALE")
                if state.incident or state.connection != "CONNECTED":
                    raise ValueError("ACCOUNT_UNRECONCILED_OR_DISCONNECTED")
                validate_spec(state, allow_conversion=True)
                if not session_open(state):
                    raise ValueError("MARKET_CLOSED_OR_CALENDAR_UNVERIFIED")
                multiplier = payoff_multiplier(state.spec, context.financial, at)
                loss_conversion(
                    state.spec.profit_currency, account.currency, context.financial.fx, at
                )
                per_margin = context.financial.margin_per_unit
                if per_margin is None:
                    raise ValueError("MARGIN_UNVERIFIED")
                local_risk = ZERO
                for position in positions:
                    count += 1
                    mark = quote.bid if position.side == "BUY" else quote.ask
                    pnl = (mark - position.entry_price) * position.volume * multiplier
                    signed_pnl = pnl if position.side == "BUY" else -pnl
                    pnl_fx = loss_conversion(
                        state.spec.profit_currency,
                        account.currency,
                        context.financial.fx,
                        at,
                        liability=signed_pnl < 0,
                    )
                    unrealized += signed_pnl * pnl_fx
                    request = OrderRequest(
                        side=position.side,
                        order_type="MARKET",
                        volume=position.volume,
                        stop_loss=position.stop_loss,
                        take_profit=position.take_profit,
                    )
                    risk = request_risk(state, context, request, position.volume, mark, at)
                    opened += risk
                    local_risk += risk
                    margin += position.volume * per_margin
                for order in orders:
                    count += 1
                    remaining = order.request.volume - order.filled_volume
                    reference = order.request.price or (
                        quote.ask if order.request.side == "BUY" else quote.bid
                    )
                    risk = request_risk(state, context, order.request, remaining, reference, at)
                    pending += risk
                    local_risk += risk
                    margin += remaining * per_margin
                group = context.financial.correlation_group
                groups[group] = groups.get(group, ZERO) + local_risk
            except (ValueError, ArithmeticError) as error:
                reasons.append(str(error) if isinstance(error, ValueError) else "NUMERIC_RANGE")
        reservations = list(
            db.scalars(
                select(Reservation).where(
                    Reservation.account_id == account.id, Reservation.state != "RELEASED"
                )
            )
        )
        reserved = sum((r.amount for r in reservations), ZERO)
        margin = max(margin, sum((r.margin for r in reservations), ZERO))
        for reservation in reservations:
            strategies[reservation.strategy] = (
                strategies.get(reservation.strategy, ZERO) + reservation.amount
            )
        # Reserve grouping independently; use the larger observed/reserved group exposure.
        for group in {r.group for r in reservations}:
            groups[group] = max(
                groups.get(group, ZERO),
                sum((r.amount for r in reservations if r.group == group), ZERO),
            )
    return EquityValues(
        balance=ledger_money(balance),
        equity=ledger_money(balance + unrealized),
        realized_pnl=ledger_money(realized),
        unrealized_pnl=ledger_money(unrealized),
        commissions=ledger_money(commissions),
        funding=ledger_money(funding),
        open_risk=opened,
        pending_risk=pending,
        reserved_risk=reserved,
        margin_used=ceil_money(margin),
        position_count=count,
        groups=groups,
        strategies=strategies,
    ), sorted(set(reasons))


def drawdown_state(
    previous: dict[str, object],
    values: EquityValues,
    initial: Decimal,
    at: datetime,
    policy: PolicyTerms,
) -> dict[str, object]:
    start = period_start(at, policy)
    period = start.isoformat()
    old_period = previous.get("period")
    if previous.get("reset_reference_missing") == period:
        raise ValueError("DAILY_RESET_REFERENCE_MISSING")
    day_balance = Decimal(str(previous.get("day_balance", values.balance)))
    day_equity = Decimal(str(previous.get("day_equity", values.equity)))
    if old_period != period:
        # A reset equity cannot be reconstructed from a later quote with overnight exposure.
        if at != start and values.position_count and policy.daily_reference != "INITIAL":
            raise ValueError("DAILY_RESET_REFERENCE_MISSING")
        day_balance, day_equity = values.balance, values.equity
    high_balance = max(initial, Decimal(str(previous.get("high_balance", initial))), values.balance)
    high_equity = max(initial, Decimal(str(previous.get("high_equity", initial))), values.equity)
    reference = {
        "BALANCE": day_balance,
        "EQUITY": day_equity,
        "MAX_BALANCE_EQUITY": max(day_balance, day_equity),
        "INITIAL": initial,
    }[policy.daily_reference]
    amount_basis = initial if policy.daily_amount_basis == "INITIAL" else reference
    metric = values.equity if policy.include_floating else values.balance
    daily_floor = reference - amount_basis * policy.daily_loss_pct / 100
    high = {"STATIC": initial, "TRAILING_BALANCE": high_balance, "TRAILING_EQUITY": high_equity}[
        policy.total_mode
    ]
    total_amount_basis = initial if policy.trailing_amount_basis == "INITIAL" else high
    total_floor = high - total_amount_basis * policy.total_loss_pct / 100
    return {
        "period": period,
        "day_balance": str(day_balance),
        "day_equity": str(day_equity),
        "high_balance": str(high_balance),
        "high_equity": str(high_equity),
        "daily_reference": str(reference),
        "policy_daily_floor": str(daily_floor),
        "policy_total_floor": str(total_floor),
        "policy_daily_headroom": str(metric - daily_floor),
        "policy_total_headroom": str(metric - total_floor),
    }


def verify_ledger(db: Session, control: AccountControl) -> bool:
    previous, sequence = "0" * 64, 0
    last_payload: dict[str, object] = {}
    for entry in db.scalars(
        select(RiskLedger)
        .where(RiskLedger.account_id == control.account_id)
        .order_by(RiskLedger.sequence)
    ):
        sequence += 1
        expected = digest(
            {
                "account_id": str(control.account_id),
                "sequence": sequence,
                "previous": previous,
                "timestamp": entry.timestamp.astimezone(UTC).isoformat(),
                "payload": entry.payload,
            }
        )
        if (
            entry.sequence != sequence
            or entry.previous_digest != previous
            or entry.digest != expected
        ):
            return False
        previous, last_payload = entry.digest, entry.payload
    return (
        control.sequence == sequence
        and control.digest == previous
        and digest(control.state) == digest(last_payload)
    )


def append_ledger(
    db: Session, control: AccountControl, payload: dict[str, object], at: datetime
) -> None:
    if not verify_ledger(db, control):
        raise ValueError("RISK_LEDGER_INTEGRITY_FAILURE")
    if control.sequence >= 20000:
        raise ValueError("RISK_LEDGER_CAPACITY_REACHED")
    sequence = control.sequence + 1
    hashed = digest(
        {
            "account_id": str(control.account_id),
            "sequence": sequence,
            "previous": control.digest,
            "timestamp": at.astimezone(UTC).isoformat(),
            "payload": payload,
        }
    )
    db.add(
        RiskLedger(
            owner_id=control.owner_id,
            account_id=control.account_id,
            sequence=sequence,
            timestamp=at,
            payload=payload,
            previous_digest=control.digest,
            digest=hashed,
        )
    )
    control.sequence, control.digest, control.state = sequence, hashed, payload
    control.clock = at if control.clock is None else max(control.clock, at)


def sync_reservations(db: Session, run: SimulationRun, state: SimState) -> None:
    reservations = db.scalars(select(Reservation).where(Reservation.run_id == run.id))
    for reservation in reservations:
        order = state.orders.get(str(reservation.order_id))
        if order is None:
            raise ValueError("RESERVATION_ORDER_MISSING")
        position = state.positions.get(str(order.id))
        remaining = order.request.volume - order.filled_volume if order.state in ACTIVE else ZERO
        if order.state == "UNKNOWN":
            reservation.state = "UNKNOWN"
            continue
        if state.spec.account_mode == "NETTING":
            # Keep the original filled allocation until the run is flat: conservative across
            # strategies/protection replacement; never net an uncertain reservation away.
            held = order.filled_volume if any(p.volume for p in state.positions.values()) else ZERO
        else:
            held = position.volume if position else ZERO
        retained = min(order.request.volume, remaining + held)
        if retained == 0:
            reservation.amount, reservation.margin = ZERO, ZERO
            reservation.state = "RELEASED"
        else:
            authorization = db.get(RiskAuthorization, reservation.authorization_id)
            if authorization is None:
                raise ValueError("RESERVATION_AUTHORIZATION_MISSING")
            original = Decimal(str(authorization.scope["estimated_risk"]))
            original_margin = Decimal(str(authorization.scope["estimated_margin"]))
            reservation.amount = ceil_money(original * retained / order.request.volume)
            reservation.margin = ceil_money(original_margin * retained / order.request.volume)
            reservation.state = "RESERVED" if remaining else "OPEN"
