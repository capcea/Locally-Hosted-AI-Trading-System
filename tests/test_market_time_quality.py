"""Explicit synthetic fixtures for time, quality and leakage invariants."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from packages.market.contracts import ImportSpec
from packages.market.processing import SCHEMA, input_rows, parquet_bytes
from packages.market.quality import Quality, normalize
from packages.market.time import aggregate, asof, source_time

NOW = datetime(2024, 1, 2, tzinfo=UTC)


def spec(**changes: object) -> ImportSpec:
    return ImportSpec.model_validate(
        {
            "provider_id": uuid4(),
            "instrument_id": uuid4(),
            "account_id": uuid4(),
            "source_symbol": "EURUSD.test",
            "data_type": "BAR",
            "timeframe": "M1",
            "start": NOW,
            "end": NOW + timedelta(minutes=5),
            "provenance": "SYNTHETIC_TEST_FIXTURE",
            "calendar": {"verified_until": NOW + timedelta(days=2), "source": "synthetic calendar"},
            **changes,
        }
    )


def raw(number: int = 0, /, **changes: object) -> dict[str, object]:
    t = NOW + timedelta(minutes=number)
    return {
        "event_time": t.isoformat(),
        "observed_at": (t + timedelta(minutes=1)).isoformat(),
        "available_at": (t + timedelta(minutes=1)).isoformat(),
        "open": "1.1000",
        "high": "1.1002",
        "low": "1.0998",
        "close": "1.1001",
        "volume": "10",
        "sequence": str(number),
        **changes,
    }


def test_dst_requires_fold_and_rejects_nonexistent_times() -> None:
    with pytest.raises(ValueError, match="Ambiguous"):
        source_time("2024-11-03T01:30:00", "America/New_York")
    first = source_time("2024-11-03T01:30:00", "America/New_York", "0")
    second = source_time("2024-11-03T01:30:00", "America/New_York", "1")
    assert second - first == timedelta(hours=1)
    with pytest.raises(ValueError, match="Nonexistent"):
        source_time("2024-03-10T02:30:00", "America/New_York")
    with pytest.raises(ValueError, match="disagrees"):
        source_time("2024-01-02T12:00:00+03:00", "America/New_York")


def test_future_cross_asset_news_and_revisions_are_not_visible() -> None:
    base = normalize(raw(), spec(), 1)
    decision = NOW + timedelta(minutes=1)
    future = base.model_copy(
        update={
            "observed_at": decision + timedelta(seconds=1),
            "available_at": decision + timedelta(seconds=1),
            "close": Decimal("99"),
        }
    )
    assert asof([base, future], decision) == base
    release = base.model_copy(
        update={"event_id": "CPI", "published_at": decision, "value": Decimal("1"), "revision": 0}
    )
    revision = release.model_copy(
        update={
            "published_at": decision + timedelta(days=1),
            "available_at": decision + timedelta(days=1),
            "value": Decimal("2"),
            "revision": 1,
        }
    )
    assert asof([release, revision], decision) == release
    assert asof([future], decision) is None
    assert (
        asof([base.model_copy(update={"event_time": decision + timedelta(seconds=1)})], decision)
        is None
    )


def test_aggregation_is_exact_deterministic_and_not_available_before_close() -> None:
    rows = [normalize(raw(i), spec(), i) for i in range(5)]
    result = list(aggregate(rows, "M1", "M5"))
    assert len(result) == 1 and result[0].volume == Decimal(50)
    assert result[0].open == rows[0].open and result[0].close == rows[-1].close
    assert result[0].available_at == NOW + timedelta(minutes=5)
    assert result == list(aggregate(rows, "M1", "M5"))
    assert asof(result, NOW + timedelta(minutes=4)) is None
    with pytest.raises(ValueError, match="incomplete"):
        list(aggregate(rows[:-1], "M1", "M5"))


@pytest.mark.parametrize(
    "change,code",
    [
        ({"bid": "2", "ask": "1"}, "CROSSED_QUOTE"),
        ({"bid": "1", "ask": "2", "spread": "0.1"}, "SPREAD_MISMATCH"),
        ({"open": "0"}, "NONPOSITIVE_PRICE"),
        ({"volume": "-1"}, "NEGATIVE_SPREAD_OR_VOLUME"),
        ({"available_at": NOW.isoformat()}, "BAR_AVAILABLE_BEFORE_CLOSE"),
        ({"symbol": "different.broker.suffix"}, "SOURCE_SYMBOL_MISMATCH"),
        ({"high": "1"}, "OHLC_INCONSISTENT"),
    ],
)
def test_bad_market_records_fail_closed(
    tmp_path: Path, change: dict[str, object], code: str
) -> None:
    config = spec()
    validator = Quality(config, tmp_path / "quality.db")
    try:
        value = raw(**change)
        validator.accept(normalize(value, config, 1), value, 1)
        report = validator.report()
        assert code in report["counts"] and report["status"] == "REJECTED"
    finally:
        validator.close()


def test_duplicates_gaps_ordering_holiday_and_unknown_calendar(tmp_path: Path) -> None:
    config = spec()
    validator = Quality(config, tmp_path / "quality.db")
    try:
        for i in (2, 0, 0):
            value = raw(i)
            validator.accept(normalize(value, config, i), value, i)
        report = validator.report()
        assert {"DUPLICATE_RECORD", "MISSING_BARS", "OUT_OF_ORDER"} <= set(report["counts"])
        assert report["coverage_pct"] == "40" and report["unique_bar_slots"] == 2
    finally:
        validator.close()
    holiday = spec(
        calendar={
            "verified_until": NOW + timedelta(days=2),
            "source": "synthetic",
            "holidays": [NOW.date()],
        }
    )
    validator = Quality(holiday, tmp_path / "holiday.db")
    try:
        validator.accept(normalize(raw(), holiday, 1), raw(), 1)
        assert "CLOSED_SESSION_OR_HOLIDAY" in validator.report()["counts"]
    finally:
        validator.close()


def test_parquet_roundtrip_and_exact_prices() -> None:
    config = spec(format="PARQUET")
    rows = [normalize(raw(i), config, i) for i in range(5)]
    content = parquet_bytes([r.model_dump() for r in rows], SCHEMA)
    imported = list(input_rows(content, config, "LOCAL", NOW))
    assert [normalize(r, config, i) for i, r in enumerate(imported)] == rows


def test_same_timestamp_ticks_keep_explicit_sequence_and_unknown_volume() -> None:
    config = spec(data_type="TICK", timeframe="TICK")
    first = normalize(raw(sequence="1", bid="1", ask="1.1", volume=""), config, 1)
    second = first.model_copy(update={"sequence": 2, "bid": Decimal("1.01")})
    assert asof([first, second], first.available_at) == second
    assert asof([first, second], first.available_at, sequence_cutoff=1) == first
    assert first.volume is None and first.spread == Decimal("0.1")


def test_rate_limit_provider_failure_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    from packages.market import providers
    from packages.market.providers import ProviderFailure, retry_delay

    config = spec(source_symbol="D.USD.EUR.SP00.A", data_type="REFERENCE", timeframe="D1")
    actual_client = httpx.Client

    def limited(**kwargs: object) -> httpx.Client:
        return actual_client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(429, headers={"Retry-After": "120"})
            )
        )

    monkeypatch.setattr(httpx, "Client", limited)
    with pytest.raises(ProviderFailure) as error:
        providers.ecb_download(config, "EURUSD")
    assert error.value.code == "PROVIDER_RATE_LIMIT" and error.value.delay == 120
    assert retry_delay(1, error.value.delay) == 120 and retry_delay(3) == 8
    with pytest.raises(ProviderFailure, match="UNSUPPORTED"):
        providers.ecb_download(config, "XAUUSD")


def test_spike_and_unknown_calendar_cannot_be_research_valid(tmp_path: Path) -> None:
    config = spec(calendar=None)
    quality = Quality(config, tmp_path / "spike.db")
    try:
        first = raw()
        second = raw(1, open="2", low="2", high="2", close="2")
        quality.accept(normalize(first, config, 0), first, 0)
        quality.accept(normalize(second, config, 1), second, 1)
        report = quality.report()
        assert report["status"] == "DEGRADED"
        assert {"PRICE_SPIKE", "SESSION_CALENDAR_UNVERIFIED"} <= set(report["counts"])
    finally:
        quality.close()


@pytest.mark.parametrize("field", ["source_timezone", "calendar"])
def test_unknown_timezones_are_schema_rejections(field: str) -> None:
    from pydantic import ValidationError

    change: dict[str, object] = (
        {"source_timezone": "Invalid/Unknown_Source_Zone"}
        if field == "source_timezone"
        else {
            "calendar": {
                "timezone": "Invalid/Unknown_Source_Zone",
                "verified_until": NOW + timedelta(days=2),
                "source": "synthetic calendar",
            }
        }
    )
    with pytest.raises(ValidationError, match="Unknown or invalid IANA timezone"):
        spec(**change)
