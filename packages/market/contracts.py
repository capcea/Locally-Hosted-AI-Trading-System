"""Bounded import contracts. Availability is explicit, never inferred from event time."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AwareDatetime, Field, field_validator, model_validator

from packages.domain.validation import Input

TIMEFRAMES = {"TICK": 0, "M1": 60, "M5": 300, "M15": 900, "H1": 3600, "H4": 14400, "D1": 86400}
CORE_SYMBOLS = (
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "XAUUSD",
    "XAGUSD",
    "EURGBP",
    "US500",
    "BTCUSD",
    "ETHUSD",
)


def valid_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError("Unknown or invalid IANA timezone") from error
    return value


class ProviderInput(Input):
    name: str = Field(min_length=1, max_length=120)
    adapter: Literal["LOCAL", "ECB", "MT5_EXPORT", "PREMIUM"]
    rights_reference: str = Field(min_length=5, max_length=1000)
    attribution: str = Field(min_length=3, max_length=500)
    usage_rights_acknowledged: Literal[True]

    @field_validator("rights_reference")
    @classmethod
    def public_rights_reference(cls, value: str) -> str:
        if value.startswith(("http:", "https:")):
            url = urlsplit(value)
            if not url.hostname or url.username or url.password or url.query or url.fragment:
                raise ValueError(
                    "Rights URLs cannot contain credentials, query strings or fragments"
                )
        return value


class SessionCalendar(Input):
    timezone: str = "UTC"
    weekdays: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4], min_length=1, max_length=7)
    holidays: list[date] = Field(default_factory=list, max_length=2000)
    opens: int = Field(0, ge=0, le=1439)
    closes: int = Field(1440, ge=1, le=1440)
    verified_until: AwareDatetime
    source: str = Field(min_length=3, max_length=1000)

    @field_validator("timezone")
    @classmethod
    def valid_zone(cls, value: str) -> str:
        return valid_timezone(value)

    @model_validator(mode="after")
    def ordered(self) -> "SessionCalendar":
        if self.opens >= self.closes or any(day not in range(7) for day in self.weekdays):
            raise ValueError("Use explicit same-day session intervals and weekdays 0..6")
        return self


class ImportSpec(Input):
    provider_id: UUID
    instrument_id: UUID
    account_id: UUID
    source_symbol: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.:/-]+$")
    data_type: Literal["TICK", "BAR", "EVENT", "REFERENCE", "SESSION"]
    timeframe: Literal["TICK", "M1", "M5", "M15", "H1", "H4", "D1"]
    source_timezone: str = "UTC"
    start: AwareDatetime
    end: AwareDatetime
    provenance: Literal["USER_SUPPLIED", "SYNTHETIC_TEST_FIXTURE", "PUBLIC_PROVIDER"]
    format: Literal["CSV", "PARQUET"] = "CSV"
    calendar: SessionCalendar | None = None
    price_increment: Annotated[Decimal, Field(gt=0, max_digits=38, decimal_places=12)] | None = None
    spike_fraction: Annotated[Decimal, Field(gt=0, le=1)] = Decimal("0.2")
    transform_timeframe: Literal["M1", "M5", "M15", "H1", "H4", "D1"] | None = None
    transformation_reason: str | None = Field(default=None, max_length=1000)

    @field_validator("source_timezone")
    @classmethod
    def zone(cls, value: str) -> str:
        return valid_timezone(value)

    @field_validator("price_increment", "spike_fraction", mode="before")
    @classmethod
    def exact(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("Decimal strings required")
        return value

    @model_validator(mode="after")
    def coherent(self) -> "ImportSpec":
        if self.end <= self.start or (self.end - self.start).days > 3660:
            raise ValueError("Import range must be positive and at most ten years")
        if self.data_type == "TICK" and self.timeframe != "TICK":
            raise ValueError("Ticks require TICK timeframe")
        if self.data_type == "BAR" and self.timeframe == "TICK":
            raise ValueError("Bars require a bar timeframe")
        if self.transform_timeframe:
            if self.data_type != "BAR" or not self.transformation_reason:
                raise ValueError("Aggregation requires bars and an explicit transformation reason")
            if TIMEFRAMES[self.transform_timeframe] <= TIMEFRAMES[self.timeframe]:
                raise ValueError("Only coarser timeframe aggregation is permitted")
        return self


class Row(Input):
    event_time: AwareDatetime
    observed_at: AwareDatetime
    available_at: AwareDatetime
    published_at: AwareDatetime | None = None
    original_timestamp: str
    source_timezone: str
    sequence: int = Field(ge=0)
    event_id: str = ""
    revision: int = Field(ge=0, default=0)
    bid: Decimal | None = None
    ask: Decimal | None = None
    spread: Decimal | None = None
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None
    price: Decimal | None = None
    volume: Decimal | None = None
    tick_volume: Decimal | None = None
    value: Decimal | None = None
    symbol: str | None = None
    session_end: AwareDatetime | None = None


class ProviderView(Input):
    id: UUID
    name: str
    adapter: str
    rights_reference: str
    attribution: str
    capabilities: dict[str, object]


class JobView(Input):
    id: UUID
    dataset_id: UUID
    state: str
    attempts: int
    progress_rows: int
    cancel_requested: bool
    error_code: str | None
    next_attempt_at: datetime
    created_at: datetime


class DatasetView(Input):
    id: UUID
    version: int
    account_id: UUID
    provider_id: UUID
    instrument_id: UUID
    symbol: str
    spec: ImportSpec
    status: str
    record_count: int
    earliest: datetime | None
    latest: datetime | None
    coverage_pct: str | None
    quality: dict[str, object]
    manifest_sha256: str | None
    created_at: datetime
    published_at: datetime | None


class DatasetPage(Input):
    items: list[DatasetView]
    total: int
    offset: int
    limit: int


class Sample(Input):
    items: list[Row]
    limit: int
    truncated: bool
    dataset_id: UUID
    decision_at: datetime
    quality_status: str
    provenance: str
    research_eligible: bool


class Comparison(Input):
    left: UUID
    right: UUID
    same_series: bool
    same_input: bool
    row_count_delta: int
    left_status: str
    right_status: str


class AsOfRequest(Input):
    account_id: UUID
    dataset_ids: list[UUID] = Field(min_length=1, max_length=5)
    start: AwareDatetime
    decision_at: AwareDatetime
    sequence_cutoffs: dict[UUID, Annotated[int, Field(ge=0)]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def cutoff_scope(self) -> "AsOfRequest":
        if not self.sequence_cutoffs.keys() <= set(self.dataset_ids):
            raise ValueError("Sequence cutoffs must belong to requested datasets")
        return self


class AsOfResult(Input):
    decision_at: datetime
    observations: dict[str, Row | None]
