"""Inference-only worker with scoped SQL, bounded leases and ambiguous-completion fencing."""

import json
import time
from contextlib import suppress
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4

from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from packages.ai.contracts import OUTPUTS, Generation, ModelResponseMetadata, Provider
from packages.ai.lifecycle import CONTEXT_NAMESPACE, context_key, event
from packages.ai.models import AIArtifact, AIConnection, AIContent, AIJob, AIRequest, AIVerification
from packages.ai.prompts import VERSION, canonical, digest, validate_output
from packages.ai.providers import ProviderFailure, create_provider
from packages.ai.settings import GatewaySettings
from packages.persistence.models import utcnow
from packages.persistence.store import Store


class Cancelled(RuntimeError):
    pass


class Worker:
    def __init__(self, config: GatewaySettings):
        if not config.database_url or not config.redis_url:
            raise ValueError("AI_WORKER_CONFIGURATION_REQUIRED")
        self.config = config
        self.cipher = config.cipher()
        self.store = Store(config.database_url.get_secret_value())
        self.queue = Redis.from_url(
            config.redis_url.get_secret_value(), socket_connect_timeout=1, socket_timeout=1
        )
        with self.store.engine.connect() as db:
            unsafe = db.scalar(
                text(
                    "SELECT rolsuper OR rolcreaterole OR rolcreatedb "
                    "OR has_table_privilege(current_user,'users','SELECT') "
                    "OR has_table_privilege(current_user,'risk_profile_versions','SELECT') "
                    "OR has_table_privilege(current_user,'ai_connections','UPDATE') "
                    "FROM pg_roles WHERE rolname=current_user"
                )
            )
            if unsafe is not False:
                raise ValueError("AI_WORKER_REQUIRES_SCOPED_DATABASE_ROLE")

    def close(self) -> None:
        self.queue.close()
        self.store.engine.dispose()

    def once(self) -> bool:
        try:
            self.queue.set("ai:worker-heartbeat", str(time.time()), ex=20)
            self.queue.rpop("ai:jobs")
        except RedisError:
            pass  # Durable PostgreSQL claims do not depend on wakeup delivery.
        self.purge()
        with self.store.engine.connect() as slot:
            acquired = next(
                (
                    i
                    for i in range(self.config.global_concurrency)
                    if slot.scalar(text("SELECT pg_try_advisory_lock(640062,:slot)"), {"slot": i})
                ),
                None,
            )
            if acquired is None:
                return False
            try:
                return self.work()
            finally:
                slot.execute(text("SELECT pg_advisory_unlock(640062,:slot)"), {"slot": acquired})

    def purge(self) -> None:
        now = utcnow()
        with self.store.session() as db, db.begin():
            for request, content in db.execute(
                select(AIRequest, AIContent)
                .join(AIContent, AIContent.request_id == AIRequest.id)
                .where(or_(AIRequest.retain_until < now, AIRequest.expires_at < now))
                .limit(100)
            ):
                content.input_ciphertext = None
                content.partial_ciphertext = None
                if request.retain_until < now:
                    content.output_ciphertext = None

    @staticmethod
    def authorized(db: Session, request: AIRequest) -> bool:
        return (
            db.scalar(
                text("SELECT authorized FROM ai_request_authority WHERE request_id=:id"),
                {"id": request.id},
            )
            is True
        )

    @staticmethod
    def clear_input(db: Session, identifier: UUID) -> None:
        content = db.get(AIContent, identifier)
        if content:
            content.input_ciphertext = None
            content.partial_ciphertext = None

    def finish_failure(
        self,
        identifier: UUID,
        token: UUID,
        code: str,
        *,
        state: str = "FAILED",
        retry: bool = False,
    ) -> None:
        with self.store.session() as db, db.begin():
            job = db.get(AIJob, identifier, with_for_update=True)
            if job is None or job.worker_token != token or job.state != "RUNNING":
                return
            if job.cancel_requested:
                state, code, retry = "CANCELLED", "AI_CANCELLATION_CONFIRMED", False
            request = db.get(AIRequest, identifier)
            if request and request.specification.get("cloud"):
                retry = False
            if (
                retry
                and job.attempts < 3
                and request
                and request.expires_at > utcnow() + timedelta(seconds=5)
            ):
                job.state = "RETRY"
                job.lease_until = utcnow() + timedelta(seconds=2**job.attempts)
                job.dispatched_at = None  # Only a proven refused/unconnected attempt is retried.
                event(db, job, "RETRY_SCHEDULED", {"code": code})
                return
            job.state, job.error, job.completed_at = state, code, utcnow()
            job.lease_until = None
            self.clear_input(db, identifier)
            event(db, job, state, {"code": code})

    def work(self) -> bool:
        now = utcnow()
        with self.store.session() as db, db.begin():
            job = db.scalar(
                select(AIJob)
                .join(AIRequest, AIRequest.id == AIJob.request_id)
                .where(
                    AIJob.state.in_(["QUEUED", "RUNNING", "RETRY"]),
                    or_(AIJob.lease_until.is_(None), AIJob.lease_until < now),
                )
                .order_by(AIRequest.created_at)
                .with_for_update(of=AIJob, skip_locked=True)
                .limit(1)
            )
            if job is None:
                return False
            request = db.get(AIRequest, job.request_id)
            if request is None:
                raise ValueError("AI_REQUEST_MISSING")
            if (
                job.cancel_requested
                or request.expires_at <= now
                or not self.authorized(db, request)
            ):
                job.state = "CANCELLED" if job.cancel_requested else "FAILED"
                job.error = "AI_CANCELLED" if job.cancel_requested else "AI_AUTHORIZATION_EXPIRED"
                job.completed_at = now
                self.clear_input(db, job.request_id)
                event(db, job, job.state, {"code": job.error})
                return True
            if job.state == "RUNNING" and job.dispatched_at is not None:
                job.worker_token = uuid4()  # Fence late completion from the lost process.
                job.state, job.error, job.completed_at = (
                    "UNKNOWN",
                    "AI_WORKER_LOST_AFTER_DISPATCH",
                    now,
                )
                self.clear_input(db, job.request_id)
                event(db, job, "UNKNOWN", {"code": job.error})
                return True
            if job.attempts >= 3:
                job.state, job.error, job.completed_at = "FAILED", "AI_RETRY_LIMIT", now
                self.clear_input(db, job.request_id)
                event(db, job, "FAILED", {"code": job.error})
                return True
            token = uuid4()
            job.worker_token, job.lease_until = token, now + timedelta(seconds=40)
            job.state, job.started_at = "RUNNING", now
            job.attempts += 1
            event(db, job, "PROCESSING", {"attempt": job.attempts})
            identifier, owner, attempt = job.request_id, request.owner_id, job.attempts
            spec, kind, role, started = request.specification, request.kind, request.role, now

        with self.store.engine.connect() as context_slot:
            locked = context_slot.scalar(
                text("SELECT pg_try_advisory_lock_shared(:namespace,:owner)"),
                {"namespace": CONTEXT_NAMESPACE, "owner": context_key(owner)},
            )
            if not locked:
                self.finish_failure(identifier, token, "AI_CONTEXT_BUSY", retry=True)
                return True
            try:
                self.execute(identifier, token, spec, kind, role, attempt, started)
            except Cancelled:
                self.finish_failure(identifier, token, "AI_CANCELLED_OR_REVOKED", state="CANCELLED")
            except ProviderFailure as exc:
                self.finish_failure(
                    identifier,
                    token,
                    exc.code,
                    state="UNKNOWN" if exc.ambiguous else "FAILED",
                    retry=exc.retryable,
                )
            except ValueError as exc:
                code = str(exc)
                # Only our bounded constant codes are retained, never provider data or exceptions.
                safe = (
                    code
                    if code.startswith("AI_")
                    and len(code) <= 80
                    and all(c.isupper() or c.isdigit() or c == "_" for c in code)
                    else "AI_VALIDATION_FAILED"
                )
                self.finish_failure(identifier, token, safe)
            except Exception:
                self.finish_failure(identifier, token, "AI_WORKER_FAILED")
            finally:
                context_slot.execute(
                    text("SELECT pg_advisory_unlock_shared(:namespace,:owner)"),
                    {"namespace": CONTEXT_NAMESPACE, "owner": context_key(owner)},
                )
        return True

    def execute(
        self,
        identifier: UUID,
        token: UUID,
        spec: dict[str, Any],
        kind: str,
        role: str,
        attempt: int,
        started: datetime,
    ) -> None:
        models = spec.get("models", [])
        selected = models[min(attempt - 1, len(models) - 1)] if models else spec
        endpoint = self.config.endpoint(selected["endpoint_id"])
        if digest(endpoint.model_dump(mode="json")) != selected["endpoint_digest"]:
            raise ValueError("AI_ENDPOINT_VERSION_CHANGED")
        connection_id = UUID(selected["connection_id"])
        begun = time.monotonic()
        last_update = 0.0

        def heartbeat(partial: str = "", *, dispatched: bool = False, force: bool = False) -> None:
            nonlocal last_update
            current_time = time.monotonic()
            if current_time - last_update < 0.25 and not force and not dispatched:
                return
            with self.store.session() as db, db.begin():
                job = db.get(AIJob, identifier, with_for_update=True)
                request = db.get(AIRequest, identifier)
                connection = db.get(AIConnection, connection_id)
                if (
                    job is None
                    or request is None
                    or job.worker_token != token
                    or job.state != "RUNNING"
                    or job.cancel_requested
                    or request.expires_at <= utcnow()
                    or not self.authorized(db, request)
                    or connection is None
                    or not connection.enabled
                    or connection.owner_id != request.owner_id
                ):
                    raise Cancelled()
                if selected.get("cloud"):
                    from packages.ai.cloud import unchanged
                    from packages.ai.models import AICloudReservation

                    if (
                        not self.config.openrouter_enabled
                        or not unchanged(db, request.owner_id, connection_id, selected["cloud"])
                        or db.get(AICloudReservation, identifier) is None
                    ):
                        raise Cancelled()
                if current_time - begun > spec.get("parameters", {}).get("max_seconds", 180):
                    raise ProviderFailure(
                        "AI_DEADLINE_EXCEEDED", ambiguous=job.dispatched_at is not None
                    )
                if job.lease_until is None or job.lease_until < utcnow():
                    raise Cancelled()
                job.lease_until = utcnow() + timedelta(seconds=40)
                if dispatched:
                    job.dispatched_at = utcnow()
                    event(db, job, "DISPATCHED", {"model_id": selected.get("model_id")})
                content = db.get(AIContent, identifier)
                if content is None or content.input_ciphertext is None:
                    raise Cancelled()
                if partial.lstrip().startswith("{"):
                    content.partial_ciphertext = self.cipher.encrypt(partial.encode()).decode()
            last_update = current_time
            with suppress(RedisError):
                self.queue.set("ai:worker-heartbeat", str(time.time()), ex=20)

        heartbeat(force=True)
        with self.store.session() as db:
            content = db.get(AIContent, identifier)
            if content is None or content.input_ciphertext is None:
                raise Cancelled()
            payload = json.loads(self.cipher.decrypt(content.input_ciphertext.encode()))
            if digest(payload) != spec["input_digest"]:
                raise ValueError("AI_INPUT_INTEGRITY_FAILED")
        cloud_options: dict[str, Any] = {}
        if selected.get("cloud"):
            from packages.ai.cloud_contracts import CloudPolicy
            from packages.ai.models import AIConnectionSecret

            with self.store.session() as db:
                secret = db.get(AIConnectionSecret, connection_id)
                origin = db.get(AIRequest, identifier)
                if secret is None or origin is None or secret.owner_id != origin.owner_id:
                    raise ValueError("AI_CREDENTIAL_REQUIRED")
                cloud_options = {
                    "bearer_token": self.cipher.decrypt(secret.ciphertext.encode()).decode(),
                    "cloud_policy": CloudPolicy.model_validate(selected["cloud"]["policy"]),
                }
        adapter = create_provider(
            endpoint,
            cast(Provider, selected["provider"]),
            proxy=self.config.egress_proxy,
            secret_root=self.config.secret_root,
            **cloud_options,
        )
        try:
            if kind == "DISCOVER":
                heartbeat(dispatched=True)
                output: Any = {"models": adapter.discover(), "gpu_availability": "UNKNOWN"}
                if selected["provider"] == "OPENROUTER":
                    output.update(catalog_limit=100, catalog_complete=False)
                metadata: dict[str, Any] = {
                    "kind": kind,
                    "endpoint_id": selected["endpoint_id"],
                    "provider": selected["provider"],
                    "gpu_availability": "UNKNOWN",
                }
            elif kind == "PROBE":
                heartbeat(dispatched=True)
                output = adapter.probe(
                    selected["model_name"], selected["context_ceiling"], progress=heartbeat
                )
                if selected.get("cloud"):
                    output["cloud"] = selected["cloud"]
                metadata = {
                    "kind": kind,
                    "model_id": selected["model_id"],
                    "provider": selected["provider"],
                }
            else:
                parameters = Generation.model_validate(spec["parameters"])
                if spec["prompt_version"] != VERSION:
                    raise ValueError("AI_PROMPT_VERSION_CHANGED")
                if selected["remote"] and (
                    not spec.get("allow_remote")
                    or not selected["profile"]["policy"]["remote_processing"]
                ):
                    raise ValueError("AI_REMOTE_POLICY_REFUSED")
                verified_until = datetime.fromisoformat(selected["verification_expires_at"])
                if verified_until <= utcnow():
                    raise ValueError("AI_MODEL_VERIFICATION_EXPIRED")
                identity = adapter.identity(selected["model_name"])
                expected_digest = selected["capabilities"].get("model_digest")
                if expected_digest is not None and identity.get("digest") != expected_digest:
                    raise ValueError("AI_MODEL_VERSION_CHANGED")
                body = adapter.body(
                    selected["model_name"],
                    payload["messages"],
                    OUTPUTS[role].model_json_schema(),
                    parameters,
                )
                heartbeat(dispatched=True)
                completed = adapter.complete(
                    body,
                    max_bytes=self.config.max_output_bytes,
                    max_seconds=parameters.max_seconds,
                    progress=heartbeat,
                )
                if (
                    completed.output_tokens is not None
                    and completed.output_tokens > parameters.output_tokens
                ):
                    raise ValueError("AI_PROVIDER_OUTPUT_TOKEN_LIMIT")
                output = validate_output(
                    role, completed.content, set(spec["allowed_refs"])
                ).model_dump(mode="json")
                cost = None
                if (
                    endpoint.cost_per_million_input is not None
                    and endpoint.cost_per_million_output is not None
                    and completed.input_tokens is not None
                    and completed.output_tokens is not None
                ):
                    cost = (
                        Decimal(endpoint.cost_per_million_input) * completed.input_tokens
                        + Decimal(endpoint.cost_per_million_output) * completed.output_tokens
                    ) / Decimal(1000000)
                metadata = ModelResponseMetadata(
                    request_id=identifier,
                    model_id=UUID(selected["model_id"]),
                    provider=cast(Provider, selected["provider"]),
                    model_name=selected["model_name"],
                    model_digest=identity.get("digest"),
                    provider_version=selected["capabilities"].get("provider_version"),
                    quantization=selected["capabilities"].get("quantization"),
                    prompt_version=VERSION,
                    input_refs=spec["input_refs"],
                    parameters=parameters,
                    started_at=started,
                    completed_at=utcnow(),
                    latency_ms=round((time.monotonic() - begun) * 1000),
                    input_tokens=completed.input_tokens,
                    output_tokens=completed.output_tokens,
                    configured_cost_estimate=cost,
                    usage_source="PROVIDER_REPORTED"
                    if completed.input_tokens is not None or completed.output_tokens is not None
                    else "UNKNOWN",
                    output_sha256=digest(output),
                ).model_dump(mode="json")
            if len(canonical(output).encode()) > self.config.max_output_bytes:
                raise ValueError("AI_OUTPUT_BYTE_LIMIT")
            heartbeat(force=True)
            with self.store.session() as db, db.begin():
                job = db.get(AIJob, identifier, with_for_update=True)
                request = db.get(AIRequest, identifier)
                content = db.get(AIContent, identifier)
                if (
                    job is None
                    or request is None
                    or job.worker_token != token
                    or job.state != "RUNNING"
                    or job.cancel_requested
                    or not self.authorized(db, request)
                    or request.expires_at <= utcnow()
                    or request.retain_until <= utcnow()
                    or content is None
                ):
                    raise Cancelled()
                if db.get(AIArtifact, identifier):
                    raise ValueError("AI_FINAL_ARTIFACT_ALREADY_EXISTS")
                db.add(
                    AIArtifact(
                        request_id=identifier, digest=digest(output), artifact_metadata=metadata
                    )
                )
                if kind == "PROBE":
                    db.add(
                        AIVerification(
                            model_id=UUID(selected["model_id"]),
                            request_id=identifier,
                            capabilities=output,
                            expires_at=utcnow() + timedelta(hours=24),
                        )
                    )
                content.output_ciphertext = self.cipher.encrypt(canonical(output).encode()).decode()
                content.input_ciphertext = None
                content.partial_ciphertext = None
                job.state, job.completed_at, job.lease_until = "SUCCEEDED", utcnow(), None
                event(db, job, "COMPLETED", {"artifact_sha256": digest(output)})
        finally:
            adapter.close()
