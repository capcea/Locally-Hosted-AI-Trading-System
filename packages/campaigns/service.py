"""Transactional lineage and Phase5 planning; no session impersonation."""

import hashlib
import json
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.campaigns.contracts import (
    ExperimentPlan,
    ParameterCandidate,
    ResearchObjective,
    StrategyHypothesis,
)
from packages.campaigns.models import CampaignLineage, CampaignRuntime, ResearchCampaign
from packages.execution.journal import digest
from packages.market.storage import ObjectStore
from packages.persistence.models import User, utcnow
from packages.research.approval import assert_current
from packages.research.contracts import ExperimentInput
from packages.research.data import pinned
from packages.research.models import ResearchRun

RESULT_RESERVATION = (
    3 * 16 * 1024 * 1024
)  # Phase5 allows up to three attempts, each bounded to16MiB.


def software_digest() -> str:
    root = Path(__file__).resolve().parents[2]
    files = sorted(Path(__file__).parent.glob("*.py")) + [
        root / "apps/api/campaigns/routes.py",
        root / "scripts/campaign_worker.py",
    ]
    return digest(
        {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    )


def objective(campaign: ResearchCampaign) -> ResearchObjective:
    return ResearchObjective.model_validate(campaign.specification)


def latest(db: Session, campaign: UUID, kind: str) -> CampaignLineage | None:
    return db.scalar(
        select(CampaignLineage)
        .where(
            CampaignLineage.campaign_id == campaign,
            CampaignLineage.kind == kind,
        )
        .order_by(CampaignLineage.sequence.desc())
        .limit(1)
    )


def record(
    db: Session,
    campaign: ResearchCampaign,
    runtime: CampaignRuntime,
    kind: str,
    payload: dict[str, Any],
    parent: UUID | None = None,
) -> CampaignLineage:
    spec = objective(campaign)
    body = {"schema_version": 1, "source": spec.mode, **payload}
    size = len(json.dumps(body, sort_keys=True).encode())
    # Reserve room for fail-closed control events even after ordinary evidence exhaustion.
    emergency = (kind == "STATE" and payload.get("state") in {"UNKNOWN", "STOPPED", "FAILED"}) or (
        kind == "CONTROL" and payload.get("action") == "CANCEL"
    )
    ceiling = spec.budgets.lineage_bytes + (8192 if emergency else 0)
    if size > 65536 or runtime.lineage_bytes + size > ceiling:
        raise ValueError("CAMPAIGN_LINEAGE_STORAGE_BUDGET_EXHAUSTED")
    if parent:
        row = db.get(CampaignLineage, parent)
        if row is None or row.campaign_id != campaign.id or row.owner_id != campaign.owner_id:
            raise ValueError("CROSS_CAMPAIGN_LINEAGE_REFUSED")
    runtime.sequence += 1
    checksum = digest(
        {
            "campaign": str(campaign.id),
            "sequence": runtime.sequence,
            "parent": str(parent) if parent else None,
            "kind": kind,
            "previous": runtime.head,
            "payload": body,
        }
    )
    row = CampaignLineage(
        id=uuid4(),
        owner_id=campaign.owner_id,
        campaign_id=campaign.id,
        sequence=runtime.sequence,
        kind=kind,
        payload=body,
        parent_id=parent,
        source=spec.mode,
        previous_digest=runtime.head,
        digest=checksum,
    )
    db.add(row)
    runtime.head = checksum
    runtime.lineage_bytes += size
    db.flush()
    return row


def transition(
    db: Session,
    campaign: ResearchCampaign,
    runtime: CampaignRuntime,
    state: str,
    reason: str | None = None,
    pending: str | None = None,
) -> None:
    previous = runtime.state
    runtime.state, runtime.reason, runtime.pending = state, reason, pending
    record(
        db,
        campaign,
        runtime,
        "STATE",
        {"from": previous, "state": state, "reason": reason, "pending": pending},
    )


def current(
    db: Session, campaign: ResearchCampaign, runtime: CampaignRuntime, objects: ObjectStore
) -> ResearchObjective:
    spec = objective(campaign)
    user = db.get(User, campaign.owner_id)
    if not user or not user.active or user.role != "OWNER" or not runtime.approval:
        raise ValueError("CAMPAIGN_AUTHORIZATION_REVOKED")
    if runtime.deadline is None or utcnow() >= runtime.deadline:
        raise ValueError("CAMPAIGN_RUNTIME_BUDGET_EXHAUSTED")
    if runtime.approval.get("campaign_software_digest") != software_digest():
        raise ValueError("CAMPAIGN_SOFTWARE_VERSION_CHANGED")
    plan = spec.template
    # Reuse existing source-account/policy/profile/software revocation checks.
    shadow = ResearchRun(approval_snapshot=runtime.approval)
    assert_current(db, shadow, plan)
    pinned(db, plan, campaign.owner_id, objects, read=False)
    if spec.mode == "AI_GATEWAY":
        from packages.ai.models import AIConnection, AIRoute
        from packages.ai.registry import latest_verification

        for role, saved in runtime.approval.get("gateway_roles", {}).items():
            binding = db.scalar(
                select(AIRoute)
                .where(
                    AIRoute.owner_id == campaign.owner_id,
                    AIRoute.role == role,
                )
                .order_by(AIRoute.revision.desc())
                .limit(1)
            )
            model = saved["model"]
            if model.get("cloud"):
                from packages.ai.cloud import unchanged

                if not unchanged(
                    db, campaign.owner_id, UUID(model["connection_id"]), model["cloud"]
                ):
                    raise ValueError("MODEL_UNAVAILABLE_OR_AUTHORIZATION_REVOKED")
            connection = db.get(AIConnection, UUID(model["connection_id"]))
            verification = latest_verification(db, UUID(model["model_id"]))
            if (
                binding is None
                or str(binding.id) != saved["route_id"]
                or connection is None
                or not connection.enabled
                or verification is None
                or str(verification.id) != model["verification_id"]
                or verification.expires_at <= utcnow()
            ):
                raise ValueError("MODEL_UNAVAILABLE_OR_AUTHORIZATION_REVOKED")
        if len(runtime.approval.get("gateway_roles", {})) != 2:
            raise ValueError("MODEL_UNAVAILABLE")
    return spec


def admit_candidate(
    db: Session,
    campaign: ResearchCampaign,
    runtime: CampaignRuntime,
    hypothesis: StrategyHypothesis,
    candidate: ParameterCandidate,
) -> CampaignLineage:
    spec = objective(campaign)
    if (
        hypothesis.source != spec.mode
        or candidate.source != spec.mode
        or hypothesis.strategy != spec.template.strategy
        or candidate.strategy != spec.template.strategy
        or hypothesis.strategy_digest != spec.template.strategy_digest
        or candidate.strategy_digest != spec.template.strategy_digest
    ):
        raise ValueError("CANDIDATE_SCOPE_OR_VERSION_REFUSED")
    if candidate.parameters not in spec.search_space:
        raise ValueError("PARAMETERS_OUTSIDE_OWNER_AUTHORIZED_FINITE_DOMAIN")
    key = digest(candidate.parameters.model_dump(mode="json"))
    for old in db.scalars(
        select(CampaignLineage).where(
            CampaignLineage.campaign_id == campaign.id,
            CampaignLineage.kind == "CANDIDATE",
        )
    ):
        if old.payload["candidate_digest"] == key:
            raise ValueError("DUPLICATE_CAMPAIGN_CANDIDATE")
    if runtime.proposals >= spec.budgets.candidate_proposals:
        raise ValueError("CAMPAIGN_PROPOSAL_BUDGET_EXHAUSTED")
    runtime.proposals += 1
    feedback = latest(db, campaign.id, "FEEDBACK")
    h = record(
        db,
        campaign,
        runtime,
        "HYPOTHESIS",
        hypothesis.model_dump(mode="json"),
        feedback.id if feedback else None,
    )
    return record(
        db,
        campaign,
        runtime,
        "CANDIDATE",
        {"candidate": candidate.model_dump(mode="json"), "candidate_digest": key},
        h.id,
    )


def fixture_proposal(db: Session, campaign: ResearchCampaign, runtime: CampaignRuntime) -> None:
    spec = objective(campaign)
    # A fixed seed chooses an explicit finite order; no profit-driven or generated search.
    parameters = spec.search_space[(spec.seed + runtime.iteration) % len(spec.search_space)]
    admit_candidate(
        db,
        campaign,
        runtime,
        StrategyHypothesis(
            title="Synthetic bounded hypothesis",
            rationale=spec.objective,
            strategy=spec.template.strategy,
            strategy_digest=spec.template.strategy_digest,
            source="SYNTHETIC_FIXTURE",
        ),
        ParameterCandidate(
            strategy=spec.template.strategy,
            strategy_digest=spec.template.strategy_digest,
            parameters=parameters,
            source="SYNTHETIC_FIXTURE",
        ),
    )


def plan_candidate(db: Session, campaign: ResearchCampaign, runtime: CampaignRuntime) -> None:
    spec = objective(campaign)
    candidate = latest(db, campaign.id, "CANDIDATE")
    if candidate is None:
        raise ValueError("CAMPAIGN_CANDIDATE_MISSING")
    if (
        runtime.iteration >= spec.budgets.iterations
        or runtime.experiments >= spec.budgets.experiments
        or runtime.reserved_bytes + RESULT_RESERVATION + spec.budgets.lineage_bytes + 8192
        > spec.budgets.artifact_bytes
        or runtime.reserved_seconds + 3 * spec.template.max_seconds > spec.budgets.runtime_seconds
    ):
        raise ValueError("CAMPAIGN_EXPERIMENT_OR_RESOURCE_BUDGET_EXHAUSTED")
    runtime.iteration += 1
    runtime.reserved_bytes += RESULT_RESERVATION
    runtime.reserved_seconds += 3 * spec.template.max_seconds
    c = ParameterCandidate.model_validate(candidate.payload["candidate"])
    data = spec.template.model_dump(mode="json")
    data.update(
        key=f"campaign-{campaign.id.hex}-{runtime.iteration}",
        name=f"[{spec.mode}] {spec.title[:60]} / {runtime.iteration}",
        parameters=[c.parameters.model_dump(mode="json")],
        seed=spec.seed,
    )
    plan = ExperimentPlan(
        iteration=runtime.iteration,
        parent_proposal=candidate.id,
        experiment=ExperimentInput.model_validate(data),
        source=spec.mode,
    )
    record(db, campaign, runtime, "PLAN", plan.model_dump(mode="json"), candidate.id)
    transition(
        db, campaign, runtime, "AWAITING_APPROVAL", "RECENT_OWNER_MFA_REQUIRED", "SUBMIT_EXPERIMENT"
    )


def reserve_authorization(
    db: Session,
    campaign: ResearchCampaign,
    runtime: CampaignRuntime,
    snapshot: dict[str, Any],
    global_limit: int,
    owner_limit: int,
) -> None:
    from sqlalchemy import text

    db.execute(text("SELECT pg_advisory_xact_lock(70701,0)"))
    active = select(CampaignRuntime).where(
        CampaignRuntime.active, CampaignRuntime.campaign_id != campaign.id
    )
    total = db.scalar(select(func.count()).select_from(active.subquery())) or 0
    owned = (
        db.scalar(
            select(func.count()).select_from(
                active.where(CampaignRuntime.owner_id == campaign.owner_id).subquery()
            )
        )
        or 0
    )
    if total >= global_limit or owned >= owner_limit:
        raise ValueError("CAMPAIGN_CONCURRENCY_LIMIT")
    spec = objective(campaign)
    # Resume does not extend the original deadline or reset counters.
    runtime.deadline = runtime.deadline or utcnow() + timedelta(
        seconds=spec.budgets.runtime_seconds
    )
    if runtime.deadline <= utcnow():
        raise ValueError("CAMPAIGN_RUNTIME_BUDGET_EXHAUSTED")
    runtime.approval = snapshot
    runtime.active = True
    runtime.paused = False
    record(
        db,
        campaign,
        runtime,
        "AUTHORIZATION",
        {
            "campaign_digest": campaign.digest,
            "snapshot": snapshot,
            "deadline": runtime.deadline.isoformat(),
            "unattended_submission": False,
        },
    )
