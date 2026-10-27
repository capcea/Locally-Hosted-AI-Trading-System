"""Additive typed extension of the existing broker/account registry and immutable journal."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from packages.persistence.models import Base, scoped_fk, utcnow


class BrokerRuntime(Base):
    __tablename__ = "broker_runtime"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    mode: Mapped[str] = mapped_column(String(24))
    provider: Mapped[str] = mapped_column(String(16))
    external_account: Mapped[str | None] = mapped_column(String(100))
    server: Mapped[str | None] = mapped_column(String(120))
    public_key: Mapped[str | None] = mapped_column(String(64))
    last_sequence: Mapped[int] = mapped_column(default=-1)
    status: Mapped[str] = mapped_column(String(24), default="UNVERIFIED")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    snapshot: Mapped[dict[str, object] | None] = mapped_column(JSON)
    __table_args__ = (
        UniqueConstraint("id", "owner_id"),
        scoped_fk("id", "broker_connections"),
        CheckConstraint("mode IN ('SIMULATED','DEMO_READ_ONLY')"),
        CheckConstraint("provider IN ('SIMULATOR','MT5','CTRADER')"),
        CheckConstraint("(mode='SIMULATED') = (provider='SIMULATOR')"),
    )


class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    connection_id: Mapped[UUID]
    account_id: Mapped[UUID]
    instrument_id: Mapped[UUID]
    name: Mapped[str] = mapped_column(String(120))
    state: Mapped[dict[str, object]] = mapped_column(JSON)
    source_binding: Mapped[dict[str, object] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    sequence: Mapped[int] = mapped_column(default=0)
    digest: Mapped[str] = mapped_column(String(64), default="0" * 64)
    __table_args__ = (
        UniqueConstraint("id", "owner_id"),
        scoped_fk("connection_id", "broker_runtime"),
        scoped_fk("account_id", "trading_accounts"),
        scoped_fk("instrument_id", "instruments"),
        CheckConstraint("sequence >= 0"),
    )


class SimulationCommand(Base):
    __tablename__ = "simulation_commands"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    run_id: Mapped[UUID]
    key: Mapped[str] = mapped_column(String(100))
    request_digest: Mapped[str] = mapped_column(String(64))
    command: Mapped[dict[str, object]] = mapped_column(JSON)
    response: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (scoped_fk("run_id", "simulation_runs"), UniqueConstraint("run_id", "key"))


class ExecutionEvent(Base):
    __tablename__ = "execution_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    run_id: Mapped[UUID]
    sequence: Mapped[int]
    order_id: Mapped[UUID | None] = mapped_column(index=True)
    kind: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    correlation_id: Mapped[UUID]
    previous_digest: Mapped[str] = mapped_column(String(64))
    digest: Mapped[str] = mapped_column(String(64))
    __table_args__ = (
        scoped_fk("run_id", "simulation_runs"),
        UniqueConstraint("run_id", "sequence"),
    )


class BrokerObservation(Base):
    __tablename__ = "broker_observations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    connection_id: Mapped[UUID]
    sequence: Mapped[int]
    digest: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        scoped_fk("connection_id", "broker_runtime"),
        UniqueConstraint("connection_id", "sequence"),
    )
