"""Chunked Parquet normalization/quality, bounded queries and immutable manifests."""

import csv
import hashlib
import io
import json
import tempfile
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from packages.market.contracts import ImportSpec, Row
from packages.market.providers import adapter_for
from packages.market.quality import DECIMALS, Quality, normalize
from packages.market.storage import DataIntegrityError, ObjectStore
from packages.market.time import aggregate, visible

CHUNK = 10000


class QueryBudgetExceeded(ValueError):
    pass


SCHEMA = pa.schema(
    [
        (
            name,
            pa.decimal128(38, 12)
            if name in DECIMALS
            else pa.timestamp("us", tz="UTC")
            if name in {"event_time", "available_at", "observed_at", "published_at", "session_end"}
            else pa.int64()
            if name in {"sequence", "revision"}
            else pa.string(),
        )
        for name in Row.model_fields
    ]
)
RAW_SCHEMA = pa.schema([("source_row", pa.int64()), ("payload_json", pa.string())])


def input_rows(
    content: bytes, spec: ImportSpec, adapter: str, observed: datetime
) -> Iterator[dict[str, Any]]:
    adapted = adapter_for(adapter).source_rows(content, observed)
    if adapted is not None:
        yield from adapted
    elif spec.format == "CSV":
        source = io.StringIO(content.decode("utf-8-sig"))
        reader = csv.DictReader(source)
        if (
            not reader.fieldnames
            or len(reader.fieldnames) > 40
            or len(set(reader.fieldnames)) != len(reader.fieldnames)
        ):
            raise ValueError("CSV header must contain unique bounded columns")
        for row in reader:
            if None in row or any(len(str(v)) > 4096 for v in row.values()):
                raise ValueError("Malformed or oversized CSV record")
            yield dict(row)
    else:
        parquet = pq.ParquetFile(io.BytesIO(content))
        if parquet.metadata.num_rows > 1000000 or parquet.metadata.num_columns > 40:
            raise ValueError("Parquet dimensions exceed import limits")
        if (
            sum(
                parquet.metadata.row_group(i).total_byte_size for i in range(parquet.num_row_groups)
            )
            > 128 * 1024 * 1024
        ):
            raise ValueError("Parquet uncompressed payload exceeds memory budget")
        for batch in parquet.iter_batches(batch_size=CHUNK):
            yield from batch.to_pylist()


def parquet_bytes(rows: list[dict[str, Any]], schema: Any) -> bytes:
    buffer = io.BytesIO()
    pq.write_table(
        pa.Table.from_pylist(rows, schema=schema), buffer, compression="zstd", row_group_size=CHUNK
    )
    return buffer.getvalue()


def process(
    content: bytes,
    spec: ImportSpec,
    adapter: str,
    store: ObjectStore,
    prefix: str,
    observed: datetime,
    max_rows: int,
    heartbeat: Any,
    revision_warning: bool = False,
) -> dict[str, Any]:
    artifacts: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="market-quality-") as directory:
        quality = Quality(spec, Path(directory) / "seen.sqlite")
        if revision_warning:
            quality.issue("UNEXPECTED_SOURCE_REVISION", 0, False)
        raw_batch: list[dict[str, Any]] = []
        normalized: list[dict[str, Any]] = []
        part = 0

        def publish(rows: list[dict[str, Any]], layer: str, schema: Any) -> None:
            nonlocal part
            if not rows:
                return
            groups: dict[str, list[dict[str, Any]]] = {}
            for item in rows:
                month = str(item.get("event_time", item.get("period", "unknown")))[:7]
                groups.setdefault(month, []).append(item)
            for month, group in groups.items():
                data = parquet_bytes(group, schema)
                digest = hashlib.sha256(data).hexdigest()
                info = store.put(f"{prefix}/{month}/{layer}-{part:06d}-{digest}.parquet", data)
                part += 1
                info.update(layer=layer, rows=len(group), period=month)
                if layer != "raw":
                    times = [item["event_time"] for item in group]
                    info.update(earliest=min(times).isoformat(), latest=max(times).isoformat())
                artifacts.append(info)

        try:
            for number, raw in enumerate(input_rows(content, spec, adapter, observed), 1):
                if number > max_rows:
                    raise ValueError("Row quota exceeded")
                if any(len(str(value)) > 4096 for value in raw.values()):
                    raise ValueError("Source cell exceeds import size limit")
                raw_batch.append(
                    {
                        "source_row": number,
                        "payload_json": json.dumps(raw, sort_keys=True, default=str),
                    }
                )
                try:
                    row = normalize(raw, spec, number)
                except (ValueError, TypeError, ArithmeticError):
                    quality.issue("INVALID_ROW_SCHEMA_OR_TIME", number)
                else:
                    raw_batch[-1]["period"] = row.event_time.strftime("%Y-%m")
                    quality.accept(row, raw, number)
                    normalized.append(row.model_dump())
                if number % CHUNK == 0:
                    publish(raw_batch, "raw", RAW_SCHEMA)
                    publish(normalized, "normalized", SCHEMA)
                    raw_batch = []
                    normalized = []
                    heartbeat(number)
            publish(raw_batch, "raw", RAW_SCHEMA)
            publish(normalized, "normalized", SCHEMA)
            heartbeat(quality.count)
            report = quality.report()
            report["raw_record_count"] = sum(
                int(str(a["rows"])) for a in artifacts if a["layer"] == "raw"
            )
            if spec.transform_timeframe and report["status"] == "VALID":
                try:
                    converted = aggregate(
                        read_rows(store, artifacts), spec.timeframe, spec.transform_timeframe
                    )
                    chunk = []
                    for row in converted:
                        chunk.append(row.model_dump())
                        if len(chunk) == CHUNK:
                            publish(chunk, "derived", SCHEMA)
                            chunk = []
                    publish(chunk, "derived", SCHEMA)
                except ValueError:
                    quality.issue("INCOMPLETE_AGGREGATION", 0)
                    report = quality.report()
            return {
                "quality": report,
                "artifacts": artifacts,
                "earliest": quality.first.event_time if quality.first else None,
                "latest": quality.last.event_time if quality.last else None,
            }
        finally:
            quality.close()


def read_rows(
    store: ObjectStore,
    artifacts: list[dict[str, object]],
    *,
    layer: str = "normalized",
    start: datetime | None = None,
    end: datetime | None = None,
) -> Iterator[Row]:
    for artifact in artifacts:
        if artifact["layer"] != layer:
            continue
        if start and datetime.fromisoformat(str(artifact["latest"])) < start:
            continue
        if end and datetime.fromisoformat(str(artifact["earliest"])) >= end:
            continue
        source = pq.ParquetFile(io.BytesIO(store.get(artifact)))
        for batch in source.iter_batches(batch_size=CHUNK):
            for value in batch.to_pylist():
                row = Row.model_validate(value)
                if (start is None or row.event_time >= start) and (
                    end is None or row.event_time < end
                ):
                    yield row


def sample(
    store: ObjectStore,
    artifacts: list[dict[str, object]],
    start: datetime,
    end: datetime,
    decision: datetime,
    limit: int,
    layer: str = "normalized",
    sequence_cutoff: int | None = None,
) -> tuple[list[Row], bool]:
    result: list[Row] = []
    bounded_end = min(end, decision + timedelta(microseconds=1))
    for number, row in enumerate(
        read_rows(store, artifacts, layer=layer, start=start, end=bounded_end)
    ):
        if number >= 100000:
            raise QueryBudgetExceeded("Narrow the range; scan budget reached")
        if visible(row, decision, sequence_cutoff):
            if len(result) == limit:
                return result, True
            result.append(row)
    return result, False


def manifest_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()


def verify_manifest(store: ObjectStore, key: str, version: str, digest: str) -> dict[str, Any]:
    response = store.client.stat_object(store.bucket, key, version_id=version)
    content = store.get({"key": key, "version": version, "sha256": digest, "bytes": response.size})
    value = json.loads(content)
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise DataIntegrityError("Invalid dataset manifest")
    return value
