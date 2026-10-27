"""Ordinary development paths cannot read sealed data or mutate research-managed journals."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from packages.market.models import MarketDataset
from packages.research.models import HoldoutSeal


def seal_for(db: Session, dataset: MarketDataset) -> HoldoutSeal | None:
    # Protect equivalent intervals/aliases, comparing actual aware instants, never ISO text order.
    for original, seal in db.execute(
        select(MarketDataset, HoldoutSeal)
        .join(HoldoutSeal, HoldoutSeal.dataset_id == MarketDataset.id)
        .where(
            MarketDataset.owner_id == dataset.owner_id,
        )
    ):
        if datetime.fromisoformat(str(dataset.spec["start"])) < datetime.fromisoformat(
            str(original.spec["end"])
        ) and datetime.fromisoformat(str(dataset.spec["end"])) > datetime.fromisoformat(
            str(original.spec["start"])
        ):
            return seal
    return None


def sealed(db: Session, dataset: MarketDataset) -> bool:
    return seal_for(db, dataset) is not None


def public_query(owner_id: UUID) -> Select[MarketDataset]:
    from sqlalchemy import DateTime, cast, exists
    from sqlalchemy.orm import aliased

    protected = aliased(MarketDataset)
    overlap = exists(
        select(HoldoutSeal.id)
        .join(protected, HoldoutSeal.dataset_id == protected.id)
        .where(
            protected.owner_id == owner_id,
            cast(protected.spec["start"].as_string(), DateTime(timezone=True))
            < cast(MarketDataset.spec["end"].as_string(), DateTime(timezone=True)),
            cast(protected.spec["end"].as_string(), DateTime(timezone=True))
            > cast(MarketDataset.spec["start"].as_string(), DateTime(timezone=True)),
        )
    )
    return select(MarketDataset).where(MarketDataset.owner_id == owner_id, ~overlap)
