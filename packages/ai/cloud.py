"""Explicit cloud authorization and conservative, atomic spend reservations."""

from decimal import ROUND_CEILING, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from packages.ai.cloud_contracts import CloudPolicy
from packages.ai.models import AICloudAuthorization, AICloudReservation, AIConnectionSecret
from packages.ai.settings import GatewaySettings
from packages.persistence.models import utcnow


def authorization(db: Session, owner: UUID) -> AICloudAuthorization:
    row = db.scalar(
        select(AICloudAuthorization)
        .where(AICloudAuthorization.owner_id == owner)
        .order_by(AICloudAuthorization.revision.desc())
        .limit(1)
    )
    if row is None:
        raise ValueError("AI_CLOUD_AUTHORIZATION_REQUIRED")
    return row


def snapshot(db: Session, owner: UUID, connection: UUID, config: GatewaySettings) -> dict[str, Any]:
    if not config.openrouter_enabled:
        raise ValueError("AI_CLOUD_OPERATOR_OPT_IN_REQUIRED")
    auth = authorization(db, owner)
    credential = db.get(AIConnectionSecret, connection)
    if credential is None or credential.owner_id != owner:
        raise ValueError("AI_CREDENTIAL_REQUIRED")
    return {
        "authorization_id": str(auth.id),
        "policy": auth.policy,
        "credential_revision": credential.revision,
    }


def unchanged(db: Session, owner: UUID, connection: UUID, saved: dict[str, Any]) -> bool:
    secret = db.get(AIConnectionSecret, connection, populate_existing=True)
    return (
        secret is not None
        and secret.owner_id == owner
        and secret.revision == saved["credential_revision"]
        and str(authorization(db, owner).id) == saved["authorization_id"]
    )


def reserve(
    db: Session,
    owner: UUID,
    identifier: UUID,
    saved: dict[str, Any],
    kind: str,
    context: int,
    output: int,
    acknowledged: bool,
) -> None:
    if kind != "DISCOVER" and acknowledged is not True:
        raise ValueError("AI_CLOUD_COST_ACKNOWLEDGEMENT_REQUIRED")
    policy = CloudPolicy.model_validate(saved["policy"])
    amount = (
        Decimal(0)
        if kind == "DISCOVER"
        else (
            (
                Decimal(policy.input_usd_per_million) * context
                + Decimal(policy.output_usd_per_million) * output
            )
            / Decimal(1000000)
        ).quantize(Decimal("0.00000001"), rounding=ROUND_CEILING)
    )
    db.execute(text("SELECT pg_advisory_xact_lock(70703,0)"))
    midnight = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    base = select(func.coalesce(func.sum(AICloudReservation.amount), 0)).where(
        AICloudReservation.created_at >= midnight
    )
    total = db.scalar(base) or Decimal(0)
    owned = db.scalar(base.where(AICloudReservation.owner_id == owner)) or Decimal(0)
    if (
        amount > Decimal(policy.request_usd)
        or owned + amount > Decimal(policy.daily_usd)
        or total + amount > Decimal("50")
    ):
        raise ValueError("AI_CLOUD_BUDGET_EXCEEDED")
    db.add(
        AICloudReservation(
            request_id=identifier,
            owner_id=owner,
            authorization_id=UUID(saved["authorization_id"]),
            amount=amount,
        )
    )
