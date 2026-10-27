"""All external data is attributed, bounded and explicitly incapable of submitting orders."""

from typing import Literal, Never, Protocol
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from packages.execution.contracts import AccountMode, Contract, Number, Positive, Quote, TradeIntent


class BrokerSymbol(Contract):
    broker_symbol: str = Field(min_length=1, max_length=100)
    symbol_id: str = Field(min_length=1, max_length=100)
    canonical_symbol: str | None = Field(default=None, max_length=40)
    asset_class: Literal["FOREX", "METAL", "INDEX", "CRYPTO", "OTHER"] | None = None
    digits: int | None = Field(default=None, ge=0, le=12)
    tick_size: Positive | None = None
    contract_size: Positive | None = None
    min_volume: Positive | None = None
    max_volume: Positive | None = None
    volume_step: Positive | None = None
    stop_distance: Number | None = None
    freeze_distance: Number | None = None
    margin_rate: Number | None = None
    account_currency: str | None = None
    supported_order_types: list[str] = Field(default_factory=list, max_length=10)
    sessions: list[dict[str, object]] = Field(default_factory=list, max_length=100)
    metadata: dict[str, object] = Field(default_factory=dict)
    observed_at: AwareDatetime
    source: str = Field(min_length=3, max_length=100)
    tradability_verified: Literal[False] = False


class ObservedOrder(Contract):
    broker_id: str = Field(min_length=1, max_length=100)
    symbol: str = Field(min_length=1, max_length=100)
    side: str = Field(max_length=20)
    state: str = Field(max_length=40)
    volume: Number
    price: Number | None = None
    stop_loss: Number | None = None
    take_profit: Number | None = None
    observed_at: AwareDatetime
    source_sequence: int = Field(ge=0)


class BrokerSnapshot(Contract):
    provider: Literal["MT5", "CTRADER", "SIMULATOR"]
    environment: Literal["SIMULATED", "DEMO_READ_ONLY"]
    account_id: str = Field(min_length=1, max_length=100)
    server: str = Field(min_length=1, max_length=120)
    account_mode: AccountMode | None = None
    currency: str = Field(pattern=r"^[A-Z]{3,8}$")
    balance: Number | None = None
    equity: Number | None = None
    observed_at: AwareDatetime
    source_sequence: int = Field(ge=0)
    source: Literal["BROKER_OBSERVED", "CONTRACT_FIXTURE", "SIMULATED"]
    healthy: bool
    authorization: Literal["READ_ONLY", "UNVERIFIED", "REVOKED"]
    symbols: list[BrokerSymbol] = Field(default_factory=list, max_length=100)
    quotes: list[Quote] = Field(default_factory=list, max_length=100)
    orders: list[ObservedOrder] = Field(default_factory=list, max_length=500)
    positions: list[ObservedOrder] = Field(default_factory=list, max_length=500)
    history: list[ObservedOrder] = Field(default_factory=list, max_length=500)
    history_complete: bool = False
    reconnect_attempt: int = Field(default=0, ge=0, le=1000)
    latency_ms: int | None = Field(default=None, ge=0)
    restrictions: list[str] = Field(
        default_factory=lambda: ["EXTERNAL_EXECUTION_DISABLED"], max_length=20
    )
    external_execution_enabled: Literal[False] = False

    @model_validator(mode="after")
    def source_matches_mode(self) -> "BrokerSnapshot":
        if (self.environment == "SIMULATED") != (self.provider == "SIMULATOR"):
            raise ValueError("Provider/environment mismatch")
        if self.source == "SIMULATED" and self.provider != "SIMULATOR":
            raise ValueError("External observations cannot masquerade as simulator data")
        if any(q.available_at > self.observed_at for q in self.quotes):
            raise ValueError("Future quote in snapshot")
        return self


class SnapshotRequest(Contract):
    account_id: str = Field(min_length=1, max_length=100)
    server: str = Field(min_length=1, max_length=120)
    symbols: list[str] = Field(default_factory=list, max_length=20)
    history_days: int = Field(default=1, ge=1, le=7)
    source_sequence: int = Field(ge=0)


class SignedObservation(Contract):
    connection_id: UUID
    snapshot: BrokerSnapshot
    signature: str = Field(pattern=r"^[a-f0-9]{128}$")


class BrokerAdapter(Protocol):
    def snapshot(self, request: SnapshotRequest) -> BrokerSnapshot: ...
    def submit(self, intent: TradeIntent) -> Never: ...
    def cancel(self, broker_id: str) -> Never: ...
    def modify(self, broker_id: str) -> Never: ...


class ExternalExecutionDenied(PermissionError):
    pass


class ReadOnlyAdapter:
    def submit(self, intent: TradeIntent) -> Never:
        raise ExternalExecutionDenied("Phase 4 risk gateway and owner authorization unavailable")

    def cancel(self, broker_id: str) -> Never:
        raise ExternalExecutionDenied("External cancellation is disabled")

    def modify(self, broker_id: str) -> Never:
        raise ExternalExecutionDenied("External modification is disabled")
