"""One-time MFA-reviewed standing consent and truthful inference readiness."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import select

from apps.api.ai.routes import configured, privileged, quota_available, status
from apps.api.identity.dependencies import FullIdentity, require_owner
from packages.ai.cloud import budget_state, reservation_amount
from packages.ai.models import AIRoute, AIStandingAuthorization
from packages.ai.prompts import digest
from packages.ai.registry import snapshot
from packages.ai.standing import build_policy, latest, require
from packages.ai.standing_contracts import DataCategory, StandingInput
from packages.persistence.models import utcnow

router = APIRouter(prefix="/api/v1/ai", tags=["Standing inference consent; no execution authority"])


def view(row: AIStandingAuthorization | None) -> dict[str, Any]:
    return {
        "authorization": {
            "id": str(row.id),
            "revision": row.revision,
            "active": row.active,
            "policy": row.policy,
            "created_at": row.created_at,
        }
        if row
        else None
    }


@router.get("/standing-authorization")
def read(identity: FullIdentity) -> dict[str, Any]:
    return view(latest(identity.db, identity.user.id))


@router.post("/standing-authorization", status_code=201)
def activate(body: StandingInput, identity: FullIdentity, request: Request) -> dict[str, Any]:
    privileged(identity)
    try:
        policy = build_policy(identity.db, identity.user.id, body, configured(request))
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    old = latest(identity.db, identity.user.id)
    if old and old.active and old.policy == policy:
        return view(old)
    row = AIStandingAuthorization(
        owner_id=identity.user.id,
        revision=old.revision + 1 if old else 1,
        active=True,
        policy=policy,
    )
    identity.db.add(row)
    identity.db.flush()
    identity.audit(
        "ai.standing_activated",
        entity_id=row.id,
        after={"revision": row.revision, "policy_digest": digest(policy)},
    )
    return view(row)


@router.post("/standing-authorization/revoke")
def revoke(identity: FullIdentity) -> dict[str, Any]:
    privileged(identity)
    old = latest(identity.db, identity.user.id)
    if old is None or not old.active:
        return view(old)
    row = AIStandingAuthorization(
        owner_id=identity.user.id, revision=old.revision + 1, active=False, policy=old.policy
    )
    identity.db.add(row)
    identity.db.flush()
    identity.audit("ai.standing_revoked", entity_id=row.id, after={"superseded_id": str(old.id)})
    return view(row)


@router.get("/inference-readiness")
def readiness(
    identity: FullIdentity,
    request: Request,
    role: str = Query("RESEARCH", pattern="^(RESEARCH|CODING|CRITIC|LIGHTWEIGHT)$"),
    category: DataCategory = "documentation",
    context_tokens: int = Query(4096, ge=1024, le=131072),
    output_tokens: int = Query(768, ge=64, le=4096),
) -> dict[str, Any]:
    config = configured(request)
    observed = status(identity, request)
    row = latest(identity.db, identity.user.id)
    result: dict[str, Any] = {
        "ready": False,
        "reason": None,
        "observed_at": utcnow(),
        "gateway_configured": observed["configured"],
        "worker_state": observed["worker_state"],
        "worker_expires_at": observed["worker_expires_at"],
        "model_id": None,
        "standing_authorization_id": str(row.id) if row and row.active else None,
        "standing_active": bool(row and row.active),
        "model_verified": False,
        "budget": None,
        "external_execution": "DENY_ALL",
        "generated_code_execution": False,
    }
    model = None
    model_reason = "AI_ROLE_NOT_CONFIGURED"
    try:
        binding = identity.db.scalar(
            select(AIRoute)
            .where(AIRoute.owner_id == identity.user.id, AIRoute.role == role)
            .order_by(AIRoute.revision.desc())
            .limit(1)
        )
        if binding is None:
            raise ValueError("AI_ROLE_NOT_CONFIGURED")
        model = snapshot(identity.db, identity.user.id, binding.model_id, config)
        result["model_verified"] = True
        result["model_id"] = model["model_id"]
    except ValueError as exc:
        model_reason = str(exc)
    try:
        require_owner(identity)
        if not observed["configured"]:
            raise ValueError("AI_NOT_CONFIGURED")
        if row is None or not row.active:
            raise ValueError("AI_STANDING_AUTHORIZATION_REQUIRED")
        if model is None:
            raise ValueError(model_reason)
        require(
            identity.db,
            identity.user.id,
            row.id,
            config,
            kind="INFER",
            role=role,
            categories=[category],
            connections=[UUID(model["connection_id"])],
        )
        if context_tokens > model["capabilities"].get("context_tokens", 0):
            raise ValueError("AI_CONTEXT_BUDGET_UNVERIFIED")
        if (
            model["remote"]
            and category not in {"strategy", "documentation"}
            and not model["profile"]["policy"]["account_context_remote"]
        ):
            raise ValueError("AI_REMOTE_CONTEXT_POLICY_REFUSED")
        if model.get("cloud"):
            amount = reservation_amount(model["cloud"], "INFER", context_tokens, output_tokens)
            result["budget"] = budget_state(
                identity.db, identity.user.id, model["cloud"], amount, row.policy
            )
            if not result["budget"]["available"]:
                raise ValueError("AI_CLOUD_BUDGET_EXCEEDED")
        else:
            result["budget"] = {
                "available": True,
                "basis": "PRIVATE_PROVIDER_NO_CLOUD_RESERVATION",
                "reservation_usd": str(Decimal(0)),
            }
        if not quota_available(identity, config, role):
            raise ValueError("AI_QUOTA_REACHED")
        if observed["worker_state"] != "OBSERVED_RECENTLY":
            raise ValueError("AI_WORKER_UNAVAILABLE")
        result["ready"] = True
    except ValueError as exc:
        result["reason"] = str(exc)
    except HTTPException as exc:
        result["reason"] = "AI_OWNER_REQUIRED" if exc.status_code == 403 else "AI_UNAVAILABLE"
    return result
