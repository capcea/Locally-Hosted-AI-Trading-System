"""Immutable campaign specifications, append-only lineage and fenced runtime state."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from packages.persistence.models import Base, scoped_fk, utcnow


class ResearchCampaign(Base):
    __tablename__ = "research_campaigns"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    account_id: Mapped[UUID]
    key: Mapped[str] = mapped_column(String(80))
    digest: Mapped[str] = mapped_column(String(64))
    specification: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        UniqueConstraint("id", "owner_id"),
        UniqueConstraint("owner_id", "key"),
        scoped_fk("account_id", "trading_accounts"),
    )


class CampaignRuntime(Base):
    __tablename__ = "campaign_runtime"
    campaign_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    state: Mapped[str] = mapped_column(String(32), default="DRAFT", index=True)
    pending: Mapped[str | None] = mapped_column(String(40))
    reason: Mapped[str | None] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(default=False)
    cancel_requested: Mapped[bool] = mapped_column(default=False)
    paused: Mapped[bool] = mapped_column(default=False)
    proposals: Mapped[int] = mapped_column(default=0)
    experiments: Mapped[int] = mapped_column(default=0)
    iteration: Mapped[int] = mapped_column(default=0)
    lineage_bytes: Mapped[int] = mapped_column(default=0)
    reserved_bytes: Mapped[int] = mapped_column(default=0)
    reserved_seconds: Mapped[int] = mapped_column(default=0)
    sequence: Mapped[int] = mapped_column(default=0)
    head: Mapped[str] = mapped_column(String(64), default="0" * 64)
    approval: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worker_token: Mapped[UUID | None]
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(default=0)
    __table_args__ = (
        scoped_fk("campaign_id", "research_campaigns"),
        CheckConstraint("proposals>=0 AND proposals<=8 AND experiments>=0 AND experiments<=12"),
        CheckConstraint("iteration>=0 AND iteration<=2 AND attempts>=0 AND attempts<=3"),
        CheckConstraint("lineage_bytes>=0 AND reserved_bytes>=0 AND reserved_seconds>=0"),
        CheckConstraint("sequence>=0"),
        CheckConstraint(
            "state IN ('DRAFT','AWAITING_APPROVAL','QUEUED','PLANNING','TESTING',"
            "'EVALUATING','CRITIQUING','READY_FOR_NEXT_ITERATION','COMPLETED',"
            "'STOPPED','FAILED','UNKNOWN')"
        ),
    )


class CampaignLineage(Base):
    __tablename__ = "campaign_lineage"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    campaign_id: Mapped[UUID]
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("campaign_lineage.id"))
    sequence: Mapped[int]
    kind: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String(24))
    previous_digest: Mapped[str] = mapped_column(String(64))
    digest: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        scoped_fk("campaign_id", "research_campaigns"),
        UniqueConstraint("id", "owner_id"),
        UniqueConstraint("campaign_id", "sequence"),
        CheckConstraint("sequence>0"),
        CheckConstraint("source IN ('SYNTHETIC_FIXTURE','AI_GATEWAY')"),
    )


class CampaignExperiment(Base):
    __tablename__ = "campaign_experiments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    campaign_id: Mapped[UUID]
    plan_id: Mapped[UUID]
    run_id: Mapped[UUID]
    ordinal: Mapped[int]
    __table_args__ = (
        scoped_fk("campaign_id", "research_campaigns"),
        scoped_fk("plan_id", "campaign_lineage"),
        scoped_fk("run_id", "research_runs"),
        UniqueConstraint("plan_id"),
        UniqueConstraint("run_id"),
        UniqueConstraint("campaign_id", "ordinal"),
    )
