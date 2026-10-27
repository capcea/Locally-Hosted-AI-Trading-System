"""Durable PG outbox/leases with Redis hints, bounded slots and fenced publication."""

import hashlib
from datetime import timedelta
from uuid import UUID, uuid4

from redis import Redis
from sqlalchemy import or_, select, text

from apps.api.config import Settings
from packages.market.contracts import ImportSpec
from packages.market.models import IngestionJob, MarketDataset, MarketProvider
from packages.market.processing import manifest_bytes, process
from packages.market.providers import ProviderFailure, adapter_for, polite_pause, retry_delay
from packages.market.storage import ObjectStore
from packages.persistence.audit import append_event
from packages.persistence.models import TradingAccount, User, utcnow
from packages.persistence.store import Store

QUEUE = "market:ingestion:v1"


def enqueue(config: Settings, job_id: UUID) -> None:
    if config.redis_url:
        try:
            with (
                Redis.from_url(
                    config.redis_url.get_secret_value(), socket_timeout=2, socket_connect_timeout=2
                ) as client,
                client.pipeline() as pipe,
            ):
                pipe.rpush(QUEUE, str(job_id))
                pipe.ltrim(QUEUE, -10000, -1)
                pipe.execute()
        except (OSError, ConnectionError):
            pass
        except Exception as error:
            # Redis is a wakeup hint. PostgreSQL is the durable outbox and recovery source of truth.
            from redis.exceptions import RedisError

            if not isinstance(error, RedisError):
                raise


class Cancelled(RuntimeError):
    pass


class Worker:
    def __init__(self, config: Settings):
        if not config.database_url or not config.auth_encryption_key:
            raise RuntimeError("Persistent data worker configuration is missing")
        self.config = config
        self.db = Store(config.database_url.get_secret_value())
        self.objects = ObjectStore(config)
        self.key = config.auth_encryption_key.get_secret_value()

    def once(self) -> bool:
        # Independent data worker, not the prohibited experimental-code runner.
        with self.db.engine.connect() as slot:
            acquired = None
            for number in range(2):
                if slot.scalar(text("SELECT pg_try_advisory_lock(38291,:slot)"), {"slot": number}):
                    acquired = number
                    break
            if acquired is None:
                return False
            try:
                return self._claim_and_run()
            finally:
                slot.execute(text("SELECT pg_advisory_unlock(38291,:slot)"), {"slot": acquired})

    def _claim_and_run(self) -> bool:
        now = utcnow()
        if self.config.redis_url:
            from redis.exceptions import RedisError

            try:
                with Redis.from_url(
                    self.config.redis_url.get_secret_value(),
                    socket_timeout=2,
                    socket_connect_timeout=2,
                ) as redis:
                    redis.lpop(QUEUE)
            except RedisError:
                pass
        with self.db.session() as db, db.begin():
            job = db.scalar(
                select(IngestionJob)
                .where(
                    IngestionJob.state.in_(["QUEUED", "RETRY", "RUNNING"]),
                    IngestionJob.next_attempt_at <= now,
                    or_(IngestionJob.lease_until.is_(None), IngestionJob.lease_until < now),
                )
                .order_by(IngestionJob.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if job is None:
                return False
            token = uuid4()
            job.state, job.worker_token, job.lease_until = (
                "RUNNING",
                token,
                now + timedelta(seconds=90),
            )
            job.attempts += 1
            job_id, dataset_id = job.id, job.dataset_id
            dataset = db.get(MarketDataset, dataset_id)
            if dataset is None:
                raise RuntimeError("Dataset registry invariant failed")
            dataset.status = "VALIDATING"
            spec = ImportSpec.model_validate(dataset.spec)
            provider = db.get(MarketProvider, dataset.provider_id)
            if provider is None:
                raise RuntimeError("Provider invariant failed")
            adapter, symbol = provider.adapter, dataset.symbol
            input_artifact = {
                "key": dataset.input_key,
                "version": dataset.input_version,
                "sha256": dataset.input_sha256,
                "bytes": dataset.input_size,
            }
            prefix = (
                f"providers/{provider.id}/instruments/{dataset.instrument_id}/"
                f"{spec.data_type}/{dataset.id}/attempt-{job.attempts}"
            )
            observed = dataset.downloaded_at or dataset.created_at
            previous = db.scalar(
                select(MarketDataset)
                .where(
                    MarketDataset.series_key == dataset.series_key,
                    MarketDataset.version < dataset.version,
                )
                .order_by(MarketDataset.version.desc())
                .limit(1)
            )
            prior_hash = previous.input_sha256 if previous else None
            revision_warning = (
                previous is not None
                and previous.input_sha256 != dataset.input_sha256
                and not spec.transformation_reason
            )

        def heartbeat(progress: int) -> None:
            with self.db.session() as db, db.begin():
                current = db.scalar(
                    select(IngestionJob).where(IngestionJob.id == job_id).with_for_update()
                )
                if current is None or current.worker_token != token or current.cancel_requested:
                    raise Cancelled("Cancelled or lease superseded")
                current.progress_rows = progress
                current.lease_until = utcnow() + timedelta(seconds=90)

        try:
            heartbeat(0)
            content = self.objects.get(input_artifact)
            if adapter_for(adapter).network and not content:
                polite_pause()
                content = adapter_for(adapter).download(spec, symbol)
                observed = utcnow()
                artifact = self.objects.put(f"{prefix}/provider-response.csv", content)
                # Pin response before parsing so retries reproduce the same bytes.
                with self.db.session() as db, db.begin():
                    current = db.get(IngestionJob, job_id, with_for_update=True)
                    if current is None or current.worker_token != token or current.cancel_requested:
                        raise Cancelled("Lease changed")
                    current_data = db.get(MarketDataset, dataset_id)
                    if current_data is None:
                        raise RuntimeError("Dataset missing")
                    current_data.input_key = str(artifact["key"])
                    current_data.input_version = str(artifact["version"])
                    current_data.input_sha256 = hashlib.sha256(content).hexdigest()
                    current_data.input_size = len(content)
                    current_data.downloaded_at = observed
                    input_artifact = artifact
            revision_warning = (
                prior_hash is not None
                and prior_hash != hashlib.sha256(content).hexdigest()
                and not spec.transformation_reason
            )
            outcome = process(
                content,
                spec,
                adapter,
                self.objects,
                prefix,
                observed,
                self.config.market_max_rows,
                heartbeat,
                revision_warning,
            )
            with self.db.session() as db, db.begin():
                # Current authorization is checked again before publication.
                data = db.get(MarketDataset, dataset_id)
                if data is None:
                    raise RuntimeError("Dataset missing")
                owner = db.get(User, data.owner_id, with_for_update=True)
                account = db.get(TradingAccount, data.account_id, with_for_update=True)
                current = db.get(IngestionJob, job_id, with_for_update=True)
                if current is None or current.worker_token != token or current.cancel_requested:
                    raise Cancelled("Lease changed before commit")
                if (
                    owner is None
                    or not owner.active
                    or owner.role not in {"OWNER", "OPERATOR"}
                    or account is None
                    or account.archived
                ):
                    raise ProviderFailure("AUTHORIZATION_REVOKED")
                manifest = {
                    "schema_version": 1,
                    "dataset_id": str(data.id),
                    "version": data.version,
                    "owner_id": str(data.owner_id),
                    "account_id": str(data.account_id),
                    "spec": data.spec,
                    "input": input_artifact,
                    "artifacts": outcome["artifacts"],
                    "quality": outcome["quality"],
                    "ingested_at": utcnow().isoformat(),
                    "downloaded_at": observed.isoformat() if adapter_for(adapter).network else None,
                    "provider": {
                        "id": str(provider.id),
                        "name": provider.name,
                        "adapter": adapter,
                        "rights_reference": provider.rights_reference,
                        "attribution": provider.attribution,
                    },
                    "transformations": [
                        "UTC normalization; original timestamp/zone retained",
                        "spread = ask - bid only when both quotes supplied",
                    ]
                    + ([spec.transformation_reason] if spec.transform_timeframe else []),
                    "source_revision_warning": revision_warning,
                }
                info = self.objects.put(f"{prefix}/manifest.json", manifest_bytes(manifest))
                quality = outcome["quality"]
                data.status = quality["status"]
                data.quality = quality
                data.coverage_pct = quality["coverage_pct"]
                data.record_count = quality["record_count"]
                data.artifacts = outcome["artifacts"]
                data.earliest, data.latest = outcome["earliest"], outcome["latest"]
                data.manifest_key, data.manifest_version, data.manifest_sha256 = (
                    str(info["key"]),
                    str(info["version"]),
                    str(info["sha256"]),
                )
                data.published_at = utcnow()
                current.state, current.error_code, current.lease_until = "SUCCEEDED", None, None
                append_event(
                    db,
                    self.key,
                    "market.dataset_published",
                    actor=owner,
                    mfa=False,
                    entity_id=data.id,
                    after={
                        "status": data.status,
                        "manifest_sha256": data.manifest_sha256,
                        "records": data.record_count,
                    },
                )
        except Cancelled:
            self._failure(job_id, token, "CANCELLED", cancel=True)
        except ProviderFailure as error:
            self._failure(job_id, token, error.code, delay=error.delay)
        except (ValueError, UnicodeError, ArithmeticError):
            self._failure(job_id, token, "INVALID_INPUT", permanent=True)
        except Exception:
            # No exception/raw payload/credential logging. Durable bounded code for owner review.
            self._failure(job_id, token, "SERVICE_OR_STORAGE_FAILURE")
        return True

    def _failure(
        self,
        job_id: UUID,
        token: UUID,
        code: str,
        *,
        delay: int = 0,
        permanent: bool = False,
        cancel: bool = False,
    ) -> None:
        with self.db.session() as db, db.begin():
            job = db.get(IngestionJob, job_id, with_for_update=True)
            if job is None or job.worker_token != token:
                return
            job.error_code, job.lease_until = code, None
            job.state = (
                "CANCELLED"
                if cancel or job.cancel_requested
                else "FAILED"
                if permanent or job.attempts >= 3
                else "RETRY"
            )
            job.next_attempt_at = utcnow() + timedelta(seconds=retry_delay(job.attempts, delay))
            dataset = db.get(MarketDataset, job.dataset_id)
            if dataset and dataset.published_at is None:
                dataset.status = "REJECTED" if job.state in {"FAILED", "CANCELLED"} else "PENDING"
                dataset.quality = {"status": dataset.status, "error_code": code}
            actor = db.get(User, job.owner_id)
            append_event(
                db,
                self.key,
                "market.job_" + job.state.lower(),
                actor=actor,
                entity_id=job.id,
                after={"error_code": code, "attempt": job.attempts},
            )

    def close(self) -> None:
        self.db.engine.dispose()
