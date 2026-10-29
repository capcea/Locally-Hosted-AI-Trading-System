"""AI request orchestration. No provider credentials/HTTP calls or model execution tools here."""

import json
import re
import time
from collections.abc import Iterator
from datetime import timedelta
from typing import Any, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from apps.api.ai.context import ContextScope, assemble
from apps.api.identity.dependencies import (
    FullIdentity,
    Principal,
    require_owner,
    require_recent_mfa,
)
from packages.ai.contracts import (
    ActionKey,
    AIJobView,
    ConnectionInput,
    ContextReference,
    EnabledInput,
    ModelInput,
    RequestInput,
    RouteInput,
    State,
)
from packages.ai.lifecycle import event
from packages.ai.models import (
    AIArtifact,
    AIConnection,
    AIContent,
    AIEvent,
    AIJob,
    AIModel,
    AIRequest,
    AIRoute,
)
from packages.ai.prompts import VERSION, canonical, digest, messages, validate_output
from packages.ai.registry import latest_verification, snapshot
from packages.ai.settings import GatewaySettings
from packages.persistence.models import LoginSession, User, utcnow
from packages.persistence.store import Store

router = APIRouter(prefix="/api/v1/ai", tags=["Private AI — untrusted analysis, no execution"])


def configured(request: Request) -> GatewaySettings:
    config: GatewaySettings = request.app.state.ai_config
    return config


def privileged(identity: Principal) -> None:
    require_owner(identity)
    require_recent_mfa(identity)


def scoped(identity: Principal, row_type: type[Any], identifier: UUID) -> Any:
    row = identity.db.scalar(
        select(row_type).where(row_type.id == identifier, row_type.owner_id == identity.user.id)
    )
    if row is None:
        raise HTTPException(404, "AI_RECORD_NOT_FOUND")
    return row


def job_view(db: Session, row: AIRequest, config: GatewaySettings) -> AIJobView:
    job = db.get(AIJob, row.id)
    if job is None:
        raise HTTPException(404, "AI_RECORD_NOT_FOUND")
    artifact = db.get(AIArtifact, row.id)
    content = db.get(AIContent, row.id)
    output = None
    expired = row.retain_until <= utcnow()
    context_available = True
    if row.kind == "INFER" and artifact:
        try:
            assemble(
                ContextScope(db, row.owner_id),
                [
                    ContextReference.model_validate(r)
                    for r in row.specification.get("references", [])
                ],
                config,
            )
        except HTTPException:
            context_available = False
    if artifact and content and content.output_ciphertext and not expired and context_available:
        try:
            output = json.loads(config.cipher().decrypt(content.output_ciphertext.encode()))
            if digest(output) != artifact.digest:
                raise ValueError("AI_ARTIFACT_INTEGRITY")
            if row.kind == "INFER":
                validate_output(
                    row.role, canonical(output), set(row.specification.get("allowed_refs", []))
                )
        except Exception as exc:
            raise HTTPException(409, "AI_ARTIFACT_UNAVAILABLE_OR_INVALID") from exc
    return AIJobView(
        id=row.id,
        kind=row.kind,
        role=row.role,
        state=cast(State, job.state),
        attempts=job.attempts,
        cancel_requested=job.cancel_requested,
        error=job.error,
        created_at=row.created_at,
        expires_at=row.expires_at,
        retain_until=row.retain_until,
        output=output,
        metadata=artifact.artifact_metadata if artifact else None,
        content_expired=expired,
        context_available=context_available,
    )


def enqueue(
    identity: Principal,
    request: Request,
    *,
    key: str,
    kind: str,
    role: str,
    fingerprint: str,
    spec: dict[str, Any],
    content: dict[str, Any],
    processing_minutes: int,
    retention_hours: int,
    cloud_acknowledged: bool = False,
) -> AIJobView:
    config = configured(request)
    previous = identity.db.scalar(
        select(AIRequest).where(AIRequest.owner_id == identity.user.id, AIRequest.key == key)
    )
    if previous:
        if previous.digest != fingerprint:
            raise HTTPException(409, "AI_IDEMPOTENCY_CONFLICT")
        return job_view(identity.db, previous, config)
    try:
        cipher = config.cipher()
    except (ValueError, OSError) as exc:
        raise HTTPException(503, "AI_NOT_CONFIGURED") from exc
    if len(canonical(content).encode()) > config.max_input_bytes:
        raise HTTPException(422, "AI_INPUT_BYTE_LIMIT")
    # FullIdentity already serializes this owner's mutations on the existing user row.
    now = utcnow()
    total = (
        identity.db.scalar(
            select(func.count())
            .select_from(AIRequest)
            .where(AIRequest.owner_id == identity.user.id)
        )
        or 0
    )
    hourly = (
        identity.db.scalar(
            select(func.count())
            .select_from(AIRequest)
            .where(
                AIRequest.owner_id == identity.user.id,
                AIRequest.created_at > now - timedelta(hours=1),
            )
        )
        or 0
    )
    hourly_role = (
        identity.db.scalar(
            select(func.count())
            .select_from(AIRequest)
            .where(
                AIRequest.owner_id == identity.user.id,
                AIRequest.role == role,
                AIRequest.created_at > now - timedelta(hours=1),
            )
        )
        or 0
    )
    pending = (
        identity.db.scalar(
            select(func.count())
            .select_from(AIJob)
            .where(
                AIJob.owner_id == identity.user.id, AIJob.state.in_(["QUEUED", "RUNNING", "RETRY"])
            )
        )
        or 0
    )
    if (
        total >= config.metadata_limit
        or hourly >= config.hourly_owner_limit
        or hourly_role >= config.hourly_role_limit
        or pending >= 8
    ):
        raise HTTPException(429, "AI_QUOTA_REACHED")
    if identity.session.mfa_at is None:
        raise HTTPException(403, "AI_RECENT_MFA_REQUIRED")
    selected = spec.get("models", [spec])[0]
    if selected.get("cloud"):
        spec = {**spec, "cloud": selected["cloud"]}
    row = AIRequest(
        id=uuid4(),
        owner_id=identity.user.id,
        key=key,
        digest=fingerprint,
        kind=kind,
        role=role,
        specification={
            **spec,
            "session_id": str(identity.session.id),
            "input_digest": digest(content),
        },
        expires_at=min(
            now + timedelta(minutes=processing_minutes),
            identity.session.mfa_at + timedelta(minutes=5),
        ),
        retain_until=now + timedelta(hours=retention_hours),
    )
    job = AIJob(request_id=row.id, owner_id=identity.user.id)
    # Explicit parent flush: these immutable records deliberately have no cascading ORM
    # relationships. Child inserts must not race the request FK inside the unit of work.
    identity.db.add(row)
    identity.db.flush()
    if selected.get("cloud"):
        from packages.ai.cloud import reserve

        parameters = spec.get("parameters", {})
        try:
            reserve(
                identity.db,
                identity.user.id,
                row.id,
                selected["cloud"],
                kind,
                parameters.get("context_tokens", selected.get("context_ceiling", 4096)),
                parameters.get("output_tokens", 64),
                cloud_acknowledged,
            )
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
    identity.db.add_all(
        [
            job,
            AIContent(
                request_id=row.id,
                input_ciphertext=cipher.encrypt(canonical(content).encode()).decode(),
            ),
        ]
    )
    identity.db.flush()
    event(identity.db, job, "REQUESTED", {"kind": kind, "role": role})
    identity.audit(
        "ai.requested",
        entity_id=row.id,
        after={
            "kind": kind,
            "role": role,
            "request_digest": fingerprint,
            "prompt_version": VERSION,
        },
    )
    # Redis is a wakeup hint only; PG polling recovers a pre-commit/missing hint.
    if config.redis_url:
        try:
            with Redis.from_url(
                config.redis_url.get_secret_value(), socket_connect_timeout=1, socket_timeout=1
            ) as queue:
                queue.lpush("ai:jobs", str(row.id))
                queue.ltrim("ai:jobs", 0, 999)
        except RedisError:
            event(identity.db, job, "QUEUE_HINT_UNAVAILABLE")
    return job_view(identity.db, row, config)


@router.get("/status")
def status(identity: FullIdentity, request: Request) -> dict[str, Any]:
    config = configured(request)
    ready = False
    try:
        config.cipher()
        ready = True
    except (ValueError, OSError):
        pass
    count = (
        identity.db.scalar(
            select(func.count()).select_from(AIModel).where(AIModel.owner_id == identity.user.id)
        )
        or 0
    )
    worker_state = "UNKNOWN"
    if config.redis_url:
        try:
            with Redis.from_url(
                config.redis_url.get_secret_value(), socket_connect_timeout=1, socket_timeout=1
            ) as queue:
                stamp = queue.get("ai:worker-heartbeat")
                if stamp and 0 <= time.time() - float(stamp) < 20:
                    worker_state = "OBSERVED_RECENTLY"
        except (RedisError, ValueError):
            pass
    return {
        "configured": ready,
        "configuration_error": request.app.state.ai_error,
        "model_count": count,
        "worker_state": worker_state,
        "gpu_availability": "UNKNOWN",
        "external_execution": "DENY_ALL",
        "generated_code_execution": False,
        "roles": ["RESEARCH", "CODING", "CRITIC", "LIGHTWEIGHT"],
        "limits": {
            "hourly_owner": config.hourly_owner_limit,
            "hourly_role": config.hourly_role_limit,
            "metadata_records": config.metadata_limit,
            "input_bytes": config.max_input_bytes,
            "output_bytes": config.max_output_bytes,
            "global_concurrency": config.global_concurrency,
        },
    }


@router.get("/endpoints")
def endpoints(identity: FullIdentity, request: Request) -> list[dict[str, Any]]:
    from packages.ai.cloud import authorization

    approved = False
    if configured(request).openrouter_enabled:
        try:
            authorization(identity.db, identity.user.id)
            approved = True
        except ValueError:
            pass
    return [
        {"id": e.id, "label": e.label, "transport": e.transport}
        for e in configured(request).endpoints
        if e.transport != "OPENROUTER_PUBLIC" or approved
    ]


@router.get("/connections")
def connections(identity: FullIdentity) -> list[dict[str, Any]]:
    from packages.ai.models import AIConnectionSecret

    return [
        {
            "id": str(row.id),
            "enabled": row.enabled,
            **row.specification,
            "credential_configured": identity.db.get(AIConnectionSecret, row.id) is not None,
        }
        for row in identity.db.scalars(
            select(AIConnection)
            .where(AIConnection.owner_id == identity.user.id)
            .order_by(AIConnection.created_at)
            .limit(100)
        )
    ]


@router.post("/connections", status_code=201)
def create_connection(
    body: ConnectionInput, identity: FullIdentity, request: Request
) -> dict[str, str]:
    privileged(identity)
    try:
        endpoint = configured(request).endpoint(body.endpoint_id)
    except ValueError as exc:
        raise HTTPException(409, "AI_ENDPOINT_NOT_ALLOWLISTED") from exc
    if (body.provider == "OPENROUTER") != (endpoint.transport == "OPENROUTER_PUBLIC"):
        raise HTTPException(409, "AI_PROVIDER_DESTINATION_MISMATCH")
    if body.provider == "OPENROUTER":
        from packages.ai.cloud import authorization

        try:
            authorization(identity.db, identity.user.id)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if (
            not configured(request).openrouter_enabled
            or not body.policy.cloud_processing_acknowledged
            or not body.policy.remote_processing
        ):
            raise HTTPException(409, "AI_CLOUD_EXPLICIT_CONSENT_REQUIRED")
    if (
        endpoint.transport in {"SSH_TUNNEL", "AUTHENTICATED_TLS"}
        and not body.policy.remote_processing
    ):
        raise HTTPException(409, "AI_REMOTE_POLICY_REQUIRED")
    count = (
        identity.db.scalar(
            select(func.count())
            .select_from(AIConnection)
            .where(AIConnection.owner_id == identity.user.id)
        )
        or 0
    )
    if count >= 20:
        raise HTTPException(429, "AI_CONNECTION_QUOTA")
    row = AIConnection(owner_id=identity.user.id, specification=body.model_dump(mode="json"))
    identity.db.add(row)
    identity.db.flush()
    identity.audit(
        "ai.connection_created",
        entity_id=row.id,
        after={"specification_digest": digest(row.specification)},
    )
    return {"id": str(row.id)}


@router.patch("/connections/{connection_id}")
def enable_connection(
    connection_id: UUID, body: EnabledInput, identity: FullIdentity
) -> dict[str, bool]:
    privileged(identity)
    row = scoped(identity, AIConnection, connection_id)
    row.enabled = body.enabled
    identity.audit("ai.connection_enabled", entity_id=row.id, after={"enabled": row.enabled})
    return {"enabled": row.enabled}


@router.post("/connections/{connection_id}/discover", response_model=AIJobView, status_code=202)
def discover(
    connection_id: UUID, body: ActionKey, identity: FullIdentity, request: Request
) -> AIJobView:
    privileged(identity)
    row = scoped(identity, AIConnection, connection_id)
    profile = ConnectionInput.model_validate(row.specification)
    if not row.enabled:
        raise HTTPException(409, "AI_CONNECTION_DISABLED")
    config = configured(request)
    try:
        endpoint = config.endpoint(profile.endpoint_id)
    except ValueError as exc:
        raise HTTPException(409, "AI_ENDPOINT_NOT_ALLOWLISTED") from exc
    spec: dict[str, Any] = {
        "connection_id": str(row.id),
        "provider": profile.provider,
        "endpoint_id": profile.endpoint_id,
        "endpoint_digest": digest(endpoint.model_dump(mode="json")),
        "prompt_version": VERSION,
    }
    if profile.provider == "OPENROUTER":
        from packages.ai.cloud import snapshot as cloud_snapshot

        try:
            spec["cloud"] = cloud_snapshot(identity.db, identity.user.id, row.id, config)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
    return enqueue(
        identity,
        request,
        key=body.key,
        kind="DISCOVER",
        role="LIGHTWEIGHT",
        fingerprint=digest({"discover": str(row.id), "key": body.key}),
        spec=spec,
        content={},
        processing_minutes=5,
        retention_hours=1,
    )


@router.get("/models")
def models(identity: FullIdentity, request: Request) -> list[dict[str, Any]]:
    result = []
    for row in identity.db.scalars(
        select(AIModel)
        .where(AIModel.owner_id == identity.user.id)
        .order_by(AIModel.created_at)
        .limit(100)
    ):
        verification = latest_verification(identity.db, row.id)
        current = bool(verification and verification.expires_at > utcnow())
        if current:
            try:
                snapshot(identity.db, identity.user.id, row.id, configured(request))
            except ValueError:
                current = False
        result.append(
            {
                "id": str(row.id),
                "connection_id": str(row.connection_id),
                "name": row.name,
                "context_ceiling": row.context_ceiling,
                "verification": verification.capabilities if verification else None,
                "verified_until": verification.expires_at if verification else None,
                "verification_current": current,
            }
        )
    return result


@router.post("/models", status_code=201)
def register_model(body: ModelInput, identity: FullIdentity) -> dict[str, str]:
    privileged(identity)
    connection = scoped(identity, AIConnection, body.connection_id)
    if connection.specification.get("provider") == "OPENROUTER" and (
        not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9][A-Za-z0-9_.:+-]{0,119}", body.name)
        or body.name.startswith("openrouter/")
    ):
        raise HTTPException(422, "AI_EXACT_MODEL_ID_REQUIRED")
    count = (
        identity.db.scalar(
            select(func.count()).select_from(AIModel).where(AIModel.owner_id == identity.user.id)
        )
        or 0
    )
    if count >= 50:
        raise HTTPException(429, "AI_MODEL_QUOTA")
    row = AIModel(
        owner_id=identity.user.id,
        connection_id=body.connection_id,
        name=body.name,
        context_ceiling=body.context_ceiling,
    )
    identity.db.add(row)
    identity.db.flush()
    identity.audit(
        "ai.model_registered", entity_id=row.id, after={"connection_id": str(body.connection_id)}
    )
    return {"id": str(row.id)}


@router.post("/models/{model_id}/probe", response_model=AIJobView, status_code=202)
def probe(model_id: UUID, body: ActionKey, identity: FullIdentity, request: Request) -> AIJobView:
    privileged(identity)
    try:
        model = snapshot(
            identity.db, identity.user.id, model_id, configured(request), verified=False
        )
    except ValueError as exc:
        raise HTTPException(409, "AI_MODEL_OR_CONNECTION_UNAVAILABLE") from exc
    return enqueue(
        identity,
        request,
        key=body.key,
        kind="PROBE",
        cloud_acknowledged=body.cloud_cost_acknowledged,
        role="LIGHTWEIGHT",
        fingerprint=digest({"probe": str(model_id), "key": body.key}),
        spec={"models": [model], "prompt_version": VERSION},
        content={},
        processing_minutes=5,
        retention_hours=1,
    )


@router.get("/routes")
def routes(identity: FullIdentity) -> list[dict[str, Any]]:
    return [
        {
            "id": str(r.id),
            "role": r.role,
            "revision": r.revision,
            "model_id": str(r.model_id),
            "fallback_ids": r.fallback_ids,
        }
        for r in identity.db.scalars(
            select(AIRoute)
            .where(AIRoute.owner_id == identity.user.id)
            .order_by(AIRoute.created_at.desc())
            .limit(100)
        )
    ]


@router.post("/routes", status_code=201)
def route_role(body: RouteInput, identity: FullIdentity, request: Request) -> dict[str, Any]:
    privileged(identity)
    for model_id in [body.model_id, *body.fallback_ids]:
        try:
            snapshot(identity.db, identity.user.id, model_id, configured(request))
        except ValueError as exc:
            raise HTTPException(409, "AI_MODEL_REQUIRES_VERIFICATION") from exc
    revision = (
        identity.db.scalar(
            select(func.max(AIRoute.revision)).where(
                AIRoute.owner_id == identity.user.id, AIRoute.role == body.role
            )
        )
        or 0
    ) + 1
    if revision > 100:
        raise HTTPException(429, "AI_ROUTE_VERSION_QUOTA")
    row = AIRoute(
        owner_id=identity.user.id,
        role=body.role,
        revision=revision,
        model_id=body.model_id,
        fallback_ids=[str(i) for i in body.fallback_ids],
    )
    identity.db.add(row)
    identity.db.flush()
    identity.audit(
        "ai.role_routed",
        entity_id=row.id,
        after={"role": row.role, "revision": revision, "model_id": str(row.model_id)},
    )
    return {"id": str(row.id), "revision": revision}


@router.post("/requests", response_model=AIJobView, status_code=202)
def submit(body: RequestInput, identity: FullIdentity, request: Request) -> AIJobView:
    privileged(identity)
    config = configured(request)
    # Idempotency is checked before re-reading mutable context; retries must not silently change it.
    previous = identity.db.scalar(
        select(AIRequest).where(AIRequest.owner_id == identity.user.id, AIRequest.key == body.key)
    )
    fingerprint = digest(body.model_dump(mode="json"))
    if previous:
        if previous.digest != fingerprint:
            raise HTTPException(409, "AI_IDEMPOTENCY_CONFLICT")
        return job_view(identity.db, previous, config)
    binding = identity.db.scalar(
        select(AIRoute)
        .where(AIRoute.owner_id == identity.user.id, AIRoute.role == body.role)
        .order_by(AIRoute.revision.desc())
        .limit(1)
    )
    if binding is None:
        raise HTTPException(409, "AI_ROLE_NOT_CONFIGURED")
    ids = [
        binding.model_id,
        *([UUID(i) for i in binding.fallback_ids] if body.allow_fallback else []),
    ]
    try:
        selected = [snapshot(identity.db, identity.user.id, model_id, config) for model_id in ids]
    except ValueError as exc:
        raise HTTPException(409, "AI_MODEL_REQUIRES_VERIFICATION") from exc
    if any(m.get("cloud") for m in selected) and len(selected) != 1:
        raise HTTPException(409, "AI_CLOUD_FALLBACK_PROHIBITED")
    context = assemble(ContextScope(identity.db, identity.user.id), body.references, config)
    for model in selected:
        policy = ConnectionInput.model_validate(model["profile"]).policy
        if model["remote"] and (
            not body.allow_remote
            or not policy.remote_processing
            or (
                any(r.kind not in {"strategy", "documentation"} for r in body.references)
                and not policy.account_context_remote
            )
        ):
            raise HTTPException(409, "AI_REMOTE_CONTEXT_POLICY_REFUSED")
        capabilities = model["capabilities"]
        if body.parameters.context_tokens > capabilities.get("context_tokens", 0):
            raise HTTPException(422, "AI_CONTEXT_BUDGET_UNVERIFIED")
        if (
            body.parameters.reasoning == "DISABLED"
            and capabilities.get("reasoning_controls") != "VERIFIED_DISABLED"
        ):
            raise HTTPException(422, "AI_REASONING_CONTROL_UNVERIFIED")
        if (
            body.parameters.seed is not None
            and capabilities.get("seed_control") != "VERIFIED_ACCEPTED"
        ):
            raise HTTPException(422, "AI_SEED_CONTROL_UNVERIFIED")
    try:
        prompt = messages(body.role, body.question, context)
    except ValueError as exc:
        raise HTTPException(422, "AI_SECRET_LIKE_INPUT_REFUSED") from exc
    # Bytes conservatively bound text tokens; reserve chat/template overhead. Not a tokenizer claim.
    if (
        len(canonical(prompt).encode()) + body.parameters.output_tokens + 512
        > body.parameters.context_tokens
    ):
        raise HTTPException(422, "AI_CONTEXT_BUDGET_EXCEEDED")
    spec = {
        "models": selected,
        "route_id": str(binding.id),
        "route_revision": binding.revision,
        "parameters": body.parameters.model_dump(mode="json"),
        "references": [r.model_dump() for r in body.references],
        "allowed_refs": [c["reference"] for c in context],
        "input_refs": [{"reference": c["reference"], "sha256": c["sha256"]} for c in context],
        "question_sha256": digest(body.question),
        "prompt_version": VERSION,
        "allow_fallback": body.allow_fallback,
        "allow_remote": body.allow_remote,
    }
    policies = [ConnectionInput.model_validate(m["profile"]).policy for m in selected]
    return enqueue(
        identity,
        request,
        key=body.key,
        kind="INFER",
        cloud_acknowledged=body.cloud_cost_acknowledged,
        role=body.role,
        fingerprint=fingerprint,
        spec=spec,
        content={"messages": prompt},
        processing_minutes=min(p.temporary_processing_minutes for p in policies),
        retention_hours=min(p.structured_retention_hours for p in policies),
    )


@router.get("/requests", response_model=list[AIJobView])
def requests(
    identity: FullIdentity, request: Request, offset: int = Query(0, ge=0, le=10000)
) -> list[AIJobView]:
    return [
        job_view(identity.db, row, configured(request))
        for row in identity.db.scalars(
            select(AIRequest)
            .where(AIRequest.owner_id == identity.user.id)
            .order_by(AIRequest.created_at.desc())
            .offset(offset)
            .limit(25)
        )
    ]


@router.get("/requests/{request_id}", response_model=AIJobView)
def get_request(request_id: UUID, identity: FullIdentity, request: Request) -> AIJobView:
    return job_view(identity.db, scoped(identity, AIRequest, request_id), configured(request))


@router.post("/requests/{request_id}/cancel", response_model=AIJobView, status_code=202)
def cancel(request_id: UUID, identity: FullIdentity, request: Request) -> AIJobView:
    require_owner(identity)
    row = scoped(identity, AIRequest, request_id)
    job = identity.db.get(AIJob, row.id, with_for_update=True)
    if job and job.state in {"QUEUED", "RUNNING", "RETRY"} and not job.cancel_requested:
        job.cancel_requested = True
        event(identity.db, job, "CANCELLATION_REQUESTED")
        identity.audit("ai.cancellation_requested", entity_id=row.id)
    return job_view(identity.db, row, configured(request))


@router.delete("/requests/{request_id}/content", status_code=204)
def erase_content(request_id: UUID, identity: FullIdentity) -> None:
    require_owner(identity)
    scoped(identity, AIRequest, request_id)
    job = identity.db.get(AIJob, request_id, with_for_update=True)
    if job and job.state in {"QUEUED", "RUNNING", "RETRY"}:
        job.cancel_requested = True
    content = identity.db.get(AIContent, request_id)
    if content:
        identity.db.delete(content)
    identity.audit("ai.content_erased", entity_id=request_id)


@router.get("/requests/{request_id}/events")
def events(
    request_id: UUID, identity: FullIdentity, request: Request, after: int = Query(0, ge=0)
) -> list[dict[str, Any]]:
    scoped(identity, AIRequest, request_id)
    return [
        {"sequence": e.sequence, "kind": e.kind, "details": e.details, "at": e.created_at}
        for e in identity.db.scalars(
            select(AIEvent)
            .where(AIEvent.request_id == request_id, AIEvent.sequence > after)
            .order_by(AIEvent.sequence)
            .limit(100)
        )
    ]


def stream_authorized(db: Session, owner: UUID, session_id: UUID) -> bool:
    session = db.get(LoginSession, session_id)
    user = db.get(User, owner)
    now = utcnow()
    return bool(
        user
        and user.active
        and session
        and session.user_id == owner
        and session.state == "FULL"
        and session.revoked_at is None
        and session.expires_at > now
        and session.idle_expires_at > now
    )


@router.get("/requests/{request_id}/stream")
def stream(request_id: UUID, identity: FullIdentity, request: Request) -> StreamingResponse:
    scoped(identity, AIRequest, request_id)
    owner, session_id, store = identity.user.id, identity.session.id, request.app.state.store
    config = configured(request)
    # Release FullIdentity's user lock BEFORE yielding; cancellation must stay reachable.
    identity.db.commit()

    def chunks() -> Iterator[str]:
        previous = ""
        began = time.monotonic()
        with store.engine.connect() as slot:
            acquired = slot.scalar(
                text("SELECT pg_try_advisory_lock(640063,:owner)"),
                {"owner": owner.int % 2147483647},
            )
            if not acquired:
                yield 'event: limit\ndata: {"code":"AI_STREAM_LIMIT"}\n\n'
                return
            try:
                while time.monotonic() - began < 30:
                    with store.session() as db:
                        if not stream_authorized(db, owner, session_id):
                            return
                        row = db.get(AIRequest, request_id)
                        job = db.get(AIJob, request_id)
                        content = db.get(AIContent, request_id)
                        if row is None or row.owner_id != owner or job is None:
                            return
                        if content and content.partial_ciphertext and row.expires_at > utcnow():
                            partial = (
                                config.cipher()
                                .decrypt(content.partial_ciphertext.encode())
                                .decode()
                            )
                            if partial != previous:
                                yield (
                                    "event: partial\ndata: "
                                    + json.dumps({"unvalidated": True, "text": partial})
                                    + "\n\n"
                                )
                                previous = partial
                        yield (
                            "event: state\ndata: "
                            + json.dumps(
                                {"state": job.state, "cancel_requested": job.cancel_requested}
                            )
                            + "\n\n"
                        )
                        if job.state not in {"QUEUED", "RUNNING", "RETRY"}:
                            return
                    time.sleep(0.25)
            finally:
                slot.execute(
                    text("SELECT pg_advisory_unlock(640063,:owner)"),
                    {"owner": owner.int % 2147483647},
                )

    return StreamingResponse(
        chunks(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@router.get("/requests/{request_id}/wait", response_model=AIJobView)
def wait(
    request_id: UUID,
    identity: FullIdentity,
    request: Request,
    seconds: int = Query(10, ge=0, le=15),
) -> AIJobView:
    scoped(identity, AIRequest, request_id)
    owner, session_id = identity.user.id, identity.session.id
    store: Store = request.app.state.store
    config = configured(request)
    identity.db.commit()
    deadline = time.monotonic() + seconds
    while True:
        with store.session() as db:
            if not stream_authorized(db, owner, session_id):
                raise HTTPException(401, "AI_SESSION_EXPIRED")
            row = db.get(AIRequest, request_id)
            if row is None or row.owner_id != owner:
                raise HTTPException(404, "AI_RECORD_NOT_FOUND")
            view = job_view(db, row, config)
        if view.state not in {"QUEUED", "RUNNING", "RETRY"} or time.monotonic() >= deadline:
            return view
        time.sleep(0.2)
