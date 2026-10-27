"""SQLAlchemy entities. Trading records describe simulation configuration only."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Role(Base):
    __tablename__ = "roles"
    name: Mapped[str] = mapped_column(String(16), primary_key=True)
    __table_args__ = (CheckConstraint("name IN ('OWNER','OPERATOR','VIEWER')"),)


class SecurityState(Base):
    __tablename__ = "security_state"
    id: Mapped[int] = mapped_column(primary_key=True)
    bootstrapped: Mapped[bool] = mapped_column(default=False)
    __table_args__ = (CheckConstraint("id = 1"),)


class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    display_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(ForeignKey("roles.name"))
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    mfa_secret: Mapped[str | None] = mapped_column(Text)
    pending_mfa_secret: Mapped[str | None] = mapped_column(Text)
    pending_mfa_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_totp_step: Mapped[int] = mapped_column(BigInteger, default=-1)


class LoginSession(Base):
    __tablename__ = "login_sessions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    state: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    idle_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    mfa_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (CheckConstraint("state IN ('ENROLLMENT','MFA','FULL')"),)


class RecoveryCode(Base):
    __tablename__ = "recovery_codes"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RateBucket(Base):
    __tablename__ = "rate_buckets"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class Scoped(Base):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    revision: Mapped[int] = mapped_column(default=1)
    source: Mapped[str] = mapped_column(String(32), default="USER_ENTERED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


def scope_constraints() -> tuple[UniqueConstraint, CheckConstraint, CheckConstraint]:
    return (
        UniqueConstraint("id", "owner_id"),
        CheckConstraint("revision > 0"),
        CheckConstraint("source IN ('USER_ENTERED','SYNTHETIC_TEST_FIXTURE')"),
    )


def scoped_fk(column: str, target: str) -> ForeignKeyConstraint:
    return ForeignKeyConstraint([column, "owner_id"], [f"{target}.id", f"{target}.owner_id"])


class Firm(Scoped):
    __tablename__ = "prop_firms"
    website: Mapped[str | None] = mapped_column(String(500))
    __table_args__ = scope_constraints()


class Program(Scoped):
    __tablename__ = "account_programs"
    firm_id: Mapped[UUID]
    phase: Mapped[str] = mapped_column(String(80))
    platform: Mapped[str] = mapped_column(String(80))
    __table_args__ = (*scope_constraints(), scoped_fk("firm_id", "prop_firms"))


class Venue(Scoped):
    __tablename__ = "trading_venues"
    venue_type: Mapped[str] = mapped_column(String(24))
    __table_args__ = scope_constraints()


class Instrument(Scoped):
    __tablename__ = "instruments"
    venue_id: Mapped[UUID]
    symbol: Mapped[str] = mapped_column(String(40))
    asset_class: Mapped[str] = mapped_column(String(16))
    # Catalog entries never certify tradability, contract specifications or a live feed.
    __table_args__ = (
        *scope_constraints(),
        scoped_fk("venue_id", "trading_venues"),
        UniqueConstraint("owner_id", "venue_id", "symbol"),
        CheckConstraint("asset_class IN ('FOREX','METAL','INDEX','CRYPTO','OTHER')"),
    )


class TradingAccount(Scoped):
    __tablename__ = "trading_accounts"
    currency: Mapped[str] = mapped_column(String(3))
    initial_capital: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    environment: Mapped[str] = mapped_column(String(16), default="SIMULATED")
    program_id: Mapped[UUID | None]
    archived: Mapped[bool] = mapped_column(default=False)
    __table_args__ = (
        *scope_constraints(),
        scoped_fk("program_id", "account_programs"),
        CheckConstraint("environment = 'SIMULATED'"),
        CheckConstraint("initial_capital >= 0"),
    )


class BrokerConnection(Scoped):
    __tablename__ = "broker_connections"
    account_id: Mapped[UUID]
    adapter: Mapped[str] = mapped_column(String(16))
    __table_args__ = (
        *scope_constraints(),
        scoped_fk("account_id", "trading_accounts"),
        CheckConstraint("adapter IN ('MT5','CTRADER','CUSTOM')"),
    )


class RiskProfile(Scoped):
    __tablename__ = "risk_profiles"
    account_id: Mapped[UUID]
    per_trade_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4))
    daily_loss_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4))
    total_loss_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4))
    aggregate_risk_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4))
    __table_args__ = (
        *scope_constraints(),
        scoped_fk("account_id", "trading_accounts"),
        *(
            CheckConstraint(f"{field} > 0 AND {field} <= 100")
            for field in ("per_trade_pct", "daily_loss_pct", "total_loss_pct", "aggregate_risk_pct")
        ),
        CheckConstraint("per_trade_pct <= aggregate_risk_pct"),
        CheckConstraint("daily_loss_pct <= total_loss_pct"),
    )


class FirmPolicy(Scoped):
    __tablename__ = "firm_policies"
    program_id: Mapped[UUID]
    account_id: Mapped[UUID]
    version: Mapped[int]
    account_revision: Mapped[int]
    program_revision: Mapped[int]
    source_references: Mapped[list[str]] = mapped_column(JSON)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    verification_status: Mapped[str] = mapped_column(String(16), default="UNVERIFIED")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    document_digest: Mapped[str] = mapped_column(String(64))
    __table_args__ = (
        *scope_constraints(),
        scoped_fk("program_id", "account_programs"),
        scoped_fk("account_id", "trading_accounts"),
        UniqueConstraint("account_id", "program_id", "version"),
        CheckConstraint("version > 0 AND expires_at > effective_at"),
        CheckConstraint("verification_status IN ('UNVERIFIED','VERIFIED','REJECTED')"),
        CheckConstraint(
            "verification_status != 'VERIFIED' OR "
            "(verified_at IS NOT NULL AND verified_by IS NOT NULL)"
        ),
    )


class Strategy(Scoped):
    __tablename__ = "strategies"
    account_id: Mapped[UUID]
    hypothesis: Mapped[str] = mapped_column(String(2000))
    __table_args__ = (*scope_constraints(), scoped_fk("account_id", "trading_accounts"))


class StrategyVersion(Scoped):
    __tablename__ = "strategy_versions"
    strategy_id: Mapped[UUID]
    version: Mapped[int]
    artifact_digest: Mapped[str] = mapped_column(String(64))
    __table_args__ = (
        *scope_constraints(),
        scoped_fk("strategy_id", "strategies"),
        UniqueConstraint("strategy_id", "version"),
        CheckConstraint("version > 0"),
    )


class ResearchExperiment(Scoped):
    __tablename__ = "research_experiments"
    strategy_version_id: Mapped[UUID]
    research_question: Mapped[str] = mapped_column(String(2000))
    __table_args__ = (*scope_constraints(), scoped_fk("strategy_version_id", "strategy_versions"))


class ApprovalRequest(Scoped):
    __tablename__ = "approval_requests"
    strategy_version_id: Mapped[UUID]
    account_id: Mapped[UUID]
    status: Mapped[str] = mapped_column(String(16), default="PENDING")
    __table_args__ = (
        *scope_constraints(),
        scoped_fk("strategy_version_id", "strategy_versions"),
        scoped_fk("account_id", "trading_accounts"),
        CheckConstraint("status IN ('PENDING','REVIEWED','REJECTED')"),
    )


class Incident(Scoped):
    __tablename__ = "system_incidents"
    account_id: Mapped[UUID | None]
    severity: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="OPEN")
    __table_args__ = (
        *scope_constraints(),
        scoped_fk("account_id", "trading_accounts"),
        CheckConstraint("status IN ('OPEN','RESOLVED')"),
        CheckConstraint("severity IN ('INFO','WARNING','CRITICAL')"),
    )


class AuditHead(Base):
    __tablename__ = "audit_head"
    id: Mapped[int] = mapped_column(primary_key=True)
    sequence: Mapped[int] = mapped_column(BigInteger, default=0)
    digest: Mapped[str] = mapped_column(String(64), default="0" * 64)
    __table_args__ = (CheckConstraint("id = 1 AND sequence >= 0"),)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    sequence: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    id: Mapped[UUID] = mapped_column(unique=True, default=uuid4)
    timestamp: Mapped[str] = mapped_column(String(40))
    actor_id: Mapped[UUID | None] = mapped_column(index=True)
    actor_role: Mapped[str] = mapped_column(String(16))
    mfa_verified: Mapped[bool]
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[UUID | None] = mapped_column(index=True)
    correlation_id: Mapped[UUID]
    before: Mapped[dict[str, object] | None] = mapped_column(JSON)
    after: Mapped[dict[str, object] | None] = mapped_column(JSON)
    previous_digest: Mapped[str] = mapped_column(String(64))
    digest: Mapped[str] = mapped_column(String(64))
