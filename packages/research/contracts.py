"""Bounded trusted research inputs; no source, module, URL or broker capability fields."""

from datetime import timedelta
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from packages.execution.contracts import (
    Contract,
    Nonnegative,
    Positive,
    SimulationModel,
    SymbolSpec,
)
from packages.risk.contracts import Context

StrategyName = Literal[
    "EMA_TREND",
    "MA_CROSS",
    "DONCHIAN",
    "BOLLINGER",
    "RSI",
    "ATR_BREAKOUT",
    "OPENING_RANGE",
    "SESSION_MOMENTUM",
]


class Parameters(Contract):
    fast: int = Field(default=5, ge=2, le=100)
    slow: int = Field(default=20, ge=3, le=200)
    lookback: int = Field(default=14, ge=2, le=200)
    threshold: Positive = Decimal("2")
    stop_ticks: int = Field(default=20, ge=1, le=10000)
    reward_multiple: Positive = Decimal("2")
    volume: Positive = Decimal("0.01")
    cross_asset_confirmation: bool = False
    confirmation_direction: Literal["SAME", "INVERSE"] = "SAME"
    confirmation_max_age_seconds: int = Field(default=86400, ge=1, le=604800)
    entry_order_type: Literal["MARKET", "LIMIT", "STOP"] = "MARKET"
    entry_offset_ticks: int = Field(default=1, ge=1, le=10000)
    pending_expiry_seconds: int = Field(default=60, ge=1, le=86400)
    direction: Literal["LONG_ONLY", "SHORT_ONLY", "LONG_SHORT"] = "LONG_SHORT"
    session_open: int = Field(default=0, ge=0, le=1439)
    session_close: int = Field(default=1440, ge=1, le=1440)
    opening_minutes: int = Field(default=15, ge=1, le=240)
    session_exit_buffer_seconds: int = Field(default=60, ge=0, le=3600)
    flat_before_risk_reset: bool = True
    max_hold_seconds: int = Field(default=3600, ge=1, le=86400)
    random_keep_pct: int = Field(default=100, ge=0, le=100)

    @model_validator(mode="after")
    def coherent(self) -> "Parameters":
        if self.fast >= self.slow or self.session_open >= self.session_close:
            raise ValueError("INVALID_STRATEGY_PARAMETERS")
        return self


class DatasetPin(Contract):
    dataset_id: UUID
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    role: Literal["EXECUTION", "CONFIRMATION"] = "EXECUTION"
    symbol: SymbolSpec
    context: Context


class Chronology(Contract):
    start: AwareDatetime
    discovery_end: AwareDatetime
    calibration_end: AwareDatetime
    validation_end: AwareDatetime
    end: AwareDatetime
    purge_seconds: int = Field(default=3600, ge=0, le=604800)
    embargo_seconds: int = Field(default=60, ge=0, le=86400)
    walk_forward_folds: int = Field(default=2, ge=1, le=5)

    @model_validator(mode="after")
    def ordered(self) -> "Chronology":
        if (
            not self.start
            < self.discovery_end
            < self.calibration_end
            < self.validation_end
            < self.end
        ):
            raise ValueError("TRAIN_VALIDATION_TEST_CHRONOLOGY_INVALID")
        if self.end - self.start > timedelta(days=3660):
            raise ValueError("RESEARCH_RANGE_TOO_LARGE")
        return self


class ExperimentInput(Contract):
    key: str = Field(min_length=8, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    source_account_id: UUID
    strategy: StrategyName
    strategy_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    datasets: list[DatasetPin] = Field(min_length=1, max_length=8)
    parameters: list[Parameters] = Field(min_length=1, max_length=16)
    chronology: Chronology
    phase: Literal["DISCOVERY", "CALIBRATION", "VALIDATION", "FINAL_HOLDOUT"]
    validation_mode: Literal["DIRECT", "WALK_FORWARD"] = "DIRECT"
    engine: Literal["SCREEN", "EVENT"]
    assumptions: SimulationModel
    bar_spread: Nonnegative | None = None
    cost_multipliers: list[Positive] = Field(
        default_factory=lambda: [Decimal(1)], min_length=1, max_length=3
    )
    seed: int = Field(default=0, ge=0, le=2147483647)
    max_rows: int = Field(default=1000, ge=10, le=5000)
    max_seconds: int = Field(default=120, ge=5, le=300)
    bootstrap_samples: int = Field(default=200, ge=100, le=1000)
    holdout_release_id: UUID | None = None
    acknowledged_clone_policy_to_isolated_accounts: Literal[True]
    acknowledged_research_only: Literal[True]
    acknowledged_cost_and_bar_assumptions: Literal[True]

    @model_validator(mode="after")
    def bounded(self) -> "ExperimentInput":
        if len({p.dataset_id for p in self.datasets}) != len(self.datasets):
            raise ValueError("DUPLICATE_DATASET_PIN")
        count = len(self.parameters) * len(self.cost_multipliers)
        if self.validation_mode == "WALK_FORWARD":
            if self.phase != "VALIDATION" or self.engine != "EVENT":
                raise ValueError("WALK_FORWARD_REQUIRES_VALIDATION_EVENT_ENGINE")
            count = (count + len(self.cost_multipliers)) * self.chronology.walk_forward_folds
        if count > 24:
            raise ValueError("TRIAL_QUOTA_EXCEEDED")
        if any(p.max_hold_seconds > self.chronology.purge_seconds for p in self.parameters):
            raise ValueError("PURGE_MUST_COVER_MAXIMUM_LABEL_HORIZON")
        if self.phase == "FINAL_HOLDOUT" and (
            self.engine != "EVENT"
            or len(self.parameters) != 1
            or self.cost_multipliers != [Decimal(1)]
        ):
            raise ValueError("HOLDOUT_REQUIRES_ONE_FROZEN_EVENT_TRIAL")
        return self


class SealInput(Contract):
    dataset_id: UUID
    reason: str = Field(min_length=10, max_length=1000)
    acknowledged_prior_exposure_unknown: Literal[True]


class ReleaseInput(Contract):
    experiment: ExperimentInput
    acknowledged_single_final_evaluation: Literal[True]
    acknowledged_not_certified_untouched: Literal[True]


class DSRRequest(Contract):
    trial: int = Field(default=0, ge=0, le=23)
    independent_trials: int = Field(ge=2, le=1000000)
    trial_sharpe_variance: Positive
    independence_model_reference: str = Field(min_length=10, max_length=1000)
    acknowledged_assumption_not_certification: Literal[True]
