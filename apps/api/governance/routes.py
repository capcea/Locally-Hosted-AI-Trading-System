"""Account-scoped metadata repositories with transactional governance auditing."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from apps.api.governance import schemas
from apps.api.governance.schemas import (
    AuditVerification,
    AuditView,
    Eligibility,
    PolicyVerification,
    RecordBody,
    RecordPage,
    RecordView,
    Review,
)
from apps.api.identity.dependencies import (
    FullIdentity,
    Principal,
    require_owner,
    require_recent_mfa,
)
from packages.persistence.audit import verify_chain
from packages.persistence.models import (
    ApprovalRequest,
    AuditEvent,
    BrokerConnection,
    Firm,
    FirmPolicy,
    Incident,
    Instrument,
    Program,
    ResearchExperiment,
    RiskProfile,
    Scoped,
    Strategy,
    StrategyVersion,
    TradingAccount,
    Venue,
    utcnow,
)

router = APIRouter(prefix="/api/v1", tags=["Governance"])
RECORDS: dict[str, type[Scoped]] = {
    "firms": Firm,
    "programs": Program,
    "venues": Venue,
    "instruments": Instrument,
    "accounts": TradingAccount,
    "brokers": BrokerConnection,
    "risk-profiles": RiskProfile,
    "policies": FirmPolicy,
    "strategies": Strategy,
    "strategy-versions": StrategyVersion,
    "experiments": ResearchExperiment,
    "approvals": ApprovalRequest,
    "incidents": Incident,
}
REFERENCES: dict[str, type[Scoped]] = {
    "firm_id": Firm,
    "program_id": Program,
    "venue_id": Venue,
    "account_id": TradingAccount,
    "strategy_id": Strategy,
    "strategy_version_id": StrategyVersion,
}
SCHEMAS: dict[str, type[schemas.RecordInput]] = {
    "firms": schemas.FirmInput,
    "programs": schemas.ProgramInput,
    "venues": schemas.VenueInput,
    "instruments": schemas.InstrumentInput,
    "accounts": schemas.AccountInput,
    "brokers": schemas.BrokerInput,
    "risk-profiles": schemas.RiskInput,
    "policies": schemas.PolicyInput,
    "strategies": schemas.StrategyInput,
    "strategy-versions": schemas.VersionInput,
    "experiments": schemas.ExperimentInput,
    "approvals": schemas.ApprovalInput,
    "incidents": schemas.IncidentInput,
}


def model_for(kind: str) -> type[Scoped]:
    if kind not in RECORDS:
        raise HTTPException(404, "Record type not found")
    return RECORDS[kind]


def owned(identity: Principal, model: type[Scoped], record_id: UUID) -> Scoped:
    query = select(model).where(model.id == record_id, model.owner_id == identity.user.id)
    # Immutable versions cannot be updated/deleted by this role. FOR UPDATE would require the
    # very UPDATE privilege deliberately withheld from it; a normal read is stable here.
    if model is not StrategyVersion:
        query = query.with_for_update()
    row = identity.db.scalar(query)
    if row is None:
        raise HTTPException(404, "Record not found")
    return row


def record_view(kind: str, record: Scoped) -> RecordView:
    # Only the corresponding validated public input fields are exposed.
    values = {column.name: getattr(record, column.name) for column in record.__table__.columns}
    schema = SCHEMAS[kind]
    data = {"kind": kind, **{k: v for k, v in values.items() if k in schema.model_fields}}
    state = getattr(record, "verification_status", getattr(record, "status", None))
    return RecordView.model_validate(
        dict(
            id=record.id,
            owner_id=record.owner_id,
            revision=record.revision,
            created_at=record.created_at,
            updated_at=record.updated_at,
            data=data,
            state=state,
            policy_attestation=(
                dict(
                    verified_at=record.verified_at,
                    verified_by=record.verified_by,
                    account_revision=record.account_revision,
                    program_revision=record.program_revision,
                )
                if isinstance(record, FirmPolicy)
                else None
            ),
        )
    )


def writable(identity: Principal) -> None:
    if identity.user.role not in {"OWNER", "OPERATOR"}:
        raise HTTPException(403, "This role cannot mutate management records")


def validate_links(body: RecordBody, identity: Principal) -> None:
    for field, model in REFERENCES.items():
        value = getattr(body, field, None)
        if value is not None:
            linked = owned(identity, model, value)
            if isinstance(linked, TradingAccount) and linked.archived:
                raise HTTPException(409, "Account is archived")
    if body.kind == "policies":
        account = owned(identity, TradingAccount, body.account_id)
        if not isinstance(account, TradingAccount) or account.program_id != body.program_id:
            raise HTTPException(409, "Policy program must match the exact account program")
    if body.kind == "approvals":
        version = owned(identity, StrategyVersion, body.strategy_version_id)
        if not isinstance(version, StrategyVersion):
            raise HTTPException(409, "Strategy version required")
        strategy = owned(identity, Strategy, version.strategy_id)
        if not isinstance(strategy, Strategy) or strategy.account_id != body.account_id:
            raise HTTPException(409, "Approval must match the strategy account")


@router.get("/records/{kind}", response_model=RecordPage)
def list_records(
    kind: str,
    identity: FullIdentity,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    q: str = Query("", max_length=80),
    account_id: UUID | None = None,
) -> RecordPage:
    model = model_for(kind)
    query = select(model).where(model.owner_id == identity.user.id)
    if model is TradingAccount:
        from packages.research.models import ResearchAccount

        query = query.where(TradingAccount.id.not_in(select(ResearchAccount.account_id)))
    if q:
        query = query.where(model.name.contains(q, autoescape=True))
    if account_id is not None:
        owned(identity, TradingAccount, account_id)
        if not hasattr(model, "account_id"):
            raise HTTPException(400, "This record type has no direct account filter")
        query = query.where(model.account_id == account_id)
    total = identity.db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = identity.db.scalars(
        query.order_by(model.created_at.desc(), model.id).offset(offset).limit(limit)
    )
    return RecordPage(
        items=[record_view(kind, row) for row in rows], offset=offset, limit=limit, total=total
    )


@router.get("/records/{kind}/{record_id}", response_model=RecordView)
def get_record(kind: str, record_id: UUID, identity: FullIdentity) -> RecordView:
    return record_view(kind, owned(identity, model_for(kind), record_id))


@router.post("/records/{kind}", response_model=RecordView, status_code=201)
def create_record(kind: str, body: RecordBody, identity: FullIdentity) -> RecordView:
    writable(identity)
    model = model_for(kind)
    if body.kind != kind:
        raise HTTPException(422, "Record discriminator must match the path")
    validate_links(body, identity)
    values = body.model_dump(exclude={"kind"})
    if body.kind == "firms" and body.website:
        values["website"] = str(body.website)
    if body.kind == "policies":
        values["source_references"] = [str(url) for url in body.source_references]
        values["account_revision"] = owned(identity, TradingAccount, body.account_id).revision
        values["program_revision"] = owned(identity, Program, body.program_id).revision
    record = model(owner_id=identity.user.id, **values)
    identity.db.add(record)
    identity.db.flush()
    view = record_view(kind, record)
    identity.audit(f"{kind}.created", entity_id=record.id, after=view.model_dump(mode="json"))
    return view


@router.put("/records/{kind}/{record_id}", response_model=RecordView)
def update_record(
    kind: str,
    record_id: UUID,
    body: RecordBody,
    identity: FullIdentity,
    expected_revision: Annotated[int, Query(ge=1)],
) -> RecordView:
    writable(identity)
    if kind in {"policies", "strategy-versions", "approvals"}:
        raise HTTPException(
            409, "Versioned/governance records require a new version or explicit review"
        )
    if body.kind != kind:
        raise HTTPException(422, "Record discriminator must match the path")
    record = owned(identity, model_for(kind), record_id)
    if record.revision != expected_revision:
        raise HTTPException(409, "Revision conflict; reload before editing")
    validate_links(body, identity)
    before = record_view(kind, record).model_dump(mode="json")
    for field, value in body.model_dump(exclude={"kind"}).items():
        if field in REFERENCES and value != getattr(record, field):
            raise HTTPException(409, "Record ownership/scope references cannot be changed")
        if field == "website" and value is not None:
            value = str(value)
        setattr(record, field, value)
    record.revision += 1
    record.updated_at = utcnow()
    identity.db.flush()
    view = record_view(kind, record)
    identity.audit(
        f"{kind}.updated", entity_id=record.id, before=before, after=view.model_dump(mode="json")
    )
    return view


@router.post("/policies/{record_id}/verify", response_model=RecordView)
def verify_policy(record_id: UUID, body: PolicyVerification, identity: FullIdentity) -> RecordView:
    require_owner(identity)
    require_recent_mfa(identity)
    policy = owned(identity, FirmPolicy, record_id)
    if not isinstance(policy, FirmPolicy) or policy.revision != body.expected_revision:
        raise HTTPException(409, "Revision conflict")
    if policy.expires_at <= utcnow():
        raise HTTPException(409, "Expired policy cannot be verified")
    account = owned(identity, TradingAccount, policy.account_id)
    program = owned(identity, Program, policy.program_id)
    if account.revision != policy.account_revision or program.revision != policy.program_revision:
        raise HTTPException(409, "Policy scope changed; create a new policy version")
    before = record_view("policies", policy).model_dump(mode="json")
    policy.verification_status, policy.verified_by, policy.verified_at = (
        body.decision,
        identity.user.id,
        utcnow(),
    )
    policy.revision += 1
    policy.updated_at = utcnow()
    identity.db.flush()
    view = record_view("policies", policy)
    identity.audit(
        "policy.verification_recorded",
        entity_id=policy.id,
        before=before,
        after=view.model_dump(mode="json"),
    )
    return view


@router.get("/accounts/{account_id}/policy-eligibility", response_model=Eligibility)
def policy_eligibility(account_id: UUID, identity: FullIdentity) -> Eligibility:
    account = owned(identity, TradingAccount, account_id)
    if not isinstance(account, TradingAccount):
        raise HTTPException(404, "Account not found")
    # Only the latest version counts; an older verified version cannot bypass a new unverified one.
    policy = identity.db.scalar(
        select(FirmPolicy)
        .where(
            FirmPolicy.account_id == account_id,
            FirmPolicy.owner_id == identity.user.id,
            FirmPolicy.program_id == account.program_id,
        )
        .order_by(FirmPolicy.version.desc())
        .limit(1)
    )
    reasons = []
    if account.archived:
        reasons.append("ACCOUNT_ARCHIVED")
    if policy is None:
        reasons.append("POLICY_MISSING")
    else:
        program = owned(identity, Program, policy.program_id)
        if (
            account.revision != policy.account_revision
            or program.revision != policy.program_revision
        ):
            reasons.append("POLICY_SCOPE_CHANGED")
        if policy.verification_status != "VERIFIED":
            reasons.append("POLICY_UNVERIFIED")
        if not policy.effective_at <= utcnow() < policy.expires_at:
            reasons.append("POLICY_OUTSIDE_EFFECTIVE_PERIOD")
    return Eligibility(policy_eligible=not reasons, reasons=[*reasons, "EXECUTION_DISABLED"])


@router.post("/approvals/{record_id}/review", response_model=RecordView)
def review_approval(record_id: UUID, body: Review, identity: FullIdentity) -> RecordView:
    require_owner(identity)
    require_recent_mfa(identity)
    record = owned(identity, ApprovalRequest, record_id)
    if (
        not isinstance(record, ApprovalRequest)
        or record.status != "PENDING"
        or record.revision != body.expected_revision
    ):
        raise HTTPException(409, "Review conflict")
    before = record_view("approvals", record).model_dump(mode="json")
    record.status, record.updated_at = body.decision, utcnow()
    record.revision += 1
    identity.db.flush()
    view = record_view("approvals", record)
    identity.audit(
        "approval.research_reviewed",
        entity_id=record.id,
        before=before,
        after=view.model_dump(mode="json"),
    )
    return view


@router.get("/audit", response_model=list[AuditView])
def audit_events(
    identity: FullIdentity,
    after_sequence: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    event_type: str | None = Query(None, max_length=80),
) -> list[AuditView]:
    query = select(AuditEvent).where(AuditEvent.sequence > after_sequence)
    if identity.user.role != "OWNER":
        query = query.where(AuditEvent.actor_id == identity.user.id)
    if event_type:
        query = query.where(AuditEvent.event_type == event_type)
    return [
        AuditView.model_validate(row)
        for row in identity.db.scalars(query.order_by(AuditEvent.sequence).limit(limit))
    ]


@router.get("/audit/verify", response_model=AuditVerification)
def audit_verify(identity: FullIdentity) -> AuditVerification:
    require_owner(identity)
    valid, sequence, digest = verify_chain(identity.db, identity.key)
    return AuditVerification(valid=valid, sequence=sequence, digest=digest)
