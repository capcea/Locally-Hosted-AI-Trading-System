"""Simulation-only short-lived, single-use HMAC capabilities; never broker permissions."""

import hashlib
import hmac
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from packages.domain.serialization import canonical
from packages.risk.contracts import AuthorizationScope
from packages.risk.models import AuthorizationUse, RiskAuthorization


def signature(key: str, scope: dict[str, object]) -> str:
    return hmac.new(
        key.encode(), b"simulated-risk-v1\0" + canonical(scope), hashlib.sha256
    ).hexdigest()


def consume(
    db: Session, authorization_id: UUID, key: str, expected: AuthorizationScope, at: datetime
) -> None:
    record = db.get(RiskAuthorization, authorization_id)
    if record is None:
        raise ValueError("RISK_AUTHORIZATION_MISSING")
    body = expected.model_dump(mode="json")
    if (
        record.account_id != expected.account_id
        or record.run_id != expected.run_id
        or not hmac.compare_digest(record.signature, signature(key, record.scope))
        or canonical(body) != canonical(record.scope)
        or not expected.issued_at <= at < expected.expires_at
        or db.get(AuthorizationUse, authorization_id) is not None
    ):
        raise ValueError("RISK_AUTHORIZATION_TAMPER_EXPIRED_OR_REPLAYED")
    db.add(
        AuthorizationUse(
            authorization_id=authorization_id,
            run_id=expected.run_id,
            command_digest=expected.command_digest,
            consumed_at=at,
        )
    )
    db.flush()
