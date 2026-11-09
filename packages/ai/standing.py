"""Persistent, pinned owner consent. This module grants inference only, never tools or orders."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.ai.cloud import authorization as cloud_authorization
from packages.ai.contracts import ConnectionInput
from packages.ai.models import AIConnection, AIStandingAuthorization
from packages.ai.prompts import digest
from packages.ai.settings import GatewaySettings
from packages.ai.standing_contracts import StandingInput


def latest(db: Session, owner: UUID) -> AIStandingAuthorization | None:
    return db.scalar(
        select(AIStandingAuthorization)
        .where(AIStandingAuthorization.owner_id == owner)
        .order_by(AIStandingAuthorization.revision.desc())
        .limit(1)
    )


def grant(db: Session, owner: UUID, connection: UUID, config: GatewaySettings) -> dict[str, Any]:
    row = db.scalar(
        select(AIConnection).where(AIConnection.id == connection, AIConnection.owner_id == owner)
    )
    if row is None or not row.enabled:
        raise ValueError("AI_STANDING_CONNECTION_UNAVAILABLE")
    profile = ConnectionInput.model_validate(row.specification)
    endpoint = config.endpoint(profile.endpoint_id)
    if (
        endpoint.transport in {"AUTHENTICATED_TLS", "SSH_TUNNEL", "OPENROUTER_PUBLIC"}
        and not profile.policy.remote_processing
    ):
        raise ValueError("AI_REMOTE_CONTEXT_POLICY_REFUSED")
    cloud_id = None
    if profile.provider == "OPENROUTER":
        if not config.openrouter_enabled or not profile.policy.cloud_processing_acknowledged:
            raise ValueError("AI_CLOUD_EXPLICIT_CONSENT_REQUIRED")
        cloud_id = str(cloud_authorization(db, owner).id)
    return {
        "connection_id": str(row.id),
        "provider": profile.provider,
        "endpoint_id": endpoint.id,
        "destination": endpoint.url,
        "endpoint_digest": digest(endpoint.model_dump(mode="json")),
        "profile_digest": digest(row.specification),
        "cloud_authorization_id": cloud_id,
    }


def build_policy(
    db: Session, owner: UUID, body: StandingInput, config: GatewaySettings
) -> dict[str, Any]:
    return {
        **body.model_dump(mode="json"),
        "grants": [grant(db, owner, identifier, config) for identifier in body.connection_ids],
        "trading_authority": False,
        "generated_code_execution": False,
        "processing": "TEMPORARY_ENCRYPTED",
        "retention": "EXISTING_CONNECTION_POLICY",
    }


def require(
    db: Session,
    owner: UUID,
    identifier: UUID,
    config: GatewaySettings,
    *,
    kind: str,
    role: str,
    categories: list[str],
    connections: list[UUID],
) -> AIStandingAuthorization:
    row = latest(db, owner)
    if row is None or not row.active or row.id != identifier:
        raise ValueError("AI_STANDING_AUTHORIZATION_REQUIRED")
    if (
        kind not in row.policy["operations"]
        or role not in row.policy["roles"]
        or not set(categories) <= set(row.policy["data_categories"])
    ):
        raise ValueError("AI_STANDING_SCOPE_REFUSED")
    for identifier in connections:
        current = grant(db, owner, identifier, config)
        if current not in row.policy["grants"]:
            raise ValueError("AI_STANDING_SCOPE_CHANGED")
    return row
