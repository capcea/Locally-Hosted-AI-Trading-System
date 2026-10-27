"""Synthetic commands never dispatch to external adapters. Owner MFA scopes every operation."""

from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi import APIRouter, HTTPException, Query, Request, Response
from sqlalchemy import func, select

from apps.api.execution.schemas import (
    ConnectionInput,
    ConnectionView,
    ReplayInput,
    RunInput,
    RunSummary,
    RunView,
)
from apps.api.governance.routes import owned, writable
from apps.api.identity.dependencies import (
    FullIdentity,
    Principal,
    require_owner,
    require_recent_mfa,
)
from apps.api.market.query_slots import QuerySlot
from apps.api.market.routes import dataset_for, object_store
from packages.brokers.contracts import BrokerSnapshot, SignedObservation
from packages.execution.contracts import Command, Quote, SimState
from packages.execution.engine import validate_spec
from packages.execution.journal import canonical, digest, execute, verify
from packages.execution.models import (
    BrokerObservation,
    BrokerRuntime,
    ExecutionEvent,
    SimulationRun,
)
from packages.market.processing import sample, verify_manifest
from packages.persistence.models import (
    BrokerConnection,
    Incident,
    Instrument,
    Strategy,
    StrategyVersion,
    TradingAccount,
    utcnow,
)
from packages.risk.ledger import lock_account
from packages.risk.models import AccountControl

router = APIRouter(
    prefix="/api/v1/execution", tags=["Synthetic execution and read-only broker data"]
)


def connection_for(
    identity: Principal, connection_id: UUID
) -> tuple[BrokerRuntime, BrokerConnection]:
    metadata = owned(identity, BrokerConnection, connection_id)
    if not isinstance(metadata, BrokerConnection):
        raise HTTPException(404, "Broker metadata not found")
    runtime = identity.db.scalar(
        select(BrokerRuntime)
        .where(BrokerRuntime.id == connection_id, BrokerRuntime.owner_id == identity.user.id)
        .with_for_update()
    )
    if runtime is None:
        raise HTTPException(404, "Broker runtime not configured")
    account = owned(identity, TradingAccount, metadata.account_id)
    if not isinstance(account, TradingAccount) or account.archived:
        raise HTTPException(409, "Active account required")
    return runtime, metadata


def connection_view(runtime: BrokerRuntime, metadata: BrokerConnection) -> ConnectionView:
    status = runtime.status
    if runtime.last_synced_at and utcnow() - runtime.last_synced_at > timedelta(seconds=60):
        status = "STALE"
    snapshot = BrokerSnapshot.model_validate(runtime.snapshot) if runtime.snapshot else None
    if (
        status == "READ_ONLY"
        and snapshot
        and any(utcnow() - quote.event_time > timedelta(seconds=30) for quote in snapshot.quotes)
    ):
        status = "STALE_QUOTES"
    return ConnectionView(
        id=runtime.id,
        account_id=metadata.account_id,
        name=metadata.name,
        provider=runtime.provider,
        mode=runtime.mode,
        status=status,
        last_synced_at=runtime.last_synced_at,
        snapshot=snapshot,
    )


@router.post("/connections", response_model=ConnectionView, status_code=201)
def configure_connection(body: ConnectionInput, identity: FullIdentity) -> ConnectionView:
    writable(identity)
    require_owner(identity)
    require_recent_mfa(identity)
    metadata = owned(identity, BrokerConnection, body.broker_connection_id)
    if not isinstance(metadata, BrokerConnection):
        raise HTTPException(404, "Broker metadata missing")
    account = owned(identity, TradingAccount, metadata.account_id)
    if not isinstance(account, TradingAccount) or account.archived:
        raise HTTPException(409, "Active account required")
    if metadata.adapter != ("CUSTOM" if body.provider == "SIMULATOR" else body.provider):
        raise HTTPException(409, "Broker adapter identity mismatch")
    if identity.db.get(BrokerRuntime, metadata.id):
        raise HTTPException(
            409, "Pinned identity already exists; register a new connection to rotate"
        )
    runtime = BrokerRuntime(
        id=metadata.id,
        owner_id=identity.user.id,
        provider=body.provider,
        mode=body.mode,
        external_account=body.external_account,
        server=body.server,
        public_key=body.public_key,
        status="SIMULATED" if body.provider == "SIMULATOR" else "UNVERIFIED",
    )
    identity.db.add(runtime)
    identity.db.flush()
    identity.audit(
        "broker.identity_pinned",
        entity_id=runtime.id,
        after={"mode": body.mode, "provider": body.provider, "external_execution": False},
    )
    return connection_view(runtime, metadata)


@router.get("/connections", response_model=list[ConnectionView])
def connections(
    identity: FullIdentity, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)
) -> list[ConnectionView]:
    rows = identity.db.execute(
        select(BrokerRuntime, BrokerConnection)
        .join(BrokerConnection, BrokerRuntime.id == BrokerConnection.id)
        .where(BrokerRuntime.owner_id == identity.user.id)
        .order_by(BrokerRuntime.id)
        .offset(offset)
        .limit(limit)
    )
    return [connection_view(runtime, metadata) for runtime, metadata in rows]


@router.post("/connections/{connection_id}/observations")
def observe(
    connection_id: UUID, body: SignedObservation, identity: FullIdentity
) -> dict[str, object]:
    writable(identity)
    require_owner(identity)
    require_recent_mfa(identity)
    runtime, metadata = connection_for(identity, connection_id)
    snapshot = body.snapshot
    if (
        runtime.mode != "DEMO_READ_ONLY"
        or not runtime.public_key
        or body.connection_id != runtime.id
        or snapshot.provider != runtime.provider
        or snapshot.account_id != runtime.external_account
        or snapshot.server != runtime.server
        or snapshot.environment != "DEMO_READ_ONLY"
    ):
        raise HTTPException(409, "Pinned demo identity mismatch")
    payload = {"connection_id": str(connection_id), "snapshot": snapshot.model_dump(mode="json")}
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(runtime.public_key)).verify(
            bytes.fromhex(body.signature), canonical(payload)
        )
    except (InvalidSignature, ValueError) as error:
        raise HTTPException(403, "Bridge signature rejected") from error
    hashed = digest(payload)
    previous = identity.db.scalar(
        select(BrokerObservation).where(
            BrokerObservation.connection_id == connection_id,
            BrokerObservation.sequence == snapshot.source_sequence,
        )
    )
    if previous:
        if previous.digest != hashed:
            raise HTTPException(409, "Sequence payload conflict")
        return {"duplicate": True, "external_execution": False}
    if snapshot.source_sequence <= runtime.last_sequence:
        raise HTTPException(409, "Out-of-order observation rejected")
    if abs(utcnow() - snapshot.observed_at) > timedelta(seconds=60):
        raise HTTPException(409, "Stale or future observation refused")
    differences: list[str] = []
    if runtime.last_sequence >= 0 and snapshot.source_sequence != runtime.last_sequence + 1:
        differences.append("SOURCE_SEQUENCE_GAP")
    if not snapshot.healthy or snapshot.authorization != "READ_ONLY":
        differences.append("BROKER_UNAVAILABLE_OR_REVOKED")
    if runtime.snapshot:
        old = BrokerSnapshot.model_validate(runtime.snapshot)

        def observed_content(rows: Any) -> list[dict[str, Any]]:
            return sorted(
                (
                    row.model_dump(mode="json", exclude={"observed_at", "source_sequence"})
                    for row in rows
                ),
                key=lambda row: row["broker_id"],
            )

        if observed_content(old.orders) != observed_content(snapshot.orders) or observed_content(
            old.positions
        ) != observed_content(snapshot.positions):
            differences.append("BROKER_REPORTED_ORDER_OR_POSITION_CHANGE")
    if differences:
        identity.db.add(
            Incident(
                id=uuid4(),
                owner_id=identity.user.id,
                account_id=metadata.account_id,
                name="Read-only broker reconciliation: " + differences[0],
                severity="WARNING",
                status="OPEN",
                source="USER_ENTERED",
            )
        )
    identity.db.add(
        BrokerObservation(
            owner_id=identity.user.id,
            connection_id=runtime.id,
            sequence=snapshot.source_sequence,
            digest=hashed,
            payload=payload,
        )
    )
    runtime.last_sequence, runtime.last_synced_at = snapshot.source_sequence, utcnow()
    runtime.snapshot = snapshot.model_dump(mode="json")
    runtime.status = (
        "FIXTURE_ONLY"
        if snapshot.source == "CONTRACT_FIXTURE"
        else "UNKNOWN"
        if differences
        else "READ_ONLY"
    )
    identity.audit(
        "broker.observation_recorded",
        entity_id=runtime.id,
        after={"digest": hashed, "source": snapshot.source, "differences": differences},
    )
    return {
        "duplicate": False,
        "differences": differences,
        "external_execution": False,
        "reconciliation": "UNKNOWN" if differences else "CONSISTENT",
    }


def run_for(identity: Principal, run_id: UUID) -> SimulationRun:
    account_id = identity.db.scalar(
        select(SimulationRun.account_id).where(
            SimulationRun.id == run_id, SimulationRun.owner_id == identity.user.id
        )
    )
    if account_id is None:
        raise HTTPException(404, "Simulation not found")
    lock_account(identity.db, account_id)
    run = identity.db.scalar(
        select(SimulationRun)
        .where(SimulationRun.id == run_id, SimulationRun.owner_id == identity.user.id)
        .with_for_update()
    )
    if run is None:
        raise HTTPException(404, "Simulation not found")
    runtime, metadata = connection_for(identity, run.connection_id)
    if (
        runtime.mode != "SIMULATED"
        or runtime.provider != "SIMULATOR"
        or metadata.account_id != run.account_id
    ):
        raise HTTPException(403, "Only isolated synthetic accounts accept simulator commands")
    if not verify(identity.db, run):
        raise HTTPException(409, "Journal integrity verification failed")
    return run


def view(run: SimulationRun) -> RunView:
    return RunView(
        id=run.id,
        account_id=run.account_id,
        connection_id=run.connection_id,
        instrument_id=run.instrument_id,
        name=run.name,
        sequence=run.sequence,
        digest=run.digest,
        state=SimState.model_validate(run.state),
        source_binding=run.source_binding,
    )


@router.post("/simulations", response_model=RunView, status_code=201)
def create_run(body: RunInput, identity: FullIdentity) -> RunView:
    writable(identity)
    runtime, metadata = connection_for(identity, body.connection_id)
    if runtime.provider != "SIMULATOR" or runtime.mode != "SIMULATED":
        raise HTTPException(403, "External demo/live accounts cannot execute simulator commands")
    instrument = owned(identity, Instrument, body.instrument_id)
    account = owned(identity, TradingAccount, metadata.account_id)
    if (
        not isinstance(instrument, Instrument)
        or instrument.symbol != body.spec.canonical_symbol
        or instrument.asset_class != body.spec.asset_class
        or not isinstance(account, TradingAccount)
        or account.currency != body.assumptions.account_currency
        or account.initial_capital != body.assumptions.synthetic_initial_balance
    ):
        raise HTTPException(409, "Account/instrument/currency mismatch")
    lock_account(identity.db, account.id)
    risk_control = identity.db.get(AccountControl, account.id)
    if risk_control and risk_control.clock and body.start_at < risk_control.clock:
        raise HTTPException(409, "ACCOUNT_CLOCK_REVERSED")
    count = (
        identity.db.scalar(
            select(func.count())
            .select_from(SimulationRun)
            .where(SimulationRun.owner_id == identity.user.id)
        )
        or 0
    )
    if count >= 100:
        raise HTTPException(429, "Simulation quota reached")
    state = SimState(
        clock=body.start_at,
        spec=body.spec,
        model=body.assumptions,
        cash=body.assumptions.synthetic_initial_balance,
    )
    try:
        validate_spec(state, allow_conversion=True)
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    binding: dict[str, object] | None = None
    if body.dataset_id:
        dataset = dataset_for(identity, body.dataset_id)
        if (
            dataset.status != "VALID"
            or dataset.account_id != metadata.account_id
            or dataset.instrument_id != instrument.id
            or dataset.spec["data_type"] != "TICK"
            or dataset.spec["source_symbol"] != body.spec.symbol
            or not dataset.manifest_sha256
        ):
            raise HTTPException(
                409, "Replay requires matching VALID tick data with explicit bid/ask"
            )
        binding = {
            "dataset_id": str(dataset.id),
            "manifest_sha256": dataset.manifest_sha256,
            "source_provenance": str(dataset.spec["provenance"]),
            "quality": dataset.status,
        }
    run = SimulationRun(
        id=uuid4(),
        owner_id=identity.user.id,
        connection_id=runtime.id,
        account_id=metadata.account_id,
        instrument_id=instrument.id,
        name=body.name,
        state=state.model_dump(mode="json"),
        source_binding=binding,
        sequence=0,
        digest="0" * 64,
    )
    identity.db.add(run)
    identity.db.flush()
    execute(
        identity.db,
        run,
        Command(key="initialize-synthetic-run", action="FAULT", at=body.start_at, fault="NONE"),
        identity.correlation_id,
        risk_key=identity.key,
    )
    identity.audit(
        "simulation.created",
        entity_id=run.id,
        after={"source": "SIMULATED", "state_digest": digest(run.state), "head": run.digest},
    )
    return view(run)


@router.get("/simulations", response_model=list[RunSummary])
def runs(
    identity: FullIdentity, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50)
) -> list[RunSummary]:
    from packages.research.models import ResearchAccount

    records = identity.db.scalars(
        select(SimulationRun)
        .where(
            SimulationRun.owner_id == identity.user.id,
            SimulationRun.account_id.not_in(select(ResearchAccount.account_id)),
        )
        .order_by(SimulationRun.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    output = []
    for record in records:
        run = run_for(identity, record.id)
        state = SimState.model_validate(run.state)
        output.append(
            RunSummary(
                id=run.id,
                name=run.name,
                account_id=run.account_id,
                connection_id=run.connection_id,
                instrument_id=run.instrument_id,
                clock=state.clock,
                symbol=state.spec.symbol,
                account_mode=state.spec.account_mode,
                order_count=len(state.orders),
                fill_count=len(state.fills),
            )
        )
    return output


@router.get("/simulations/{run_id}", response_model=RunView)
def get_run(run_id: UUID, identity: FullIdentity) -> RunView:
    return view(run_for(identity, run_id))


def apply_command(identity: Principal, run: SimulationRun, body: Command) -> dict[str, Any]:
    from packages.research.models import ResearchAccount

    if identity.db.get(ResearchAccount, run.account_id):
        raise HTTPException(403, "RESEARCH_JOURNAL_IS_MANAGED_AND_READ_ONLY")
    if body.order and body.order.strategy_version_id:
        version = owned(identity, StrategyVersion, body.order.strategy_version_id)
        if isinstance(version, StrategyVersion):
            strategy = owned(identity, Strategy, version.strategy_id)
            if not isinstance(strategy, Strategy) or strategy.account_id != run.account_id:
                raise HTTPException(409, "Strategy/account mismatch")
    try:
        response, changed = execute(
            identity.db, run, body, identity.correlation_id, risk_key=identity.key
        )
    except ArithmeticError as error:
        raise HTTPException(409, "SYNTHETIC_NUMERIC_MODEL_RANGE_EXCEEDED") from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    if changed:
        state = SimState.model_validate(run.state)
        if state.incident:
            identity.db.add(
                Incident(
                    id=uuid4(),
                    owner_id=identity.user.id,
                    account_id=run.account_id,
                    name="SIMULATED: " + state.incident,
                    severity="WARNING",
                    status="OPEN",
                    source="SYNTHETIC_TEST_FIXTURE",
                )
            )
        identity.audit(
            "simulation.command_committed",
            entity_id=run.id,
            after={
                "command": body.action,
                "command_key": body.key,
                "head": run.digest,
                "state_digest": digest(run.state),
                "source": "SIMULATED",
            },
        )
    return response


@router.post("/simulations/{run_id}/commands")
def command(
    run_id: UUID, body: Command, identity: FullIdentity, response: Response
) -> dict[str, Any]:
    writable(identity)
    run = run_for(identity, run_id)
    if run.source_binding and body.action == "TICK":
        raise HTTPException(409, "Dataset-bound runs accept only verified replay ticks")
    result = apply_command(identity, run, body)
    if (
        body.action in {"SUBMIT", "MODIFY"}
        and result.get("risk")
        and result["risk"]["decision"] != "ALLOW"
    ):
        response.status_code = 409
    return result


@router.post("/simulations/{run_id}/replay", response_model=RunView)
def replay(
    run_id: UUID, body: ReplayInput, identity: FullIdentity, request: Request, slot: QuerySlot
) -> RunView:
    writable(identity)
    run = run_for(identity, run_id)
    if not run.source_binding:
        raise HTTPException(409, "Run is not bound to a dataset")
    dataset = dataset_for(identity, UUID(str(run.source_binding["dataset_id"])))
    if (
        dataset.status != "VALID"
        or dataset.manifest_sha256 != run.source_binding["manifest_sha256"]
    ):
        raise HTTPException(409, "Dataset quality/provenance binding no longer valid")
    if not dataset.manifest_key or not dataset.manifest_version or not dataset.manifest_sha256:
        raise HTTPException(409, "Immutable manifest missing")
    if (
        body.end <= body.start
        or body.end - body.start > timedelta(days=3660)
        or body.decision_at > utcnow()
    ):
        raise HTTPException(422, "Invalid historical replay range")
    store = object_store(request)
    manifest = verify_manifest(
        store, dataset.manifest_key, dataset.manifest_version, dataset.manifest_sha256
    )
    rows, truncated = sample(
        store,
        manifest["artifacts"],
        body.start,
        body.end,
        body.decision_at,
        body.limit,
        "normalized",
        None,
    )
    if truncated:
        raise HTTPException(422, "Narrow the replay range; never silently truncate an experiment")
    for row in rows:
        if row.bid is None or row.ask is None:
            raise HTTPException(409, "Bid/ask required; OHLC or fabricated spreads are refused")
        tick = Quote(
            symbol=row.symbol or str(dataset.spec["source_symbol"]),
            event_time=row.event_time,
            available_at=row.available_at,
            sequence=row.sequence,
            bid=row.bid,
            ask=row.ask,
        )
        apply_command(
            identity,
            run,
            Command(
                key=body.key + ":" + digest(row.model_dump(mode="json"))[:16],
                at=row.available_at,
                action="TICK",
                quote=tick,
            ),
        )
    return view(run)


@router.get("/simulations/{run_id}/events")
def events(
    run_id: UUID,
    identity: FullIdentity,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[dict[str, Any]]:
    run_for(identity, run_id)
    return [
        {
            "sequence": e.sequence,
            "event": e.payload,
            "digest": e.digest,
            "correlation_id": str(e.correlation_id),
        }
        for e in identity.db.scalars(
            select(ExecutionEvent)
            .where(ExecutionEvent.run_id == run_id)
            .order_by(ExecutionEvent.sequence)
            .offset(offset)
            .limit(limit)
        )
    ]


@router.post("/connections/{connection_id}/orders", status_code=403)
@router.post("/connections/{connection_id}/orders/cancel", status_code=403)
@router.post("/connections/{connection_id}/orders/modify", status_code=403)
def deny_external(connection_id: UUID, identity: FullIdentity) -> None:
    connection_for(identity, connection_id)
    raise HTTPException(403, "All external demo/live order capabilities are disabled until Phase 4")
