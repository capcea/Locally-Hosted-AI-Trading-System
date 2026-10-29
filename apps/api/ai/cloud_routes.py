"""Owner-reviewed cloud setup. No provider calls or plaintext-key reads."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import func, select

from apps.api.ai.routes import configured, privileged, scoped
from apps.api.identity.dependencies import FullIdentity
from packages.ai.cloud import authorization
from packages.ai.cloud_contracts import CLOUD_POLICY, OPENROUTER_URL, CloudPolicy, CredentialInput
from packages.ai.models import (
    AICloudAuthorization,
    AICloudReservation,
    AIConnection,
    AIConnectionSecret,
)

router = APIRouter(prefix="/api/v1/ai", tags=["Explicit opt-in public AI cloud"])


@router.get("/cloud-policy")
def policy(identity: FullIdentity, request: Request) -> dict[str, Any]:
    try:
        row = authorization(identity.db, identity.user.id)
    except ValueError:
        row = None
    return {
        "operator_enabled": configured(request).openrouter_enabled,
        "provider": "OPENROUTER",
        "base_url": OPENROUTER_URL,
        "policy_version": CLOUD_POLICY,
        "authorization": {"id": str(row.id), "policy": row.policy} if row else None,
        "billing_reservations": [
            {
                "request_id": str(r.request_id),
                "reserved_usd": str(r.amount),
                "created_at": r.created_at,
            }
            for r in identity.db.scalars(
                select(AICloudReservation)
                .where(AICloudReservation.owner_id == identity.user.id)
                .order_by(AICloudReservation.created_at.desc())
                .limit(25)
            )
        ],
        "disclosure": (
            "OpenRouter and the approved upstream process your context. "
            "ZDR/no-training routing is requested, not independently certified. "
            "No paid call is made by saving setup."
        ),
    }


@router.post("/endpoints/openrouter", status_code=201)
def register(body: CloudPolicy, identity: FullIdentity, request: Request) -> dict[str, str]:
    privileged(identity)
    if not configured(request).openrouter_enabled:
        raise HTTPException(409, "AI_CLOUD_OPERATOR_OPT_IN_REQUIRED")
    try:
        old = authorization(identity.db, identity.user.id)
    except ValueError:
        old = None
    if old and old.policy == body.model_dump(mode="json"):
        return {"id": "openrouter", "authorization_id": str(old.id)}
    count = (
        identity.db.scalar(
            select(func.count())
            .select_from(AICloudAuthorization)
            .where(AICloudAuthorization.owner_id == identity.user.id)
        )
        or 0
    )
    if count >= 50:
        raise HTTPException(429, "AI_CLOUD_POLICY_QUOTA")
    row = AICloudAuthorization(
        owner_id=identity.user.id,
        revision=(old.revision + 1 if old else 1),
        policy=body.model_dump(mode="json"),
    )
    identity.db.add(row)
    identity.db.flush()
    identity.audit(
        "ai.cloud_authorized",
        entity_id=row.id,
        after={"version": body.version, "revision": row.revision},
    )
    return {"id": "openrouter", "authorization_id": str(row.id)}


@router.post("/connections/{connection_id}/credential")
def credential(
    connection_id: UUID, body: CredentialInput, identity: FullIdentity, request: Request
) -> dict[str, Any]:
    privileged(identity)
    row = scoped(identity, AIConnection, connection_id)
    if (
        row.specification.get("provider") != "OPENROUTER"
        or not configured(request).openrouter_enabled
    ):
        raise HTTPException(409, "AI_OPENROUTER_CREDENTIAL_REFUSED")
    try:
        authorization(identity.db, identity.user.id)
        cipher = configured(request).cipher()
    except (OSError, ValueError) as exc:
        raise HTTPException(409, "AI_CLOUD_AUTHORIZATION_OR_KEY_UNAVAILABLE") from exc
    secret = identity.db.get(AIConnectionSecret, connection_id, with_for_update=True)
    encrypted = cipher.encrypt(body.api_key.get_secret_value().encode()).decode()
    if secret is None:
        secret = AIConnectionSecret(
            connection_id=connection_id, owner_id=identity.user.id, ciphertext=encrypted, revision=1
        )
        identity.db.add(secret)
    else:
        secret.ciphertext, secret.revision = encrypted, secret.revision + 1
    identity.audit(
        "ai.credential_saved", entity_id=connection_id, after={"revision": secret.revision}
    )
    return {"configured": True, "revision": secret.revision, "reverification_required": True}
