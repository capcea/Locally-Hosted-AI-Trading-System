"""Streaming validation. Suspicious input is recorded, never silently repaired."""

import hashlib
import json
import sqlite3
from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from packages.market.contracts import TIMEFRAMES, ImportSpec, Row
from packages.market.time import source_time, utc

DECIMALS = (
    "bid",
    "ask",
    "spread",
    "open",
    "high",
    "low",
    "close",
    "price",
    "volume",
    "tick_volume",
    "value",
)


def normalize(raw: dict[str, Any], spec: ImportSpec, number: int) -> Row:
    values: dict[str, Any] = {}
    for name in DECIMALS:
        value = raw.get(name)
        if value is not None and value != "":
            if isinstance(value, float):
                raise ValueError("Floating point input loses exact source prices")
            decimal = Decimal(str(value))
            if (
                not decimal.is_finite()
                or int(decimal.as_tuple().exponent) < -12
                or len(decimal.as_tuple().digits) > 38
            ):
                raise ValueError("Decimal exceeds exact storage precision")
            values[name] = decimal
    event_time = str(raw.get("original_timestamp") or raw.get("event_time", ""))
    values.update(
        event_time=source_time(event_time, spec.source_timezone, raw.get("fold")),
        original_timestamp=event_time,
        source_timezone=spec.source_timezone,
        observed_at=utc(str(raw.get("observed_at", ""))),
        available_at=utc(str(raw.get("available_at", ""))),
        published_at=utc(str(raw["published_at"])) if raw.get("published_at") else None,
        sequence=number if raw.get("sequence") in {None, ""} else int(raw["sequence"]),
        revision=int(raw.get("revision") or 0),
        event_id=str(raw.get("event_id") or ""),
        symbol=raw.get("symbol") or None,
        session_end=utc(str(raw["session_end"])) if raw.get("session_end") else None,
    )
    if (
        values.get("bid") is not None
        and values.get("ask") is not None
        and values.get("spread") is None
    ):
        values["spread"] = values["ask"] - values["bid"]
    return Row.model_validate(values)


def in_session(row: Row, spec: ImportSpec) -> bool:
    calendar = spec.calendar
    if calendar is None:
        return True
    local = row.event_time.astimezone(ZoneInfo(calendar.timezone))
    minute = local.hour * 60 + local.minute
    return (
        local.weekday() in calendar.weekdays
        and local.date() not in calendar.holidays
        and calendar.opens <= minute < calendar.closes
    )


class Quality:
    def __init__(self, spec: ImportSpec, path: Path):
        self.spec = spec
        self.counts: Counter[str] = Counter()
        self.samples: dict[str, list[int]] = {}
        self.blocking: set[str] = set()
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE seen (key BLOB PRIMARY KEY) WITHOUT ROWID")
        self.previous: Row | None = None
        self.count = 0
        self.unique_bar_slots = 0
        self.first: Row | None = None
        self.last: Row | None = None
        self.spread_min: Decimal | None = None
        self.spread_max: Decimal | None = None
        self.spread_sum = Decimal(0)
        self.spread_count = 0
        self.spread_histogram: Counter[str] = Counter()
        self.observed_gaps: list[dict[str, str]] = []
        if spec.calendar is None:
            self.issue("SESSION_CALENDAR_UNVERIFIED", 0, False)
        elif spec.calendar.verified_until < spec.end:
            self.issue("SESSION_CALENDAR_EXPIRED", 0, True)

    def issue(self, code: str, number: int, blocking: bool = True) -> None:
        self.counts[code] += 1
        if len(self.samples.setdefault(code, [])) < 10:
            self.samples[code].append(number)
        if blocking:
            self.blocking.add(code)

    def accept(self, row: Row, raw: dict[str, Any], number: int) -> None:
        self.count += 1
        if self.first is None or row.event_time < self.first.event_time:
            self.first = row
        if self.last is None or row.event_time > self.last.event_time:
            self.last = row
        spec = self.spec
        if not spec.start <= row.event_time < spec.end:
            self.issue("OUTSIDE_REQUESTED_RANGE", number)
        if row.symbol and row.symbol != spec.source_symbol:
            self.issue("SOURCE_SYMBOL_MISMATCH", number)
        if row.available_at < row.observed_at or (
            row.published_at and row.available_at < row.published_at
        ):
            self.issue("AVAILABILITY_PRECEDES_OBSERVATION", number)
        if spec.data_type in {"BAR", "TICK", "REFERENCE"} and row.observed_at < row.event_time:
            self.issue("OBSERVATION_PRECEDES_PRICE", number)
        if spec.data_type == "BAR":
            width = TIMEFRAMES[spec.timeframe]
            if row.event_time.timestamp() % width:
                self.issue("MISALIGNED_BAR", number)
            if row.available_at < row.event_time + timedelta(seconds=width):
                self.issue("BAR_AVAILABLE_BEFORE_CLOSE", number)
            prices = [row.open, row.high, row.low, row.close]
            if any(p is None for p in prices):
                self.issue("OHLC_MISSING", number)
            elif (
                row.low is not None
                and row.high is not None
                and (
                    row.low > min(p for p in prices if p is not None)
                    or row.high < max(p for p in prices if p is not None)
                )
            ):
                self.issue("OHLC_INCONSISTENT", number)
        if spec.data_type == "TICK" and (row.bid is None or row.ask is None):
            self.issue("BID_ASK_MISSING", number)
        if spec.data_type == "REFERENCE" and row.price is None:
            self.issue("REFERENCE_PRICE_MISSING", number)
        if spec.data_type == "EVENT" and (not row.event_id or row.published_at is None):
            self.issue("EVENT_VINTAGE_MISSING", number)
        if spec.data_type == "SESSION" and (
            row.session_end is None or row.session_end <= row.event_time
        ):
            self.issue("SESSION_INTERVAL_INVALID", number)
        for name in DECIMALS:
            value = getattr(row, name)
            if value is not None and name not in {"value", "spread", "volume", "tick_volume"}:
                if value <= 0:
                    self.issue("NONPOSITIVE_PRICE", number)
                if spec.price_increment and value % spec.price_increment:
                    self.issue("PRICE_INCREMENT_MISMATCH", number)
            if value is not None and name in {"spread", "volume", "tick_volume"} and value < 0:
                self.issue("NEGATIVE_SPREAD_OR_VOLUME", number)
        if row.bid is not None and row.ask is not None:
            if row.ask < row.bid:
                self.issue("CROSSED_QUOTE", number)
            if row.spread != row.ask - row.bid:
                self.issue("SPREAD_MISMATCH", number)
        if row.spread is not None:
            band = (
                "zero"
                if row.spread == 0
                else "lt_0.0001"
                if row.spread < Decimal("0.0001")
                else "lt_0.001"
                if row.spread < Decimal("0.001")
                else "lt_0.01"
                if row.spread < Decimal("0.01")
                else "gte_0.01"
            )
            self.spread_histogram[band] += 1
            self.spread_count += 1
            self.spread_sum += row.spread
            self.spread_min = (
                min(self.spread_min, row.spread) if self.spread_min is not None else row.spread
            )
            self.spread_max = (
                max(self.spread_max, row.spread) if self.spread_max is not None else row.spread
            )
        if not in_session(row, spec):
            self.issue("CLOSED_SESSION_OR_HOLIDAY", number)
        previous = self.previous
        if (
            previous
            and spec.data_type == "BAR"
            and row.event_time > previous.event_time + timedelta(seconds=TIMEFRAMES[spec.timeframe])
            and len(self.observed_gaps) < 20
        ):
            self.observed_gaps.append(
                {
                    "start": (
                        previous.event_time + timedelta(seconds=TIMEFRAMES[spec.timeframe])
                    ).isoformat(),
                    "end": row.event_time.isoformat(),
                }
            )
        if previous and (row.event_time, row.sequence) < (previous.event_time, previous.sequence):
            self.issue("OUT_OF_ORDER", number)
        price = row.close or row.price or row.bid
        last_price = (previous.close or previous.price or previous.bid) if previous else None
        if price is not None and last_price and abs(price / last_price - 1) > spec.spike_fraction:
            self.issue("PRICE_SPIKE", number, False)
        # Bars have one observation per bucket. Explicit tick sequences distinguish same-ms quotes.
        identity = [row.event_time.isoformat()]
        if spec.data_type == "EVENT":
            identity.extend([row.event_id, str(row.revision)])
        elif spec.data_type == "TICK":
            identity.append(
                str(row.sequence)
                if raw.get("sequence") not in {None, ""}
                else json.dumps(raw, sort_keys=True, default=str)
            )
        digest = hashlib.sha256(json.dumps(identity).encode()).digest()
        try:
            self.db.execute("INSERT INTO seen VALUES (?)", (digest,))
            if (
                spec.data_type == "BAR"
                and spec.start <= row.event_time < spec.end
                and in_session(row, spec)
                and row.event_time.timestamp() % TIMEFRAMES[spec.timeframe] == 0
            ):
                self.unique_bar_slots += 1
        except sqlite3.IntegrityError:
            self.issue("DUPLICATE_RECORD", number)
        self.previous = row

    def report(self) -> dict[str, Any]:
        if not self.count:
            self.issue("EMPTY_DATASET", 0)
        expected: int | None = None
        if self.spec.data_type == "BAR" and self.spec.calendar is not None:
            step = TIMEFRAMES[self.spec.timeframe]
            cursor = datetime.fromtimestamp(int(self.spec.start.timestamp()) // step * step, UTC)
            if cursor < self.spec.start:
                cursor += timedelta(seconds=step)
            expected = 0
            while cursor < self.spec.end:
                dummy = Row(
                    event_time=cursor,
                    observed_at=cursor,
                    available_at=cursor,
                    original_timestamp=cursor.isoformat(),
                    source_timezone="UTC",
                    sequence=0,
                )
                expected += int(in_session(dummy, self.spec))
                cursor += timedelta(seconds=step)
            if self.unique_bar_slots < expected:
                self.issue("MISSING_BARS", 0, False)
                self.counts["MISSING_BARS"] = expected - self.unique_bar_slots
        coverage = (
            str(min(Decimal(100), Decimal(self.unique_bar_slots) * 100 / expected))
            if expected
            else None
        )
        state = "REJECTED" if self.blocking else "DEGRADED" if self.counts else "VALID"
        return {
            "status": state,
            "counts": dict(self.counts),
            "samples": self.samples,
            "blocking_codes": sorted(self.blocking),
            "record_count": self.count,
            "expected_records": expected,
            "unique_bar_slots": self.unique_bar_slots,
            "coverage_pct": coverage,
            "observed_gaps_including_closed_sessions": self.observed_gaps,
            "coverage_basis": "DECLARED_SESSION_BAR_GRID"
            if expected
            else "UNKNOWN_NO_EXPECTED_TICK_COUNT",
            "spread": {
                "min": str(self.spread_min) if self.spread_min is not None else None,
                "max": str(self.spread_max) if self.spread_max is not None else None,
                "mean": str(self.spread_sum / self.spread_count) if self.spread_count else None,
                "count": self.spread_count,
                "histogram_price_units": dict(self.spread_histogram),
            },
        }

    def close(self) -> None:
        self.db.close()
