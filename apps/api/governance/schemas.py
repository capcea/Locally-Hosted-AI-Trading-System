"""Discriminated, generated contracts for scoped records and exact decimal values."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, HttpUrl, field_validator, model_validator

from apps.api.identity.schemas import Input

Money = Annotated[Decimal, Field(ge=0, max_digits=24, decimal_places=8)]
Percent = Annotated[Decimal, Field(gt=0, le=100, max_digits=7, decimal_places=4)]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class RecordInput(Input):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    source: Literal["USER_ENTERED", "SYNTHETIC_TEST_FIXTURE"] = "USER_ENTERED"

    @field_validator("website", "source_references", check_fields=False)
    @classmethod
    def public_source_urls(cls, value: HttpUrl | list[HttpUrl] | None) -> object:
        urls = value if isinstance(value, list) else [value]
        if any(url and (url.username or url.password or url.query or url.fragment) for url in urls):
            raise ValueError("Source URLs cannot contain credentials, query strings or fragments")
        return value


class FirmInput(RecordInput):
    kind: Literal["firms"]
    website: HttpUrl | None = None


class ProgramInput(RecordInput):
    kind: Literal["programs"]
    firm_id: UUID
    phase: Annotated[str, Field(min_length=1, max_length=80)]
    platform: Annotated[str, Field(min_length=1, max_length=80)]


class VenueInput(RecordInput):
    kind: Literal["venues"]
    venue_type: Literal["BROKER", "EXCHANGE", "CUSTOM"]


class InstrumentInput(RecordInput):
    kind: Literal["instruments"]
    venue_id: UUID
    symbol: Annotated[str, Field(min_length=1, max_length=40)]
    asset_class: Literal["FOREX", "METAL", "INDEX", "CRYPTO", "OTHER"]


class AccountInput(RecordInput):
    kind: Literal["accounts"]
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    initial_capital: Money
    environment: Literal["SIMULATED"] = "SIMULATED"
    program_id: UUID | None = None
    archived: bool = False

    @field_validator("initial_capital", mode="before")
    @classmethod
    def exact_money(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("Financial values must be decimal strings, never floating point")
        return value


class BrokerInput(RecordInput):
    kind: Literal["brokers"]
    account_id: UUID
    adapter: Literal["MT5", "CTRADER", "CUSTOM"]


class RiskInput(RecordInput):
    kind: Literal["risk-profiles"]
    account_id: UUID
    per_trade_pct: Percent
    daily_loss_pct: Percent
    total_loss_pct: Percent
    aggregate_risk_pct: Percent

    @field_validator(
        "per_trade_pct", "daily_loss_pct", "total_loss_pct", "aggregate_risk_pct", mode="before"
    )
    @classmethod
    def exact_percent(cls, value: object) -> object:
        return AccountInput.exact_money(value)

    @model_validator(mode="after")
    def ordered_limits(self) -> "RiskInput":
        if (
            self.per_trade_pct > self.aggregate_risk_pct
            or self.daily_loss_pct > self.total_loss_pct
        ):
            raise ValueError("Per-trade/daily limits cannot exceed aggregate/total limits")
        return self


class PolicyInput(RecordInput):
    kind: Literal["policies"]
    program_id: UUID
    account_id: UUID
    version: Annotated[int, Field(ge=1)]
    source_references: Annotated[list[HttpUrl], Field(min_length=1, max_length=20)]
    effective_at: AwareDatetime
    expires_at: AwareDatetime
    document_digest: Digest

    @model_validator(mode="after")
    def dates(self) -> "PolicyInput":
        if self.expires_at <= self.effective_at:
            raise ValueError("Policy expiration must follow its effective date")
        return self


class StrategyInput(RecordInput):
    kind: Literal["strategies"]
    account_id: UUID
    hypothesis: Annotated[str, Field(min_length=1, max_length=2000)]


class VersionInput(RecordInput):
    kind: Literal["strategy-versions"]
    strategy_id: UUID
    version: Annotated[int, Field(ge=1)]
    artifact_digest: Digest


class ExperimentInput(RecordInput):
    kind: Literal["experiments"]
    strategy_version_id: UUID
    research_question: Annotated[str, Field(min_length=1, max_length=2000)]


class ApprovalInput(RecordInput):
    kind: Literal["approvals"]
    strategy_version_id: UUID
    account_id: UUID


class IncidentInput(RecordInput):
    kind: Literal["incidents"]
    account_id: UUID | None = None
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    status: Literal["OPEN", "RESOLVED"] = "OPEN"


RecordBody = Annotated[
    FirmInput
    | ProgramInput
    | VenueInput
    | InstrumentInput
    | AccountInput
    | BrokerInput
    | RiskInput
    | PolicyInput
    | StrategyInput
    | VersionInput
    | ExperimentInput
    | ApprovalInput
    | IncidentInput,
    Field(discriminator="kind"),
]


class PolicyAttestation(Input):
    verified_at: datetime | None
    verified_by: UUID | None
    account_revision: int
    program_revision: int


class RecordView(Input):
    id: UUID
    owner_id: UUID
    revision: int
    created_at: datetime
    updated_at: datetime
    data: RecordBody
    state: str | None = None
    policy_attestation: PolicyAttestation | None = None


class RecordPage(Input):
    items: list[RecordView]
    offset: int
    limit: int
    total: int


class PolicyVerification(Input):
    decision: Literal["VERIFIED", "REJECTED"]
    source_review_acknowledged: Literal[True]
    expected_revision: Annotated[int, Field(ge=1)]


class Review(Input):
    decision: Literal["REVIEWED", "REJECTED"]
    expected_revision: Annotated[int, Field(ge=1)]


class Eligibility(Input):
    policy_eligible: bool
    trading_authorized: Literal[False] = False
    reasons: list[str]


class AuditView(Input):
    model_config = {"from_attributes": True, "extra": "forbid"}
    sequence: int
    id: UUID
    timestamp: str
    actor_id: UUID | None
    actor_role: str
    mfa_verified: bool
    event_type: str
    entity_id: UUID | None
    correlation_id: UUID
    before: dict[str, object] | None
    after: dict[str, object] | None
    previous_digest: str
    digest: str


class AuditVerification(Input):
    valid: bool
    sequence: int
    digest: str
