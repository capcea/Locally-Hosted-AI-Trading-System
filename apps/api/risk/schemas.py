"""Owner configuration and read-only risk reports; no externally executable token input."""

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, field_validator

from packages.execution.contracts import Contract, OrderRequest
from packages.risk.contracts import Context, EquityValues, Limits, PolicyTerms


class ProfileInput(Contract):
    name: str = Field(min_length=1, max_length=120)
    scope: Literal["ACCOUNT", "STRATEGY", "INSTRUMENT", "ASSET_CLASS", "FIRM", "PROGRAM_PHASE"]
    reference_id: UUID | None = None
    asset_class: Literal["FOREX", "METAL", "INDEX", "CRYPTO"] | None = None
    profile_id: UUID | None = None
    limits: Limits = Field(default_factory=Limits)
    acknowledged_internal_defaults: Literal[True]


class ProfileView(Contract):
    id: UUID
    profile_id: UUID
    scope_key: str
    version: int
    limits: Limits


class PolicyInput(Contract):
    kind: Literal["PERSONAL", "PROP"]
    firm_policy_id: UUID | None = None
    terms: PolicyTerms
    effective_at: AwareDatetime
    expires_at: AwareDatetime
    document_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_references: list[str] = Field(min_length=1, max_length=20)

    @field_validator("source_references")
    @classmethod
    def safe_references(cls, values: list[str]) -> list[str]:
        from urllib.parse import urlsplit

        for value in values:
            parsed = urlsplit(value)
            if (
                len(value) > 1000
                or len(value) < 5
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(
                    "Public provenance references cannot include credentials or queries"
                )
        return values


class PolicyView(PolicyInput):
    id: UUID
    version: int
    status: str
    verified_at: AwareDatetime | None


class Attestation(Contract):
    document_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    action: Literal["VERIFY", "REVOKE"]
    acknowledged_exact_program_and_effective_dates: Literal[True]


class ContextInput(Context):
    pass


class WhatIf(Contract):
    run_id: UUID
    at: AwareDatetime
    order: OrderRequest
    auto_size: bool = False


class Emergency(Contract):
    key: str = Field(min_length=8, max_length=80)
    action: Literal["STOP_NEW_ENTRIES", "CLEAR_STOP", "FLATTEN"]
    expected_revision: int = Field(ge=1)
    acknowledged_simulated_only: Literal[True]


class AccountStatus(Contract):
    account_id: UUID
    currency: str
    configured: bool
    ledger_verified: bool
    data_verified: bool
    manual_stop: bool
    automatic_stop: bool
    reasons: list[str]
    revision: int
    monitor_at: AwareDatetime | None
    clock: AwareDatetime | None
    values: EquityValues | None
    daily_headroom: Decimal | None
    total_headroom: Decimal | None
    ledger_sequence: int
    ledger_digest: str
    source: Literal["SIMULATED"] = "SIMULATED"
    external_execution_authorized: Literal[False] = False
