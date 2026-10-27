"""UTC/DST validation and conservative point-in-time operations."""

from collections.abc import Iterable, Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from packages.market.contracts import TIMEFRAMES, Row


def source_time(value: str, zone: str, fold: str | None = None) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    tz = ZoneInfo(zone)
    if parsed.tzinfo:
        if parsed.utcoffset() != parsed.astimezone(tz).utcoffset():
            raise ValueError("Source offset disagrees with declared timezone")
        return parsed.astimezone(UTC)
    candidates = [parsed.replace(tzinfo=tz, fold=n) for n in (0, 1)]
    valid = [
        c for c in candidates if c.astimezone(UTC).astimezone(tz).replace(tzinfo=None) == parsed
    ]
    if not valid:
        raise ValueError("Nonexistent DST timestamp")
    if candidates[0].utcoffset() != candidates[1].utcoffset():
        if fold not in {"0", "1"}:
            raise ValueError("Ambiguous DST timestamp needs explicit fold")
        return candidates[int(fold)].astimezone(UTC)
    return valid[0].astimezone(UTC)


def utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Availability/publication/observation timestamps must include an offset")
    return parsed.astimezone(UTC)


def visible(row: Row, decision: datetime, sequence_cutoff: int | None = None) -> bool:
    if decision.tzinfo is None:
        raise ValueError("Decision cutoff must be aware")
    return (
        row.event_time <= decision
        and row.available_at <= decision
        and row.observed_at <= decision
        and (row.published_at is None or row.published_at <= decision)
        and (
            sequence_cutoff is None
            or row.available_at != decision
            or row.sequence <= sequence_cutoff
        )
    )


def asof(rows: Iterable[Row], decision: datetime, sequence_cutoff: int | None = None) -> Row | None:
    # A revised release cannot replace the vintage that was actually available at this cutoff.
    return max(
        (r for r in rows if visible(r, decision, sequence_cutoff)),
        key=lambda r: (r.event_time, r.available_at, r.revision, r.sequence),
        default=None,
    )


def aggregate(rows: Iterable[Row], source: str, target: str) -> Iterator[Row]:
    width, step = TIMEFRAMES[target], TIMEFRAMES[source]
    if not step or width <= step or width % step:
        raise ValueError("Only integral coarser bar aggregation is permitted")
    bucket: list[Row] = []
    previous: tuple[datetime, int] | None = None

    def emit(values: list[Row]) -> Row:
        start = datetime.fromtimestamp(int(values[0].event_time.timestamp()) // width * width, UTC)
        expected = [start + timedelta(seconds=n * step) for n in range(width // step)]
        if [r.event_time for r in values] != expected:
            raise ValueError("Cannot aggregate an incomplete or duplicate bar bucket")
        if any(
            any(getattr(r, field) is None for field in ("open", "high", "low", "close"))
            for r in values
        ):
            raise ValueError("Bar OHLC required")
        return values[0].model_copy(
            update={
                "event_time": start,
                "original_timestamp": start.isoformat(),
                "source_timezone": "UTC",
                "open": values[0].open,
                "high": max(r.high for r in values if r.high is not None),
                "low": min(r.low for r in values if r.low is not None),
                "close": values[-1].close,
                "available_at": max(
                    start + timedelta(seconds=width), *(r.available_at for r in values)
                ),
                "observed_at": max(r.observed_at for r in values),
                "published_at": max(
                    (r.published_at for r in values if r.published_at), default=None
                ),
                "volume": sum((r.volume for r in values if r.volume is not None), Decimal(0))
                if all(r.volume is not None for r in values)
                else None,
                "tick_volume": sum(
                    (r.tick_volume for r in values if r.tick_volume is not None), Decimal(0)
                )
                if all(r.tick_volume is not None for r in values)
                else None,
                "spread": None,
                "bid": None,
                "ask": None,
            }
        )

    for row in rows:
        key = (row.event_time, row.sequence)
        if previous is not None and key <= previous:
            raise ValueError("Aggregation requires strictly ordered input")
        previous = key
        if (
            bucket
            and int(row.event_time.timestamp()) // width
            != int(bucket[0].event_time.timestamp()) // width
        ):
            yield emit(bucket)
            bucket = []
        bucket.append(row)
    if bucket:
        yield emit(bucket)
