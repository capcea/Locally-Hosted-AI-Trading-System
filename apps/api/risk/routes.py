"""Owner/MFA risk configuration and account-scoped simulation control, never broker orders."""

from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import func, select

from apps.api.governance.routes import owned
from apps.api.identity.dependencies import (
    FullIdentity,
    Principal,
    require_owner,
    require_recent_mfa,
)
from apps.api.risk.schemas import (
    AccountStatus,
    Attestation,
    ContextInput,
    Emergency,
    PolicyInput,
    PolicyView,
    ProfileInput,
    ProfileView,
    WhatIf,
)
from packages.execution.contracts import Command, SimState
from packages.execution.engine import ACTIVE
from packages.execution.journal import execute, verify
from packages.execution.models import SimulationRun
from packages.persistence.models import (
    Firm,
    FirmPolicy,
    Instrument,
    Program,
    RiskProfile,
    Strategy,
    TradingAccount,
    utcnow,
)
from packages.risk.contracts import Context, Decision, EquityValues, Limits, PolicyTerms
from packages.risk.gateway import Gateway
from packages.risk.ledger import digest, lock_account, verify_ledger
from packages.risk.models import (
    AccountControl,
    EmergencyCommand,
    ProfileBinding,
    Reservation,
    RiskDecision,
    RiskLedger,
    RiskPolicy,
    RunContext,
)
from packages.risk.monitor import poll
from packages.risk.sizing import payoff_multiplier

router = APIRouter(prefix="/api/v1/risk", tags=["Simulated risk gateway"])


def owner(identity: Principal) -> None:
    require_owner(identity)
    require_recent_mfa(identity)


def account_for(identity: Principal, account_id: UUID) -> TradingAccount:
    record = owned(identity, TradingAccount, account_id)
    if not isinstance(record, TradingAccount):
        raise HTTPException(404, "Account not found")
    return lock_account(identity.db, account_id)


def control_for(identity: Principal, account: TradingAccount) -> AccountControl:
    control = identity.db.get(AccountControl, account.id)
    if control is None:
        control = AccountControl(
            account_id=account.id,
            owner_id=identity.user.id,
            account_revision=account.revision,
            manual_stop=True,
            automatic_stop=False,
            reasons=["OWNER_CONFIGURATION_REVIEW_REQUIRED"],
            state={},
            sequence=0,
            digest="0" * 64,
            revision=1,
        )
        identity.db.add(control)
        identity.db.flush()
    return control


def scope_key(identity: Principal, account: TradingAccount, body: ProfileInput) -> str:
    if body.scope == "ACCOUNT":
        if body.reference_id or body.asset_class:
            raise HTTPException(422, "Account scope takes no extra reference")
        return "ACCOUNT"
    if body.scope == "ASSET_CLASS":
        if not body.asset_class or body.reference_id:
            raise HTTPException(422, "Explicit asset-class scope required")
        return "ASSET_CLASS:" + body.asset_class
    if body.reference_id is None or body.asset_class:
        raise HTTPException(422, "Explicit owned scope reference required")
    models = {
        "STRATEGY": Strategy,
        "INSTRUMENT": Instrument,
        "FIRM": Firm,
        "PROGRAM_PHASE": Program,
    }
    record = owned(identity, models[body.scope], body.reference_id)
    if isinstance(record, Strategy) and record.account_id != account.id:
        raise HTTPException(409, "Strategy/account scope mismatch")
    program = identity.db.get(Program, account.program_id) if account.program_id else None
    if isinstance(record, Program):
        if program is None or program.id != record.id:
            raise HTTPException(409, "Exact account program required")
        return body.scope + ":" + str(record.id) + ":" + record.phase
    if isinstance(record, Firm) and (program is None or record.id != program.firm_id):
        raise HTTPException(409, "Exact account firm required")
    return body.scope + ":" + str(record.id)


def enforce_policy_caps(limits: Limits, terms: PolicyTerms) -> None:
    if limits.daily_loss_pct > terms.daily_loss_pct or limits.total_loss_pct > terms.total_loss_pct:
        raise HTTPException(409, "INTERNAL_LIMIT_EXCEEDS_VERIFIED_POLICY")


@router.post("/accounts/{account_id}/profiles", response_model=ProfileView, status_code=201)
def configure_profile(account_id: UUID, body: ProfileInput, identity: FullIdentity) -> ProfileView:
    owner(identity)
    account = account_for(identity, account_id)
    scope = scope_key(identity, account, body)
    policy = identity.db.scalar(
        select(RiskPolicy)
        .where(RiskPolicy.account_id == account.id)
        .order_by(RiskPolicy.version.desc())
        .limit(1)
    )
    if policy and policy.status == "VERIFIED":
        enforce_policy_caps(body.limits, PolicyTerms.model_validate(policy.terms))
    if body.profile_id:
        profile = owned(identity, RiskProfile, body.profile_id)
        if not isinstance(profile, RiskProfile) or profile.account_id != account.id:
            raise HTTPException(409, "Risk profile/account mismatch")
        for field in ("per_trade_pct", "daily_loss_pct", "total_loss_pct", "aggregate_risk_pct"):
            if getattr(profile, field) != getattr(body.limits, field):
                raise HTTPException(409, "BASE_RISK_PROFILE_VALUES_CHANGED")
    else:
        profile = RiskProfile(
            owner_id=identity.user.id,
            account_id=account.id,
            name=body.name,
            per_trade_pct=body.limits.per_trade_pct,
            daily_loss_pct=body.limits.daily_loss_pct,
            total_loss_pct=body.limits.total_loss_pct,
            aggregate_risk_pct=body.limits.aggregate_risk_pct,
            source="USER_ENTERED",
        )
        identity.db.add(profile)
        identity.db.flush()
    count = (
        identity.db.scalar(
            select(func.count())
            .select_from(ProfileBinding)
            .where(ProfileBinding.account_id == account.id)
        )
        or 0
    )
    if count >= 500:
        raise HTTPException(429, "Risk profile version quota")
    version = (
        identity.db.scalar(
            select(func.max(ProfileBinding.version)).where(
                ProfileBinding.account_id == account.id, ProfileBinding.scope_key == scope
            )
        )
        or 0
    ) + 1
    binding = ProfileBinding(
        owner_id=identity.user.id,
        account_id=account.id,
        profile_id=profile.id,
        profile_revision=profile.revision,
        scope_key=scope,
        version=version,
        limits=body.limits.model_dump(mode="json"),
    )
    identity.db.add(binding)
    control = control_for(identity, account)
    control.manual_stop, control.account_revision = True, account.revision
    control.revision += 1
    identity.db.flush()
    identity.audit(
        "risk.profile_version_created",
        entity_id=binding.id,
        after={"scope": scope, "version": version, "limits": binding.limits, "source": "SIMULATED"},
    )
    return ProfileView(
        id=binding.id, profile_id=profile.id, scope_key=scope, version=version, limits=body.limits
    )


@router.get("/accounts/{account_id}/profiles", response_model=list[ProfileView])
def list_profiles(account_id: UUID, identity: FullIdentity) -> list[ProfileView]:
    account_for(identity, account_id)
    return [
        ProfileView(
            id=b.id,
            profile_id=b.profile_id,
            scope_key=b.scope_key,
            version=b.version,
            limits=Limits.model_validate(b.limits),
        )
        for b in identity.db.scalars(
            select(ProfileBinding)
            .where(ProfileBinding.account_id == account_id)
            .order_by(ProfileBinding.version.desc())
            .limit(500)
        )
    ]


def policy_view(policy: RiskPolicy) -> PolicyView:
    return PolicyView(
        id=policy.id,
        version=policy.version,
        status=policy.status,
        verified_at=policy.verified_at,
        kind="PERSONAL" if policy.kind == "PERSONAL" else "PROP",
        firm_policy_id=policy.firm_policy_id,
        terms=PolicyTerms.model_validate(policy.terms),
        effective_at=policy.effective_at,
        expires_at=policy.expires_at,
        document_digest=policy.document_digest,
        source_references=policy.source_references,
    )


@router.post("/accounts/{account_id}/policies", response_model=PolicyView, status_code=201)
def create_policy(account_id: UUID, body: PolicyInput, identity: FullIdentity) -> PolicyView:
    owner(identity)
    account = account_for(identity, account_id)
    if body.expires_at <= body.effective_at or body.terms.currency != account.currency:
        raise HTTPException(422, "Invalid policy period/currency")
    if account.program_id is None:
        if body.kind != "PERSONAL" or body.firm_policy_id:
            raise HTTPException(409, "Explicit personal policy required")
    else:
        firm = owned(identity, FirmPolicy, body.firm_policy_id) if body.firm_policy_id else None
        if (
            body.kind != "PROP"
            or not isinstance(firm, FirmPolicy)
            or firm.account_id != account.id
            or firm.program_id != account.program_id
            or body.document_digest != firm.document_digest
            or set(body.source_references) != set(firm.source_references)
            or body.effective_at < firm.effective_at
            or body.expires_at > firm.expires_at
        ):
            raise HTTPException(409, "Exact prop policy/program/provenance required")
    version = (
        identity.db.scalar(
            select(func.max(RiskPolicy.version)).where(RiskPolicy.account_id == account.id)
        )
        or 0
    ) + 1
    if version > 100:
        raise HTTPException(429, "Risk policy version quota")
    policy = RiskPolicy(
        owner_id=identity.user.id,
        account_id=account.id,
        account_revision=account.revision,
        firm_policy_id=body.firm_policy_id,
        kind=body.kind,
        version=version,
        terms=body.terms.model_dump(mode="json"),
        effective_at=body.effective_at,
        expires_at=body.expires_at,
        source_references=body.source_references,
        document_digest=body.document_digest,
        status="UNVERIFIED",
    )
    identity.db.add(policy)
    control = control_for(identity, account)
    control.manual_stop = True
    control.revision += 1
    identity.db.flush()
    identity.audit(
        "risk.policy_version_created",
        entity_id=policy.id,
        after=policy_view(policy).model_dump(mode="json"),
    )
    return policy_view(policy)


@router.get("/accounts/{account_id}/policies", response_model=list[PolicyView])
def list_policies(account_id: UUID, identity: FullIdentity) -> list[PolicyView]:
    account_for(identity, account_id)
    return [
        policy_view(p)
        for p in identity.db.scalars(
            select(RiskPolicy)
            .where(RiskPolicy.account_id == account_id)
            .order_by(RiskPolicy.version.desc())
            .limit(100)
        )
    ]


@router.post("/policies/{policy_id}/attest", response_model=PolicyView)
def attest(policy_id: UUID, body: Attestation, identity: FullIdentity) -> PolicyView:
    owner(identity)
    policy = identity.db.scalar(
        select(RiskPolicy).where(
            RiskPolicy.id == policy_id, RiskPolicy.owner_id == identity.user.id
        )
    )
    if policy is None:
        raise HTTPException(404, "Policy not found")
    account = account_for(identity, policy.account_id)
    if body.document_digest != policy.document_digest:
        raise HTTPException(409, "Policy digest acknowledgement mismatch")
    if body.action == "VERIFY":
        if policy.account_revision != account.revision:
            raise HTTPException(409, "Policy account revision changed")
        seen_scopes: set[str] = set()
        for binding in identity.db.scalars(
            select(ProfileBinding)
            .where(ProfileBinding.account_id == account.id)
            .order_by(ProfileBinding.version.desc())
        ):
            if binding.scope_key in seen_scopes:
                continue
            seen_scopes.add(binding.scope_key)
            enforce_policy_caps(
                Limits.model_validate(binding.limits), PolicyTerms.model_validate(policy.terms)
            )
        if policy.kind == "PROP":
            firm = identity.db.get(FirmPolicy, policy.firm_policy_id)
            program = identity.db.get(Program, account.program_id) if account.program_id else None
            if (
                firm is None
                or firm.verification_status != "VERIFIED"
                or program is None
                or firm.account_revision != account.revision
                or firm.program_revision != program.revision
            ):
                raise HTTPException(409, "Exact external program policy not verified")
        policy.status = "VERIFIED"
        policy.verified_by, policy.verified_at = identity.user.id, utcnow()
    else:
        policy.status = "REVOKED"
    control = control_for(identity, account)
    control.manual_stop = True
    control.revision += 1
    identity.audit(
        "risk.policy_attestation",
        entity_id=policy.id,
        after={"status": policy.status, "document_digest": policy.document_digest},
    )
    return policy_view(policy)


def run_for(identity: Principal, run_id: UUID) -> SimulationRun:
    account_id = identity.db.scalar(
        select(SimulationRun.account_id).where(
            SimulationRun.id == run_id, SimulationRun.owner_id == identity.user.id
        )
    )
    if account_id is None:
        raise HTTPException(404, "Simulation not found")
    account_for(identity, account_id)
    run = identity.db.scalar(
        select(SimulationRun).where(SimulationRun.id == run_id).with_for_update()
    )
    if run is None or not verify(identity.db, run):
        raise HTTPException(409, "Simulation integrity failure")
    return run


@router.post("/runs/{run_id}/contexts", status_code=201)
def configure_context(
    run_id: UUID, body: ContextInput, identity: FullIdentity
) -> dict[str, object]:
    owner(identity)
    run = run_for(identity, run_id)
    state = SimState.model_validate(run.state)
    last = identity.db.scalar(
        select(RunContext)
        .where(RunContext.run_id == run.id)
        .order_by(RunContext.version.desc())
        .limit(1)
    )
    if last and (
        any(p.volume for p in state.positions.values())
        or any(o.state in ACTIVE | {"UNKNOWN"} for o in state.orders.values())
    ):
        prior = Context.model_validate(last.body)
        if prior.financial.model_dump(exclude={"fx"}) != body.financial.model_dump(exclude={"fx"}):
            raise HTTPException(409, "Cannot replace active execution assumptions")
        previous_fx = {(q.base, q.quote): q for q in prior.financial.fx}
        current_fx = {(q.base, q.quote): q for q in body.financial.fx}
        if set(previous_fx) != set(current_fx) or any(
            current_fx[pair].observed_at < old.observed_at
            or current_fx[pair].available_at < old.available_at
            for pair, old in previous_fx.items()
        ):
            raise HTTPException(409, "FX_EVIDENCE_CLOCK_OR_PATH_CHANGED")
        if prior.calendar and (
            body.calendar is None
            or body.calendar.observed_at < prior.calendar.observed_at
            or body.calendar.available_at < prior.calendar.available_at
        ):
            raise HTTPException(409, "CALENDAR_EVIDENCE_CLOCK_REVERSED")
    if last and last.version >= 100:
        raise HTTPException(429, "Context version quota")
    if body.financial.payoff in {"LINEAR_CONTRACT", "LINEAR_TICK"}:
        try:
            payoff_multiplier(state.spec, body.financial, state.clock)
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
    context = RunContext(
        owner_id=identity.user.id,
        run_id=run.id,
        version=last.version + 1 if last else 1,
        spec_digest=digest(state.spec.model_dump(mode="json")),
        body=body.model_dump(mode="json"),
    )
    identity.db.add(context)
    control = control_for(identity, account_for(identity, run.account_id))
    control.manual_stop = True
    control.revision += 1
    identity.db.flush()
    identity.audit(
        "risk.context_version_created",
        entity_id=context.id,
        after={"run_id": str(run.id), "spec_digest": context.spec_digest, "source": "SIMULATED"},
    )
    return {
        "id": str(context.id),
        "version": context.version,
        "context": context.body,
        "spec_digest": context.spec_digest,
    }


@router.get("/runs/{run_id}/contexts")
def get_contexts(run_id: UUID, identity: FullIdentity) -> list[dict[str, object]]:
    run_for(identity, run_id)
    return [
        {"id": str(c.id), "version": c.version, "context": c.body, "spec_digest": c.spec_digest}
        for c in identity.db.scalars(
            select(RunContext)
            .where(RunContext.run_id == run_id)
            .order_by(RunContext.version.desc())
            .limit(100)
        )
    ]


@router.get("/accounts/{account_id}/status", response_model=AccountStatus)
def status(account_id: UUID, identity: FullIdentity) -> AccountStatus:
    account = account_for(identity, account_id)
    control = identity.db.get(AccountControl, account_id)
    ledger_verified = verify_ledger(identity.db, control) if control else False
    data_verified = bool(control and ledger_verified and control.state.get("data_verified") is True)
    values = control.state.get("values") if control and data_verified else None
    return AccountStatus(
        account_id=account_id,
        currency=account.currency,
        configured=control is not None,
        ledger_verified=ledger_verified,
        data_verified=data_verified,
        manual_stop=control.manual_stop if control else True,
        automatic_stop=control.automatic_stop if control else False,
        reasons=control.reasons if control else ["RISK_CONFIGURATION_REQUIRED"],
        revision=control.revision if control else 1,
        monitor_at=control.monitor_at if control else None,
        clock=control.clock if control else None,
        values=EquityValues.model_validate(values) if values else None,
        daily_headroom=Decimal(str(control.state["daily_headroom"]))
        if control and data_verified and "daily_headroom" in control.state
        else None,
        total_headroom=Decimal(str(control.state["total_headroom"]))
        if control and data_verified and "total_headroom" in control.state
        else None,
        ledger_sequence=control.sequence if control else 0,
        ledger_digest=control.digest if control else "0" * 64,
    )


@router.post("/accounts/{account_id}/monitor", response_model=AccountStatus)
def monitor_now(account_id: UUID, identity: FullIdentity) -> AccountStatus:
    owner(identity)
    account = account_for(identity, account_id)
    reasons = poll(identity.db, account)
    identity.audit("risk.monitor_checked", entity_id=account_id, after={"reasons": reasons})
    return status(account_id, identity)


@router.post("/what-if", response_model=Decision)
def what_if(body: WhatIf, identity: FullIdentity) -> Decision:
    if identity.user.role == "VIEWER":
        raise HTTPException(403, "Read-only role")
    run = run_for(identity, body.run_id)
    command = Command(key="what-if-" + uuid4().hex, action="SUBMIT", at=body.at, order=body.order)
    gateway = Gateway(identity.db, run, identity.key, command, identity.correlation_id)
    result, _, _ = gateway.assess(
        body.order, SimState.model_validate(run.state), body.at, auto=body.auto_size
    )
    gateway.record(result, body.at, ":what-if", enforce=False)
    identity.audit(
        "risk.what_if_calculated", entity_id=run.id, after=result.model_dump(mode="json")
    )
    return result


@router.get("/accounts/{account_id}/decisions")
def decisions(
    account_id: UUID,
    identity: FullIdentity,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[dict[str, object]]:
    account_for(identity, account_id)
    return [
        {
            "id": str(r.id),
            "run_id": str(r.run_id),
            "key": r.command_key,
            "timestamp": r.timestamp.isoformat(),
            "result": r.result,
        }
        for r in identity.db.scalars(
            select(RiskDecision)
            .where(RiskDecision.account_id == account_id)
            .order_by(RiskDecision.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ]


@router.get("/accounts/{account_id}/reservations")
def reservations(
    account_id: UUID,
    identity: FullIdentity,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[dict[str, object]]:
    account_for(identity, account_id)
    return [
        {
            "order_id": str(r.order_id),
            "run_id": str(r.run_id),
            "amount": str(r.amount),
            "margin": str(r.margin),
            "state": r.state,
            "group": r.group,
            "strategy": r.strategy,
        }
        for r in identity.db.scalars(
            select(Reservation)
            .where(Reservation.account_id == account_id)
            .order_by(Reservation.order_id)
            .offset(offset)
            .limit(limit)
        )
    ]


@router.get("/accounts/{account_id}/ledger")
def ledger(
    account_id: UUID,
    identity: FullIdentity,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[dict[str, object]]:
    account_for(identity, account_id)
    return [
        {
            "sequence": r.sequence,
            "timestamp": r.timestamp.isoformat(),
            "payload": r.payload,
            "digest": r.digest,
            "previous_digest": r.previous_digest,
        }
        for r in identity.db.scalars(
            select(RiskLedger)
            .where(RiskLedger.account_id == account_id)
            .order_by(RiskLedger.sequence.desc())
            .offset(offset)
            .limit(limit)
        )
    ]


@router.post("/accounts/{account_id}/emergency")
def emergency(
    account_id: UUID, body: Emergency, identity: FullIdentity, response: Response
) -> dict[str, Any]:
    owner(identity)
    account = account_for(identity, account_id)
    control = control_for(identity, account)
    requested = digest(body.model_dump(mode="json"))
    previous = identity.db.scalar(
        select(EmergencyCommand).where(
            EmergencyCommand.account_id == account_id, EmergencyCommand.key == body.key
        )
    )
    if previous:
        if previous.request_digest != requested:
            raise HTTPException(409, "EMERGENCY_IDEMPOTENCY_CONFLICT")
        return {
            **previous.response,
            "original_receipt": previous.response,
            "current_control_revision": control.revision,
            "manual_stop": control.manual_stop,
            "automatic_stop": control.automatic_stop,
        }
    result: dict[str, Any] = {
        "source": "SIMULATED",
        "external_positions_closed": False,
        "action": body.action,
        "completed": True,
        "remaining_positions": 0,
    }
    if body.action != "STOP_NEW_ENTRIES" and body.expected_revision != control.revision:
        raise HTTPException(409, "RISK_CONTROL_REVISION_CHANGED")
    if body.action == "CLEAR_STOP":
        reasons = poll(identity.db, account)
        if reasons and reasons != ["NO_SIMULATED_RUN"]:
            response.status_code = 409
            result.update({"completed": False, "reasons": reasons})
        else:
            control.manual_stop, control.automatic_stop = False, False
            control.reasons = []
    else:
        control.manual_stop = True
        if body.action == "FLATTEN":
            errors = []
            for run in identity.db.scalars(
                select(SimulationRun)
                .where(SimulationRun.account_id == account.id)
                .order_by(SimulationRun.id)
                .with_for_update()
            ):
                state = SimState.model_validate(run.state)
                operations: list[tuple[str, UUID, Decimal | None]] = [
                    ("CANCEL", o.id, None) for o in state.orders.values() if o.state in ACTIVE
                ]
                operations += [
                    ("CLOSE", p.id, p.volume) for p in state.positions.values() if p.volume > 0
                ]
                for action, target, volume in operations:
                    try:
                        with identity.db.begin_nested():
                            state = SimState.model_validate(run.state)
                            command = Command.model_validate(
                                {
                                    "key": body.key + ":" + str(target),
                                    "action": action,
                                    "at": max(state.clock, control.clock)
                                    if control.clock
                                    else state.clock,
                                    "target_id": target,
                                    "volume": volume,
                                }
                            )
                            execute(
                                identity.db,
                                run,
                                command,
                                identity.correlation_id,
                                risk_key=identity.key,
                            )
                            identity.audit(
                                "risk.simulated_flatten_step",
                                entity_id=run.id,
                                after={
                                    "target": str(target),
                                    "action": action,
                                    "source": "SIMULATED",
                                },
                            )
                    except ValueError as error:
                        errors.append(str(error))
                state = SimState.model_validate(run.state)
                result["remaining_positions"] += sum(
                    1 for p in state.positions.values() if p.volume > 0
                )
                if any(o.state == "UNKNOWN" for o in state.orders.values()):
                    errors.append("UNKNOWN_ORDERS_RETAINED")
            result["completed"] = not errors and result["remaining_positions"] == 0
            result["reasons"] = sorted(set(errors))
    control.revision += 1
    result["revision"] = control.revision
    result["manual_stop"] = control.manual_stop
    result["automatic_stop"] = control.automatic_stop
    identity.db.add(
        EmergencyCommand(
            owner_id=identity.user.id,
            account_id=account_id,
            key=body.key,
            request_digest=requested,
            response=result,
        )
    )
    identity.audit("risk.emergency_" + body.action.lower(), entity_id=account_id, after=result)
    return result
