"""Phase 0 API contracts. Monetary reference values serialize as decimal strings."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, json_schema_serialization_defaults_required=True
    )


class ServiceStatus(StrEnum):
    HEALTHY = "HEALTHY"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    DISABLED = "DISABLED"
    PENDING_IMPLEMENTATION = "PENDING_IMPLEMENTATION"


class ServiceHealth(Contract):
    id: str
    name: str
    status: ServiceStatus
    detail: str
    latency_ms: int | None = None


class SafetyState(Contract):
    mode: Literal["SIMULATED"] = "SIMULATED"
    live_trading_enabled: Literal[False] = False
    order_submission_enabled: Literal[False] = False
    executor_capability: Literal["DENY_ALL"] = "DENY_ALL"
    generated_code_execution: Literal[False] = False
    read_only: Literal[True] = Field(
        default=True,
        description=(
            "Legacy trading capability flag. "
            "Authenticated metadata management can write; trading cannot."
        ),
    )
    reasons: tuple[str, ...] = (
        "LIVE_EXECUTION_NOT_IMPLEMENTED",
        "LIVE_APPROVAL_NOT_IMPLEMENTED",
        "BROKER_ADAPTERS_NOT_CONNECTED",
        "POLICY_PACKS_UNVERIFIED",
    )


class ReferenceProfile(Contract):
    provenance: Literal["CONFIGURATION_EXAMPLE"] = "CONFIGURATION_EXAMPLE"
    currency: Literal["USD"] = "USD"
    equity: Decimal = Decimal("25000.00")
    risk_per_trade_pct: Decimal = Decimal("0.25")
    daily_loss_pct: Decimal = Decimal("1.00")
    total_drawdown_pct: Decimal = Decimal("3.00")
    open_risk_pct: Decimal = Decimal("1.00")
    enforced: Literal[False] = False


class Phase(Contract):
    number: int
    title: str
    status: Literal["CURRENT", "PLANNED"]
    acceptance: str


class Overview(Contract):
    application: str = "AI Trading Research Platform"
    version: str = "0.1.0"
    phase: int = 4
    timestamp: datetime
    uptime_seconds: int
    safety: SafetyState
    services: list[ServiceHealth]
    reference_profile: ReferenceProfile
    roadmap: list[Phase]
    trading_data_available: Literal[False] = False
    performance_data_available: Literal[False] = False
