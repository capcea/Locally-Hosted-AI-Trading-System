"""Trusted historical orchestrator: every actual fill passes the existing journal/RiskGateway."""

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import ROUND_CEILING, Decimal, localcontext
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from packages.execution.contracts import Command, Quote, SimState
from packages.execution.journal import digest, execute
from packages.execution.models import BrokerRuntime, SimulationRun
from packages.persistence.audit import append_event
from packages.persistence.models import (
    BrokerConnection,
    FirmPolicy,
    RiskProfile,
    Strategy,
    StrategyVersion,
    TradingAccount,
)
from packages.research.contracts import ExperimentInput, Parameters
from packages.research.data import phase_range
from packages.research.models import ResearchAccount, ResearchRun
from packages.research.statistics import metrics
from packages.risk.contracts import Limits
from packages.risk.models import AccountControl, ProfileBinding, RiskPolicy, RunContext
from packages.risk.monitor import poll

D = Decimal


def isolated_account(
    db: Session, research: ResearchRun, plan: ExperimentInput, attempt: int, ordinal: int, key: str
) -> TradingAccount:
    from packages.research.approval import assert_current

    assert_current(db, research, plan)
    snapshot = research.approval_snapshot
    source = db.get(TradingAccount, plan.source_account_id)
    if source is None or source.archived or source.revision != snapshot["account_revision"]:
        raise ValueError("SOURCE_ACCOUNT_APPROVAL_CHANGED")
    account = TradingAccount(
        id=uuid4(),
        owner_id=research.owner_id,
        name=f"Research {research.id} {attempt}/{ordinal}",
        currency=source.currency,
        initial_capital=source.initial_capital,
        source="SYNTHETIC_TEST_FIXTURE",
        program_id=source.program_id,
        revision=1,
        environment="SIMULATED",
    )
    db.add(account)
    db.flush()
    db.add(
        ResearchAccount(
            account_id=account.id,
            owner_id=research.owner_id,
            run_id=research.id,
            attempt=attempt,
            ordinal=ordinal,
        )
    )
    limits = Limits.model_validate(snapshot["limits"])
    profile = RiskProfile(
        id=uuid4(),
        owner_id=research.owner_id,
        account_id=account.id,
        name="Frozen research risk",
        revision=1,
        source="SYNTHETIC_TEST_FIXTURE",
        per_trade_pct=limits.per_trade_pct,
        daily_loss_pct=limits.daily_loss_pct,
        total_loss_pct=limits.total_loss_pct,
        aggregate_risk_pct=limits.aggregate_risk_pct,
    )
    db.add(profile)
    db.flush()
    db.add(
        ProfileBinding(
            owner_id=research.owner_id,
            account_id=account.id,
            profile_id=profile.id,
            profile_revision=1,
            scope_key="ACCOUNT",
            version=1,
            limits=limits.model_dump(mode="json"),
        )
    )
    policy = db.get(RiskPolicy, UUID(snapshot["policy_id"]))
    if policy is None or policy.status != "VERIFIED":
        raise ValueError("FROZEN_POLICY_REVOKED")
    firm_id = None
    if policy.firm_policy_id:
        source_firm = db.get(FirmPolicy, policy.firm_policy_id)
        if source_firm is None or source_firm.verification_status != "VERIFIED":
            raise ValueError("PROP_POLICY_REVOKED")
        firm = FirmPolicy(
            id=uuid4(),
            owner_id=research.owner_id,
            account_id=account.id,
            name="Frozen research prop scope",
            revision=1,
            source="SYNTHETIC_TEST_FIXTURE",
            program_id=source_firm.program_id,
            version=1,
            account_revision=1,
            program_revision=source_firm.program_revision,
            source_references=source_firm.source_references,
            effective_at=source_firm.effective_at,
            expires_at=source_firm.expires_at,
            verification_status="VERIFIED",
            verified_at=source_firm.verified_at,
            verified_by=source_firm.verified_by,
            document_digest=source_firm.document_digest,
        )
        db.add(firm)
        db.flush()
        firm_id = firm.id
    db.add(
        RiskPolicy(
            owner_id=research.owner_id,
            account_id=account.id,
            account_revision=1,
            firm_policy_id=firm_id,
            kind=policy.kind,
            version=1,
            terms=policy.terms,
            effective_at=policy.effective_at,
            expires_at=policy.expires_at,
            document_digest=policy.document_digest,
            source_references=policy.source_references,
            status="VERIFIED",
            verified_by=policy.verified_by,
            verified_at=policy.verified_at,
        )
    )
    db.add(
        AccountControl(
            account_id=account.id,
            owner_id=research.owner_id,
            account_revision=1,
            manual_stop=False,
            automatic_stop=False,
            reasons=[],
            revision=1,
            state={},
            sequence=0,
            digest="0" * 64,
        )
    )
    db.flush()
    append_event(
        db,
        key,
        "research.isolated_account_authorized",
        entity_id=account.id,
        after={
            "research_run": str(research.id),
            "source_account": str(source.id),
            "approval_digest": digest(snapshot),
            "source": "SIMULATED",
        },
    )
    return account


def closing_window(
    db: Session,
    account: TradingAccount,
    plan: ExperimentInput,
    dataset: dict[str, Any],
    p: Parameters,
    at: datetime,
) -> bool:
    from packages.market.contracts import TIMEFRAMES
    from packages.risk.clock import period_start
    from packages.risk.contracts import PolicyTerms
    from packages.risk.policy import applicable_policy

    terms = PolicyTerms.model_validate(applicable_policy(db, account, at).terms)
    spec = dataset["pin"].symbol
    buffer = (
        max(p.session_exit_buffer_seconds, TIMEFRAMES[dataset["timeframe"]])
        + (plan.assumptions.latency_ms + plan.assumptions.latency_jitter_ms + 999) // 1000
    )
    utc = at.astimezone(UTC)
    local = at.astimezone(ZoneInfo(spec.calendar.timezone)) if spec.calendar else utc
    strategy_remaining = p.session_close * 60 - (utc.hour * 3600 + utc.minute * 60 + utc.second)
    venue_remaining = (
        spec.calendar.closes * 60 - (local.hour * 3600 + local.minute * 60 + local.second)
        if spec.calendar
        else 0
    )
    reset = p.flat_before_risk_reset and period_start(at, terms) != period_start(
        at + timedelta(seconds=buffer), terms
    )
    return min(strategy_remaining, venue_remaining) <= buffer or reset


def _event_trial(
    db: Session,
    research: ResearchRun,
    plan: ExperimentInput,
    datasets: list[dict[str, Any]],
    p: Parameters,
    stress: Decimal,
    attempt: int,
    ordinal: int,
    key: str,
    heartbeat: Callable[[int], None],
    evaluation_range: tuple[datetime, datetime] | None = None,
) -> dict[str, Any]:
    account = isolated_account(db, research, plan, attempt, ordinal, key)
    version = Strategy(
        id=uuid4(),
        owner_id=research.owner_id,
        account_id=account.id,
        name=plan.strategy,
        hypothesis="Trusted experimental research baseline; no profitability claim",
        source="SYNTHETIC_TEST_FIXTURE",
        revision=1,
    )
    db.add(version)
    db.flush()
    artifact = StrategyVersion(
        id=uuid4(),
        owner_id=research.owner_id,
        strategy_id=version.id,
        name="Frozen trusted benchmark",
        version=1,
        artifact_digest=plan.strategy_digest,
        source="SYNTHETIC_TEST_FIXTURE",
        revision=1,
    )
    db.add(artifact)
    db.flush()
    # Only execution streams have broker journal state; confirmation streams remain
    # visible-only features.
    runs: dict[str, SimulationRun] = {}
    histories: dict[str, list[dict[str, Any]]] = {}
    signals = []
    fx_observations: list[tuple[dict[str, Any], Any]] = []
    curve: list[dict[str, Any]] = []
    start, end = evaluation_range or phase_range(plan)
    for dataset in datasets:
        histories[dataset["dataset_id"]] = []
        if dataset["pin"].role != "EXECUTION":
            continue
        pin = dataset["pin"]
        first = min(r.available_at for r in dataset["rows"])
        connection = BrokerConnection(
            id=uuid4(),
            owner_id=research.owner_id,
            account_id=account.id,
            name="Research internal simulator",
            adapter="CUSTOM",
            source="SYNTHETIC_TEST_FIXTURE",
            revision=1,
        )
        db.add(connection)
        db.flush()
        db.add(
            BrokerRuntime(
                id=connection.id, owner_id=research.owner_id, provider="SIMULATOR", mode="SIMULATED"
            )
        )
        model = plan.assumptions.model_copy(
            update={
                "commission_per_unit": plan.assumptions.commission_per_unit * stress,
                "slippage_ticks": int(
                    (D(plan.assumptions.slippage_ticks) * stress).to_integral_value(
                        rounding=ROUND_CEILING
                    )
                ),
            }
        )
        state = SimState(
            clock=min(first, plan.chronology.start),
            spec=pin.symbol,
            model=model,
            cash=account.initial_capital,
        )
        run = SimulationRun(
            id=uuid4(),
            owner_id=research.owner_id,
            connection_id=connection.id,
            account_id=account.id,
            instrument_id=dataset["instrument_id"],
            name=f"Research {ordinal} {dataset['dataset_id']}",
            state=state.model_dump(mode="json"),
            sequence=0,
            digest="0" * 64,
            source_binding={
                "dataset_id": dataset["dataset_id"],
                "manifest_sha256": pin.manifest_sha256,
                "research_run_id": str(research.id),
            },
        )
        db.add(run)
        db.flush()
        db.add(
            RunContext(
                owner_id=research.owner_id,
                run_id=run.id,
                version=1,
                spec_digest=digest(pin.symbol.model_dump(mode="json")),
                body=pin.context.model_dump(mode="json"),
            )
        )
        runs[dataset["dataset_id"]] = run
    db.flush()
    db.commit()
    # Make all runs exist before first assessment; each trial has one independent account-
    # global clock.
    for run in runs.values():
        execute(
            db,
            run,
            Command(
                key="research-initialize", action="FAULT", at=plan.chronology.start, fault="NONE"
            ),
            uuid4(),
            risk_key=key,
        )
    append_event(
        db,
        key,
        "research.simulation_initialized",
        entity_id=account.id,
        after={"source": "SIMULATED", "research_run": str(research.id)},
    )
    db.flush()
    poll(db, account)
    db.commit()
    records = sorted(
        [
            (row.available_at, row.sequence, d["dataset_id"], row, d)
            for d in datasets
            for row in d["rows"]
        ],
        key=lambda x: (x[0], x[1], x[2]),
    )
    sequences = {k: 0 for k in runs}
    regimes: dict[str, dict[str, str]] = {k: {} for k in runs}
    pending_exits: set[str] = set()
    emitted_signal: dict[str, str] = {}
    trace: list[dict[str, Any]] = []

    def command(run: SimulationRun, action: str, at: datetime, **kwargs: Any) -> dict[str, Any]:
        correlation_id = uuid4()
        account_control = db.get(AccountControl, account.id)
        if account_control is None or account_control.manual_stop:
            raise ValueError("RESEARCH_ACCOUNT_EMERGENCY_STOP")
        receipt, _ = execute(
            db,
            run,
            Command.model_validate(
                {"key": f"research-{len(trace)}-{action}", "action": action, "at": at, **kwargs}
            ),
            correlation_id,
            risk_key=key,
        )
        append_event(
            db,
            key,
            "research.simulated_command",
            entity_id=run.id,
            correlation_id=correlation_id,
            after={
                "action": action,
                "journal_head": run.digest,
                "risk": receipt.get("risk"),
                "source": "SIMULATED",
            },
        )
        control_now = db.get(AccountControl, account.id)
        if start <= at <= end and control_now:
            if not control_now.state.get("data_verified"):
                raise ValueError("RESEARCH_ACCOUNT_DATA_UNVERIFIED")
            values_now: Any = control_now.state["values"]
            curve.append(
                {
                    "at": at.isoformat(),
                    "timestamp": at.timestamp(),
                    "equity": str(values_now["equity"]),
                    "daily_headroom": control_now.state.get("daily_headroom"),
                    "total_headroom": control_now.state.get("total_headroom"),
                    "open_risk": str(values_now["open_risk"]),
                    "pending_risk": str(values_now["pending_risk"]),
                }
            )
        db.commit()
        trace.append(
            {
                "dataset_id": next(k for k, v in runs.items() if v.id == run.id),
                "action": action,
                "at": at.isoformat(),
                "risk": receipt.get("risk"),
                "journal_sequence": run.sequence,
            }
        )
        return receipt

    def close_available(run: SimulationRun, at: datetime) -> bool:
        current = SimState.model_validate(run.state)
        for order in current.orders.values():
            if order.state in {"ACKNOWLEDGED", "PARTIALLY_FILLED", "SUBMITTED"}:
                command(run, "CANCEL", at, target_id=str(order.id))
        for position in current.positions.values():
            if not position.volume:
                continue
            current = SimState.model_validate(run.state)
            available = current.bid_remaining if position.side == "BUY" else current.ask_remaining
            quantity = (
                min(position.volume, available) / current.spec.volume_step
            ).to_integral_value(rounding="ROUND_DOWN") * current.spec.volume_step
            if quantity >= current.spec.min_volume:
                command(run, "CLOSE", at, target_id=str(position.id), volume=str(quantity))
        return not any(p.volume for p in SimState.model_validate(run.state).positions.values())

    for index, (at, _, dataset_id, row, dataset) in enumerate(records):
        if at > end:
            continue
        if index % 10 == 0:
            heartbeat(min(95, index * 95 // len(records)))
        from packages.research.fx import update as update_fx

        fx_observations.append((dataset, row))
        update_fx(db, plan, datasets, fx_observations, runs, at, key)
        if dataset["pin"].role == "FX":
            continue
        close = row.close if row.close is not None else (row.bid + row.ask) / 2
        history = histories[dataset_id]
        if dataset["pin"].role in {"SIGNAL", "CONFIRMATION"}:
            history.append(
                {
                    "at": at.isoformat(),
                    "close": str(close),
                    "high": str(row.high or close),
                    "low": str(row.low or close),
                }
            )
            continue
        run = runs[dataset_id]
        state = SimState.model_validate(run.state)
        spec = state.spec
        from packages.risk.ledger import position_opened_at

        window_is_closing = closing_window(db, account, plan, dataset, p, at)
        horizon_due = any(
            position.volume
            and (at - (position_opened_at(state, position.id) or at)).total_seconds()
            >= p.max_hold_seconds
            for position in state.positions.values()
        )
        exit_is_due = dataset_id in pending_exits or horizon_due or window_is_closing
        # OHLC extrema are used only after bar availability, explicitly as modeled quotes.
        # If both protective levels are spanned, no unknown path is selected optimistically.
        quotes = []
        bar_bid_budget = state.model.liquidity_per_tick
        bar_ask_budget = state.model.liquidity_per_tick
        if dataset["type"] == "BAR":
            if row.high is None or row.low is None or row.open is None:
                raise ValueError("BAR_FIELDS_MISSING")
            from packages.risk.clock import period_start
            from packages.risk.contracts import PolicyTerms
            from packages.risk.policy import applicable_policy

            terms = PolicyTerms.model_validate(applicable_policy(db, account, at).terms)
            exposed = any(p.volume for p in state.positions.values()) or any(
                o.state in {"ACKNOWLEDGED", "PARTIALLY_FILLED", "SUBMITTED", "UNKNOWN"}
                for o in state.orders.values()
            )
            if exposed and period_start(row.event_time, terms) != period_start(at, terms):
                raise ValueError("OHLC_EXPOSURE_CROSSES_UNOBSERVED_DAILY_RESET")
            for position in state.positions.values():
                if (
                    position.volume
                    and position.stop_loss is not None
                    and position.take_profit is not None
                    and row.low
                    <= min(position.stop_loss, position.take_profit)
                    <= max(position.stop_loss, position.take_profit)
                    <= row.high
                ):
                    raise ValueError("AMBIGUOUS_OHLC_SL_TP_ORDER")
            for order in state.orders.values():
                request = order.request
                if (
                    order.state in {"ACKNOWLEDGED", "PARTIALLY_FILLED", "SUBMITTED"}
                    and request.stop_loss is not None
                    and request.take_profit is not None
                    and row.low
                    <= min(request.stop_loss, request.take_profit)
                    <= max(request.stop_loss, request.take_profit)
                    <= row.high
                ):
                    raise ValueError("AMBIGUOUS_OHLC_PENDING_PROTECTION_ORDER")
            spread = plan.bar_spread * stress if plan.bar_spread is not None else None
            if spread is None:
                raise ValueError("BAR_SPREAD_REQUIRED")
            # One-sided adverse extreme first. Mixed directions cannot establish
            # one conservative path.
            directions = {p.side for p in state.positions.values() if p.volume} | {
                o.request.side
                for o in state.orders.values()
                if o.state in {"ACKNOWLEDGED", "PARTIALLY_FILLED", "SUBMITTED"}
            }
            if len(directions) > 1:
                raise ValueError("MIXED_OHLC_EXPOSURE_PATH_UNVERIFIABLE")
            adverse = row.low if directions != {"SELL"} else row.high
            favorable = row.high if directions != {"SELL"} else row.low
            quotes = [(price, price + spread) for price in (row.open, adverse, favorable, close)]
        else:
            if row.bid is None or row.ask is None:
                raise ValueError("TICK_BID_ASK_MISSING")
            quotes = [(row.bid, row.ask)]
        for quote_index, (bid, ask) in enumerate(quotes):
            sequences[dataset_id] += 1
            quote = Quote(
                symbol=spec.symbol,
                event_time=at if dataset["type"] == "BAR" else row.event_time,
                available_at=at,
                sequence=sequences[dataset_id],
                bid=bid,
                ask=ask,
                bid_liquidity=bar_bid_budget if dataset["type"] == "BAR" else None,
                ask_liquidity=bar_ask_budget if dataset["type"] == "BAR" else None,
            )
            command(run, "TICK", at, quote=quote.model_dump(mode="json"))
            if quote_index == 0 and exit_is_due:
                if close_available(run, at):
                    pending_exits.discard(dataset_id)
                else:
                    pending_exits.add(dataset_id)
            if dataset["type"] == "BAR":
                marked = SimState.model_validate(run.state)
                bar_bid_budget, bar_ask_budget = marked.bid_remaining, marked.ask_remaining
        state = SimState.model_validate(run.state)
        history.append(
            {
                "at": at.isoformat(),
                "close": str(close),
                "high": str(row.high or close),
                "low": str(row.low or close),
            }
        )
        from packages.research.strategies import signal

        features = history
        if plan.signal_timeframe != "NATIVE":
            feature_stream = next(
                d
                for d in datasets
                if d["pin"].role == "SIGNAL"
                and d["instrument_id"] == dataset["instrument_id"]
                and d["timeframe"] == plan.signal_timeframe
            )
            features = [
                point
                for point in histories[feature_stream["dataset_id"]]
                if datetime.fromisoformat(point["at"]) < at
            ]
        fresh_feature = bool(features) and emitted_signal.get(dataset_id) != features[-1]["at"]
        direction = (
            signal(plan.strategy, features, p, at) if fresh_feature and start <= at < end else 0
        )
        if fresh_feature:
            emitted_signal[dataset_id] = features[-1]["at"]
        for confirmation in datasets:
            if confirmation["pin"].role == "CONFIRMATION" and (
                confirmation["instrument_id"] == dataset["instrument_id"]
                or p.cross_asset_confirmation
            ):
                h = [
                    x
                    for x in histories[confirmation["dataset_id"]]
                    if datetime.fromisoformat(x["at"]) < at
                ]
                compared = direction * (1 if p.confirmation_direction == "SAME" else -1)
                if (
                    len(h) < p.slow
                    or (at - datetime.fromisoformat(h[-1]["at"])).total_seconds()
                    > p.confirmation_max_age_seconds
                    or (
                        compared > 0
                        and D(h[-1]["close"]) <= sum(D(x["close"]) for x in h[-p.slow :]) / p.slow
                    )
                    or (
                        compared < 0
                        and D(h[-1]["close"]) >= sum(D(x["close"]) for x in h[-p.slow :]) / p.slow
                    )
                ):
                    direction = 0
        keep = (
            int.from_bytes(
                hashlib.sha256(f"{plan.seed}:{dataset_id}:{row.sequence}".encode()).digest()[:8],
                "big",
            )
            % 100
            < p.random_keep_pct
        )
        exit_direction = direction
        if not keep or window_is_closing:
            direction = 0
        if any(
            position.volume and exit_direction and (position.side == "BUY") != (exit_direction > 0)
            for position in state.positions.values()
        ):
            pending_exits.add(dataset_id)
        state = SimState.model_validate(run.state)
        active = any(
            o.state in {"ACKNOWLEDGED", "PARTIALLY_FILLED", "SUBMITTED", "UNKNOWN"}
            for o in state.orders.values()
        ) or any(p.volume for p in state.positions.values())
        if direction and not active:
            if state.quote is None:
                raise ValueError("QUOTE_REQUIRED")
            entry = state.quote.ask if direction > 0 else state.quote.bid
            if p.entry_order_type != "MARKET":
                offset = spec.tick_size * p.entry_offset_ticks
                entry += (
                    offset
                    * (1 if direction > 0 else -1)
                    * (1 if p.entry_order_type == "STOP" else -1)
                )
            distance = spec.tick_size * p.stop_ticks
            stop = entry - distance if direction > 0 else entry + distance
            take = (
                entry + distance * p.reward_multiple
                if direction > 0
                else entry - distance * p.reward_multiple
            )
            if stop <= 0:
                raise ValueError("PROTECTIVE_PRICE_NONPOSITIVE")
            poll(db, account)  # same actual monitor code, not a manufactured heartbeat timestamp
            receipt = command(
                run,
                "SUBMIT",
                at,
                order={
                    "side": "BUY" if direction > 0 else "SELL",
                    "order_type": p.entry_order_type,
                    "price": str(entry) if p.entry_order_type != "MARKET" else None,
                    "expires_at": (at + timedelta(seconds=p.pending_expiry_seconds)).isoformat()
                    if p.entry_order_type != "MARKET"
                    else None,
                    "volume": str(p.volume),
                    "stop_loss": str(stop),
                    "take_profit": str(take),
                    "strategy_version_id": str(artifact.id),
                },
            )
            from packages.research.strategies import observed_regime

            known_regime = observed_regime(features, p, spec.tick_size)
            for submitted_order in SimState.model_validate(run.state).orders.values():
                if submitted_order.idempotency_key == f"research-{len(trace) - 1}-SUBMIT":
                    regimes[dataset_id][str(submitted_order.id)] = known_regime
            if receipt.get("risk", {}).get("decision") == "INDETERMINATE":
                raise ValueError("ENTRY_RISK_INDETERMINATE:" + str(receipt["risk"]["reasons"][0]))
            signals.append(
                {
                    "regime": known_regime,
                    "source_sequence": row.sequence,
                    "feature_window_digest": digest(features),
                    "dataset_id": dataset_id,
                    "at": at.isoformat(),
                    "direction": direction,
                    "decision": receipt.get("risk"),
                }
            )
        control = db.get(AccountControl, account.id)
        if control is None or not control.state.get("data_verified"):
            # No pre-entry risk config shortcut; failures cannot become published performance.
            raise ValueError("RESEARCH_ACCOUNT_DATA_UNVERIFIED")
        values: Any = control.state["values"]
        if at >= start:
            curve.append(
                {
                    "at": at.isoformat(),
                    "timestamp": at.timestamp(),
                    "equity": str(values["equity"]),
                    "daily_headroom": control.state.get("daily_headroom"),
                    "total_headroom": control.state.get("total_headroom"),
                    "open_risk": str(values["open_risk"]),
                    "pending_risk": str(values["pending_risk"]),
                }
            )
    if not curve:
        raise ValueError("NO_EVALUATION_OBSERVATIONS")
    final_at = end
    from packages.research.fx import update as update_fx

    update_fx(db, plan, datasets, fx_observations, runs, final_at, key)
    for run in runs.values():
        state = SimState.model_validate(run.state)
        for order in state.orders.values():
            if order.state in {"ACKNOWLEDGED", "PARTIALLY_FILLED", "SUBMITTED"}:
                command(run, "CANCEL", final_at, target_id=str(order.id))
        for position in state.positions.values():
            if position.volume:
                command(
                    run, "CLOSE", final_at, target_id=str(position.id), volume=str(position.volume)
                )
    db.flush()
    poll(db, account)
    db.commit()
    control = db.get(AccountControl, account.id)
    if control is None or not control.state.get("data_verified"):
        raise ValueError("FINAL_EQUITY_UNVERIFIED")
    final_values: Any = control.state["values"]
    curve.append(
        {
            "at": final_at.isoformat(),
            "timestamp": final_at.timestamp(),
            "equity": final_values["equity"],
        }
    )
    trades: list[dict[str, Any]] = []
    fills = []
    exposure = {}
    cost = D(0)
    for dataset_id, run in runs.items():
        state = SimState.model_validate(run.state)
        fills.extend([{"dataset_id": dataset_id, **f.model_dump(mode="json")} for f in state.fills])
        cost += state.fees - state.swap
        from packages.research.accounting import round_trips

        trades.extend(round_trips(db, state, regimes[dataset_id]))
        exposure[dataset_id] = {
            "symbol": state.spec.canonical_symbol,
            "fills": len(state.fills),
            "holding_seconds": sum(
                t["holding_seconds"]
                for t in trades
                if t["instrument"] == state.spec.canonical_symbol
            ),
        }
    limits = Limits.model_validate(research.approval_snapshot["limits"])
    initial = account.initial_capital
    daily_cap = initial * limits.daily_loss_pct / 100
    total_cap = initial * limits.total_loss_pct / 100
    daily_util = [
        D(1) - D(str(point["daily_headroom"])) / daily_cap
        for point in curve
        if point.get("daily_headroom") is not None
    ]
    total_util = [
        D(1) - D(str(point["total_headroom"])) / total_cap
        for point in curve
        if point.get("total_headroom") is not None
    ]
    result_metrics = metrics(
        curve, trades, account.initial_capital, plan.seed, plan.bootstrap_samples
    )
    result_metrics["maximum_daily_internal_risk_utilization"] = str(max(daily_util, default=D(0)))
    result_metrics["maximum_total_internal_risk_utilization"] = str(max(total_util, default=D(0)))
    regime: dict[str, Any] = {}
    for trade in trades:
        # Session is known at entry; no future price/regime classifier is used.
        session = (
            "ASIA_UTC"
            if trade["session_utc"] < 8
            else "EUROPE_UTC"
            if trade["session_utc"] < 16
            else "AMERICAS_UTC"
        )
        item = regime.setdefault(session, {"trade_count": 0, "net": D(0)})
        item["trade_count"] += 1
        item["net"] += D(trade["net"])
    result_metrics["requested_exit_horizon_seconds"] = p.max_hold_seconds
    result_metrics["liquidity_delayed_exit_count"] = sum(
        t["holding_seconds"] > p.max_hold_seconds for t in trades
    )
    trend_regimes: dict[str, Any] = {}
    for trade in trades:
        label = trade["regime"]
        item = trend_regimes.setdefault(label, {"trade_count": 0, "net": D(0)})
        item["trade_count"] += 1
        item["net"] += D(trade["net"])
    result_metrics["causal_trend_volatility_regimes"] = {
        name: {"trade_count": item["trade_count"], "net": str(item["net"])}
        for name, item in trend_regimes.items()
    }
    result_metrics["session_regimes"] = {
        name: {"trade_count": item["trade_count"], "net": str(item["net"])}
        for name, item in regime.items()
    }
    return {
        "ordinal": ordinal,
        "parameters": p.model_dump(mode="json"),
        "cost_multiplier": str(stress),
        "metrics": result_metrics,
        "equity": curve,
        "trades": trades,
        "fills": fills,
        "signals": signals,
        "replay": trace,
        "exposure": exposure,
        "transaction_costs": str(cost),
        "risk_validated": True,
        "source": "SIMULATED",
        "source_provenance": [d["provenance"] for d in datasets],
        "ohlc_rule": "MODELED_AT_BAR_AVAILABILITY_ADVERSE_FIRST_REJECT_BOTH_TOUCH",
        "paper_eligible": False,
    }


def event_trial(
    db: Session,
    research: ResearchRun,
    plan: ExperimentInput,
    datasets: list[dict[str, Any]],
    p: Parameters,
    stress: Decimal,
    attempt: int,
    ordinal: int,
    key: str,
    heartbeat: Callable[[int], None],
    evaluation_range: tuple[datetime, datetime] | None = None,
) -> dict[str, Any]:
    with localcontext() as precision:
        precision.prec = 80
        return _event_trial(
            db,
            research,
            plan,
            datasets,
            p,
            stress,
            attempt,
            ordinal,
            key,
            heartbeat,
            evaluation_range,
        )
