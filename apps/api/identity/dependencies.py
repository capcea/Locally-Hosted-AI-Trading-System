"""Cookie authentication, CSRF and persistent rate limiting."""

import hmac
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from apps.api.config import Settings
from apps.api.identity.crypto import keyed_digest, token_digest
from packages.persistence.audit import append_event
from packages.persistence.models import LoginSession, RateBucket, User, utcnow
from packages.persistence.store import Store

COOKIE = "research_session"


def settings(request: Request) -> Settings:
    value: Settings = request.app.state.settings
    return value


def key_for(request: Request) -> str:
    key = settings(request).auth_encryption_key
    if key is None:
        raise HTTPException(503, "Identity service requires private encryption configuration")
    return key.get_secret_value()


def store_for(request: Request) -> Store:
    store: Store | None = request.app.state.store
    if store is None or store.engine.dialect.name != "postgresql":
        raise HTTPException(503, "Identity service requires PostgreSQL")
    with store.engine.connect() as connection:
        unsafe = connection.execute(
            text(
                "SELECT rolsuper OR rolcreaterole OR rolcreatedb OR "
                "has_table_privilege(current_user, 'audit_events', 'UPDATE,DELETE,TRUNCATE') "
                "FROM pg_roles WHERE rolname = current_user"
            )
        ).scalar_one()
        if unsafe:
            raise HTTPException(
                503, "Identity service requires the restricted runtime database role"
            )
    return store


def origin_guard(request: Request) -> None:
    if request.headers.get("origin") not in settings(request).auth_origins:
        raise HTTPException(403, "Origin rejected")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Cross-site request rejected")


def rate_limit(request: Request, purpose: str, subject: str, limit: int) -> None:
    key = keyed_digest(key_for(request), "rate", f"{purpose}:{subject}")
    now = utcnow()
    with store_for(request).session() as db, db.begin():
        db.execute(
            insert(RateBucket)
            .values(key=key, count=0, expires_at=now + timedelta(minutes=15))
            .on_conflict_do_nothing(index_elements=[RateBucket.key])
        )
        row = db.execute(
            select(RateBucket).where(RateBucket.key == key).with_for_update()
        ).scalar_one()
        if row.expires_at <= now:
            row.count, row.expires_at = 0, now + timedelta(minutes=15)
        row.count += 1
        denied = row.count > limit
    if denied:
        raise HTTPException(429, "Too many attempts; retry later", headers={"Retry-After": "900"})


def auth_attempt(request: Request, subject: str) -> None:
    origin_guard(request)
    address = request.client.host if request.client else "unknown"
    rate_limit(request, "auth-address", address, 60)
    rate_limit(request, "auth-subject", subject, 10)


@dataclass
class Principal:
    db: Session
    user: User
    session: LoginSession
    token: str
    key: str
    correlation_id: UUID

    def audit(
        self,
        event: str,
        *,
        entity_id: UUID | None = None,
        before: dict[str, object] | None = None,
        after: dict[str, object] | None = None,
    ) -> None:
        append_event(
            self.db,
            self.key,
            event,
            actor=self.user,
            mfa=self.session.state == "FULL",
            entity_id=entity_id,
            correlation_id=self.correlation_id,
            before=before,
            after=after,
        )


def authenticated(request: Request) -> Iterator[Principal]:
    key, store = key_for(request), store_for(request)
    raw = request.cookies.get(COOKIE, "")
    if len(raw) != 43:
        raise HTTPException(401, "Authentication required")
    with store.session() as db, db.begin():
        session = db.scalar(
            select(LoginSession).where(LoginSession.token_hash == token_digest(raw))
        )
        if session is None:
            raise HTTPException(401, "Authentication required")
        user = db.execute(
            select(User).where(User.id == session.user_id).with_for_update()
        ).scalar_one()
        db.refresh(session, with_for_update=True)
        now = utcnow()
        if (
            not user.active
            or session.revoked_at is not None
            or session.expires_at <= now
            or session.idle_expires_at <= now
        ):
            raise HTTPException(401, "Session expired or revoked")
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin_guard(request)
            expected = keyed_digest(key, "csrf", raw)
            if not hmac.compare_digest(request.headers.get("x-csrf-token", ""), expected):
                raise HTTPException(403, "CSRF validation failed")
        session.idle_expires_at = min(
            session.expires_at, now + timedelta(seconds=settings(request).session_idle_seconds)
        )
        yield Principal(db, user, session, raw, key, request.state.correlation_id)


Identity = Annotated[Principal, Depends(authenticated)]


def fully_authenticated(identity: Identity) -> Principal:
    if identity.session.state != "FULL" or identity.user.mfa_secret is None:
        raise HTTPException(403, "Complete MFA before accessing management records")
    return identity


FullIdentity = Annotated[Principal, Depends(fully_authenticated)]


def require_owner(identity: Principal) -> None:
    if identity.user.role != "OWNER":
        raise HTTPException(403, "Owner role required")


def require_recent_mfa(identity: Principal) -> None:
    if identity.session.mfa_at is None or identity.session.mfa_at < utcnow() - timedelta(minutes=5):
        raise HTTPException(403, "Recent MFA verification required")
