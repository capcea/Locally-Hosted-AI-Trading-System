"""Allowlisted data adapters. No arbitrary HTTP URLs and no broker credentials."""

import csv
import io
import time
from datetime import datetime, timedelta
from typing import Any, Protocol

import httpx

from packages.market.contracts import ImportSpec

ECB_RIGHTS = "https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html"
ECB_API = "https://data-api.ecb.europa.eu/service/data/EXR/"

CAPABILITIES: dict[str, dict[str, object]] = {
    "LOCAL": {"formats": ["CSV", "PARQUET"], "network": False, "resumable": False},
    "ECB": {
        "data_types": ["REFERENCE"],
        "timeframes": ["D1"],
        "bid_ask": False,
        "volume": False,
        "resumable": False,
        "availability": "INGESTION_TIME_CONSERVATIVE",
    },
    "MT5_EXPORT": {
        "formats": ["CSV"],
        "connectivity": "BLOCKED_WITHOUT_AUTHORIZED_WINDOWS_TERMINAL",
        "network": False,
    },
    "PREMIUM": {"status": "NOT_IMPLEMENTED", "network": False},
}


class ProviderFailure(RuntimeError):
    def __init__(self, code: str, delay: int = 0):
        super().__init__(code)
        self.code, self.delay = code, min(3600, max(0, delay))


def ecb_download(spec: ImportSpec, symbol: str) -> bytes:
    # Standard ECB EXR currencies, explicit quote/base direction; never fabricate cross rates.
    quotes = {"EURUSD": "USD", "EURGBP": "GBP", "EURJPY": "JPY", "EURCHF": "CHF", "EURAUD": "AUD"}
    if (
        spec.data_type != "REFERENCE"
        or spec.timeframe != "D1"
        or spec.format != "CSV"
        or spec.source_timezone != "UTC"
        or symbol not in quotes
        or spec.source_symbol != f"D.{quotes[symbol]}.EUR.SP00.A"
    ):
        raise ProviderFailure("ECB_UNSUPPORTED_SYMBOL_OR_TYPE")
    params = {
        "startPeriod": spec.start.date().isoformat(),
        "endPeriod": (spec.end - timedelta(microseconds=1)).date().isoformat(),
        "format": "csvdata",
    }
    try:
        with (
            httpx.Client(timeout=30, follow_redirects=False, trust_env=False) as client,
            client.stream("GET", ECB_API + spec.source_symbol, params=params) as response,
        ):
            if response.status_code == 429:
                retry = response.headers.get("retry-after", "60")
                raise ProviderFailure("PROVIDER_RATE_LIMIT", int(retry) if retry.isdigit() else 60)
            if response.status_code != 200:
                raise ProviderFailure("PROVIDER_HTTP_FAILURE")
            chunks = []
            size = 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > 20 * 1024 * 1024:
                    raise ProviderFailure("PROVIDER_SIZE_LIMIT")
                chunks.append(chunk)
    except httpx.HTTPError as error:
        raise ProviderFailure("PROVIDER_NETWORK_FAILURE") from error
    # Keep the original provider response as the immutable input; normalization occurs in a worker.
    return b"".join(chunks)


def ecb_rows(content: bytes, observed: datetime) -> list[dict[str, Any]]:
    result = []
    for index, row in enumerate(csv.DictReader(io.StringIO(content.decode("utf-8-sig")))):
        result.append(
            {
                "event_time": row["TIME_PERIOD"],
                "observed_at": observed.isoformat(),
                "available_at": observed.isoformat(),
                "price": row["OBS_VALUE"],
                "sequence": index,
                "symbol": row["KEY"].removeprefix("EXR."),
            }
        )
    return result


def retry_delay(attempt: int, provider_delay: int = 0) -> int:
    return int(max(min(300, 2 ** min(attempt, 8)), provider_delay))


def polite_pause() -> None:
    # Data worker rate cap; ECB jobs also share the two-slot global data concurrency gate.
    time.sleep(0.25)


class DataProvider(Protocol):
    network: bool
    allows_upload: bool

    def download(self, spec: ImportSpec, symbol: str) -> bytes: ...
    def source_rows(self, content: bytes, observed: datetime) -> list[dict[str, Any]] | None: ...


class LocalProvider:
    network = False
    allows_upload = True

    def download(self, spec: ImportSpec, symbol: str) -> bytes:
        raise ProviderFailure("PROVIDER_CONNECTIVITY_UNAVAILABLE")

    def source_rows(self, content: bytes, observed: datetime) -> list[dict[str, Any]] | None:
        return None


class ECBProvider(LocalProvider):
    network = True
    allows_upload = False

    def download(self, spec: ImportSpec, symbol: str) -> bytes:
        return ecb_download(spec, symbol)

    def source_rows(self, content: bytes, observed: datetime) -> list[dict[str, Any]] | None:
        return ecb_rows(content, observed)


class PremiumProvider(LocalProvider):
    allows_upload = False


PROVIDERS: dict[str, DataProvider] = {
    "LOCAL": LocalProvider(),
    "MT5_EXPORT": LocalProvider(),
    "ECB": ECBProvider(),
    "PREMIUM": PremiumProvider(),
}


def adapter_for(name: str) -> DataProvider:
    if name not in PROVIDERS:
        raise ProviderFailure("PROVIDER_NOT_IMPLEMENTED")
    return PROVIDERS[name]
