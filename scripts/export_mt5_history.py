"""Read-only export on an explicitly authorized, already logged-in Windows terminal.

Never invoked by API/data worker. No login, password, order or executor method exists here.
The optional official Windows package must be installed by the terminal operator.
"""

import argparse
import csv
import importlib
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def export(
    reader: Any, symbol: str, start: datetime, end: datetime, target: Path, timeframe: str
) -> int:

    if start.tzinfo is None or end.tzinfo is None or end <= start:
        raise ValueError("Explicit aware positive UTC range required")
    info = reader.symbol_info(symbol)
    if info is None:
        raise RuntimeError("Terminal has no such source symbol")
    digits = int(info.digits)
    if not 0 <= digits <= 12:
        raise ValueError("Source display precision exceeds normalized storage")
    observed = datetime.now(UTC).isoformat()
    count = 0
    with target.open("x", newline="", encoding="utf-8") as output:
        fields = [
            "event_time",
            "observed_at",
            "available_at",
            "sequence",
            "symbol",
            "bid",
            "ask",
            "open",
            "high",
            "low",
            "close",
            "tick_volume",
            "volume",
            "spread_points",
        ]
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        cursor = start.astimezone(UTC)
        while cursor < end:
            until = min(cursor + timedelta(days=1), end)
            rows = (
                reader.copy_ticks_range(symbol, cursor, until, reader.COPY_TICKS_INFO)
                if timeframe == "TICK"
                else reader.copy_rates_range(
                    symbol, getattr(reader, f"TIMEFRAME_{timeframe}"), cursor, until
                )
            )
            if rows is None:
                raise RuntimeError(
                    "Authorized terminal history retrieval failed; partial export is unusable"
                )
            for row in rows:
                timestamp = (
                    float(row["time_msc"]) / 1000 if timeframe == "TICK" else int(row["time"])
                )
                when = datetime.fromtimestamp(timestamp, UTC)
                if not cursor <= when < until:
                    continue
                result = {
                    "event_time": when.isoformat(),
                    "observed_at": observed,
                    "available_at": observed,
                    "sequence": count,
                    "symbol": symbol,
                }
                names = ("bid", "ask") if timeframe == "TICK" else ("open", "high", "low", "close")
                result.update({key: format(float(row[key]), f".{digits}f") for key in names})
                if timeframe != "TICK":
                    result["tick_volume"] = str(row["tick_volume"])
                    result["volume"] = str(row["real_volume"]) if row["real_volume"] > 0 else ""
                    result["spread_points"] = str(row["spread"])
                writer.writerow(result)
                count += 1
            cursor = until
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorized-local-terminal", action="store_true", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument(
        "--timeframe", choices=["TICK", "M1", "M5", "M15", "H1", "H4", "D1"], required=True
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != "win32":
        raise RuntimeError("BLOCKED: official MT5 history needs an authorized Windows terminal")
    reader = importlib.import_module("MetaTrader5")
    if not reader.initialize():
        raise RuntimeError("Existing authorized terminal connection unavailable")
    try:
        count = export(
            reader,
            args.symbol,
            datetime.fromisoformat(args.start),
            datetime.fromisoformat(args.end),
            args.output,
            args.timeframe,
        )
        print(f"Exported {count} terminal rows; availability conservatively set to export time.")
    finally:
        reader.shutdown()


if __name__ == "__main__":
    main()
