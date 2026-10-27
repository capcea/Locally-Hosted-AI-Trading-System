"""Transactionally appended, ordered HMAC chain. Runtime cannot rewrite events."""

import json
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.identity.crypto import keyed_digest
from packages.persistence.models import AuditEvent, AuditHead, User, utcnow


def payload(event: AuditEvent) -> dict[str, object]:
    return {
        "sequence": event.sequence,
        "id": str(event.id),
        "timestamp": event.timestamp,
        "actor_id": str(event.actor_id) if event.actor_id else None,
        "actor_role": event.actor_role,
        "mfa_verified": event.mfa_verified,
        "event_type": event.event_type,
        "entity_id": str(event.entity_id) if event.entity_id else None,
        "correlation_id": str(event.correlation_id),
        "before": event.before,
        "after": event.after,
        "previous_digest": event.previous_digest,
    }


def event_digest(key: str, event: AuditEvent) -> str:
    return keyed_digest(
        key, "audit-v1", json.dumps(payload(event), sort_keys=True, separators=(",", ":"))
    )


def append_event(
    db: Session,
    key: str,
    event_type: str,
    *,
    actor: User | None = None,
    mfa: bool = False,
    entity_id: UUID | None = None,
    correlation_id: UUID | None = None,
    before: dict[str, object] | None = None,
    after: dict[str, object] | None = None,
) -> AuditEvent:
    head = db.execute(select(AuditHead).where(AuditHead.id == 1).with_for_update()).scalar_one()
    event = AuditEvent(
        sequence=head.sequence + 1,
        id=uuid4(),
        timestamp=utcnow().isoformat(),
        actor_id=actor.id if actor else None,
        actor_role=actor.role if actor else "ANONYMOUS",
        mfa_verified=mfa,
        event_type=event_type,
        entity_id=entity_id,
        correlation_id=correlation_id or uuid4(),
        before=before,
        after=after,
        previous_digest=head.digest,
    )
    event.digest = event_digest(key, event)
    db.add(event)
    head.sequence, head.digest = event.sequence, event.digest
    db.flush()
    return event


def verify_chain(db: Session, key: str) -> tuple[bool, int, str]:
    # Same lock as appends: the head cannot move while we verify the committed prefix.
    head = db.execute(select(AuditHead).where(AuditHead.id == 1).with_for_update()).scalar_one()
    previous, sequence = "0" * 64, 0
    for event in db.scalars(select(AuditEvent).order_by(AuditEvent.sequence)):
        if (
            event.sequence != sequence + 1
            or event.previous_digest != previous
            or event.digest != event_digest(key, event)
        ):
            return False, sequence, previous
        sequence, previous = event.sequence, event.digest
    return (sequence == head.sequence and previous == head.digest), sequence, previous
