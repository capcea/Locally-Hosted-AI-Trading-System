"""Mandatory deterministic journal guard; scoped monetary approval is SIMULATED only."""

import hmac
from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal, localcontext
from uuid import UUID, uuid5
from zoneinfo import ZoneInfo

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.execution.contracts import Command, OrderRequest, SimOrder, SimState
from packages.execution.engine import ACTIVE, advance_clock, prices_ok, session_open
from packages.execution.models import BrokerRuntime, SimulationRun
from packages.persistence.models import Program, Strategy, StrategyVersion, TradingAccount, utcnow
from packages.risk.authorization import consume, signature
from packages.risk.clock import period_start
from packages.risk.contracts import AuthorizationScope, Decision, PolicyTerms
from packages.risk.ledger import (
    append_ledger,
    context_for,
    digest,
    drawdown_state,
    incident,
    lock_account,
    position_opened_at,
    project,
    sync_reservations,
    verify_ledger,
)
from packages.risk.models import (
    AccountControl,
    Reservation,
    RiskAuthorization,
    RiskDecision,
    RiskPolicy,
)
from packages.risk.policy import applicable_policy, profiles, strictest
from packages.risk.sizing import ZERO, ceil_money, loss_conversion, payoff_multiplier, size


def portfolio_restrictions(
    db: Session,
    account: TradingAccount,
    at: datetime,
    terms: PolicyTerms,
    overrides: dict[UUID, SimState] | None = None,
) -> list[str]:
    reasons = []
    for run in db.scalars(select(SimulationRun).where(SimulationRun.account_id == account.id)):
        state = (
            overrides[run.id]
            if overrides and run.id in overrides
            else SimState.model_validate(run.state)
        )
        for position in state.positions.values():
            if not position.volume:
                continue
            opened = position_opened_at(state, position.id)
            if opened is not None:
                if (at - opened).total_seconds() >= terms.max_position_seconds:
                    reasons.append("MAX_POSITION_DURATION")
                if (
                    not terms.allow_overnight
                    and opened.astimezone(ZoneInfo(terms.timezone)).date()
                    != at.astimezone(ZoneInfo(terms.timezone)).date()
                ):
                    reasons.append("OVERNIGHT_EXPOSURE_PROHIBITED")
            if (
                state.quote
                and position.stop_loss is not None
                and (
                    state.quote.bid <= position.stop_loss
                    if position.side == "BUY"
                    else state.quote.ask >= position.stop_loss
                )
            ):
                reasons.append("PROTECTIVE_STOP_NOT_FULLY_EXECUTED")
    return sorted(set(reasons))


def refresh(
    db: Session,
    account: TradingAccount,
    control: AccountControl,
    at: datetime,
    overrides: dict[UUID, SimState] | None = None,
) -> list[str]:
    try:
        values, reasons = project(db, account, at, overrides)
    except (ValueError, ArithmeticError):
        reason = "EXPOSURE_UNVERIFIED_OR_INTEGRITY_FAILURE"
        control.automatic_stop = True
        control.reasons = sorted(set(control.reasons) | {reason})
        incident(db, account, reason)
        payload: dict[str, object] = {
            name: control.state[name]
            for name in (
                "period",
                "day_balance",
                "day_equity",
                "high_balance",
                "high_equity",
                "reset_reference_missing",
                "boundary_reference_at",
            )
            if name in control.state
        }
        payload.update(
            {
                "values": None,
                "verified": False,
                "monitor_reasons": [reason],
                "source": "SIMULATED",
                "evaluated_at": at.isoformat(),
            }
        )
        append_ledger(db, control, payload, at)
        return [reason]
    data: dict[str, object] = {
        name: control.state[name]
        for name in (
            "period",
            "day_balance",
            "day_equity",
            "high_balance",
            "high_equity",
            "reset_reference_missing",
            "boundary_reference_at",
        )
        if name in control.state
    }
    data.update(
        {
            "values": values.model_dump(mode="json"),
            "source": "SIMULATED",
            "evaluated_at": at.isoformat(),
            "data_verified": not reasons,
        }
    )
    if not reasons:
        data["high_balance"] = str(
            max(
                account.initial_capital,
                values.balance,
                Decimal(str(data.get("high_balance", account.initial_capital))),
            )
        )
        data["high_equity"] = str(
            max(
                account.initial_capital,
                values.equity,
                Decimal(str(data.get("high_equity", account.initial_capital))),
            )
        )
    try:
        policy = applicable_policy(db, account, at)
        terms = PolicyTerms.model_validate(policy.terms)
        reasons.extend(portfolio_restrictions(db, account, at, terms, overrides))
        data.update(drawdown_state(control.state, values, account.initial_capital, at, terms))
        limits = strictest(profiles(db, account.id, {"ACCOUNT"}))
        day_reference = Decimal(str(data["day_balance"]))
        internal_daily = (
            values.equity - day_reference + (account.initial_capital * limits.daily_loss_pct / 100)
        )
        internal_total = values.equity - account.initial_capital * (1 - limits.total_loss_pct / 100)
        daily = min(internal_daily, Decimal(str(data["policy_daily_headroom"])))
        total = min(internal_total, Decimal(str(data["policy_total_headroom"])))
        data.update(
            {
                "daily_headroom": str(daily),
                "total_headroom": str(total),
                "policy_id": str(policy.id),
                "limits": limits.model_dump(mode="json"),
            }
        )
        if daily <= 0:
            reasons.append("DAILY_DRAWDOWN_LIMIT")
        if total <= 0:
            reasons.append("TOTAL_DRAWDOWN_LIMIT")
        if (
            max(values.open_risk + values.pending_risk, values.reserved_risk)
            > values.equity * limits.aggregate_risk_pct / 100
        ):
            reasons.append("AGGREGATE_EXPOSURE_LIMIT")
        if values.position_count > limits.max_positions:
            reasons.append("POSITION_COUNT_LIMIT")
        if any(
            value > values.equity * limits.correlated_risk_pct / 100
            for value in values.groups.values()
        ):
            reasons.append("CORRELATED_EXPOSURE_LIMIT")
        runs = db.scalars(select(SimulationRun).where(SimulationRun.account_id == account.id))
        for run in runs:
            state = (
                overrides[run.id]
                if overrides and run.id in overrides
                else (SimState.model_validate(run.state))
            )
            held = [p for p in state.positions.values() if p.volume > 0]
            pending = [o for o in state.orders.values() if o.state in ACTIVE | {"UNKNOWN"}]
            try:
                _, context = context_for(db, run)
                if terms.news_required or limits.requires_economic_calendar:
                    evidence = context.calendar
                    if (
                        evidence is None
                        or not evidence.observed_at
                        <= evidence.available_at
                        <= at
                        <= evidence.valid_until
                    ):
                        reasons.append("ECONOMIC_CALENDAR_MISSING_OR_STALE")
                    elif terms.news_scope == "EXPOSURE" and (held or pending):
                        currencies = {
                            account.currency,
                            state.spec.profit_currency,
                            context.financial.base_currency,
                            context.financial.quote_currency,
                        }
                        if any(
                            event.severity == "HIGH"
                            and currencies.intersection(event.currencies)
                            and event.timestamp - timedelta(seconds=terms.news_before_seconds)
                            <= at
                            <= event.timestamp + timedelta(seconds=terms.news_after_seconds)
                            for event in evidence.events
                        ):
                            reasons.append("NEWS_EXPOSURE_PROHIBITED")
            except ValueError:
                if terms.news_required or limits.requires_economic_calendar:
                    reasons.append("RISK_CONTEXT_MISSING")
            if not held and not pending:
                continue
            if not session_open(state):
                reasons.append("MARKET_CLOSED_OR_CALENDAR_UNVERIFIED")
            if (
                state.quote
                and (state.quote.ask - state.quote.bid) / state.spec.tick_size
                > limits.max_spread_ticks
            ):
                reasons.append("SPREAD_SPIKE")
            if not terms.allow_weekend and at.astimezone(ZoneInfo(terms.timezone)).weekday() >= 5:
                reasons.append("WEEKEND_EXPOSURE_PROHIBITED")
            for position in held:
                opened = position_opened_at(state, position.id)
                if opened is not None:
                    if (at - opened).total_seconds() >= terms.max_position_seconds:
                        reasons.append("MAX_POSITION_DURATION")
                    if not terms.allow_overnight and (
                        opened.astimezone(ZoneInfo(terms.timezone)).date()
                        != at.astimezone(ZoneInfo(terms.timezone)).date()
                    ):
                        reasons.append("OVERNIGHT_EXPOSURE_PROHIBITED")
    except (ValueError, ArithmeticError) as error:
        reasons.append(str(error) if isinstance(error, ValueError) else "NUMERIC_RANGE_EXCEEDED")
    if account.archived or account.revision != control.account_revision:
        reasons.append("ACCOUNT_ARCHIVED_OR_REVISION_CHANGED")
    reasons = sorted(set(reasons))
    data["verified"] = not reasons
    data["monitor_reasons"] = reasons
    if reasons:
        control.automatic_stop = True
        control.reasons = sorted(set(control.reasons) | set(reasons))
        for reason in reasons:
            incident(db, account, reason)
    if digest(data) != digest(control.state):
        append_ledger(db, control, data, at)
    elif not verify_ledger(db, control):
        raise ValueError("RISK_LEDGER_INTEGRITY_FAILURE")
    return reasons


class Gateway:
    def __init__(
        self,
        db: Session,
        run: SimulationRun,
        key: str | None,
        command: Command,
        correlation_id: UUID,
    ) -> None:
        self.db, self.run, self.key, self.command = db, run, key, command
        self.correlation_id = correlation_id
        self.account = lock_account(db, run.account_id)
        self.control = db.get(AccountControl, run.account_id)
        self.last_decision: Decision | None = None

    def scopes(self, request: OrderRequest) -> set[str]:
        state = SimState.model_validate(self.run.state)
        scopes = {
            "ACCOUNT",
            "INSTRUMENT:" + str(self.run.instrument_id),
            "ASSET_CLASS:" + state.spec.asset_class,
        }
        if request.strategy_version_id:
            version = self.db.get(StrategyVersion, request.strategy_version_id)
            strategy = self.db.get(Strategy, version.strategy_id) if version else None
            if (
                strategy is None
                or strategy.owner_id != self.run.owner_id
                or strategy.account_id != self.account.id
            ):
                raise ValueError("STRATEGY_SCOPE_UNAUTHORIZED")
            scopes.add("STRATEGY:" + str(strategy.id))
        if self.account.program_id:
            program = self.db.get(Program, self.account.program_id)
            if program is None:
                raise ValueError("PROGRAM_MISSING")
            scopes.update(
                {
                    "PROGRAM_PHASE:" + str(program.id) + ":" + program.phase,
                    "FIRM:" + str(program.firm_id),
                }
            )
        return scopes

    def assess(
        self,
        request: OrderRequest,
        state: SimState,
        at: datetime,
        *,
        exclude: Reservation | None = None,
        auto: bool = False,
        price: Decimal | None = None,
    ) -> tuple[Decision, RiskPolicy | None, list[UUID]]:
        try:
            with localcontext() as precision:
                precision.prec = 80
                state, _ = advance_clock(state, at)
                if self.key is None or len(self.key) < 32:
                    raise ValueError("INDEPENDENT_RISK_SERVICE_IDENTITY_REQUIRED")
                runtime = self.db.get(BrokerRuntime, self.run.connection_id)
                if (
                    runtime is None
                    or runtime.mode != "SIMULATED"
                    or runtime.provider != "SIMULATOR"
                    or self.account.environment != "SIMULATED"
                ):
                    raise ValueError("EXTERNAL_EXECUTION_DENIED")
                control = self.control
                if control is None:
                    raise ValueError("RISK_CONFIGURATION_REQUIRED")
                if self.account.archived or self.account.revision != control.account_revision:
                    raise ValueError("ACCOUNT_ARCHIVED_OR_REVISION_CHANGED")
                if not verify_ledger(self.db, control):
                    raise ValueError("RISK_LEDGER_INTEGRITY_FAILURE")
                if control.manual_stop or control.automatic_stop:
                    return (
                        Decision(
                            decision="DENY", reasons=["STOP_NEW_ENTRIES", *control.reasons][:100]
                        ),
                        None,
                        [],
                    )
                if control.monitor_at is None or utcnow() - control.monitor_at > timedelta(
                    seconds=30
                ):
                    raise ValueError("INDEPENDENT_RISK_MONITOR_STALE")
                if control.clock is not None and at < control.clock:
                    raise ValueError("ACCOUNT_CLOCK_REVERSED")
                if state.connection != "CONNECTED" or state.incident:
                    raise ValueError("BROKER_STATE_UNRECONCILED")
                if any(o.state == "UNKNOWN" for o in state.orders.values()):
                    raise ValueError("RECONCILE_UNKNOWN_BEFORE_SUBMIT")
                policy = applicable_policy(self.db, self.account, at)
                terms = PolicyTerms.model_validate(policy.terms)
                bindings = profiles(self.db, self.account.id, self.scopes(request))
                limits = strictest(bindings)
                context_record, context = context_for(self.db, self.run)
                if state.spec.canonical_symbol not in terms.permitted_instruments:
                    raise ValueError("POLICY_INSTRUMENT_PROHIBITED")
                if context.financial.execution_style in terms.prohibited_styles:
                    raise ValueError("POLICY_EXECUTION_STYLE_PROHIBITED")
                if context.financial.automated and not terms.automation_permitted:
                    raise ValueError("AUTOMATION_NOT_PERMITTED")
                if (
                    not terms.allow_weekend
                    and at.astimezone(ZoneInfo(terms.timezone)).weekday() >= 5
                ):
                    raise ValueError("WEEKEND_ENTRY_PROHIBITED")
                if not session_open(state):
                    raise ValueError("MARKET_CLOSED_OR_CALENDAR_UNVERIFIED")
                quote = state.quote
                if (
                    quote is None
                    or quote.available_at > at
                    or (at - quote.event_time).total_seconds()
                    > min(limits.max_quote_age_seconds, state.model.max_quote_age_seconds)
                ):
                    raise ValueError("QUOTE_STALE_OR_UNAVAILABLE")
                if (quote.ask - quote.bid) / state.spec.tick_size > limits.max_spread_ticks:
                    raise ValueError("MAX_SPREAD_EXCEEDED")
                if state.model.slippage_ticks > limits.max_slippage_ticks:
                    raise ValueError("MAX_SLIPPAGE_EXCEEDED")
                if request.order_type not in state.spec.order_types:
                    raise ValueError("ORDER_CAPABILITY_UNVERIFIED")
                if request.oco_group and not state.spec.oco_supported:
                    raise ValueError("OCO_UNSUPPORTED")
                prices_ok(
                    state,
                    request,
                    price or request.price or (quote.ask if request.side == "BUY" else quote.bid),
                )
                if terms.news_required or limits.requires_economic_calendar:
                    evidence = context.calendar
                    if (
                        evidence is None
                        or not evidence.observed_at
                        <= evidence.available_at
                        <= at
                        <= evidence.valid_until
                    ):
                        raise ValueError("ECONOMIC_CALENDAR_MISSING_OR_STALE")
                    currencies = {
                        self.account.currency,
                        state.spec.profit_currency,
                        context.financial.base_currency,
                        context.financial.quote_currency,
                    }
                    for event in evidence.events:
                        if (
                            event.severity == "HIGH"
                            and currencies.intersection(event.currencies)
                            and event.timestamp - timedelta(seconds=terms.news_before_seconds)
                            <= at
                            <= event.timestamp + timedelta(seconds=terms.news_after_seconds)
                        ):
                            raise ValueError("ECONOMIC_NEWS_BLACKOUT")
                values, errors = project(self.db, self.account, at, {self.run.id: state})
                if errors:
                    raise ValueError(errors[0])
                restricted = portfolio_restrictions(
                    self.db, self.account, at, terms, {self.run.id: state}
                )
                if restricted:
                    return Decision(decision="DENY", reasons=restricted), policy, []
                previous = dict(control.state)
                calculated = drawdown_state(
                    previous, values, self.account.initial_capital, at, terms
                )
                daily_internal = (
                    values.equity
                    - Decimal(str(calculated["day_balance"]))
                    + (self.account.initial_capital * limits.daily_loss_pct / 100)
                )
                total_internal = values.equity - self.account.initial_capital * (
                    1 - limits.total_loss_pct / 100
                )
                daily = min(daily_internal, Decimal(str(calculated["policy_daily_headroom"])))
                total = min(total_internal, Decimal(str(calculated["policy_total_headroom"])))
                if min(daily, total) <= 0:
                    return (
                        Decision(decision="DENY", reasons=["DRAWDOWN_LIMIT_BREACHED"]),
                        policy,
                        [],
                    )
                excluded = exclude.amount if exclude else ZERO
                observed_risk = values.open_risk + values.pending_risk
                # Existing pending request in a fill callback already contributes to projection.
                if exclude:
                    observed_risk = max(ZERO, observed_risk - exclude.amount)
                used = max(observed_risk, max(ZERO, values.reserved_risk - excluded))
                group_used = max(
                    ZERO, values.groups.get(context.financial.correlation_group, ZERO) - excluded
                )
                buffer = self.account.initial_capital * limits.headroom_buffer_pct / 100
                budget = min(
                    values.equity * limits.per_trade_pct / 100,
                    values.equity * limits.aggregate_risk_pct / 100 - used,
                    values.equity * limits.correlated_risk_pct / 100 - group_used,
                    daily - buffer - used,
                    total - buffer - used,
                )
                # Approaching limits reduces future per-trade budget; losses never raise it.
                daily_cap = self.account.initial_capital * limits.daily_loss_pct / 100
                total_cap = self.account.initial_capital * limits.total_loss_pct / 100
                if (
                    daily / daily_cap <= 1 - limits.warning_utilization_pct / 100
                    or total / total_cap <= 1 - limits.warning_utilization_pct / 100
                ):
                    budget = min(
                        budget,
                        values.equity * limits.per_trade_pct / 100 * limits.warning_risk_multiplier,
                    )
                if exclude:
                    budget = min(budget, exclude.amount)
                if values.position_count >= limits.max_positions and exclude is None:
                    return Decision(decision="DENY", reasons=["POSITION_COUNT_LIMIT"]), policy, []
                margin_available = max(
                    ZERO, values.equity - values.margin_used + (exclude.margin if exclude else ZERO)
                )
                supplied_funding = context.financial.funding_buffer_per_unit
                rate = state.model.swap_per_unit_per_day
                known_funding = (
                    ceil_money(
                        max(ZERO, -rate) * Decimal(terms.max_position_seconds) / Decimal(86400)
                    )
                    if rate is not None
                    else ZERO
                )
                effective_financial = context.financial.model_copy(
                    update={"funding_buffer_per_unit": max(supplied_funding, known_funding)}
                )
                decision = size(
                    state.spec,
                    effective_financial,
                    quote,
                    request,
                    at,
                    self.account.currency,
                    max(ZERO, budget),
                    margin_available,
                    state.model.commission_per_unit,
                    max(state.model.slippage_ticks, limits.max_slippage_ticks),
                    auto_size=auto,
                    execution_price=price,
                )
                decision.evidence.update(
                    {
                        "policy_id": str(policy.id),
                        "effective_funding_buffer_per_unit": str(
                            effective_financial.funding_buffer_per_unit
                        ),
                        "profile_ids": [str(b.id) for b in bindings],
                        "profile_digest": digest([b.limits for b in bindings]),
                        "context_id": str(context_record.id),
                        "spec_digest": context_record.spec_digest,
                        "daily_headroom": str(daily),
                        "total_headroom": str(total),
                        "buffer": str(buffer),
                        "account_exposure": values.model_dump(mode="json"),
                        "state_digest": digest(state.model_dump(mode="json")),
                        "kill_revision": control.revision,
                    }
                )
                return decision, policy, [b.id for b in bindings]
        except (ValueError, ArithmeticError) as error:
            reason = (
                str(error)
                if isinstance(error, ValueError) and not isinstance(error, ValidationError)
                else "NUMERIC_OR_INPUT_RANGE_EXCEEDED"
            )
            return Decision(decision="INDETERMINATE", reasons=[reason]), None, []

    def record(
        self, decision: Decision, at: datetime, suffix: str = "", *, enforce: bool = True
    ) -> RiskDecision:
        result = RiskDecision(
            owner_id=self.run.owner_id,
            account_id=self.run.account_id,
            run_id=self.run.id,
            command_key=(self.command.key + suffix)[:120],
            result=decision.model_dump(mode="json"),
            timestamp=at,
        )
        self.db.add(result)
        self.db.flush()
        self.last_decision = decision
        if (
            enforce
            and self.control
            and (
                decision.decision == "INDETERMINATE"
                or any(
                    reason
                    in {
                        "DRAWDOWN_LIMIT_BREACHED",
                        "MAX_POSITION_DURATION",
                        "OVERNIGHT_EXPOSURE_PROHIBITED",
                        "PROTECTIVE_STOP_NOT_FULLY_EXECUTED",
                    }
                    for reason in decision.reasons
                )
            )
            and any(
                any(
                    word in reason
                    for word in (
                        "STALE",
                        "UNRECONCILED",
                        "POLICY",
                        "REVISION",
                        "INTEGRITY",
                        "CALENDAR",
                        "DRAWDOWN",
                        "UNVERIFIED",
                        "DURATION",
                        "OVERNIGHT",
                        "PROTECTIVE_STOP",
                    )
                )
                for reason in decision.reasons
            )
        ):
            self.control.automatic_stop = True
            self.control.reasons = sorted(set(self.control.reasons) | set(decision.reasons))
            for reason in decision.reasons:
                incident(self.db, self.account, reason)
        return result

    def authorize(
        self,
        request: OrderRequest,
        state: SimState,
        at: datetime,
        order_id: UUID,
        *,
        exclude: Reservation | None = None,
        price: Decimal | None = None,
        create_reservation: bool = True,
    ) -> Decision:
        decision, policy, binding_ids = self.assess(
            request, state, at, exclude=exclude, price=price
        )
        if exclude is not None and decision.decision == "ALLOW":
            allocation = self.db.get(RiskAuthorization, exclude.authorization_id)
            if (
                allocation is None
                or self.key is None
                or not hmac.compare_digest(
                    allocation.signature, signature(self.key, allocation.scope)
                )
                or allocation.scope.get("order_id") != str(order_id)
                or allocation.scope.get("account_id") != str(self.account.id)
                or allocation.scope.get("run_id") != str(self.run.id)
            ):
                decision = Decision(
                    decision="INDETERMINATE", reasons=["RESERVATION_SCOPE_UNVERIFIED"]
                )
            else:
                original = state.orders.get(str(order_id))
                if original is None:
                    decision = Decision(
                        decision="INDETERMINATE", reasons=["RESERVATION_ORDER_MISSING"]
                    )
                else:
                    with localcontext() as precision:
                        precision.prec = 80
                        cap = (
                            Decimal(str(allocation.scope["estimated_risk"]))
                            * request.volume
                            / original.request.volume
                        )
                    if decision.estimated_risk > cap:
                        decision.decision = "DENY"
                        decision.approved_volume = ZERO
                        decision.reasons = ["MATERIAL_CHANGE_EXCEEDS_RESERVED_RISK"]
        record = self.record(decision, at, ":" + str(order_id))
        if decision.decision != "ALLOW" or policy is None or self.key is None:
            return decision
        scope = AuthorizationScope(
            account_id=self.account.id,
            run_id=self.run.id,
            order_id=order_id,
            command_digest=digest(self.command.model_dump(mode="json")),
            request_digest=digest(request.model_dump(mode="json")),
            context_digest=digest(decision.evidence),
            policy_id=policy.id,
            profile_ids=binding_ids,
            estimated_risk=decision.estimated_risk,
            estimated_margin=decision.estimated_margin,
            issued_at=at,
            expires_at=min(at + timedelta(seconds=30), policy.expires_at),
        )
        body = scope.model_dump(mode="json")
        authorization = RiskAuthorization(
            owner_id=self.run.owner_id,
            account_id=self.account.id,
            run_id=self.run.id,
            decision_id=record.id,
            scope=body,
            signature=signature(self.key, body),
        )
        self.db.add(authorization)
        self.db.flush()
        consume(self.db, authorization.id, self.key, scope, at)
        if exclude is None and create_reservation:
            _, context = context_for(self.db, self.run)
            strategy = str(request.strategy_version_id) if request.strategy_version_id else "MANUAL"
            self.db.add(
                Reservation(
                    order_id=order_id,
                    owner_id=self.run.owner_id,
                    account_id=self.account.id,
                    run_id=self.run.id,
                    authorization_id=authorization.id,
                    amount=decision.estimated_risk,
                    margin=decision.estimated_margin,
                    group=context.financial.correlation_group,
                    strategy=strategy,
                    state="RESERVED",
                )
            )
        self.db.flush()
        return decision

    def capture_boundary(self, state: SimState) -> None:
        control = self.control
        if control is None:
            return
        try:
            policy = applicable_policy(self.db, self.account, state.clock)
            terms = PolicyTerms.model_validate(policy.terms)
        except ValueError:
            return
        start = period_start(state.clock, terms)
        period = start.isoformat()
        if control.state.get("period") == period and not control.state.get(
            "reset_reference_missing"
        ):
            return
        snapshot = state.model_copy(deep=True)
        if self.command.action == "TICK" and self.command.quote is not None:
            snapshot.quote = self.command.quote
        values, errors = project(self.db, self.account, state.clock, {self.run.id: snapshot})
        all_runs = list(
            self.db.scalars(
                select(SimulationRun).where(SimulationRun.account_id == self.account.id)
            )
        )
        states = [
            snapshot if run.id == self.run.id else SimState.model_validate(run.state)
            for run in all_runs
        ]
        held = any(p.volume for current in states for p in current.positions.values())
        unknown = any(o.state == "UNKNOWN" for current in states for o in current.orders.values())
        history = any(current.fills or current.swap for current in states)
        # A known flat balance stays constant between journal commands, including a skipped
        # reset. Held equity requires a fresh observation at the exact reset instant.
        initial_known = not history and not held and not unknown
        flat_carry = (
            not held and not unknown and control.clock is not None and control.clock < start
        )
        exact = state.clock == start and not errors
        payload = dict(control.state)
        payload["evaluated_at"] = state.clock.isoformat()
        payload["boundary_phase"] = "PRE_EXECUTION"
        payload["values"] = values.model_dump(mode="json") if not errors else None
        payload["verified"] = not errors
        payload["data_verified"] = not errors
        for old_headroom in (
            "daily_headroom",
            "total_headroom",
            "policy_daily_headroom",
            "policy_total_headroom",
        ):
            payload.pop(old_headroom, None)
        if exact or initial_known or flat_carry:
            payload.update(
                {
                    "period": period,
                    "day_balance": str(values.balance),
                    "day_equity": str(values.equity),
                    "high_balance": str(
                        max(
                            self.account.initial_capital,
                            values.balance,
                            Decimal(str(payload.get("high_balance", self.account.initial_capital))),
                        )
                    ),
                    "high_equity": str(
                        max(
                            self.account.initial_capital,
                            values.equity,
                            Decimal(str(payload.get("high_equity", self.account.initial_capital))),
                        )
                    ),
                    "boundary_reference_at": start.isoformat(),
                }
            )
            payload.pop("reset_reference_missing", None)
        else:
            payload["reset_reference_missing"] = period
            payload["verified"] = False
            payload["values"] = None
            control.automatic_stop = True
            control.reasons = sorted(set(control.reasons) | {"DAILY_RESET_REFERENCE_MISSING"})
            incident(self.db, self.account, "DAILY_RESET_REFERENCE_MISSING")
        append_ledger(self.db, control, payload, state.clock)

    def before(self, state: SimState) -> Decision | None:
        if self.command.action == "SUBMIT" and self.command.order is not None:
            state = state.model_copy(deep=True)
            state.clock = self.command.at
            return self.authorize(
                self.command.order, state, self.command.at, uuid5(self.run.id, self.command.key)
            )
        if self.command.action == "MODIFY":
            position = state.positions.get(str(self.command.target_id))
            if position and position.volume:
                # Protection modifications receive a fresh full-volume assessment; an order
                # reservation is not silently reused or released by a stop-distance change.
                request = OrderRequest(
                    side=position.side,
                    order_type="MARKET",
                    volume=position.volume,
                    stop_loss=self.command.stop_loss,
                    take_profit=self.command.take_profit,
                )
                from packages.risk.ledger import request_risk

                _, context = context_for(self.db, self.run)
                quote = state.quote
                if quote is None:
                    result = Decision(
                        decision="INDETERMINATE", reasons=["QUOTE_STALE_OR_UNAVAILABLE"]
                    )
                    self.record(result, self.command.at, ":modify")
                    return result
                mark = quote.bid if position.side == "BUY" else quote.ask
                prior = request.model_copy(
                    update={"stop_loss": position.stop_loss, "take_profit": position.take_profit}
                )
                old_risk = request_risk(
                    state, context, prior, position.volume, mark, self.command.at
                )
                new_risk = request_risk(
                    state, context, request, position.volume, mark, self.command.at
                )
                if new_risk > old_risk:
                    result = Decision(
                        decision="DENY", reasons=["PROTECTION_CANNOT_INCREASE_RESERVED_RISK"]
                    )
                    self.record(result, self.command.at, ":modify")
                    return result
                return self.authorize(
                    request, state, self.command.at, position.id, create_reservation=False
                )
        return None

    def entry(
        self, state: SimState, order: SimOrder, volume: Decimal, price: Decimal
    ) -> str | None:
        reservation = self.db.get(Reservation, order.id)
        if reservation is None or reservation.state == "RELEASED":
            self.record(
                Decision(decision="DENY", reasons=["VALID_RISK_RESERVATION_REQUIRED"]),
                state.clock,
                ":fill",
            )
            return "VALID_RISK_RESERVATION_REQUIRED"
        request = order.request.model_copy(update={"volume": volume})
        result = self.authorize(
            request, state, state.clock, order.id, exclude=reservation, price=price
        )
        return None if result.decision == "ALLOW" else "RISK_GATEWAY:" + result.reasons[0]

    def after(self, state: SimState) -> None:
        sync_reservations(self.db, self.run, state)
        self.db.flush()
        if self.control:
            if not verify_ledger(self.db, self.control):
                self.control.automatic_stop = True
                self.control.reasons = sorted(
                    set(self.control.reasons) | {"RISK_LEDGER_INTEGRITY_FAILURE"}
                )
                incident(self.db, self.account, "RISK_LEDGER_INTEGRITY_FAILURE")
                return
            at = max(state.clock, self.control.clock) if self.control.clock else state.clock
            refresh(self.db, self.account, self.control, at, {self.run.id: state})

    def financial(
        self, state: SimState
    ) -> tuple[Decimal | None, Callable[[Decimal, datetime], Decimal] | None]:
        try:
            _, context = context_for(self.db, self.run)
        except ValueError:
            return None, None
        multiplier = payoff_multiplier(state.spec, context.financial, self.command.at)

        def convert(value: Decimal, at: datetime) -> Decimal:
            with localcontext() as precision:
                precision.prec = 80
                rate = loss_conversion(
                    state.spec.profit_currency,
                    state.model.account_currency,
                    context.financial.fx,
                    at,
                    liability=value < 0,
                )
                return value * rate

        return multiplier, convert
