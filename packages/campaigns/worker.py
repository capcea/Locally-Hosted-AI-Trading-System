"""Fixed control-plane metadata worker. Never submits experiments or impersonates owners."""

import json
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import or_, select, text

from apps.api.config import Settings
from packages.ai.models import AIJob
from packages.campaigns.contracts import (
    Critique,
    ExperimentEvidence,
    FollowUpProposal,
    ParameterCandidate,
)
from packages.campaigns.evaluation import evaluate
from packages.campaigns.models import CampaignExperiment, CampaignRuntime, ResearchCampaign
from packages.campaigns.service import (
    RESULT_RESERVATION,
    current,
    fixture_proposal,
    latest,
    objective,
    plan_candidate,
    record,
    transition,
)
from packages.market.storage import ObjectStore
from packages.persistence.audit import append_event
from packages.persistence.models import User, utcnow
from packages.persistence.store import Store
from packages.research.models import ResearchJob, ResearchResult, ResearchTrial


def finish_critique(
    db: Any, campaign: ResearchCampaign, runtime: CampaignRuntime, critique: Critique
) -> None:
    decision = latest(db, campaign.id, "EVALUATION")
    plan = latest(db, campaign.id, "PLAN")
    if decision is None or plan is None:
        raise ValueError("EVALUATION_LINEAGE_MISSING")
    c = record(db, campaign, runtime, "CRITIQUE", critique.model_dump(mode="json"), decision.id)
    spec = objective(campaign)
    untried = len(spec.search_space) > runtime.iteration
    permitted = (
        decision.payload["decision"] == "NEEDS_MORE_VALIDATION"
        and spec.template.phase == "DISCOVERY"
        and untried
        and runtime.iteration < spec.budgets.iterations
        and runtime.proposals < spec.budgets.candidate_proposals
        and runtime.experiments < spec.budgets.experiments
        and runtime.reserved_seconds + 3 * spec.template.max_seconds <= spec.budgets.runtime_seconds
        and runtime.reserved_bytes + RESULT_RESERVATION + spec.budgets.lineage_bytes + 8192
        <= spec.budgets.artifact_bytes
    )
    next_candidate = (
        ParameterCandidate(
            strategy=spec.template.strategy,
            strategy_digest=spec.template.strategy_digest,
            parameters=spec.search_space[(spec.seed + runtime.iteration) % len(spec.search_space)],
            source=spec.mode,
        )
        if permitted and spec.mode == "SYNTHETIC_FIXTURE"
        else None
    )
    feedback = FollowUpProposal(
        tested_plan=plan.id,
        evaluation=decision.id,
        critique=c.id,
        justified=permitted,
        allowed_next_candidate=next_candidate,
        source=spec.mode,
        reason="Bounded training-only follow-up; repeated training is not independent OOS."
        if permitted
        else "Stop: evidence, frozen evaluation or authorized budget disallows follow-up.",
    )
    record(db, campaign, runtime, "FEEDBACK", feedback.model_dump(mode="json"), c.id)
    if decision.payload["decision"] == "INSUFFICIENT_EVIDENCE":
        runtime.active = False
        transition(db, campaign, runtime, "STOPPED", "INSUFFICIENT_EVIDENCE")
    elif permitted:
        transition(db, campaign, runtime, "READY_FOR_NEXT_ITERATION")
    else:
        runtime.active = False
        transition(db, campaign, runtime, "COMPLETED", "RESEARCH_ONLY_NO_PROMOTION")


class Worker:
    def __init__(self, config: Settings):
        if not config.database_url or not config.auth_encryption_key:
            raise RuntimeError("Campaign control-plane configuration required")
        self.config = config
        self.db = Store(config.database_url.get_secret_value())
        self.objects = ObjectStore(config)
        self.key = config.auth_encryption_key.get_secret_value()

    def close(self) -> None:
        self.db.engine.dispose()

    def once(self) -> bool:
        with self.db.engine.connect() as slot:
            acquired = None
            for i in range(self.config.campaign_global_concurrency):
                if slot.scalar(text("SELECT pg_try_advisory_lock(70702,:slot)"), {"slot": i}):
                    acquired = i
                    break
            if acquired is None:
                return False
            try:
                return self.claim()
            finally:
                slot.execute(text("SELECT pg_advisory_unlock(70702,:slot)"), {"slot": acquired})

    def claim(self) -> bool:
        with self.db.session() as db, db.begin():
            runtime = db.scalar(
                select(CampaignRuntime)
                .where(
                    CampaignRuntime.active,
                    or_(
                        CampaignRuntime.reason.is_(None),
                        CampaignRuntime.reason != "CAMPAIGN_WORKER_CRASH_LIMIT_REVIEW_REQUIRED",
                        CampaignRuntime.cancel_requested,
                    ),
                    or_(
                        CampaignRuntime.lease_until.is_(None),
                        CampaignRuntime.lease_until < utcnow(),
                    ),
                )
                .order_by(CampaignRuntime.lease_until.asc().nullsfirst())
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if runtime is None:
                return False
            token = uuid4()
            runtime.worker_token = token
            runtime.lease_until = utcnow() + timedelta(seconds=60)
            campaign_id, owner = runtime.campaign_id, runtime.owner_id
            runtime.attempts += 1
            if runtime.attempts > 3:
                # Preserve uncertain work; never issue a replacement experiment.
                runtime.attempts = 3
                runtime.state = "UNKNOWN"
                runtime.reason = "CAMPAIGN_WORKER_CRASH_LIMIT_REVIEW_REQUIRED"
                runtime.active = True
                campaign = db.get(ResearchCampaign, campaign_id)
                if campaign:
                    record(
                        db,
                        campaign,
                        runtime,
                        "STATE",
                        {"state": "UNKNOWN", "reason": runtime.reason},
                    )
                    append_event(db, self.key, "campaign.crash_limit", entity_id=campaign_id)
                return True
        state_before = "UNKNOWN"
        before = -1
        try:
            with self.db.session() as db, db.begin():
                db.get(User, owner, with_for_update=True)
                runtime = db.get(CampaignRuntime, campaign_id, with_for_update=True)
                campaign = db.get(ResearchCampaign, campaign_id)
                if (
                    runtime is None
                    or campaign is None
                    or runtime.worker_token != token
                    or runtime.lease_until is None
                    or runtime.lease_until < utcnow()
                ):
                    return False
                before = runtime.sequence
                state_before = runtime.state
                self.advance(db, campaign, runtime)
                if runtime.lease_until is None or runtime.lease_until < utcnow():
                    raise ValueError("CAMPAIGN_LEASE_EXPIRED")
                runtime.lease_until = (
                    None if runtime.sequence != before else utcnow() + timedelta(seconds=2)
                )
                # A recovery transition alone is not a successful dependency retry.
                if state_before != "UNKNOWN":
                    runtime.attempts = 0
                if runtime.sequence != before:
                    append_event(
                        db,
                        self.key,
                        "campaign.advanced",
                        entity_id=campaign.id,
                        after={
                            "state": runtime.state,
                            "head": runtime.head,
                            "source": objective(campaign).mode,
                            "paper_eligible": False,
                        },
                    )
                return runtime.sequence != before
        except Exception:
            # An unexpected DB/storage mutation outcome is not retried as a new experiment.
            with self.db.session() as db, db.begin():
                runtime = db.get(CampaignRuntime, campaign_id, with_for_update=True)
                if runtime and runtime.worker_token == token:
                    campaign = db.get(ResearchCampaign, campaign_id)
                    if campaign and runtime.sequence == before:
                        transition(
                            db,
                            campaign,
                            runtime,
                            "UNKNOWN",
                            "CAMPAIGN_DEPENDENCY_OR_MUTATION_UNCERTAINTY",
                            "RECOVER_" + state_before,
                        )
                    elif campaign:
                        record(
                            db,
                            campaign,
                            runtime,
                            "CONTROL",
                            {"commit_reconciled": True, "state": runtime.state},
                        )
                    runtime.lease_until = utcnow() + timedelta(seconds=5)
            raise

    def advance(self, db: Any, campaign: ResearchCampaign, runtime: CampaignRuntime) -> None:
        inference = latest(db, campaign.id, "GATEWAY_REQUEST")
        ai_job = db.get(AIJob, UUID(inference.payload["request_id"])) if inference else None
        link = db.scalar(
            select(CampaignExperiment)
            .where(CampaignExperiment.campaign_id == campaign.id)
            .order_by(CampaignExperiment.ordinal.desc())
            .limit(1)
        )
        job = (
            db.scalar(
                select(ResearchJob).where(ResearchJob.run_id == link.run_id).with_for_update()
            )
            if link
            else None
        )
        try:
            spec = current(db, campaign, runtime, self.objects)
        except ValueError as exc:
            runtime.cancel_requested = True
            runtime.reason = str(exc)[:100]
            spec = objective(campaign)
        if runtime.cancel_requested:
            if ai_job and ai_job.state in {"QUEUED", "RUNNING", "RETRY", "UNKNOWN"}:
                if ai_job.state != "UNKNOWN":
                    ai_job.cancel_requested = True
                if runtime.state != "UNKNOWN":
                    transition(db, campaign, runtime, "UNKNOWN", "AI_CANCELLATION_NOT_CONFIRMED")
                return
            if job and job.state in {"QUEUED", "RUNNING", "RETRY"}:
                job.cancel_requested = True
                if runtime.state != "UNKNOWN":
                    transition(
                        db, campaign, runtime, "UNKNOWN", runtime.reason or "CANCELLATION_PENDING"
                    )
                return
            runtime.active = False
            transition(
                db, campaign, runtime, "STOPPED", runtime.reason or "CANCELLATION_ACKNOWLEDGED"
            )
            return
        if runtime.paused:
            return
        if runtime.state == "UNKNOWN" and (runtime.pending or "").startswith("RECOVER_"):
            transition(db, campaign, runtime, (runtime.pending or "").removeprefix("RECOVER_"))
            return
        if runtime.state == "QUEUED":
            transition(db, campaign, runtime, "PLANNING")
        elif runtime.state == "PLANNING":
            if spec.mode == "AI_GATEWAY":
                transition(
                    db,
                    campaign,
                    runtime,
                    "AWAITING_APPROVAL",
                    "OWNER_AI_HANDOFF_REQUIRED",
                    "REQUEST_RESEARCH",
                )
            else:
                try:
                    fixture_proposal(db, campaign, runtime)
                    plan_candidate(db, campaign, runtime)
                except ValueError as exc:
                    runtime.active = False
                    transition(db, campaign, runtime, "STOPPED", str(exc)[:100])
        elif runtime.state in {"TESTING", "UNKNOWN"}:
            if job is None:
                if runtime.state == "UNKNOWN":
                    # Reconcile durable metadata; never submit a replacement experiment.
                    transition(
                        db,
                        campaign,
                        runtime,
                        "AWAITING_APPROVAL",
                        "OWNER_RECONCILIATION_REQUIRED",
                        "SUBMIT_EXPERIMENT",
                    )
                else:
                    raise ValueError("CAMPAIGN_EXPERIMENT_REFERENCE_MISSING")
            elif job.state == "SUCCEEDED":
                transition(db, campaign, runtime, "EVALUATING")
            elif job.state in {"FAILED", "CANCELLED"}:
                runtime.active = False
                transition(db, campaign, runtime, "FAILED", "CHILD_EXPERIMENT_FAILED_OR_CANCELLED")
        elif runtime.state == "EVALUATING":
            if link is None:
                raise ValueError("EXPERIMENT_EVIDENCE_MISSING")
            result = db.get(ResearchResult, link.run_id)
            if result is None:
                raise ValueError("COMPLETE_CANONICAL_RESULT_REQUIRED")
            body = json.loads(self.objects.get(result.artifact))
            campaign_runs = select(CampaignExperiment.run_id).where(
                CampaignExperiment.campaign_id == campaign.id
            )
            from sqlalchemy import func

            total = (
                db.scalar(
                    select(func.count())
                    .select_from(ResearchTrial)
                    .where(ResearchTrial.owner_id == campaign.owner_id)
                )
                or 0
            )
            attempted = (
                db.scalar(
                    select(func.count())
                    .select_from(ResearchTrial)
                    .where(ResearchTrial.run_id.in_(campaign_runs))
                )
                or 0
            )
            evidence = ExperimentEvidence(
                experiment_id=link.run_id,
                semantic_digest=result.semantic_digest,
                artifact=result.artifact,
                attempted_trials_owner=total,
                attempted_trials_campaign=attempted,
                source=spec.mode,
            )
            item = record(
                db, campaign, runtime, "EVIDENCE", evidence.model_dump(mode="json"), link.plan_id
            )
            decision = evaluate(spec, body, item.id)
            record(db, campaign, runtime, "EVALUATION", decision.model_dump(mode="json"), item.id)
            transition(db, campaign, runtime, "CRITIQUING")
        elif runtime.state == "CRITIQUING":
            if spec.mode == "AI_GATEWAY":
                transition(
                    db,
                    campaign,
                    runtime,
                    "AWAITING_APPROVAL",
                    "OWNER_AI_HANDOFF_REQUIRED",
                    "REQUEST_CRITIC",
                )
            else:
                critique_decision = latest(db, campaign.id, "EVALUATION")
                if critique_decision is None:
                    raise ValueError("EVALUATION_MISSING")
                finish_critique(
                    db,
                    campaign,
                    runtime,
                    Critique(
                        summary="Deterministic synthetic critique; not model inference.",
                        objections=critique_decision.payload["reasons"][:10],
                        source="SYNTHETIC_FIXTURE",
                    ),
                )
        elif runtime.state == "READY_FOR_NEXT_ITERATION":
            transition(
                db, campaign, runtime, "PLANNING", "TRAINING_REUSE_NOT_INDEPENDENT_VALIDATION"
            )
