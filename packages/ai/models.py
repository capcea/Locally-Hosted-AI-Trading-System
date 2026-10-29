"""Inference-only records. Worker-written rows reference AI requests, never identity secrets."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from packages.persistence.models import Base, scoped_fk, utcnow


class AIConnection(Base):
    __tablename__ = "ai_connections"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    specification: Mapped[dict[str, Any]] = mapped_column(JSON)
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("id", "owner_id"),)


class AIModel(Base):
    __tablename__ = "ai_models"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    connection_id: Mapped[UUID]
    name: Mapped[str] = mapped_column(String(150))
    context_ceiling: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        UniqueConstraint("id", "owner_id"),
        scoped_fk("connection_id", "ai_connections"),
        UniqueConstraint("connection_id", "name", "context_ceiling"),
        CheckConstraint("context_ceiling>=1024 AND context_ceiling<=32768"),
    )


class AIRoute(Base):
    __tablename__ = "ai_routes"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    revision: Mapped[int]
    model_id: Mapped[UUID]
    fallback_ids: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        scoped_fk("model_id", "ai_models"),
        UniqueConstraint("owner_id", "role", "revision"),
        CheckConstraint("role IN ('RESEARCH','CODING','CRITIC','LIGHTWEIGHT')"),
    )


class AIRequest(Base):
    __tablename__ = "ai_requests"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    key: Mapped[str] = mapped_column(String(80))
    digest: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(16))
    role: Mapped[str] = mapped_column(String(16))
    specification: Mapped[dict[str, Any]] = mapped_column(JSON)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    retain_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        UniqueConstraint("id", "owner_id"),
        UniqueConstraint("owner_id", "key"),
        CheckConstraint("kind IN ('DISCOVER','PROBE','INFER')"),
    )


class AIJob(Base):
    __tablename__ = "ai_jobs"
    request_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(index=True)
    state: Mapped[str] = mapped_column(String(16), default="QUEUED", index=True)
    attempts: Mapped[int] = mapped_column(default=0)
    cancel_requested: Mapped[bool] = mapped_column(default=False)
    worker_token: Mapped[UUID | None]
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(String(80))
    event_sequence: Mapped[int] = mapped_column(default=0)
    __table_args__ = (
        scoped_fk("request_id", "ai_requests"),
        CheckConstraint(
            "state IN ('QUEUED','RUNNING','RETRY','SUCCEEDED','FAILED','CANCELLED','UNKNOWN')"
        ),
        CheckConstraint("attempts>=0 AND attempts<=3 AND event_sequence>=0"),
    )


class AIContent(Base):
    __tablename__ = "ai_content"
    request_id: Mapped[UUID] = mapped_column(ForeignKey("ai_requests.id"), primary_key=True)
    input_ciphertext: Mapped[str | None] = mapped_column(Text)
    partial_ciphertext: Mapped[str | None] = mapped_column(Text)
    output_ciphertext: Mapped[str | None] = mapped_column(Text)


class AIArtifact(Base):
    __tablename__ = "ai_artifacts"
    request_id: Mapped[UUID] = mapped_column(ForeignKey("ai_requests.id"), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64))
    artifact_metadata: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AIEvent(Base):
    __tablename__ = "ai_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(ForeignKey("ai_requests.id"), index=True)
    sequence: Mapped[int]
    kind: Mapped[str] = mapped_column(String(32))
    details: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("request_id", "sequence"),)


class AIVerification(Base):
    __tablename__ = "ai_verifications"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    model_id: Mapped[UUID] = mapped_column(ForeignKey("ai_models.id"), index=True)
    request_id: Mapped[UUID] = mapped_column(ForeignKey("ai_requests.id"), unique=True)
    capabilities: Mapped[dict[str, Any]] = mapped_column(JSON)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AICloudAuthorization(Base):
    __tablename__ = "ai_cloud_authorizations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    revision: Mapped[int]
    policy: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("id", "owner_id"), UniqueConstraint("owner_id", "revision"))


class AIConnectionSecret(Base):
    __tablename__ = "ai_connection_secrets"
    connection_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID]
    ciphertext: Mapped[str] = mapped_column(Text)
    revision: Mapped[int] = mapped_column(default=1)
    __table_args__ = (scoped_fk("connection_id", "ai_connections"), CheckConstraint("revision>=1"))


class AICloudReservation(Base):
    __tablename__ = "ai_cloud_reservations"
    request_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID]
    authorization_id: Mapped[UUID]
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        scoped_fk("request_id", "ai_requests"),
        scoped_fk("authorization_id", "ai_cloud_authorizations"),
        CheckConstraint("amount>=0"),
    )
