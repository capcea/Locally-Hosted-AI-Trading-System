"""PostgreSQL data registry; rows become visible only after complete publication."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from packages.persistence.models import Base, scoped_fk, utcnow


class MarketProvider(Base):
    __tablename__ = "market_providers"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    adapter: Mapped[str] = mapped_column(String(24))
    rights_reference: Mapped[str] = mapped_column(String(1000))
    attribution: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        UniqueConstraint("id", "owner_id"),
        UniqueConstraint("owner_id", "name"),
        CheckConstraint("adapter IN ('LOCAL','ECB','MT5_EXPORT','PREMIUM')"),
    )


class MarketDataset(Base):
    __tablename__ = "market_datasets"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    account_id: Mapped[UUID]
    provider_id: Mapped[UUID]
    instrument_id: Mapped[UUID]
    symbol: Mapped[str] = mapped_column(String(40))
    series_key: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int]
    spec: Mapped[dict[str, object]] = mapped_column(JSON)
    input_sha256: Mapped[str] = mapped_column(String(64))
    input_key: Mapped[str] = mapped_column(String(500))
    input_version: Mapped[str] = mapped_column(String(128))
    input_size: Mapped[int]
    status: Mapped[str] = mapped_column(String(16), default="PENDING", index=True)
    record_count: Mapped[int] = mapped_column(default=0)
    earliest: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latest: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    coverage_pct: Mapped[str | None] = mapped_column(String(40))
    quality: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    artifacts: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    manifest_key: Mapped[str | None] = mapped_column(String(500))
    manifest_version: Mapped[str | None] = mapped_column(String(128))
    manifest_sha256: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("id", "owner_id"),
        UniqueConstraint("series_key", "version"),
        scoped_fk("account_id", "trading_accounts"),
        scoped_fk("provider_id", "market_providers"),
        scoped_fk("instrument_id", "instruments"),
        CheckConstraint("version > 0 AND input_size >= 0 AND record_count >= 0"),
        CheckConstraint("status IN ('PENDING','VALIDATING','VALID','DEGRADED','REJECTED')"),
    )


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    dataset_id: Mapped[UUID]
    idempotency_key: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(24), default="QUEUED", index=True)
    attempts: Mapped[int] = mapped_column(default=0)
    progress_rows: Mapped[int] = mapped_column(default=0)
    error_code: Mapped[str | None] = mapped_column(String(40))
    cancel_requested: Mapped[bool] = mapped_column(default=False)
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worker_token: Mapped[UUID | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        scoped_fk("dataset_id", "market_datasets"),
        UniqueConstraint("owner_id", "idempotency_key"),
        CheckConstraint("state IN ('QUEUED','RUNNING','RETRY','CANCELLED','FAILED','SUCCEEDED')"),
        CheckConstraint("attempts >= 0 AND progress_rows >= 0"),
    )
