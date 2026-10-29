"""Small shared inference lifecycle primitives; no account, authentication or risk writes."""

from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from packages.ai.models import AIContent, AIEvent, AIJob

CONTEXT_NAMESPACE = 640061


def context_key(owner: UUID) -> int:
    return owner.int % 2147483647


def event(db: Session, job: AIJob, kind: str, details: dict[str, Any] | None = None) -> None:
    job.event_sequence += 1
    db.add(
        AIEvent(
            request_id=job.request_id, sequence=job.event_sequence, kind=kind, details=details or {}
        )
    )


def sealing_guard(db: Session, owner: UUID) -> bool:
    """Sealing may not race an already authorized inference dispatch/read of cached context."""
    permitted = db.scalar(
        text("SELECT pg_try_advisory_xact_lock(:namespace,:owner)"),
        {"namespace": CONTEXT_NAMESPACE, "owner": context_key(owner)},
    )
    if not permitted:
        return False
    jobs = db.scalars(
        select(AIJob)
        .where(AIJob.owner_id == owner, AIJob.state.in_(["QUEUED", "RETRY"]))
        .with_for_update()
    ).all()
    for job in jobs:
        job.cancel_requested = True
        content = db.get(AIContent, job.request_id)
        if content:
            content.input_ciphertext = None
            content.partial_ciphertext = None
        event(db, job, "CONTEXT_REVOKED_FOR_SEAL")
    return True
