"""Persistent owner bootstrap, mandatory MFA and revocable opaque sessions."""

import hmac
import secrets
from datetime import timedelta
from typing import NoReturn
from uuid import UUID

import pyotp
from fastapi import APIRouter, HTTPException, Query, Request, Response
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from apps.api.identity.crypto import (
    DUMMY_HASH,
    PASSWORDS,
    accepted_totp_step,
    decrypt_secret,
    encrypt_secret,
    hash_password,
    keyed_digest,
    password_matches,
    token_digest,
)
from apps.api.identity.dependencies import (
    COOKIE,
    FullIdentity,
    Identity,
    Principal,
    auth_attempt,
    key_for,
    require_owner,
    require_recent_mfa,
    settings,
    store_for,
)
from apps.api.identity.schemas import (
    Bootstrap,
    BootstrapStatus,
    ChangePassword,
    Code,
    Credentials,
    Enrollment,
    Reauthenticate,
    RecoveryResult,
    SessionView,
    UserCreate,
    UserUpdate,
    UserView,
)
from packages.persistence.audit import append_event
from packages.persistence.models import (
    Firm,
    LoginSession,
    RecoveryCode,
    SecurityState,
    User,
    utcnow,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Identity"])


def session_view(user: User, session: LoginSession, raw: str, key: str) -> SessionView:
    return SessionView.model_validate(
        {
            "user": UserView.model_validate(user),
            "state": session.state,
            "csrf_token": keyed_digest(key, "csrf", raw),
            "expires_at": session.expires_at,
            "session_id": session.id,
        }
    )


def new_session(
    db: Session, user: User, state: str, request: Request, response: Response
) -> SessionView:
    config, now, raw = settings(request), utcnow(), secrets.token_urlsafe(32)
    lifetime = config.session_lifetime_seconds if state == "FULL" else 300
    session = LoginSession(
        user_id=user.id,
        token_hash=token_digest(raw),
        state=state,
        expires_at=now + timedelta(seconds=lifetime),
        idle_expires_at=now + timedelta(seconds=min(lifetime, config.session_idle_seconds)),
        mfa_at=now if state == "FULL" else None,
    )
    db.add(session)
    db.flush()
    response.set_cookie(
        COOKIE,
        raw,
        max_age=lifetime,
        httponly=True,
        secure=config.auth_cookie_secure,
        samesite="strict",
        path="/",
    )
    return session_view(user, session, raw, key_for(request))


def rotate(identity: Principal, state: str, request: Request, response: Response) -> SessionView:
    identity.session.revoked_at = utcnow()
    result = new_session(identity.db, identity.user, state, request, response)
    # Request-scoped yield cleanup runs after headers can be sent. Publish a rotated cookie only
    # after its new row, old-session revocation, MFA counter and audit have committed atomically.
    identity.db.commit()
    return result


def revoke_all(db: Session, user: User) -> None:
    db.execute(
        update(LoginSession)
        .where(LoginSession.user_id == user.id, LoginSession.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )


def recoveries(db: Session, user: User, key: str) -> list[str]:
    db.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
    codes = [secrets.token_hex(16) for _ in range(10)]
    db.add_all(
        RecoveryCode(user_id=user.id, code_hash=keyed_digest(key, "recovery", code))
        for code in codes
    )
    return codes


@router.get("/status", response_model=BootstrapStatus)
def status(request: Request) -> BootstrapStatus:
    with store_for(request).session() as db:
        state = db.get(SecurityState, 1)
        initialized = state is not None and state.bootstrapped
        return BootstrapStatus(
            initialized=initialized,
            setup_available=not initialized and settings(request).auth_bootstrap_token is not None,
        )


@router.post("/bootstrap", response_model=SessionView, status_code=201)
def bootstrap(body: Bootstrap, request: Request, response: Response) -> SessionView:
    auth_attempt(request, "bootstrap")
    expected = settings(request).auth_bootstrap_token
    if expected is None or not hmac.compare_digest(
        expected.get_secret_value(), body.bootstrap_token.get_secret_value()
    ):
        raise HTTPException(403, "Owner setup unavailable or token invalid")
    with store_for(request).session() as db, db.begin():
        state = db.execute(
            select(SecurityState).where(SecurityState.id == 1).with_for_update()
        ).scalar_one()
        if state.bootstrapped:
            raise HTTPException(409, "Owner is already initialized")
        user = User(
            username=body.username,
            display_name=body.display_name,
            password_hash=hash_password(body.password.get_secret_value()),
            role="OWNER",
        )
        db.add(user)
        db.flush()
        state.bootstrapped = True
        # Names are catalog metadata only; no program rules or trading permissions are seeded.
        db.add_all(Firm(owner_id=user.id, name=name) for name in ("FTMO", "FundedNext", "The5ers"))
        append_event(
            db,
            key_for(request),
            "owner.bootstrapped",
            actor=user,
            entity_id=user.id,
            correlation_id=request.state.correlation_id,
            after={"role": "OWNER"},
        )
        return new_session(db, user, "ENROLLMENT", request, response)


@router.post("/login", response_model=SessionView)
def login(body: Credentials, request: Request, response: Response) -> SessionView:
    auth_attempt(request, body.username)
    result: SessionView | None = None
    with store_for(request).session() as db, db.begin():
        user = db.scalar(select(User).where(User.username == body.username).with_for_update())
        correct = password_matches(
            user.password_hash if user else DUMMY_HASH, body.password.get_secret_value()
        )
        if correct and user and user.active:
            if PASSWORDS.check_needs_rehash(user.password_hash):
                user.password_hash = hash_password(body.password.get_secret_value())
            result = new_session(
                db, user, "MFA" if user.mfa_secret else "ENROLLMENT", request, response
            )
        append_event(
            db,
            key_for(request),
            "login.password_accepted" if result else "login.failed",
            actor=user,
            correlation_id=request.state.correlation_id,
        )
    if result is None:
        raise HTTPException(401, "Invalid credentials", headers={"X-Auth-Error": "LOGIN_INVALID"})
    return result


@router.get("/me", response_model=SessionView)
def me(identity: Identity) -> SessionView:
    return session_view(identity.user, identity.session, identity.token, identity.key)


@router.post("/logout", status_code=204)
def logout(identity: Identity, response: Response) -> None:
    identity.session.revoked_at = utcnow()
    identity.audit("session.logout", entity_id=identity.session.id)
    response.delete_cookie(COOKIE, path="/")


@router.post("/sessions/revoke-all", status_code=204)
def revoke_sessions(identity: FullIdentity, response: Response) -> None:
    revoke_all(identity.db, identity.user)
    identity.audit("session.revoked_all", entity_id=identity.user.id)
    response.delete_cookie(COOKIE, path="/")


@router.post("/mfa/enroll", response_model=Enrollment)
def enroll(identity: Identity) -> Enrollment:
    if identity.session.state != "ENROLLMENT" or identity.user.mfa_secret:
        raise HTTPException(409, "MFA enrollment not available")
    secret = pyotp.random_base32()
    identity.user.pending_mfa_secret = encrypt_secret(identity.key, secret)
    identity.user.pending_mfa_expires = utcnow() + timedelta(minutes=5)
    identity.audit("mfa.enrollment_started", entity_id=identity.user.id)
    return Enrollment(
        secret=secret,
        provisioning_uri=pyotp.TOTP(secret).provisioning_uri(
            name=identity.user.username, issuer_name="Trade Research"
        ),
    )


def consume_totp(identity: Principal, code: str, encrypted: str) -> bool:
    step = accepted_totp_step(
        decrypt_secret(identity.key, encrypted), code, utcnow(), identity.user.last_totp_step
    )
    if step is None:
        return False
    identity.user.last_totp_step = step
    return True


def mfa_failure(identity: Principal) -> NoReturn:
    # Commit the failure event without committing any credential change. The caller has not mutated
    # secrets or MFA counters on failure; the dependency's later rollback is then harmless.
    identity.audit("mfa.failed", entity_id=identity.user.id)
    identity.db.commit()
    raise HTTPException(
        401, "Invalid, expired or already used MFA code", headers={"X-Auth-Error": "MFA_INVALID"}
    )


@router.post("/mfa/confirm", response_model=RecoveryResult)
def confirm(body: Code, request: Request, response: Response, identity: Identity) -> RecoveryResult:
    auth_attempt(request, str(identity.user.id))
    user = identity.user
    if (
        identity.session.state != "ENROLLMENT"
        or user.mfa_secret
        or not user.pending_mfa_secret
        or not user.pending_mfa_expires
        or user.pending_mfa_expires <= utcnow()
    ):
        raise HTTPException(409, "Enrollment missing or expired")
    if not consume_totp(identity, body.code.get_secret_value(), user.pending_mfa_secret):
        mfa_failure(identity)
    user.mfa_secret, user.pending_mfa_secret, user.pending_mfa_expires = (
        user.pending_mfa_secret,
        None,
        None,
    )
    codes = recoveries(identity.db, user, identity.key)
    revoke_all(identity.db, user)
    identity.audit("mfa.enrolled", entity_id=user.id)
    return RecoveryResult(session=rotate(identity, "FULL", request, response), recovery_codes=codes)


@router.post("/mfa/verify", response_model=SessionView)
def verify(body: Code, request: Request, response: Response, identity: Identity) -> SessionView:
    auth_attempt(request, str(identity.user.id))
    user = identity.user
    if identity.session.state != "MFA" or not user.mfa_secret:
        raise HTTPException(409, "MFA challenge required")
    if not consume_totp(identity, body.code.get_secret_value(), user.mfa_secret):
        mfa_failure(identity)
    identity.audit("mfa.verified", entity_id=user.id)
    return rotate(identity, "FULL", request, response)


@router.post("/mfa/recover", response_model=SessionView)
def recover(body: Code, request: Request, response: Response, identity: Identity) -> SessionView:
    auth_attempt(request, str(identity.user.id))
    if identity.session.state != "MFA":
        raise HTTPException(409, "Password-authenticated MFA challenge required")
    code = identity.db.scalar(
        select(RecoveryCode)
        .where(
            RecoveryCode.user_id == identity.user.id,
            RecoveryCode.code_hash
            == keyed_digest(identity.key, "recovery", body.code.get_secret_value()),
            RecoveryCode.used_at.is_(None),
        )
        .with_for_update()
    )
    if code is None:
        mfa_failure(identity)
    code.used_at = utcnow()
    identity.user.mfa_secret = None
    identity.user.pending_mfa_secret = None
    identity.user.last_totp_step = -1
    revoke_all(identity.db, identity.user)
    identity.audit("mfa.recovery_consumed", entity_id=identity.user.id)
    return rotate(identity, "ENROLLMENT", request, response)


@router.post("/reauthenticate", response_model=SessionView)
def reauthenticate(
    body: Reauthenticate, request: Request, response: Response, identity: FullIdentity
) -> SessionView:
    auth_attempt(request, str(identity.user.id))
    encrypted = identity.user.mfa_secret
    if (
        not password_matches(identity.user.password_hash, body.password.get_secret_value())
        or encrypted is None
        or not consume_totp(identity, body.code.get_secret_value(), encrypted)
    ):
        mfa_failure(identity)
    identity.audit("session.reauthenticated", entity_id=identity.user.id)
    return rotate(identity, "FULL", request, response)


@router.post("/password", status_code=204)
def change_password(
    body: ChangePassword, request: Request, response: Response, identity: FullIdentity
) -> None:
    require_recent_mfa(identity)
    auth_attempt(request, str(identity.user.id))
    if not password_matches(identity.user.password_hash, body.current_password.get_secret_value()):
        mfa_failure(identity)
    identity.user.password_hash = hash_password(body.new_password.get_secret_value())
    revoke_all(identity.db, identity.user)
    identity.audit("password.changed", entity_id=identity.user.id)
    response.delete_cookie(COOKIE, path="/")


@router.get("/users", response_model=list[UserView])
def users(
    identity: FullIdentity, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)
) -> list[UserView]:
    require_owner(identity)
    return [
        UserView.model_validate(user)
        for user in identity.db.scalars(
            select(User).order_by(User.created_at, User.id).offset(offset).limit(limit)
        )
    ]


@router.post("/users", response_model=UserView, status_code=201)
def create_user(body: UserCreate, identity: FullIdentity) -> UserView:
    require_owner(identity)
    require_recent_mfa(identity)
    user = User(
        username=body.username,
        display_name=body.display_name,
        role=body.role,
        password_hash=hash_password(body.password.get_secret_value()),
    )
    identity.db.add(user)
    identity.db.flush()
    identity.audit("user.created", entity_id=user.id, after={"role": user.role, "active": True})
    return UserView.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserView)
def change_user(user_id: UUID, body: UserUpdate, identity: FullIdentity) -> UserView:
    require_owner(identity)
    require_recent_mfa(identity)
    user = identity.db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise HTTPException(404, "User not found")
    if user.role == "OWNER":
        raise HTTPException(403, "The initial owner cannot be demoted or disabled")
    before: dict[str, object] = {"role": user.role, "active": user.active}
    user.role, user.active = body.role, body.active
    revoke_all(identity.db, user)
    identity.audit(
        "user.authorization_changed",
        entity_id=user.id,
        before=before,
        after={"role": user.role, "active": user.active},
    )
    return UserView.model_validate(user)
