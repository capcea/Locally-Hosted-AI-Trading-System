"""Additive risk state; immutable decisions, versions, ledger and single-use grants."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from packages.persistence.models import Base, scoped_fk, utcnow


class AccountControl(Base):
    __tablename__ = "risk_account_controls"
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    account_revision: Mapped[int]
    manual_stop: Mapped[bool] = mapped_column(default=False)
    automatic_stop: Mapped[bool] = mapped_column(default=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    revision: Mapped[int] = mapped_column(default=1)
    clock: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    monitor_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    state: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    sequence: Mapped[int] = mapped_column(default=0)
    digest: Mapped[str] = mapped_column(String(64), default="0" * 64)
    __table_args__ = (scoped_fk("account_id", "trading_accounts"),)


class ProfileBinding(Base):
    __tablename__ = "risk_profile_versions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[UUID]
    profile_id: Mapped[UUID]
    profile_revision: Mapped[int]
    scope_key: Mapped[str] = mapped_column(String(180))
    version: Mapped[int]
    limits: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        UniqueConstraint("id", "owner_id"),
        scoped_fk("account_id", "trading_accounts"),
        scoped_fk("profile_id", "risk_profiles"),
        UniqueConstraint("account_id", "scope_key", "version"),
        CheckConstraint("version > 0 AND profile_revision > 0"),
    )


class RiskPolicy(Base):
    __tablename__ = "risk_policy_versions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[UUID]
    account_revision: Mapped[int]
    firm_policy_id: Mapped[UUID | None]
    kind: Mapped[str] = mapped_column(String(16))
    version: Mapped[int]
    terms: Mapped[dict[str, object]] = mapped_column(JSON)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    document_digest: Mapped[str] = mapped_column(String(64))
    source_references: Mapped[list[str]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), default="UNVERIFIED")
    verified_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("id", "owner_id"),
        scoped_fk("account_id", "trading_accounts"),
        scoped_fk("firm_policy_id", "firm_policies"),
        UniqueConstraint("account_id", "version"),
        CheckConstraint("kind IN ('PERSONAL','PROP')"),
        CheckConstraint("status IN ('UNVERIFIED','VERIFIED','REVOKED')"),
        CheckConstraint(
            "(kind='PERSONAL' AND firm_policy_id IS NULL) OR "
            "(kind='PROP' AND firm_policy_id IS NOT NULL)"
        ),
        CheckConstraint("version > 0 AND expires_at > effective_at"),
        CheckConstraint(
            "status != 'VERIFIED' OR (verified_at IS NOT NULL AND verified_by IS NOT NULL)"
        ),
    )


class RunContext(Base):
    __tablename__ = "risk_run_contexts"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    run_id: Mapped[UUID]
    version: Mapped[int]
    spec_digest: Mapped[str] = mapped_column(String(64))
    body: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        scoped_fk("run_id", "simulation_runs"),
        UniqueConstraint("run_id", "version"),
        CheckConstraint("version > 0"),
    )


class RiskDecision(Base):
    __tablename__ = "risk_decisions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[UUID]
    run_id: Mapped[UUID]
    command_key: Mapped[str] = mapped_column(String(120))
    result: Mapped[dict[str, object]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        scoped_fk("account_id", "trading_accounts"),
        scoped_fk("run_id", "simulation_runs"),
    )


class RiskAuthorization(Base):
    __tablename__ = "risk_authorizations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[UUID]
    run_id: Mapped[UUID]
    decision_id: Mapped[UUID] = mapped_column(ForeignKey("risk_decisions.id"))
    scope: Mapped[dict[str, object]] = mapped_column(JSON)
    signature: Mapped[str] = mapped_column(String(64))
    __table_args__ = (
        scoped_fk("account_id", "trading_accounts"),
        scoped_fk("run_id", "simulation_runs"),
    )


class AuthorizationUse(Base):
    __tablename__ = "risk_authorization_uses"
    authorization_id: Mapped[UUID] = mapped_column(
        ForeignKey("risk_authorizations.id"), primary_key=True
    )
    run_id: Mapped[UUID] = mapped_column(ForeignKey("simulation_runs.id"))
    command_digest: Mapped[str] = mapped_column(String(64))
    consumed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Reservation(Base):
    __tablename__ = "risk_reservations"
    order_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[UUID]
    run_id: Mapped[UUID]
    authorization_id: Mapped[UUID] = mapped_column(ForeignKey("risk_authorizations.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 8))
    margin: Mapped[Decimal] = mapped_column(Numeric(38, 8))
    group: Mapped[str] = mapped_column(String(80))
    strategy: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(16))
    __table_args__ = (
        scoped_fk("account_id", "trading_accounts"),
        scoped_fk("run_id", "simulation_runs"),
        CheckConstraint("amount >= 0 AND margin >= 0"),
        CheckConstraint("state IN ('RESERVED','OPEN','UNKNOWN','RELEASED')"),
    )


class RiskLedger(Base):
    __tablename__ = "risk_ledger"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[UUID]
    sequence: Mapped[int]
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    previous_digest: Mapped[str] = mapped_column(String(64))
    digest: Mapped[str] = mapped_column(String(64))
    __table_args__ = (
        scoped_fk("account_id", "trading_accounts"),
        UniqueConstraint("account_id", "sequence"),
    )


class EmergencyCommand(Base):
    __tablename__ = "risk_emergency_commands"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[UUID]
    key: Mapped[str] = mapped_column(String(100))
    request_digest: Mapped[str] = mapped_column(String(64))
    response: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        scoped_fk("account_id", "trading_accounts"),
        UniqueConstraint("account_id", "key"),
    )
