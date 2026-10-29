"""Owner/MFA campaign authorization and explicit Phase5/6 submission handoffs."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import func, select

from apps.api.ai.routes import configured, job_view
from apps.api.ai.routes import submit as submit_ai
from apps.api.governance.routes import owned
from apps.api.identity.dependencies import FullIdentity
from apps.api.market.routes import object_store
from apps.api.research.routes import create as create_experiment
from apps.api.research.routes import privileged, validate_plan
from packages.ai.contracts import (
    ContextReference,
    CritiqueReport,
    Generation,
    HypothesisProposal,
    RequestInput,
)
from packages.ai.models import AIRequest, AIRoute
from packages.ai.registry import snapshot as model_snapshot
from packages.campaigns.contracts import (
    Approval,
    CampaignAction,
    CreateCampaign,
    Critique,
    ExperimentPlan,
    GatewayAction,
    ParameterCandidate,
    PlanReview,
    StrategyHypothesis,
)
from packages.campaigns.models import (
    CampaignExperiment,
    CampaignLineage,
    CampaignRuntime,
    ResearchCampaign,
)
from packages.campaigns.service import (
    admit_candidate,
    current,
    latest,
    objective,
    plan_candidate,
    record,
    reserve_authorization,
    software_digest,
    transition,
)
from packages.campaigns.worker import finish_critique
from packages.execution.journal import digest
from packages.persistence.models import TradingAccount
from packages.research.models import ResearchRun

router = APIRouter(prefix="/api/v1/campaigns", tags=["Bounded research campaigns — SIMULATED"])


def scoped(identity: FullIdentity, campaign_id: UUID) -> tuple[ResearchCampaign, CampaignRuntime]:
    row = identity.db.scalar(
        select(ResearchCampaign).where(
            ResearchCampaign.id == campaign_id, ResearchCampaign.owner_id == identity.user.id
        )
    )
    if row is None:
        raise HTTPException(404, "CAMPAIGN_NOT_FOUND")
    runtime = identity.db.get(CampaignRuntime, row.id, with_for_update=True)
    if runtime is None:
        raise HTTPException(409, "CAMPAIGN_RUNTIME_MISSING")
    return row, runtime


def view(row: ResearchCampaign, runtime: CampaignRuntime) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "digest": row.digest,
        "objective": row.specification,
        "created_at": row.created_at,
        "state": runtime.state,
        "pending": runtime.pending,
        "reason": runtime.reason,
        "paused": runtime.paused,
        "cancel_requested": runtime.cancel_requested,
        "cancellation_acknowledged": runtime.cancel_requested
        and runtime.state == "STOPPED"
        and not runtime.active,
        "counts": {
            "proposals": runtime.proposals,
            "experiments": runtime.experiments,
            "iterations": runtime.iteration,
            "reserved_seconds": runtime.reserved_seconds,
            "reserved_bytes": runtime.reserved_bytes,
        },
        "deadline": runtime.deadline,
        "lineage_head": runtime.head,
        "source": row.specification["mode"],
        "paper_eligible": False,
        "external_execution": "DENY_ALL",
        "unattended_submission": False,
    }


def checked(
    identity: FullIdentity, request: Request, row: ResearchCampaign, runtime: CampaignRuntime
) -> None:
    try:
        current(identity.db, row, runtime, object_store(request))
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if runtime.paused or runtime.cancel_requested or not runtime.active:
        raise HTTPException(409, "CAMPAIGN_NOT_ACTIVE")


def authorized_snapshot(
    identity: FullIdentity, request: Request, row: ResearchCampaign
) -> dict[str, Any]:
    spec = objective(row)
    result = validate_plan(spec.template, identity, request)
    result["campaign_software_digest"] = software_digest()
    for parameters in spec.search_space:
        plan = spec.template.model_copy(update={"parameters": [parameters]})
        validate_plan(plan, identity, request)
    if spec.mode == "AI_GATEWAY":
        routes = {}
        try:
            for role in ("RESEARCH", "CRITIC"):
                binding = identity.db.scalar(
                    select(AIRoute)
                    .where(
                        AIRoute.owner_id == row.owner_id,
                        AIRoute.role == role,
                    )
                    .order_by(AIRoute.revision.desc())
                    .limit(1)
                )
                if binding is None:
                    raise ValueError("MODEL_UNAVAILABLE")
                model = model_snapshot(
                    identity.db, row.owner_id, binding.model_id, configured(request)
                )
                routes[role] = {"route_id": str(binding.id), "model": model}
        except (ValueError, HTTPException) as exc:
            raise ValueError("MODEL_UNAVAILABLE") from exc
        result["gateway_roles"] = routes
    return result


@router.post("", status_code=201)
def create(body: CreateCampaign, identity: FullIdentity, request: Request) -> dict[str, Any]:
    privileged(identity)
    fingerprint = digest(body.objective.model_dump(mode="json"))
    old = identity.db.scalar(
        select(ResearchCampaign).where(
            ResearchCampaign.owner_id == identity.user.id, ResearchCampaign.key == body.key
        )
    )
    if old:
        if old.digest != fingerprint:
            raise HTTPException(409, "CAMPAIGN_IDEMPOTENCY_CONFLICT")
        return view(old, identity.db.get(CampaignRuntime, old.id))  # type: ignore[arg-type]
    count = (
        identity.db.scalar(
            select(func.count())
            .select_from(ResearchCampaign)
            .where(ResearchCampaign.owner_id == identity.user.id)
        )
        or 0
    )
    if count >= 50:
        raise HTTPException(429, "CAMPAIGN_METADATA_QUOTA")
    owned(identity, TradingAccount, body.objective.template.source_account_id)
    # A draft grants no authority but still may not retain cross-owner input references.
    try:
        validate_plan(body.objective.template, identity, request)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    row = ResearchCampaign(
        owner_id=identity.user.id,
        account_id=body.objective.template.source_account_id,
        key=body.key,
        digest=fingerprint,
        specification=body.objective.model_dump(mode="json"),
    )
    identity.db.add(row)
    identity.db.flush()
    runtime = CampaignRuntime(campaign_id=row.id, owner_id=row.owner_id, state="DRAFT")
    identity.db.add(runtime)
    identity.db.flush()
    record(
        identity.db,
        row,
        runtime,
        "OBJECTIVE",
        {"digest": fingerprint, "title": body.objective.title},
    )
    identity.audit(
        "campaign.created",
        entity_id=row.id,
        after={"digest": fingerprint, "source": body.objective.mode},
    )
    return view(row, runtime)


@router.get("")
def campaigns(
    identity: FullIdentity, offset: int = Query(0, ge=0, le=10000)
) -> list[dict[str, Any]]:
    return [
        view(row, runtime)
        for row, runtime in identity.db.execute(
            select(ResearchCampaign, CampaignRuntime)
            .join(CampaignRuntime, CampaignRuntime.campaign_id == ResearchCampaign.id)
            .where(ResearchCampaign.owner_id == identity.user.id)
            .order_by(ResearchCampaign.created_at.desc())
            .offset(offset)
            .limit(25)
        )
    ]


@router.get("/{campaign_id}")
def get(campaign_id: UUID, identity: FullIdentity) -> dict[str, Any]:
    return view(*scoped(identity, campaign_id))


@router.get("/{campaign_id}/lineage")
def lineage(
    campaign_id: UUID, identity: FullIdentity, offset: int = Query(0, ge=0, le=10000)
) -> list[dict[str, Any]]:
    scoped(identity, campaign_id)
    return [
        {
            "id": str(r.id),
            "sequence": r.sequence,
            "kind": r.kind,
            "parent_id": str(r.parent_id) if r.parent_id else None,
            "payload": r.payload,
            "source": r.source,
            "previous_digest": r.previous_digest,
            "digest": r.digest,
            "created_at": r.created_at,
            "paper_eligible": False,
        }
        for r in identity.db.scalars(
            select(CampaignLineage)
            .where(CampaignLineage.campaign_id == campaign_id)
            .order_by(CampaignLineage.sequence)
            .offset(offset)
            .limit(100)
        )
    ]


@router.post("/{campaign_id}/approve")
def approve(
    campaign_id: UUID, body: Approval, identity: FullIdentity, request: Request
) -> dict[str, Any]:
    privileged(identity)
    row, runtime = scoped(identity, campaign_id)
    if body.expected_digest != row.digest:
        raise HTTPException(409, "CAMPAIGN_APPROVAL_DIGEST_CHANGED")
    if runtime.active and runtime.approval and not runtime.cancel_requested:
        return view(row, runtime)
    if runtime.state != "AWAITING_APPROVAL" or runtime.pending != "AUTHORIZE":
        raise HTTPException(409, "CAMPAIGN_NOT_AWAITING_AUTHORIZATION")
    try:
        snapshot = authorized_snapshot(identity, request, row)
        reserve_authorization(
            identity.db,
            row,
            runtime,
            snapshot,
            request.app.state.settings.campaign_global_concurrency,
            request.app.state.settings.campaign_owner_concurrency,
        )
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    transition(identity.db, row, runtime, "QUEUED")
    runtime.lease_until, runtime.worker_token = None, None
    identity.audit(
        "campaign.authorized",
        entity_id=row.id,
        after={"digest": row.digest, "unattended_submission": False},
    )
    return view(row, runtime)


@router.post("/{campaign_id}/control")
def control(
    campaign_id: UUID, body: CampaignAction, identity: FullIdentity, request: Request
) -> dict[str, Any]:
    privileged(identity)
    row, runtime = scoped(identity, campaign_id)
    if body.action == "REQUEST_APPROVAL":
        if runtime.state != "DRAFT":
            raise HTTPException(409, "CAMPAIGN_NOT_DRAFT")
        transition(identity.db, row, runtime, "AWAITING_APPROVAL", pending="AUTHORIZE")
    elif body.action == "PAUSE":
        if not runtime.active or runtime.cancel_requested:
            raise HTTPException(409, "CAMPAIGN_NOT_ACTIVE")
        if runtime.paused:
            return view(row, runtime)
        runtime.paused = True
        record(
            identity.db,
            row,
            runtime,
            "CONTROL",
            {"action": "PAUSE", "ongoing_experiment_may_continue": True},
        )
    elif body.action == "RESUME":
        if not runtime.paused or runtime.cancel_requested:
            raise HTTPException(409, "CAMPAIGN_NOT_PAUSED")
        try:
            current(identity.db, row, runtime, object_store(request))
            fresh = authorized_snapshot(identity, request, row)
            reserve_authorization(
                identity.db,
                row,
                runtime,
                fresh,
                request.app.state.settings.campaign_global_concurrency,
                request.app.state.settings.campaign_owner_concurrency,
            )
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
    else:
        if runtime.state in {"COMPLETED", "FAILED"} or (
            runtime.state == "STOPPED" and not runtime.active
        ):
            return view(row, runtime)
        if runtime.cancel_requested:
            return view(row, runtime)
        runtime.cancel_requested = True
        runtime.attempts = 0
        runtime.reason = "OWNER_CANCELLATION_REQUESTED"
        runtime.active = True  # Worker must acknowledge even a queued or uncertain campaign.
        record(identity.db, row, runtime, "CONTROL", {"action": "CANCEL", "acknowledged": False})
    identity.audit("campaign.control_requested", entity_id=row.id, after={"action": body.action})
    runtime.lease_until, runtime.worker_token = None, None
    return view(row, runtime)


def refuse_oos_reuse(identity: FullIdentity, row: ResearchCampaign, plan: Any) -> None:
    if plan.phase != "VALIDATION":
        return
    # Conservative owner-wide interval guard also catches same-period aliases/manual prior runs.
    # It does not certify exposure outside this registry or create a final holdout release.
    for previous in identity.db.scalars(
        select(ResearchRun).where(ResearchRun.owner_id == row.owner_id)
    ):
        if previous.plan["phase"] != "VALIDATION":
            continue
        chronology = previous.plan["chronology"]
        if (
            datetime.fromisoformat(chronology["calibration_end"]) < plan.chronology.validation_end
            and datetime.fromisoformat(chronology["validation_end"])
            > plan.chronology.calibration_end
        ):
            raise HTTPException(409, "EVALUATION_INTERVAL_ALREADY_EXPOSED_NO_RETUNING")


@router.post("/{campaign_id}/submit-plan", status_code=202)
def submit_plan(
    campaign_id: UUID, body: PlanReview, identity: FullIdentity, request: Request
) -> dict[str, Any]:
    privileged(identity)
    row, runtime = scoped(identity, campaign_id)
    plan_row = latest(identity.db, row.id, "PLAN")
    if plan_row is None:
        raise HTTPException(409, "CAMPAIGN_PLAN_NOT_READY")
    if body.plan_id != plan_row.id or body.expected_digest != plan_row.digest:
        raise HTTPException(409, "CAMPAIGN_REVIEWED_PLAN_CHANGED")
    existing = identity.db.scalar(
        select(CampaignExperiment).where(CampaignExperiment.plan_id == plan_row.id)
    )
    if existing:
        return {"experiment_id": str(existing.run_id), **view(row, runtime)}
    checked(identity, request, row, runtime)
    if runtime.state != "AWAITING_APPROVAL" or runtime.pending != "SUBMIT_EXPERIMENT":
        raise HTTPException(409, "CAMPAIGN_NOT_AWAITING_EXPERIMENT_REVIEW")
    plan = ExperimentPlan.model_validate(plan_row.payload)
    spec = objective(row)
    if runtime.experiments >= spec.budgets.experiments:
        raise HTTPException(409, "CAMPAIGN_EXPERIMENT_BUDGET_EXHAUSTED")
    refuse_oos_reuse(identity, row, plan.experiment)
    # Same real authenticated transaction, same Phase5 recent-MFA/quotas/risk/pin validation.
    experiment = create_experiment(plan.experiment, identity, request)
    identity.db.add(
        CampaignExperiment(
            owner_id=row.owner_id,
            campaign_id=row.id,
            plan_id=plan_row.id,
            run_id=UUID(experiment["id"]),
            ordinal=runtime.experiments,
        )
    )
    runtime.experiments += 1
    record(
        identity.db,
        row,
        runtime,
        "EXPERIMENT",
        {
            "experiment_id": experiment["id"],
            "request_key": plan.experiment.key,
            "plan_digest": digest(plan_row.payload),
        },
        plan_row.id,
    )
    transition(identity.db, row, runtime, "TESTING")
    runtime.lease_until, runtime.worker_token = None, None
    identity.audit(
        "campaign.experiment_handoff", entity_id=row.id, after={"experiment_id": experiment["id"]}
    )
    return {"experiment_id": experiment["id"], **view(row, runtime)}


@router.post("/{campaign_id}/gateway", status_code=202)
def gateway(
    campaign_id: UUID, body: GatewayAction, identity: FullIdentity, request: Request
) -> dict[str, Any]:
    privileged(identity)
    row, runtime = scoped(identity, campaign_id)
    checked(identity, request, row, runtime)
    spec = objective(row)
    if spec.mode != "AI_GATEWAY":
        raise HTTPException(409, "FIXTURE_CAMPAIGN_CANNOT_CLAIM_AI_INFERENCE")
    expected = "REQUEST_" + body.role
    if runtime.pending not in {expected, "ACCEPT_" + body.role}:
        raise HTTPException(409, "CAMPAIGN_GATEWAY_HANDOFF_NOT_READY")
    old = latest(identity.db, row.id, "GATEWAY_REQUEST")
    if runtime.pending == "ACCEPT_" + body.role and old:
        return {"request_id": old.payload["request_id"], **view(row, runtime)}
    question = (
        "Untrusted bounded research objective: " + spec.objective + ". No tools or code. "
        "Return a hypothesis; encode exactly one ParameterCandidate JSON object as test_plan[0]. "
        "Use only this authorized finite candidate domain: "
        + json.dumps(
            {
                "strategy": spec.template.strategy,
                "strategy_digest": spec.template.strategy_digest,
                "source": "AI_GATEWAY",
                "parameters": [p.model_dump(mode="json") for p in spec.search_space],
            }
        )
        if body.role == "RESEARCH"
        else "Critique research-only evidence; do not certify profit, policy or trading authority: "
        + json.dumps(latest(identity.db, row.id, "EVALUATION").payload)  # type: ignore[union-attr]
    )
    feedback = latest(identity.db, row.id, "FEEDBACK")
    evaluation = latest(identity.db, row.id, "EVALUATION")
    if body.role == "RESEARCH" and feedback and evaluation:
        question += " Approved training-only feedback (not independent OOS): " + json.dumps(
            {
                "decision": evaluation.payload["decision"],
                "reasons": evaluation.payload["reasons"],
                "follow_up": feedback.payload["reason"],
                "lineage": str(feedback.id),
            }
        )
    if len(question) > 4000:
        raise HTTPException(422, "CAMPAIGN_PROMPT_BUDGET_EXCEEDED")
    refs = [
        ContextReference(kind="strategy", id=spec.template.strategy),
        *[ContextReference(kind="dataset", id=str(p.dataset_id)) for p in spec.template.datasets],
    ]
    # Cached question evidence remains bound to Phase6's revalidated dataset/holdout scope.
    if body.role == "CRITIC":
        link = identity.db.scalar(
            select(CampaignExperiment)
            .where(CampaignExperiment.campaign_id == row.id)
            .order_by(CampaignExperiment.ordinal.desc())
            .limit(1)
        )
        if link is None:
            raise HTTPException(409, "CAMPAIGN_EVIDENCE_MISSING")
        refs.append(ContextReference(kind="experiment", id=str(link.run_id)))
    approval = runtime.approval
    if approval is None:
        raise HTTPException(409, "CAMPAIGN_AUTHORIZATION_REVOKED")
    output = submit_ai(
        RequestInput(
            key=f"campaign-{row.id.hex}-{runtime.iteration}-{body.role}",
            question=question,
            role=body.role,
            parameters=Generation(
                context_tokens=min(
                    8192,
                    approval["gateway_roles"][body.role]["model"]["capabilities"]["context_tokens"],
                )
            ),
            references=refs,
            allow_remote=body.allow_remote,
            cloud_cost_acknowledged=body.cloud_cost_acknowledged,
            processing_acknowledged=True,
            retain_structured_output=True,
        ),
        identity,
        request,
    )
    record(
        identity.db,
        row,
        runtime,
        "GATEWAY_REQUEST",
        {"request_id": str(output.id), "role": body.role},
    )
    runtime.pending = "ACCEPT_" + body.role
    identity.audit(
        "campaign.gateway_handoff",
        entity_id=row.id,
        after={"request_id": str(output.id), "role": body.role},
    )
    return {"request_id": str(output.id), **view(row, runtime)}


@router.post("/{campaign_id}/gateway/accept")
def accept_gateway(campaign_id: UUID, identity: FullIdentity, request: Request) -> dict[str, Any]:
    privileged(identity)
    row, runtime = scoped(identity, campaign_id)
    checked(identity, request, row, runtime)
    event = latest(identity.db, row.id, "GATEWAY_REQUEST")
    if event is None or runtime.pending != "ACCEPT_" + event.payload["role"]:
        raise HTTPException(409, "CAMPAIGN_GATEWAY_HANDOFF_NOT_READY")
    ai = identity.db.get(AIRequest, UUID(event.payload["request_id"]))
    if ai is None or ai.owner_id != row.owner_id:
        raise HTTPException(404, "CAMPAIGN_AI_REFERENCE_REFUSED")
    result = job_view(identity.db, ai, configured(request))
    if (
        result.state != "SUCCEEDED"
        or result.output is None
        or result.content_expired
        or not result.context_available
    ):
        raise HTTPException(409, "MODEL_UNAVAILABLE_OR_INFERENCE_NOT_ACCEPTED")
    try:
        if event.payload["role"] == "RESEARCH":
            proposal = HypothesisProposal.model_validate(result.output)
            if len(proposal.test_plan) != 1:
                raise ValueError("ONE_BOUNDED_CANDIDATE_REQUIRED")
            candidate = ParameterCandidate.model_validate_json(proposal.test_plan[0])
            admit_candidate(
                identity.db,
                row,
                runtime,
                StrategyHypothesis(
                    title=proposal.title,
                    rationale=proposal.hypothesis,
                    strategy=candidate.strategy,
                    strategy_digest=candidate.strategy_digest,
                    source="AI_GATEWAY",
                ),
                candidate,
            )
            plan_candidate(identity.db, row, runtime)
        else:
            critique = CritiqueReport.model_validate(result.output)
            finish_critique(
                identity.db,
                row,
                runtime,
                Critique(
                    summary=critique.summary, objections=critique.objections, source="AI_GATEWAY"
                ),
            )
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(422, "UNTRUSTED_CAMPAIGN_MODEL_OUTPUT_REFUSED") from exc
    identity.audit(
        "campaign.model_proposal_reviewed", entity_id=row.id, after={"request_id": str(ai.id)}
    )
    runtime.lease_until, runtime.worker_token = None, None
    return view(row, runtime)
