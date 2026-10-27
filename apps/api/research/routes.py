"""Owner-MFA research orchestration; immutable results and separate one-use holdout release."""

import json
from datetime import timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import func, select

from apps.api.governance.routes import owned
from apps.api.identity.dependencies import (
    FullIdentity,
    Principal,
    require_owner,
    require_recent_mfa,
)
from apps.api.market.routes import object_store
from packages.execution.journal import digest
from packages.market.models import MarketDataset
from packages.persistence.models import TradingAccount
from packages.research.contracts import DSRRequest, ExperimentInput, ReleaseInput, SealInput
from packages.research.data import frozen_digest, pinned
from packages.research.models import (
    HoldoutRelease,
    HoldoutSeal,
    ResearchJob,
    ResearchResult,
    ResearchRun,
    ResearchTrial,
)
from packages.research.strategies import NAMES, definition
from packages.risk.models import AccountControl, ProfileBinding
from packages.risk.policy import applicable_policy, profiles, strictest

router = APIRouter(prefix="/api/v1/research", tags=["Quantitative research — SIMULATED"])


def privileged(identity: Principal) -> None:
    require_owner(identity)
    require_recent_mfa(identity)


def run_for(identity: Principal, run_id: UUID) -> ResearchRun:
    row = identity.db.scalar(
        select(ResearchRun).where(
            ResearchRun.id == run_id, ResearchRun.owner_id == identity.user.id
        )
    )
    if row is None:
        raise HTTPException(404, "Research experiment not found")
    return row


def view(db: Any, run: ResearchRun) -> dict[str, Any]:
    job = db.scalar(select(ResearchJob).where(ResearchJob.run_id == run.id))
    result = db.get(ResearchResult, run.id)
    return {
        "id": str(run.id),
        "name": run.plan["name"],
        "strategy": run.plan["strategy"],
        "phase": run.plan["phase"],
        "engine": run.plan["engine"],
        "created_at": run.created_at,
        "job": {
            "id": str(job.id),
            "state": job.state,
            "progress": job.progress,
            "attempts": job.attempts,
            "error": job.error,
        }
        if job
        else None,
        "result": result.summary if result else None,
        "source": "SIMULATED",
        "paper_eligible": False,
    }


@router.get("/strategies")
def strategies(identity: FullIdentity) -> list[dict[str, Any]]:
    return [definition(name) for name in NAMES]


def validate_plan(plan: ExperimentInput, identity: Principal, request: Request) -> dict[str, Any]:
    if definition(plan.strategy)["digest"] != plan.strategy_digest:
        raise ValueError("STRATEGY_VERSION_PIN_CHANGED")
    account = owned(identity, TradingAccount, plan.source_account_id)
    if (
        not isinstance(account, TradingAccount)
        or account.initial_capital != plan.assumptions.synthetic_initial_balance
        or account.currency != plan.assumptions.account_currency
    ):
        raise ValueError("SOURCE_ACCOUNT_BALANCE_OR_CURRENCY_MISMATCH")
    control = identity.db.get(AccountControl, account.id)
    if control is None or control.manual_stop or control.automatic_stop:
        raise ValueError("REVIEW_SOURCE_RISK_CONFIGURATION_AND_STOP")
    policy = applicable_policy(identity.db, account, plan.chronology.start)
    if not policy.terms.get("automation_permitted"):
        raise ValueError("AUTOMATED_RESEARCH_REQUIRES_EXPLICIT_VERIFIED_POLICY_PERMISSION")
    if (
        applicable_policy(identity.db, account, plan.chronology.end - timedelta(microseconds=1)).id
        != policy.id
    ):
        raise ValueError("POLICY_DOES_NOT_COVER_EXPERIMENT")
    scopes = set(
        identity.db.scalars(
            select(ProfileBinding.scope_key).where(ProfileBinding.account_id == account.id)
        )
    )
    bindings = profiles(identity.db, account.id, scopes | {"ACCOUNT"})
    pinned(identity.db, plan, identity.user.id, object_store(request), read=False)
    from packages.research.approval import software_manifest

    return {
        "software": software_manifest(),
        "account_revision": account.revision,
        "policy_id": str(policy.id),
        "policy_digest": digest(policy.terms),
        "profiles": [str(p.id) for p in bindings],
        "limits": strictest(bindings).model_dump(mode="json"),
        "owner_mfa_at": identity.session.mfa_at.isoformat() if identity.session.mfa_at else None,
        "acknowledgement_digest": frozen_digest(plan),
    }


@router.post("/experiments", status_code=202)
def create(plan: ExperimentInput, identity: FullIdentity, request: Request) -> dict[str, Any]:
    privileged(identity)
    fingerprint = digest(plan.model_dump(mode="json"))
    previous = identity.db.scalar(
        select(ResearchRun).where(
            ResearchRun.owner_id == identity.user.id, ResearchRun.key == plan.key
        )
    )
    if previous:
        if previous.request_digest != fingerprint:
            raise HTTPException(409, "EXPERIMENT_IDEMPOTENCY_CONFLICT")
        return view(identity.db, previous)
    count = (
        identity.db.scalar(
            select(func.count())
            .select_from(ResearchRun)
            .where(ResearchRun.owner_id == identity.user.id)
        )
        or 0
    )
    if count >= 100:
        raise HTTPException(429, "Research experiment quota reached")
    if plan.phase == "FINAL_HOLDOUT" and plan.holdout_release_id is None:
        raise HTTPException(409, "FINAL_HOLDOUT_RELEASE_REQUIRED")
    try:
        snapshot = validate_plan(plan, identity, request)
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    run = ResearchRun(
        id=uuid4(),
        owner_id=identity.user.id,
        source_account_id=plan.source_account_id,
        key=plan.key,
        request_digest=fingerprint,
        plan=plan.model_dump(mode="json"),
        approval_snapshot=snapshot,
        family_digest=digest(
            {
                "datasets": [str(p.dataset_id) for p in plan.datasets],
                "protocol": plan.chronology.model_dump(mode="json"),
                "source_account": str(plan.source_account_id),
            }
        ),
        release_id=plan.holdout_release_id,
    )
    identity.db.add(run)
    identity.db.flush()
    specifications = []
    folds_count = (
        plan.chronology.walk_forward_folds if plan.validation_mode == "WALK_FORWARD" else 1
    )
    for fold in range(folds_count):
        for parameters in plan.parameters:
            for stress in plan.cost_multipliers:
                specifications.append(
                    {
                        "parameters": parameters.model_dump(mode="json"),
                        "cost_multiplier": str(stress),
                        "strategy_digest": plan.strategy_digest,
                        "phase": plan.phase,
                        "fold": fold,
                        "role": "TRAIN" if plan.validation_mode == "WALK_FORWARD" else "DIRECT",
                    }
                )
        if plan.validation_mode == "WALK_FORWARD":
            specifications.append(
                {
                    "fold": fold,
                    "role": "CONDITIONAL_OOS",
                    "candidate_digest": digest(
                        [p.model_dump(mode="json") for p in plan.parameters]
                    ),
                    "selection_rule": "frozen maximum train net P&L; no OOS tuning",
                }
            )
    for ordinal, specification in enumerate(specifications):
        identity.db.add(
            ResearchTrial(
                owner_id=identity.user.id,
                run_id=run.id,
                ordinal=ordinal,
                specification=specification,
            )
        )
    identity.db.add(ResearchJob(owner_id=identity.user.id, run_id=run.id, state="QUEUED"))
    identity.db.flush()
    identity.audit(
        "research.experiment_submitted",
        entity_id=run.id,
        after={
            "request_digest": fingerprint,
            "family": run.family_digest,
            "trials": len(plan.parameters) * len(plan.cost_multipliers),
            "source": "SIMULATED",
        },
    )
    return view(identity.db, run)


@router.get("/experiments")
def experiments(
    identity: FullIdentity, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)
) -> list[dict[str, Any]]:
    return [
        view(identity.db, r)
        for r in identity.db.scalars(
            select(ResearchRun)
            .where(ResearchRun.owner_id == identity.user.id)
            .order_by(ResearchRun.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ]


@router.get("/experiments/{run_id}")
def experiment(run_id: UUID, identity: FullIdentity) -> dict[str, Any]:
    return view(identity.db, run_for(identity, run_id))


@router.get("/experiments/{run_id}/provenance")
def provenance(run_id: UUID, identity: FullIdentity) -> dict[str, Any]:
    run = run_for(identity, run_id)
    trials = identity.db.scalar(
        select(func.count())
        .select_from(ResearchTrial)
        .join(ResearchRun, ResearchTrial.run_id == ResearchRun.id)
        .where(
            ResearchRun.owner_id == identity.user.id, ResearchRun.family_digest == run.family_digest
        )
    )
    return {
        "plan": run.plan,
        "approval_snapshot": run.approval_snapshot,
        "family_trial_count": trials,
        "owner_total_trial_count": identity.db.scalar(
            select(func.count())
            .select_from(ResearchTrial)
            .where(ResearchTrial.owner_id == identity.user.id)
        ),
        "independent_trials_estimated": None,
        "selection_bias_warning": (
            "All attempted parameter sets count, including failed/cancelled runs. "
            "Correlated trials are not assumed independent."
        ),
        "final_holdout_untouched_certified": False,
    }


@router.post("/experiments/{run_id}/cancel")
def cancel(run_id: UUID, identity: FullIdentity) -> dict[str, Any]:
    privileged(identity)
    run = run_for(identity, run_id)
    job = identity.db.scalar(
        select(ResearchJob).where(ResearchJob.run_id == run.id).with_for_update()
    )
    if job is None:
        raise HTTPException(404, "Job not found")
    if job.state not in {"SUCCEEDED", "FAILED", "CANCELLED"}:
        job.cancel_requested = True
        if job.state in {"QUEUED", "RETRY"}:
            job.state = "CANCELLED"
        identity.audit("research.cancel_requested", entity_id=run.id, after={"state": job.state})
    return view(identity.db, run)


def result_for(run_id: UUID, identity: Principal, request: Request) -> dict[str, Any]:
    run_for(identity, run_id)
    result = identity.db.get(ResearchResult, run_id)
    if result is None:
        raise HTTPException(409, "No complete published result")
    body = json.loads(object_store(request).get(result.artifact))
    return dict(body)


@router.get("/experiments/{run_id}/results")
def results(
    run_id: UUID,
    identity: FullIdentity,
    request: Request,
    section: Literal[
        "summary", "equity", "trades", "fills", "signals", "replay", "exposure", "walk_forward"
    ] = "summary",
    trial: int = Query(0, ge=0, le=23),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    body = result_for(run_id, identity, request)
    if trial >= len(body["trials"]):
        raise HTTPException(404, "Trial not found")
    selected = body["trials"][trial]
    if section == "summary":
        return {
            "engine": body["engine"],
            "source": body["source"],
            "phase": body["phase"],
            "warnings": body["warnings"],
            "trials": [
                {
                    k: v
                    for k, v in t.items()
                    if k
                    in {
                        "ordinal",
                        "parameters",
                        "cost_multiplier",
                        "metrics",
                        "approximate_net",
                        "transaction_costs",
                        "risk_validated",
                        "paper_eligible",
                        "source",
                    }
                }
                for t in body["trials"]
            ],
        }
    values = selected.get(section, [])
    if isinstance(values, dict):
        return {"items": values, "source": "SIMULATED"}
    return {
        "items": values[offset : offset + limit],
        "offset": offset,
        "limit": limit,
        "total": len(values),
        "source": "SIMULATED",
    }


@router.get("/experiments/{run_id}/compare/{other_id}")
def compare(
    run_id: UUID, other_id: UUID, identity: FullIdentity, request: Request
) -> dict[str, Any]:
    left = run_for(identity, run_id)
    right = run_for(identity, other_id)

    def conditions(run: ResearchRun) -> str:
        plan = dict(run.plan)
        for name in ("key", "name", "strategy", "strategy_digest", "parameters"):
            plan.pop(name, None)
        return digest(plan)

    risk_keys = ("account_revision", "policy_id", "profiles", "limits", "software")
    if conditions(left) != conditions(right) or {
        k: left.approval_snapshot[k] for k in risk_keys
    } != {k: right.approval_snapshot[k] for k in risk_keys}:
        raise HTTPException(409, "Comparison requires matched data/chronology/risk/cost conditions")
    return {
        "left": results(run_id, identity, request, "summary", 0, 0, 100),
        "right": results(other_id, identity, request, "summary", 0, 0, 100),
        "warning": (
            "Matched conditions do not eliminate selection bias; ML/LLM filtering NOT IMPLEMENTED."
        ),
    }


@router.post("/holdouts", status_code=201)
def seal(body: SealInput, identity: FullIdentity) -> dict[str, Any]:
    privileged(identity)
    dataset = identity.db.scalar(
        select(MarketDataset).where(
            MarketDataset.id == body.dataset_id, MarketDataset.owner_id == identity.user.id
        )
    )
    if (
        not isinstance(dataset, MarketDataset)
        or dataset.status != "VALID"
        or not dataset.manifest_sha256
    ):
        raise HTTPException(409, "Seal requires an admitted immutable dataset")
    row = HoldoutSeal(
        owner_id=identity.user.id,
        dataset_id=dataset.id,
        manifest_sha256=dataset.manifest_sha256,
        reason=body.reason,
    )
    identity.db.add(row)
    identity.db.flush()
    identity.audit(
        "research.holdout_sealed",
        entity_id=row.id,
        after={
            "dataset_id": str(dataset.id),
            "untouched_certified": False,
            "prior_exposure": "UNKNOWN",
        },
    )
    return {"id": str(row.id), "dataset_id": str(row.dataset_id), "untouched_certified": False}


@router.get("/holdouts")
def seals(identity: FullIdentity) -> list[dict[str, Any]]:
    return [
        {
            "id": str(s.id),
            "dataset_id": str(s.dataset_id),
            "prior_exposure": s.prior_exposure,
            "untouched_certified": False,
        }
        for s in identity.db.scalars(
            select(HoldoutSeal).where(HoldoutSeal.owner_id == identity.user.id).limit(100)
        )
    ]


@router.post("/holdouts/{seal_id}/release", status_code=201)
def release(
    seal_id: UUID, body: ReleaseInput, identity: FullIdentity, request: Request
) -> dict[str, Any]:
    privileged(identity)
    row = identity.db.get(HoldoutSeal, seal_id)
    if row is None or row.owner_id != identity.user.id:
        raise HTTPException(404, "Holdout not found")
    from packages.research.access import seal_for

    if body.experiment.phase != "FINAL_HOLDOUT":
        raise HTTPException(409, "Final event experiment required")
    for pin in body.experiment.datasets:
        dataset = identity.db.get(MarketDataset, pin.dataset_id)
        actual_seal = (
            seal_for(identity.db, dataset)
            if dataset and dataset.owner_id == identity.user.id
            else None
        )
        if actual_seal is None or actual_seal.id != row.id:
            raise HTTPException(409, "All final inputs must belong to the protected interval")
    if identity.db.scalar(
        select(ResearchRun.id).where(
            ResearchRun.owner_id == identity.user.id, ResearchRun.key == body.experiment.key
        )
    ):
        raise HTTPException(409, "Use a new experiment key for the frozen final evaluation")
    if identity.db.scalar(select(HoldoutRelease).where(HoldoutRelease.seal_id == seal_id)):
        raise HTTPException(409, "Final holdout already released; repeated tuning is prohibited")
    released = HoldoutRelease(
        owner_id=identity.user.id, seal_id=row.id, frozen_digest=frozen_digest(body.experiment)
    )
    identity.db.add(released)
    identity.db.flush()
    try:
        validate_plan(
            body.experiment.model_copy(update={"holdout_release_id": released.id}),
            identity,
            request,
        )
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    identity.audit(
        "research.final_holdout_released",
        entity_id=released.id,
        after={
            "seal_id": str(row.id),
            "frozen_digest": released.frozen_digest,
            "single_use": True,
            "untouched_certified": False,
        },
    )
    return {
        "id": str(released.id),
        "frozen_digest": released.frozen_digest,
        "untouched_certified": False,
    }


@router.post("/experiments/{run_id}/statistics/deflated-sharpe")
def dsr(run_id: UUID, body: DSRRequest, identity: FullIdentity, request: Request) -> dict[str, Any]:
    privileged(identity)
    result = result_for(run_id, identity, request)
    if body.trial >= len(result["trials"]):
        raise HTTPException(404, "Trial not found")
    observations = result["trials"][body.trial].get("metrics", {}).get("daily_returns", [])
    from statistics import mean, stdev

    from packages.research.statistics import deflated_sharpe

    answer: dict[str, Any]
    if (
        len(observations) < 30
        or not stdev(observations)
        or result["trials"][body.trial].get("metrics", {}).get("ratios_reason") is not None
    ):
        answer = {"value": None, "reason": "INSUFFICIENT_NONDEGENERATE_DAILY_RETURNS"}
    else:
        average = mean(observations)
        m2 = mean((r - average) ** 2 for r in observations)
        skew = mean((r - average) ** 3 for r in observations) / (m2**1.5)
        kurtosis = mean((r - average) ** 4 for r in observations) / (m2 * m2)
        answer = deflated_sharpe(
            average / stdev(observations),
            float(body.trial_sharpe_variance),
            body.independent_trials,
            len(observations),
            skew,
            kurtosis,
        )
    answer.update(
        {
            "source": "SIMULATED",
            "independence_model_is_user_asserted": True,
            "paper_eligible": False,
            "assumptions": body.model_dump(mode="json"),
        }
    )
    identity.audit("research.deflated_sharpe_evaluated", entity_id=run_id, after=answer)
    return answer
