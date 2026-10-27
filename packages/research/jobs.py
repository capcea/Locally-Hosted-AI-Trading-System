"""Durable bounded research jobs; PG leases/slots/fencing, immutable MinIO publication."""

import json
import platform
import time
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import or_, select, text

from apps.api.config import Settings
from packages.execution.journal import digest
from packages.market.storage import ObjectStore
from packages.persistence.audit import append_event
from packages.persistence.models import TradingAccount, User, utcnow
from packages.persistence.store import Store
from packages.research.contracts import ExperimentInput
from packages.research.data import pinned
from packages.research.engine import event_trial
from packages.research.models import ResearchJob, ResearchResult, ResearchRun
from packages.research.screening import screen
from packages.research.strategies import definition


class Cancelled(RuntimeError):
    pass


class Worker:
    def __init__(self, config: Settings):
        if not config.database_url or not config.auth_encryption_key:
            raise RuntimeError("Restricted research worker configuration required")
        self.db = Store(config.database_url.get_secret_value())
        self.objects = ObjectStore(config)
        self.key = config.auth_encryption_key.get_secret_value()

    def close(self) -> None:
        self.db.engine.dispose()

    def once(self) -> bool:
        with self.db.engine.connect() as slot:
            acquired = None
            for i in range(2):
                if slot.scalar(text("SELECT pg_try_advisory_lock(58391,:slot)"), {"slot": i}):
                    acquired = i
                    break
            if acquired is None:
                return False
            try:
                return self.work()
            finally:
                slot.execute(text("SELECT pg_advisory_unlock(58391,:slot)"), {"slot": acquired})

    def work(self) -> bool:
        now = utcnow()
        with self.db.session() as db, db.begin():
            job = db.scalar(
                select(ResearchJob)
                .where(
                    ResearchJob.state.in_(["QUEUED", "RUNNING", "RETRY"]),
                    or_(ResearchJob.lease_until.is_(None), ResearchJob.lease_until < now),
                )
                .order_by(ResearchJob.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if job is None:
                return False
            if job.cancel_requested:
                job.state = "CANCELLED"
                return True
            if job.attempts >= 3:
                job.state = "FAILED"
                job.error = "RETRY_LIMIT_EXHAUSTED"
                return True
            token = uuid4()
            job.worker_token = token
            job.lease_until = now + timedelta(seconds=30)
            job.attempts += 1
            job.state = "RUNNING"
            run_id, job_id, attempt = job.run_id, job.id, job.attempts
        began = time.monotonic()

        def heartbeat(progress: int) -> None:
            with self.db.session() as db, db.begin():
                current = db.get(ResearchJob, job_id, with_for_update=True)
                if current is None or current.worker_token != token or current.cancel_requested:
                    raise Cancelled("CANCELLED_OR_FENCED")
                if time.monotonic() - began > plan.max_seconds:
                    raise ValueError("RESEARCH_TIME_QUOTA_EXCEEDED")
                research_scope = db.get(ResearchRun, run_id)
                if research_scope is None:
                    raise ValueError("RESEARCH_PLAN_MISSING")
                from packages.research.approval import assert_current

                assert_current(db, research_scope, plan)
                current.progress = max(current.progress, progress)
                current.lease_until = utcnow() + timedelta(seconds=30)

        try:
            with self.db.session() as db:
                research = db.get(ResearchRun, run_id)
                if research is None:
                    raise ValueError("RESEARCH_PLAN_MISSING")
                plan = ExperimentInput.model_validate(research.plan)
                if definition(plan.strategy)["digest"] != plan.strategy_digest:
                    raise ValueError("TRUSTED_STRATEGY_VERSION_CHANGED")
                owner = db.get(User, research.owner_id)
                account = db.get(TradingAccount, plan.source_account_id)
                if (
                    owner is None
                    or not owner.active
                    or owner.role != "OWNER"
                    or account is None
                    or account.archived
                ):
                    raise ValueError("AUTHORIZATION_REVOKED")
                from packages.research.approval import assert_current

                assert_current(db, research, plan)
                datasets = pinned(db, plan, research.owner_id, self.objects)
                heartbeat(1)
                if plan.engine == "SCREEN":
                    result = screen(plan, datasets, heartbeat)
                elif plan.validation_mode == "WALK_FORWARD":
                    from packages.research.walk_forward import evaluate

                    result = evaluate(db, research, plan, datasets, attempt, self.key, heartbeat)
                else:
                    trials = []
                    ordinal = 0
                    for parameters in plan.parameters:
                        for stress in plan.cost_multipliers:
                            trials.append(
                                event_trial(
                                    db,
                                    research,
                                    plan,
                                    datasets,
                                    parameters,
                                    stress,
                                    attempt,
                                    ordinal,
                                    self.key,
                                    heartbeat,
                                )
                            )
                            ordinal += 1
                    result = {
                        "engine": "EVENT_JOURNAL_RISK_GATEWAY",
                        "trials": trials,
                        "source": "SIMULATED",
                        "paper_eligible": False,
                    }
                result.update(
                    {
                        "protocol": plan.chronology.model_dump(mode="json"),
                        "phase": plan.phase,
                        "strategy": definition(plan.strategy),
                        "datasets": [
                            {
                                "id": d["dataset_id"],
                                "manifest_sha256": d["pin"].manifest_sha256,
                                "version": d["manifest"]["version"],
                                "provenance": d["provenance"],
                                "coverage_pct": d["coverage"],
                            }
                            for d in datasets
                        ],
                        "runtime": {
                            "python": platform.python_version(),
                            "software": research.approval_snapshot["software"],
                            "implementation": "research-v1",
                        },
                        "seed": plan.seed,
                        "warnings": [
                            "Research only; no execution or promotion authorization.",
                            "Prior final-holdout exposure is not certified untouched.",
                        ],
                    }
                )
                # Operational journal IDs legitimately differ across attempts;
                # financial equivalence excludes them.
                semantic = {
                    "software": research.approval_snapshot["software"],
                    "strategy_digest": plan.strategy_digest,
                    "datasets": [p.manifest_sha256 for p in plan.datasets],
                    "phase": plan.phase,
                    "trials": [
                        {
                            k: t[k]
                            for k in (
                                "parameters",
                                "cost_multiplier",
                                "metrics",
                                "equity",
                                "trades",
                                "approximate_net",
                            )
                            if k in t
                        }
                        for t in result["trials"]
                    ],
                }
                semantic_hash = digest(semantic)
                db.commit()
            heartbeat(98)
            content = json.dumps(
                result, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
            if len(content) > 16 * 1024 * 1024:
                raise ValueError("RESULT_STORAGE_QUOTA_EXCEEDED")
            artifact = self.objects.put(
                f"research/{run_id}/attempt-{attempt}/{semantic_hash}.json", content
            )
            with self.db.session() as db, db.begin():
                research = db.get(ResearchRun, run_id)
                if research is None:
                    raise ValueError("RESEARCH_PLAN_MISSING")
                owner = db.get(User, research.owner_id, with_for_update=True)
                current = db.get(ResearchJob, job_id, with_for_update=True)
                if (
                    research is None
                    or current is None
                    or current.worker_token != token
                    or current.cancel_requested
                ):
                    raise Cancelled("CANCELLED_BEFORE_PUBLICATION")
                assert_current(db, research, plan)
                pinned(db, plan, research.owner_id, self.objects, read=False)
                owner = db.get(User, research.owner_id, with_for_update=True)
                if owner is None or not owner.active or owner.role != "OWNER":
                    raise ValueError("AUTHORIZATION_REVOKED")
                summary = {
                    "engine": result["engine"],
                    "trial_count": len(result["trials"]),
                    "source": "SIMULATED",
                    "paper_eligible": False,
                    "semantic_digest": semantic_hash,
                }
                db.add(
                    ResearchResult(
                        run_id=run_id,
                        owner_id=research.owner_id,
                        artifact=artifact,
                        semantic_digest=semantic_hash,
                        summary=summary,
                    )
                )
                current.state = "SUCCEEDED"
                current.progress = 100
                current.lease_until = None
                append_event(
                    db,
                    self.key,
                    "research.result_published",
                    entity_id=run_id,
                    after={**summary, "artifact": artifact},
                )
        except (Cancelled, ValueError, ArithmeticError, TimeoutError) as error:
            with self.db.session() as db, db.begin():
                current = db.get(ResearchJob, job_id, with_for_update=True)
                if current and current.worker_token == token:
                    current.state = "CANCELLED" if isinstance(error, Cancelled) else "FAILED"
                    current.error = str(error)[:100]
                    current.lease_until = None
                    append_event(
                        db,
                        self.key,
                        "research.job_stopped",
                        entity_id=run_id,
                        after={"state": current.state, "error": current.error},
                    )
        except Exception:
            # Preserve failure status without leaking storage/DSN details; retry
            # only recoverable crashes.
            with self.db.session() as db, db.begin():
                current = db.get(ResearchJob, job_id, with_for_update=True)
                if current and current.worker_token == token:
                    current.state = "FAILED"
                    current.error = "RESEARCH_DEPENDENCY_OR_INTERNAL_FAILURE"
                    current.lease_until = None
            raise
        return True
