"""Strict risk/policy data. Owner attestations never certify external broker permission."""

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, field_validator, model_validator

from packages.execution.contracts import Contract, Nonnegative, Number, Positive
from packages.market.contracts import valid_timezone

Currency = str


class Limits(Contract):
    per_trade_pct: Positive = Decimal("0.25")
    daily_loss_pct: Positive = Decimal("1")
    total_loss_pct: Positive = Decimal("3")
    aggregate_risk_pct: Positive = Decimal("1")
    correlated_risk_pct: Positive = Decimal("0.5")
    headroom_buffer_pct: Nonnegative = Decimal("0.1")
    max_positions: int = Field(default=3, ge=1, le=100)
    max_spread_ticks: Positive = Decimal("20")
    max_slippage_ticks: int = Field(default=2, ge=0, le=1000)
    max_quote_age_seconds: int = Field(default=30, ge=1, le=300)
    warning_utilization_pct: Positive = Decimal("80")
    warning_risk_multiplier: Positive = Decimal("0.5")
    requires_economic_calendar: bool = False

    @model_validator(mode="after")
    def bounded(self) -> "Limits":
        fields = (
            self.per_trade_pct,
            self.daily_loss_pct,
            self.total_loss_pct,
            self.aggregate_risk_pct,
            self.correlated_risk_pct,
            self.headroom_buffer_pct,
        )
        if (
            any(x > 100 for x in fields)
            or self.per_trade_pct > self.aggregate_risk_pct
            or self.daily_loss_pct > self.total_loss_pct
            or self.headroom_buffer_pct >= self.daily_loss_pct
            or self.warning_utilization_pct >= 100
            or self.warning_risk_multiplier > 1
        ):
            raise ValueError("INCONSISTENT_RISK_LIMITS")
        return self


class PolicyTerms(Contract):
    currency: str = Field(pattern=r"^[A-Z]{3,8}$")
    timezone: str
    reset_minute: int = Field(default=0, ge=0, le=1439)
    reset_fold: Literal["EARLIER", "LATER"]
    daily_loss_pct: Positive
    total_loss_pct: Positive
    daily_reference: Literal["BALANCE", "EQUITY", "MAX_BALANCE_EQUITY", "INITIAL"]
    daily_amount_basis: Literal["INITIAL", "DAILY_REFERENCE"]
    total_mode: Literal["STATIC", "TRAILING_BALANCE", "TRAILING_EQUITY"]
    trailing_amount_basis: Literal["INITIAL", "HIGH_WATER"]
    include_floating: bool
    include_fees: Literal[True] = True
    allow_overnight: bool
    allow_weekend: bool
    automation_permitted: bool
    max_position_seconds: int = Field(ge=1, le=604800)
    permitted_instruments: list[str] = Field(min_length=1, max_length=100)
    prohibited_styles: list[str] = Field(max_length=50)
    news_required: bool
    news_scope: Literal["NEW_ENTRIES", "EXPOSURE"]
    news_before_seconds: int = Field(default=300, ge=0, le=86400)
    news_after_seconds: int = Field(default=300, ge=0, le=86400)

    @field_validator("timezone")
    @classmethod
    def valid_zone(cls, value: str) -> str:
        return valid_timezone(value)

    @model_validator(mode="after")
    def percentages(self) -> "PolicyTerms":
        if self.daily_loss_pct > 100 or self.total_loss_pct > 100:
            raise ValueError("POLICY_PERCENTAGE_OUT_OF_RANGE")
        return self


class FXQuote(Contract):
    base: str = Field(pattern=r"^[A-Z]{3,8}$")
    quote: str = Field(pattern=r"^[A-Z]{3,8}$")
    bid: Positive
    ask: Positive
    observed_at: AwareDatetime
    available_at: AwareDatetime
    valid_until: AwareDatetime
    source_reference: str = Field(min_length=5, max_length=500)

    @model_validator(mode="after")
    def coherent(self) -> "FXQuote":
        if (
            self.base == self.quote
            or self.bid > self.ask
            or not self.observed_at <= self.available_at <= self.valid_until
        ):
            raise ValueError("INVALID_FX_QUOTE")
        return self


class FinancialTerms(Contract):
    payoff: Literal["LINEAR_CONTRACT", "LINEAR_TICK", "INVERSE", "UNVERIFIED"]
    base_currency: str | None = Field(default=None, pattern=r"^[A-Z]{3,8}$")
    quote_currency: str = Field(pattern=r"^[A-Z]{3,8}$")
    tick_value_profit_currency: Positive
    margin_per_unit: Positive | None
    funding_buffer_per_unit: Nonnegative = Decimal("0")
    correlation_group: str = Field(min_length=1, max_length=80)
    execution_style: str = Field(min_length=1, max_length=80)
    automated: bool = False
    fx: list[FXQuote] = Field(default_factory=list, max_length=6)
    source_reference: str = Field(min_length=10, max_length=1000)
    verified_at: AwareDatetime
    valid_until: AwareDatetime
    source: Literal["SIMULATED"] = "SIMULATED"

    @model_validator(mode="after")
    def times(self) -> "FinancialTerms":
        if self.valid_until <= self.verified_at:
            raise ValueError("INVALID_FINANCIAL_TERMS_VALIDITY")
        return self


class NewsEvent(Contract):
    timestamp: AwareDatetime
    currencies: list[str] = Field(min_length=1, max_length=10)
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    reference: str = Field(min_length=3, max_length=500)


class CalendarEvidence(Contract):
    observed_at: AwareDatetime
    available_at: AwareDatetime
    valid_until: AwareDatetime
    events: list[NewsEvent] = Field(max_length=500)
    source_reference: str = Field(min_length=10, max_length=1000)
    source: Literal["SIMULATED"] = "SIMULATED"

    @model_validator(mode="after")
    def times(self) -> "CalendarEvidence":
        if not self.observed_at <= self.available_at < self.valid_until:
            raise ValueError("INVALID_CALENDAR_EVIDENCE")
        return self


class Context(Contract):
    financial: FinancialTerms
    calendar: CalendarEvidence | None = None
    owner_acknowledged_synthetic_assumptions: Literal[True]


class Decision(Contract):
    decision: Literal["ALLOW", "DENY", "INDETERMINATE"]
    reasons: list[str] = Field(max_length=100)
    approved_volume: Nonnegative = Decimal(0)
    maximum_volume: Nonnegative = Decimal(0)
    estimated_risk: Nonnegative = Decimal(0)
    risk_per_unit: Nonnegative = Decimal(0)
    estimated_margin: Nonnegative = Decimal(0)
    available_budget: Nonnegative = Decimal(0)
    evidence: dict[str, object] = Field(default_factory=dict)
    source: Literal["SIMULATED"] = "SIMULATED"
    external_execution_authorized: Literal[False] = False


class AuthorizationScope(Contract):
    account_id: UUID
    run_id: UUID
    order_id: UUID
    command_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    request_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    context_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    policy_id: UUID
    profile_ids: list[UUID] = Field(min_length=1, max_length=100)
    estimated_risk: Nonnegative
    estimated_margin: Nonnegative
    issued_at: AwareDatetime
    expires_at: AwareDatetime
    source: Literal["SIMULATED"] = "SIMULATED"
    external_execution_authorized: Literal[False] = False


class EquityValues(Contract):
    balance: Number
    equity: Number
    realized_pnl: Number
    unrealized_pnl: Number
    commissions: Nonnegative
    funding: Number
    open_risk: Nonnegative
    pending_risk: Nonnegative
    reserved_risk: Nonnegative
    margin_used: Nonnegative
    position_count: int = Field(ge=0)
    groups: dict[str, Nonnegative]
    strategies: dict[str, Nonnegative] = Field(default_factory=dict)
