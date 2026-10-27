"""Additive research records; immutable plans/trials/results and fenced mutable jobs."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from packages.persistence.models import Base, scoped_fk, utcnow


class ResearchRun(Base):
    __tablename__ = "research_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    source_account_id: Mapped[UUID]
    key: Mapped[str] = mapped_column(String(80))
    request_digest: Mapped[str] = mapped_column(String(64))
    plan: Mapped[dict[str, Any]] = mapped_column(JSON)
    approval_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    family_digest: Mapped[str] = mapped_column(String(64), index=True)
    release_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("research_holdout_releases.id"), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        UniqueConstraint("id", "owner_id"),
        scoped_fk("source_account_id", "trading_accounts"),
        UniqueConstraint("owner_id", "key"),
    )


class ResearchJob(Base):
    __tablename__ = "research_jobs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    run_id: Mapped[UUID]
    state: Mapped[str] = mapped_column(String(16), default="QUEUED", index=True)
    attempts: Mapped[int] = mapped_column(default=0)
    progress: Mapped[int] = mapped_column(default=0)
    cancel_requested: Mapped[bool] = mapped_column(default=False)
    worker_token: Mapped[UUID | None]
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        scoped_fk("run_id", "research_runs"),
        UniqueConstraint("run_id"),
        CheckConstraint("state IN ('QUEUED','RUNNING','RETRY','FAILED','CANCELLED','SUCCEEDED')"),
        CheckConstraint("attempts>=0 AND progress>=0 AND progress<=100"),
    )


class ResearchTrial(Base):
    __tablename__ = "research_trials"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    run_id: Mapped[UUID]
    ordinal: Mapped[int]
    specification: Mapped[dict[str, Any]] = mapped_column(JSON)
    __table_args__ = (
        scoped_fk("run_id", "research_runs"),
        UniqueConstraint("run_id", "ordinal"),
        CheckConstraint("ordinal>=0"),
    )


class ResearchResult(Base):
    __tablename__ = "research_results"
    run_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    artifact: Mapped[dict[str, Any]] = mapped_column(JSON)
    semantic_digest: Mapped[str] = mapped_column(String(64))
    summary: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (scoped_fk("run_id", "research_runs"),)


class HoldoutSeal(Base):
    __tablename__ = "research_holdout_seals"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    dataset_id: Mapped[UUID]
    manifest_sha256: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(String(1000))
    prior_exposure: Mapped[str] = mapped_column(
        String(40), default="UNKNOWN_NOT_CERTIFIED_UNTOUCHED"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        UniqueConstraint("id", "owner_id"),
        scoped_fk("dataset_id", "market_datasets"),
        UniqueConstraint("dataset_id"),
    )


class HoldoutRelease(Base):
    __tablename__ = "research_holdout_releases"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    seal_id: Mapped[UUID]
    frozen_digest: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (scoped_fk("seal_id", "research_holdout_seals"), UniqueConstraint("seal_id"))


class ResearchAccount(Base):
    __tablename__ = "research_accounts"
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    run_id: Mapped[UUID]
    attempt: Mapped[int]
    ordinal: Mapped[int]
    __table_args__ = (
        scoped_fk("account_id", "trading_accounts"),
        scoped_fk("run_id", "research_runs"),
        UniqueConstraint("run_id", "attempt", "ordinal"),
    )
