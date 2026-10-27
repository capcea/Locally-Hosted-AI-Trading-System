"""Exact verified policy selection; never substitutes a firm's name for its program rules."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.persistence.models import FirmPolicy, Program, RiskProfile, TradingAccount
from packages.risk.contracts import Limits, PolicyTerms
from packages.risk.models import ProfileBinding, RiskPolicy


def applicable_policy(db: Session, account: TradingAccount, at: datetime) -> RiskPolicy:
    policy = db.scalar(
        select(RiskPolicy)
        .where(RiskPolicy.account_id == account.id)
        .order_by(RiskPolicy.version.desc())
        .limit(1)
    )
    if policy is None or policy.status != "VERIFIED":
        raise ValueError("POLICY_MISSING_UNVERIFIED_OR_REVOKED")
    if not policy.effective_at <= at < policy.expires_at:
        raise ValueError("POLICY_OUTSIDE_EFFECTIVE_PERIOD")
    if policy.account_revision != account.revision:
        raise ValueError("POLICY_ACCOUNT_REVISION_CHANGED")
    terms = PolicyTerms.model_validate(policy.terms)
    if terms.currency != account.currency:
        raise ValueError("POLICY_ACCOUNT_CURRENCY_MISMATCH")
    if account.program_id is None:
        if policy.kind != "PERSONAL" or policy.firm_policy_id:
            raise ValueError("PERSONAL_POLICY_REQUIRED")
    else:
        latest = db.scalar(
            select(FirmPolicy)
            .where(FirmPolicy.account_id == account.id, FirmPolicy.program_id == account.program_id)
            .order_by(FirmPolicy.version.desc())
            .limit(1)
        )
        program = db.get(Program, account.program_id)
        if (
            policy.kind != "PROP"
            or latest is None
            or latest.id != policy.firm_policy_id
            or latest.verification_status != "VERIFIED"
            or program is None
            or latest.account_revision != account.revision
            or latest.program_revision != program.revision
            or not latest.effective_at <= at < latest.expires_at
        ):
            raise ValueError("EXACT_PROP_PROGRAM_POLICY_NOT_VERIFIED")
    return policy


def profiles(db: Session, account_id: UUID, scopes: set[str]) -> list[ProfileBinding]:
    candidates = db.scalars(
        select(ProfileBinding)
        .where(ProfileBinding.account_id == account_id, ProfileBinding.scope_key.in_(scopes))
        .order_by(ProfileBinding.version.desc())
    )
    result: dict[str, ProfileBinding] = {}
    for binding in candidates:
        if binding.scope_key in result:
            continue
        base = db.get(RiskProfile, binding.profile_id)
        if base is None or base.revision != binding.profile_revision:
            raise ValueError("RISK_PROFILE_REVISION_CHANGED")
        result[binding.scope_key] = binding
    if "ACCOUNT" not in result:
        raise ValueError("ACCOUNT_RISK_PROFILE_MISSING")
    return list(result.values())


def strictest(bindings: list[ProfileBinding]) -> Limits:
    values = [Limits.model_validate(b.limits) for b in bindings]
    data = values[0].model_dump()
    for field in data:
        data[field] = (
            max if field in {"headroom_buffer_pct", "requires_economic_calendar"} else min
        )(getattr(value, field) for value in values)
    return Limits.model_validate(data)
