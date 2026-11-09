"""Append-only account selection; this is configuration, never trading authority."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from packages.persistence.models import Base, scoped_fk, utcnow


class StrategySelection(Base):
    __tablename__ = "workspace_strategy_selections"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    account_id: Mapped[UUID]
    decision_id: Mapped[UUID]
    revision: Mapped[int]
    mode: Mapped[str] = mapped_column(default="SIMULATED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        scoped_fk("account_id", "trading_accounts"),
        scoped_fk("decision_id", "campaign_lineage"),
        UniqueConstraint("owner_id", "account_id", "revision"),
        CheckConstraint("mode='SIMULATED' AND revision>0"),
    )
