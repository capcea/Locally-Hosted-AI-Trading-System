"""One row lock, deterministic command, immutable event batch and one audit transaction."""

import hashlib
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.domain.serialization import canonical as canonical
from packages.execution.contracts import Command, EngineEvent, SimState
from packages.execution.engine import Engine, advance_clock
from packages.execution.models import ExecutionEvent, SimulationCommand, SimulationRun
from packages.risk.gateway import Gateway
from packages.risk.ledger import lock_account
from packages.risk.models import AccountControl


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def execute(
    db: Session,
    run: SimulationRun,
    command: Command,
    correlation_id: UUID,
    *,
    risk_key: str | None = None,
) -> tuple[dict[str, Any], bool]:
    lock_account(db, run.account_id)
    db.refresh(run, with_for_update=True)
    body = command.model_dump(mode="json")
    request_digest = digest(body)
    if run.sequence and not verify(db, run):
        raise ValueError("JOURNAL_OR_SNAPSHOT_INTEGRITY_FAILURE")
    previous = db.scalar(
        select(SimulationCommand).where(
            SimulationCommand.run_id == run.id, SimulationCommand.key == command.key
        )
    )
    if previous:
        if previous.request_digest != request_digest:
            raise ValueError("IDEMPOTENCY_KEY_PAYLOAD_CONFLICT")
        return response_for(run, previous.response), False
    control = db.get(AccountControl, run.account_id)
    if control and control.clock and command.at < control.clock:
        raise ValueError("ACCOUNT_CLOCK_REVERSED")
    if run.sequence >= 20000:
        raise ValueError("JOURNAL_CAPACITY_REACHED")
    guard = Gateway(db, run, risk_key, command, correlation_id)
    initial_state, funding_events = advance_clock(SimState.model_validate(run.state), command.at)
    guard.capture_boundary(initial_state)
    refusal = guard.before(initial_state)
    if refusal is not None and refusal.decision != "ALLOW":
        state = initial_state
        events = [
            EngineEvent(
                kind="RISK_DENIED",
                source_sequence=state.quote.sequence if state.quote else 0,
                timestamp=state.clock,
                payload={
                    "decision": refusal.model_dump(mode="json"),
                    "requested_at": command.at.isoformat(),
                },
            )
        ]
    else:
        multiplier, converter = guard.financial(initial_state)
        state, events = Engine(
            initial_state,
            run.id,
            entry_guard=guard.entry,
            profit_converter=converter,
            pnl_multiplier=multiplier,
        ).apply(command)
    events = funding_events + events
    guard.after(state)
    if guard.last_decision:
        events.append(
            EngineEvent(
                kind="RISK_DECISION",
                source_sequence=state.quote.sequence if state.quote else 0,
                timestamp=state.clock,
                payload=guard.last_decision.model_dump(mode="json"),
            )
        )
    events.append(
        EngineEvent(
            kind="STATE_COMMITTED",
            timestamp=state.clock,
            source_sequence=state.quote.sequence if state.quote else 0,
            payload={
                "state_digest": digest(state.model_dump(mode="json")),
                "request_digest": request_digest,
            },
        )
    )
    if run.sequence + len(events) > 20000:
        raise ValueError("JOURNAL_CAPACITY_REACHED")
    for event in events:
        payload = event.model_dump(mode="json")
        sequence = run.sequence + 1
        hashed = digest(
            {
                "run_id": str(run.id),
                "sequence": sequence,
                "previous": run.digest,
                "event": payload,
                "correlation_id": str(correlation_id),
            }
        )
        db.add(
            ExecutionEvent(
                owner_id=run.owner_id,
                run_id=run.id,
                sequence=sequence,
                order_id=event.order_id,
                kind=event.kind,
                payload=payload,
                timestamp=event.timestamp,
                correlation_id=correlation_id,
                previous_digest=run.digest,
                digest=hashed,
            )
        )
        run.sequence, run.digest = sequence, hashed
    run.state = state.model_dump(mode="json")
    receipt: dict[str, Any] = {
        "run_id": str(run.id),
        "sequence": run.sequence,
        "digest": run.digest,
        "source": "SIMULATED",
    }
    if guard.last_decision:
        receipt["risk"] = guard.last_decision.model_dump(mode="json")
    db.add(
        SimulationCommand(
            owner_id=run.owner_id,
            run_id=run.id,
            key=command.key,
            request_digest=request_digest,
            command=body,
            response=receipt,
        )
    )
    db.flush()
    return response_for(run, receipt), True


def response_for(run: SimulationRun, receipt: dict[str, Any]) -> dict[str, Any]:
    # Keep a compact immutable first receipt; retries observe current authoritative state.
    return {
        "run_id": str(run.id),
        "sequence": run.sequence,
        "digest": run.digest,
        "source": "SIMULATED",
        "state": run.state,
        "original_receipt": receipt,
        "risk": receipt.get("risk"),
    }


def verify(db: Session, run: SimulationRun) -> bool:
    previous = "0" * 64
    count = 0
    snapshot_digest = None
    for event in db.scalars(
        select(ExecutionEvent)
        .where(ExecutionEvent.run_id == run.id)
        .order_by(ExecutionEvent.sequence)
        .execution_options(yield_per=100)
    ):
        count += 1
        expected = digest(
            {
                "run_id": str(run.id),
                "sequence": count,
                "previous": previous,
                "event": event.payload,
                "correlation_id": str(event.correlation_id),
            }
        )
        if event.sequence != count or event.previous_digest != previous or event.digest != expected:
            return False
        previous = event.digest
        if event.kind == "STATE_COMMITTED":
            nested = event.payload.get("payload")
            if not isinstance(nested, dict):
                return False
            snapshot_digest = nested.get("state_digest")
    return (
        count == run.sequence
        and previous == run.digest
        and (count == 0 or snapshot_digest == digest(run.state))
    )
