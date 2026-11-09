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


def reservation_amount(saved: dict[str, Any], kind: str, context: int, output: int) -> Decimal:
    policy = CloudPolicy.model_validate(saved["policy"])
    return (
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


def budget_state(
    db: Session,
    owner: UUID,
    saved: dict[str, Any],
    amount: Decimal,
    standing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = CloudPolicy.model_validate(saved["policy"])
    midnight = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    month = midnight.replace(day=1)
    daily = select(func.coalesce(func.sum(AICloudReservation.amount), 0)).where(
        AICloudReservation.created_at >= midnight
    )
    total = db.scalar(daily) or Decimal(0)
    owned = db.scalar(daily.where(AICloudReservation.owner_id == owner)) or Decimal(0)
    monthly = db.scalar(
        select(func.coalesce(func.sum(AICloudReservation.amount), 0)).where(
            AICloudReservation.owner_id == owner, AICloudReservation.created_at >= month
        )
    ) or Decimal(0)
    request_limit = (
        min(Decimal(policy.request_usd), Decimal(standing["request_usd"]))
        if standing
        else Decimal(policy.request_usd)
    )
    day_limit = (
        min(Decimal(policy.daily_usd), Decimal(standing["daily_usd"]))
        if standing
        else Decimal(policy.daily_usd)
    )
    month_limit = Decimal(standing["monthly_usd"]) if standing else None
    return {
        "available": amount <= request_limit
        and owned + amount <= day_limit
        and total + amount <= Decimal("50")
        and (month_limit is None or monthly + amount <= month_limit),
        "reservation_usd": str(amount),
        "daily_reserved_usd": str(owned),
        "monthly_reserved_usd": str(monthly),
        "request_limit_usd": str(request_limit),
        "daily_limit_usd": str(day_limit),
        "monthly_limit_usd": str(month_limit) if month_limit is not None else None,
        "basis": "CONSERVATIVE_RESERVATIONS_NOT_PROVIDER_BILLING",
        "reset_timezone": "UTC",
    }


def reserve(
    db: Session,
    owner: UUID,
    identifier: UUID,
    saved: dict[str, Any],
    kind: str,
    context: int,
    output: int,
    acknowledged: bool,
    standing: dict[str, Any] | None = None,
) -> None:
    if kind != "DISCOVER" and acknowledged is not True and standing is None:
        raise ValueError("AI_CLOUD_COST_ACKNOWLEDGEMENT_REQUIRED")
    effective = standing
    if effective is None:
        from packages.ai.standing import latest

        active_policy = latest(db, owner)
        if active_policy is not None and active_policy.active:
            effective = active_policy.policy
    amount = reservation_amount(saved, kind, context, output)
    # One lock covers legacy and standing requests, owners, authorizations, day and month totals.
    db.execute(text("SELECT pg_advisory_xact_lock(70703,0)"))
    if not budget_state(db, owner, saved, amount, effective)["available"]:
        raise ValueError("AI_CLOUD_BUDGET_EXCEEDED")
    db.add(
        AICloudReservation(
            request_id=identifier,
            owner_id=owner,
            authorization_id=UUID(saved["authorization_id"]),
            amount=amount,
        )
    )
