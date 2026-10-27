"""Broker-neutral exact contracts. None constitutes external execution authority."""

from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_validator,
)

from packages.market.contracts import SessionCalendar


def exact(value: object) -> object:
    if isinstance(value, (float, bool)):
        raise ValueError("Use exact decimal strings, never floats")
    return value


def finite(value: Decimal) -> Decimal:
    exponent = value.as_tuple().exponent
    if (
        not value.is_finite()
        or abs(value) > Decimal("1e18")
        or not isinstance(exponent, int)
        or exponent < -12
    ):
        raise ValueError("Finite bounded decimals with at most 12 places required")
    return value


Number = Annotated[Decimal, BeforeValidator(exact), AfterValidator(finite)]
Positive = Annotated[Number, Field(gt=0)]
Nonnegative = Annotated[Number, Field(ge=0)]
Side = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT", "STOP"]
OrderState = Literal[
    "CREATED",
    "VALIDATED",
    "SUBMIT_PENDING",
    "SUBMITTED",
    "ACKNOWLEDGED",
    "PARTIALLY_FILLED",
    "FILLED",
    "REJECTED",
    "CANCELLED",
    "EXPIRED",
    "UNKNOWN",
]
Mode = Literal["SIMULATED", "DEMO_READ_ONLY"]
AccountMode = Literal["HEDGING", "NETTING"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, validate_assignment=True)


class SymbolSpec(Contract):
    symbol: str = Field(min_length=1, max_length=40)
    canonical_symbol: str = Field(min_length=1, max_length=40)
    asset_class: Literal["FOREX", "METAL", "INDEX", "CRYPTO", "OTHER"]
    tick_size: Positive
    digits: int = Field(ge=0, le=12)
    contract_size: Positive
    min_volume: Positive
    max_volume: Positive
    volume_step: Positive
    stop_distance: Nonnegative | None = None
    freeze_distance: Nonnegative | None = None
    profit_currency: str = Field(pattern=r"^[A-Z]{3,8}$")
    order_types: list[OrderType] = Field(min_length=1, max_length=3)
    account_mode: AccountMode
    oco_supported: bool = False
    calendar: SessionCalendar | None = None
    source: str = Field(min_length=5, max_length=500)
    observed_at: AwareDatetime
    valid_until: AwareDatetime
    margin_rate: Nonnegative | None = None

    @model_validator(mode="after")
    def consistent(self) -> "SymbolSpec":
        if (
            self.max_volume < self.min_volume
            or self.min_volume % self.volume_step
            or self.max_volume % self.volume_step
            or self.valid_until <= self.observed_at
            or self.tick_size % Decimal(1).scaleb(-self.digits)
        ):
            raise ValueError("Inconsistent symbol specifications")
        if len(set(self.order_types)) != len(self.order_types):
            raise ValueError("Duplicate capabilities")
        return self


class Quote(Contract):
    symbol: str = Field(min_length=1, max_length=40)
    event_time: AwareDatetime
    available_at: AwareDatetime
    sequence: int = Field(ge=0)
    bid: Positive
    ask: Positive
    bid_liquidity: Nonnegative | None = None
    ask_liquidity: Nonnegative | None = None

    @model_validator(mode="after")
    def coherent(self) -> "Quote":
        if self.ask < self.bid or self.available_at < self.event_time:
            raise ValueError("Invalid quote or availability")
        return self


class SimulationModel(Contract):
    assumption_source: str = Field(min_length=10, max_length=500)
    latency_ms: int = Field(default=0, ge=0, le=60000)
    latency_jitter_ms: int = Field(default=0, ge=0, le=60000)
    slippage_ticks: int = Field(default=0, ge=0, le=1000)
    commission_per_unit: Nonnegative
    swap_per_unit_per_day: Number | None = None
    liquidity_per_tick: Positive
    max_quote_age_seconds: int = Field(default=30, ge=1, le=300)
    synthetic_initial_balance: Nonnegative
    account_currency: str = Field(pattern=r"^[A-Z]{3,8}$")
    seed: int = Field(default=0, ge=0, le=2147483647)


class OrderRequest(Contract):
    side: Side
    order_type: OrderType
    volume: Positive
    price: Positive | None = None
    stop_loss: Positive | None = None
    take_profit: Positive | None = None
    expires_at: AwareDatetime | None = None
    oco_group: str | None = Field(default=None, min_length=1, max_length=64)
    strategy_version_id: UUID | None = None

    @model_validator(mode="after")
    def pending_price(self) -> "OrderRequest":
        if (self.order_type == "MARKET") != (self.price is None):
            raise ValueError("Only pending orders require an explicit activation price")
        return self


class SimOrder(Contract):
    id: UUID
    idempotency_key: str
    request: OrderRequest
    state: OrderState
    created_at: AwareDatetime
    eligible_at: AwareDatetime
    filled_volume: Nonnegative = Decimal(0)
    average_price: Nonnegative = Decimal(0)
    broker_order_id: str | None = None
    rejection_reason: str | None = None
    activated: bool = False


class Position(Contract):
    id: UUID
    symbol: str
    side: Side
    volume: Nonnegative
    entry_price: Positive
    stop_loss: Positive | None = None
    take_profit: Positive | None = None
    realized_pnl: Number = Decimal(0)


class Fill(Contract):
    deal_id: str
    order_id: UUID | None
    position_id: UUID
    side: Side
    volume: Positive
    price: Positive
    commission: Nonnegative
    realized_pnl: Number
    timestamp: AwareDatetime
    sequence: int
    reason: str
    source: Literal["SIMULATED"] = "SIMULATED"


class EngineEvent(Contract):
    kind: str
    order_id: UUID | None = None
    timestamp: AwareDatetime
    source_sequence: int
    payload: dict[str, object]
    source: Literal["SIMULATED"] = "SIMULATED"


class SimState(Contract):
    clock: AwareDatetime
    spec: SymbolSpec
    model: SimulationModel
    source: Literal["SIMULATED"] = "SIMULATED"
    connection: Literal["CONNECTED", "DISCONNECTED"] = "CONNECTED"
    fault: Literal["NONE", "BEFORE_SUBMIT", "AFTER_SUBMIT", "REJECT_NEXT", "DELAY_ACK"] = "NONE"
    quote: Quote | None = None
    bid_remaining: Nonnegative = Decimal(0)
    ask_remaining: Nonnegative = Decimal(0)
    orders: dict[str, SimOrder] = Field(default_factory=dict)
    positions: dict[str, Position] = Field(default_factory=dict)
    # Deliberately separate simulated broker truth from the uncertain local journal state.
    broker_truth: dict[str, OrderState] = Field(default_factory=dict)
    fills: list[Fill] = Field(default_factory=list)
    cash: Number
    fees: Nonnegative = Decimal(0)
    swap: Number = Decimal(0)
    incident: str | None = None
    swap_through: AwareDatetime | None = None


class Command(Contract):
    key: str = Field(min_length=8, max_length=100)
    at: AwareDatetime
    action: Literal["SUBMIT", "TICK", "CANCEL", "MODIFY", "CLOSE", "FAULT", "RECONCILE", "SWAP"]
    order: OrderRequest | None = None
    quote: Quote | None = None
    target_id: UUID | None = None
    volume: Positive | None = None
    stop_loss: Positive | None = None
    take_profit: Positive | None = None
    fault: Literal["NONE", "BEFORE_SUBMIT", "AFTER_SUBMIT", "REJECT_NEXT", "DELAY_ACK"] | None = (
        None
    )


class AccountExposure(Contract):
    account_id: UUID
    observed_at: AwareDatetime
    gross_volume: Nonnegative
    open_risk: Nonnegative | None = None
    currency: str


class TradingPolicyStatus(Contract):
    verified: Literal[False] = False
    reason: Literal["EXTERNAL_EXECUTION_DISABLED"] = "EXTERNAL_EXECUTION_DISABLED"


class TradeIntent(Contract):
    account_id: UUID
    broker_id: UUID
    strategy_version_id: UUID
    symbol_spec_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    request: OrderRequest
    expires_at: AwareDatetime


class RiskCheckRequest(Contract):
    intent: TradeIntent
    exposure: AccountExposure
    policy: TradingPolicyStatus


class RiskCheckResult(Contract):
    allowed: Literal[False] = False
    reason: Literal["EXTERNAL_EXECUTION_DISABLED"] = "EXTERNAL_EXECUTION_DISABLED"


class RiskReservation(Contract):
    account_id: UUID
    intent_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    expires_at: AwareDatetime
    executable: Literal[False] = False


class BrokerExecutionResult(Contract):
    submitted: Literal[False] = False
    reason: Literal["EXTERNAL_EXECUTION_DISABLED"] = "EXTERNAL_EXECUTION_DISABLED"


class ReconciliationResult(Contract):
    status: Literal["CONSISTENT", "RESOLVED", "UNKNOWN"]
    account_id: UUID
    observed_at: AwareDatetime
    differences: list[str] = Field(max_length=100)
    retry_authorized: Literal[False] = False
