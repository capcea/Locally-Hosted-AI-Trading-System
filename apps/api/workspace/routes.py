"""Product-level reads/configuration; existing canonical engine owns every simulation."""

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import Field, ValidationError
from sqlalchemy import select

from apps.api.ai.context import ContextScope, assemble
from apps.api.ai.routes import configured
from apps.api.identity.dependencies import (
    FullIdentity,
    Principal,
    require_owner,
    require_sensitive_session,
)
from apps.api.research.routes import create as create_experiment
from apps.api.research.routes import result_for, run_for
from packages.ai.contracts import ContextReference, Contract
from packages.campaigns.contracts import (
    Critique,
    EvaluationDecision,
    ExperimentEvidence,
    ExperimentPlan,
)
from packages.campaigns.evaluation import evaluate
from packages.campaigns.models import (
    CampaignExperiment,
    CampaignLineage,
    CampaignRuntime,
    ResearchCampaign,
)
from packages.campaigns.service import objective
from packages.persistence.models import TradingAccount
from packages.research.contracts import ExperimentInput
from packages.research.models import ResearchJob, ResearchResult
from packages.research.selections import StrategySelection

router = APIRouter(
    prefix="/api/v1/workspace", tags=["Simple trading research workspace — SIMULATED"]
)


class SelectionInput(Contract):
    decision_id: UUID


class SimulationInput(Contract):
    key: str = Field(min_length=16, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    acknowledged_historical_simulation: Literal[True]


def candidate_for(
    identifier: UUID, identity: Principal, request: Request
) -> tuple[dict[str, Any], ExperimentInput]:
    row = identity.db.get(CampaignLineage, identifier)
    if row is None or row.owner_id != identity.user.id:
        raise HTTPException(404, "WORKSPACE_CANDIDATE_NOT_FOUND")
    if (
        row.kind != "EVALUATION"
        or row.source != "AI_GATEWAY"
        or row.payload.get("decision") != "RESEARCH_CANDIDATE"
    ):
        raise HTTPException(409, "WORKSPACE_RESEARCH_EVIDENCE_REQUIRED")
    campaign = identity.db.get(ResearchCampaign, row.campaign_id)
    runtime = identity.db.get(CampaignRuntime, row.campaign_id)
    critique = identity.db.scalar(
        select(CampaignLineage).where(
            CampaignLineage.owner_id == identity.user.id,
            CampaignLineage.campaign_id == row.campaign_id,
            CampaignLineage.parent_id == row.id,
            CampaignLineage.kind == "CRITIQUE",
            CampaignLineage.source == "AI_GATEWAY",
        )
    )
    if (
        runtime is None
        or runtime.owner_id != identity.user.id
        or runtime.state != "COMPLETED"
        or critique is None
    ):
        raise HTTPException(409, "WORKSPACE_COMPLETED_REVIEW_REQUIRED")
    evidence = identity.db.get(CampaignLineage, row.parent_id)
    if (
        not campaign
        or campaign.owner_id != identity.user.id
        or not evidence
        or evidence.owner_id != identity.user.id
        or evidence.campaign_id != row.campaign_id
        or evidence.kind != "EVIDENCE"
        or evidence.source != "AI_GATEWAY"
        or row.payload.get("evidence_id") != str(evidence.id)
    ):
        raise HTTPException(409, "WORKSPACE_LINEAGE_INVALID")
    try:
        evidence_body = ExperimentEvidence.model_validate(evidence.payload)
        evaluation = EvaluationDecision.model_validate(row.payload)
        review = Critique.model_validate(critique.payload)
        spec = objective(campaign)
    except ValidationError as exc:
        raise HTTPException(409, "WORKSPACE_LINEAGE_INVALID") from exc
    if (
        any(item.source != "AI_GATEWAY" for item in (evidence_body, evaluation, review))
        or spec.mode != "AI_GATEWAY"
    ):
        raise HTTPException(409, "WORKSPACE_LINEAGE_INVALID")
    link = identity.db.scalar(
        select(CampaignExperiment).where(
            CampaignExperiment.owner_id == identity.user.id,
            CampaignExperiment.campaign_id == campaign.id,
            CampaignExperiment.run_id == evidence_body.experiment_id,
            CampaignExperiment.plan_id == evidence.parent_id,
        )
    )
    planned = identity.db.get(CampaignLineage, evidence.parent_id) if evidence.parent_id else None
    if (
        link is None
        or planned is None
        or planned.owner_id != identity.user.id
        or planned.campaign_id != campaign.id
        or planned.kind != "PLAN"
        or planned.source != "AI_GATEWAY"
    ):
        raise HTTPException(409, "WORKSPACE_LINEAGE_INVALID")
    run = run_for(identity, evidence_body.experiment_id)
    try:
        plan = ExperimentInput.model_validate(run.plan)
        original = ExperimentPlan.model_validate(planned.payload)
    except ValidationError as exc:
        raise HTTPException(409, "WORKSPACE_LINEAGE_INVALID") from exc
    if (
        original.source != "AI_GATEWAY"
        or original.parent_proposal != planned.parent_id
        or original.experiment != plan
        or plan.source_account_id != campaign.account_id
        or run.source_account_id != campaign.account_id
        or spec.template.source_account_id != campaign.account_id
    ):
        raise HTTPException(409, "WORKSPACE_LINEAGE_INVALID")
    job = identity.db.scalar(select(ResearchJob).where(ResearchJob.run_id == run.id))
    result = identity.db.get(ResearchResult, run.id)
    if (
        not job
        or job.state != "SUCCEEDED"
        or result is None
        or result.semantic_digest != evidence_body.semantic_digest
        or result.artifact != evidence_body.artifact
        or plan.phase != "VALIDATION"
        or plan.holdout_release_id is not None
    ):
        raise HTTPException(409, "WORKSPACE_COMPLETE_VALIDATION_REQUIRED")
    # Reuse ownership, admitted-data and protected-holdout context checks.
    assemble(
        ContextScope(identity.db, identity.user.id),
        [ContextReference(kind="experiment", id=str(run.id))],
        configured(request),
    )
    body = result_for(run.id, identity, request)
    decision = evaluate(spec, body, evidence.id)
    if decision.decision != "RESEARCH_CANDIDATE":
        raise HTTPException(409, "WORKSPACE_RESEARCH_EVIDENCE_REQUIRED")
    return {
        "id": str(row.id),
        "experiment_id": str(run.id),
        "account_id": str(run.source_account_id),
        "name": run.plan["name"],
        "strategy": plan.strategy,
        "strategy_digest": plan.strategy_digest,
        "decision": "RESEARCH_CANDIDATE",
        "source": "AI_GATEWAY",
        "metrics": decision.observations,
        "limitations": decision.unknown,
        "external_execution_authorized": False,
    }, plan


@router.get("/library")
def library(
    identity: FullIdentity,
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    account_id: UUID | None = None,
) -> dict[str, Any]:
    query = select(CampaignLineage).where(
        CampaignLineage.owner_id == identity.user.id,
        CampaignLineage.kind == "EVALUATION",
        CampaignLineage.source == "AI_GATEWAY",
        CampaignLineage.payload["decision"].as_string() == "RESEARCH_CANDIDATE",
    )
    if account_id is not None:
        query = query.join(
            ResearchCampaign, ResearchCampaign.id == CampaignLineage.campaign_id
        ).where(
            ResearchCampaign.owner_id == identity.user.id,
            ResearchCampaign.account_id == account_id,
        )
    rows = list(
        identity.db.scalars(
            query.order_by(CampaignLineage.created_at.desc()).offset(offset).limit(limit + 1)
        )
    )
    items = []
    unavailable = 0
    for row in rows[:limit]:
        try:
            items.append(candidate_for(row.id, identity, request)[0])
        except HTTPException:
            unavailable += 1
    return {
        "items": items,
        "has_more": len(rows) > limit,
        "unavailable_count": unavailable,
        "external_execution_authorized": False,
    }


def selection_for(identity: Principal, account_id: UUID) -> StrategySelection | None:
    account = identity.db.get(TradingAccount, account_id)
    if account is None or account.owner_id != identity.user.id:
        raise HTTPException(404, "WORKSPACE_ACCOUNT_NOT_FOUND")
    return identity.db.scalar(
        select(StrategySelection)
        .where(
            StrategySelection.account_id == account_id,
            StrategySelection.owner_id == identity.user.id,
        )
        .order_by(StrategySelection.revision.desc())
        .limit(1)
    )


@router.get("/accounts/{account_id}/strategy")
def selection(account_id: UUID, identity: FullIdentity, request: Request) -> dict[str, Any]:
    row = selection_for(identity, account_id)
    if row is None:
        return {"selection": None, "mode": "SIMULATED", "external_execution_authorized": False}
    try:
        candidate, _ = candidate_for(row.decision_id, identity, request)
        if candidate["account_id"] != str(account_id):
            raise HTTPException(409, "WORKSPACE_ACCOUNT_VALIDATION_REQUIRED")
        reason = None
    except HTTPException as exc:
        candidate = None
        reason = exc.detail
    return {
        "selection": {
            "id": str(row.id),
            "decision_id": str(row.decision_id),
            "revision": row.revision,
            "candidate": candidate,
            "available": candidate is not None,
            "reason": reason,
        },
        "mode": "SIMULATED",
        "external_execution_authorized": False,
    }


@router.post("/accounts/{account_id}/strategy", status_code=201)
def select_strategy(
    account_id: UUID, body: SelectionInput, identity: FullIdentity, request: Request
) -> dict[str, Any]:
    require_owner(identity)
    require_sensitive_session(identity)
    old = selection_for(identity, account_id)
    candidate, _ = candidate_for(body.decision_id, identity, request)
    if candidate["account_id"] != str(account_id):
        raise HTTPException(409, "WORKSPACE_ACCOUNT_VALIDATION_REQUIRED")
    if old is None or old.decision_id != body.decision_id:
        row = StrategySelection(
            owner_id=identity.user.id,
            account_id=account_id,
            decision_id=body.decision_id,
            revision=old.revision + 1 if old else 1,
        )
        identity.db.add(row)
        identity.db.flush()
        identity.audit(
            "workspace.strategy_selected",
            entity_id=row.id,
            after={
                "account_id": str(account_id),
                "decision_id": str(body.decision_id),
                "mode": "SIMULATED",
            },
        )
    return selection(account_id, identity, request)


@router.post("/accounts/{account_id}/simulate", status_code=202)
def simulate(
    account_id: UUID, body: SimulationInput, identity: FullIdentity, request: Request
) -> dict[str, Any]:
    require_owner(identity)
    row = selection_for(identity, account_id)
    if row is None:
        raise HTTPException(409, "WORKSPACE_SELECT_STRATEGY_FIRST")
    _, plan = candidate_for(row.decision_id, identity, request)
    if plan.source_account_id != account_id:
        raise HTTPException(409, "WORKSPACE_ACCOUNT_VALIDATION_REQUIRED")
    # Revalidate the complete plan through the existing Phase5 submission/Risk Gateway path.
    # This is a bounded historical replay, not continuous or broker-connected trading.
    submitted = ExperimentInput.model_validate(
        {**plan.model_dump(mode="json"), "key": body.key, "name": ("Simulare: " + plan.name)[:120]}
    )
    return create_experiment(submitted, identity, request)
