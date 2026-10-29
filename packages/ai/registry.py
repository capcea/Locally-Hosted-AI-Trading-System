"""Scoped registry snapshots; verification comes only from measured worker probes."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.ai.contracts import ConnectionInput
from packages.ai.models import AIConnection, AIModel, AIVerification
from packages.ai.prompts import digest
from packages.ai.settings import GatewaySettings
from packages.persistence.models import utcnow


def latest_verification(db: Session, model_id: UUID) -> AIVerification | None:
    return db.scalar(
        select(AIVerification)
        .where(AIVerification.model_id == model_id)
        .order_by(AIVerification.created_at.desc())
        .limit(1)
    )


def snapshot(
    db: Session, owner: UUID, model_id: UUID, config: GatewaySettings, *, verified: bool = True
) -> dict[str, Any]:
    model = db.scalar(select(AIModel).where(AIModel.id == model_id, AIModel.owner_id == owner))
    if model is None:
        raise ValueError("AI_MODEL_NOT_FOUND")
    connection = db.scalar(
        select(AIConnection).where(
            AIConnection.id == model.connection_id, AIConnection.owner_id == owner
        )
    )
    if connection is None or not connection.enabled:
        raise ValueError("AI_CONNECTION_DISABLED")
    profile = ConnectionInput.model_validate(connection.specification)
    endpoint = config.endpoint(profile.endpoint_id)
    check = latest_verification(db, model.id)
    if verified and (
        check is None
        or check.expires_at <= utcnow()
        or check.capabilities.get("structured_outputs") != "VERIFIED"
    ):
        raise ValueError("AI_MODEL_REQUIRES_VERIFICATION")
    cloud = None
    if profile.provider == "OPENROUTER":
        from packages.ai.cloud import snapshot as cloud_snapshot

        cloud = cloud_snapshot(db, owner, connection.id, config)
        if not profile.policy.cloud_processing_acknowledged or not profile.policy.remote_processing:
            raise ValueError("AI_CLOUD_AUTHORIZATION_REQUIRED")
        if verified and (check is None or check.capabilities.get("cloud") != cloud):
            raise ValueError("AI_MODEL_REQUIRES_VERIFICATION")
    return {
        "cloud": cloud,
        "model_id": str(model.id),
        "connection_id": str(connection.id),
        "model_name": model.name,
        "context_ceiling": model.context_ceiling,
        "provider": profile.provider,
        "endpoint_id": profile.endpoint_id,
        "endpoint_digest": digest(endpoint.model_dump(mode="json")),
        "profile": profile.model_dump(mode="json"),
        "verification_id": str(check.id) if check else None,
        "capabilities": check.capabilities if check else {},
        "verification_expires_at": check.expires_at.isoformat() if check else None,
        "remote": endpoint.transport in {"SSH_TUNNEL", "AUTHENTICATED_TLS", "OPENROUTER_PUBLIC"},
    }
