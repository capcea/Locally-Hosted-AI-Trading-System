"""Actual isolated PostgreSQL/Redis/MinIO acceptance, with explicit synthetic prices."""

import hashlib
import io
import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from minio.error import S3Error
from pydantic import SecretStr
from redis import Redis
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from test_phase1_integration import System, close_system, create_system, isolated_config

from apps.api.main import create_app
from packages.market.jobs import QUEUE, Worker
from packages.market.storage import DataIntegrityError, ObjectStore
from scripts.provision_market import provision_storage

pytestmark = pytest.mark.isolated_services


def configure_market(instance: System, bucket: str) -> None:
    isolated = isolated_config()
    user = "market-test-" + isolated.run_id[:12]
    password = isolated.storage_password.get_secret_value()
    endpoint = "http://" + isolated.storage_endpoint
    provision_storage(endpoint, "phase0-test", password, user, password, bucket)
    instance.config = instance.config.model_copy(
        update={
            "object_store_url": endpoint,
            "redis_url": SecretStr(isolated.redis_url),
            "market_bucket": bucket,
            "market_storage_user": SecretStr(user),
            "market_storage_password": SecretStr(password),
        }
    )
    cast(FastAPI, instance.client.app).state.store.engine.dispose()
    instance.client.close()
    instance.client = TestClient(create_app(instance.config))


@pytest.fixture
def market() -> Iterator[System]:
    instance = create_system("p1_market_" + uuid4().hex)
    try:
        configure_market(instance, "market-" + uuid4().hex)
        instance.bootstrap()
        instance.secret, instance.recovery = instance.enroll()
        yield instance
    finally:
        close_system(instance)


def setup_import(instance: System) -> dict[str, Any]:
    def post(path: str, body: dict[str, Any]) -> dict[str, Any]:
        result = instance.post(path, body)
        assert result.status_code == 201, result.text
        return dict(result.json())

    account = instance.account()
    venue = post(
        "/api/v1/records/venues",
        {"kind": "venues", "name": "Synthetic venue", "venue_type": "CUSTOM"},
    )
    instrument = post(
        "/api/v1/records/instruments",
        {
            "kind": "instruments",
            "name": "Synthetic EURUSD",
            "symbol": "EURUSD",
            "asset_class": "FOREX",
            "venue_id": venue["id"],
        },
    )
    provider = post(
        "/api/v1/market/providers",
        {
            "name": "Synthetic CSV fixtures",
            "adapter": "LOCAL",
            "rights_reference": "Synthetic fixtures authored in test suite",
            "attribution": "SYNTHETIC_TEST_FIXTURE",
            "usage_rights_acknowledged": True,
        },
    )
    return {
        "provider_id": provider["id"],
        "account_id": account["id"],
        "instrument_id": instrument["id"],
        "source_symbol": "EURUSD.fixture",
        "data_type": "BAR",
        "timeframe": "M1",
        "format": "CSV",
        "start": "2024-01-02T00:00:00Z",
        "end": "2024-01-02T00:05:00Z",
        "provenance": "SYNTHETIC_TEST_FIXTURE",
        "calendar": {
            "verified_until": "2024-01-03T00:00:00Z",
            "source": "Synthetic session fixture",
        },
    }


def csv_content(*, bad: bool = False) -> bytes:
    lines = ["event_time,observed_at,available_at,open,high,low,close,volume,sequence"]
    for i in range(5):
        lines.append(
            f"2024-01-02T00:0{i}:00Z,2024-01-02T00:0{i + 1}:00Z,"
            f"2024-01-02T00:0{i + 1}:00Z,1.1,1.2,1.0,{'0' if bad else '1.15'},10,{i}"
        )
    return ("\n".join(lines) + "\n").encode()


def submit(instance: System, spec: dict[str, Any], content: bytes | None = None) -> dict[str, Any]:
    response = instance.client.post(
        "/api/v1/market/imports",
        headers=instance.csrf(),
        data={"spec_json": json.dumps(spec)},
        files={
            "file": ("fixture.csv", content if content is not None else csv_content(), "text/csv")
        },
    )
    assert response.status_code == 202, response.text
    return dict(response.json())


def run_worker(instance: System) -> None:
    worker = Worker(instance.config)
    try:
        assert worker.once()
    finally:
        worker.close()


def test_import_parquet_manifest_immutability_idempotency_and_limits(market: System) -> None:
    spec = setup_import(market)
    spec.update(
        transform_timeframe="M5", transformation_reason="Explicit synthetic M1 to M5 acceptance"
    )
    job = submit(market, spec)
    assert submit(market, spec)["id"] == job["id"]
    run_worker(market)
    path = f"/api/v1/market/datasets/{job['dataset_id']}"
    data = market.client.get(path).json()
    assert data["status"] == "VALID" and data["coverage_pct"] == "100" and data["record_count"] == 5
    provenance = market.client.get(path + "/provenance")
    assert provenance.status_code == 200
    manifest = provenance.json()
    store = ObjectStore(market.config)
    raw = [a for a in manifest["artifacts"] if a["layer"] == "raw"][0]
    normalized = [a for a in manifest["artifacts"] if a["layer"] == "normalized"][0]
    assert store.get(raw).startswith(b"PAR1") and store.get(normalized).endswith(b"PAR1")
    assert hashlib.sha256(store.get(raw)).hexdigest() == raw["sha256"]
    with pytest.raises(DataIntegrityError):
        store.get({**normalized, "sha256": "0" * 64})
    with pytest.raises(S3Error):
        store.client.remove_object(store.bucket, str(raw["key"]), version_id=str(raw["version"]))
    before = store.get(raw)
    replacement = store.put(str(raw["key"]), b"different new version")
    assert (
        replacement["version"] != raw["version"] and ObjectStore(market.config).get(raw) == before
    )
    engine = create_engine(market.runtime_url)
    try:
        with pytest.raises(DBAPIError), engine.begin() as connection:
            connection.execute(
                text("UPDATE market_datasets SET status='VALID' WHERE id=:id"),
                {"id": job["dataset_id"]},
            )
    finally:
        engine.dispose()
    params = {
        "start": spec["start"],
        "end": spec["end"],
        "decision_at": "2024-01-02T00:03:00Z",
        "limit": 2,
    }
    sample = market.client.get(path + "/sample", params=params)
    assert (
        sample.status_code == 200
        and len(sample.json()["items"]) == 2
        and sample.json()["truncated"]
    )
    assert sample.json()["items"][0]["close"] == "1.150000000000"
    assert (
        market.client.get(path + "/sample", params={**params, "limit": 1000000}).status_code == 422
    )
    assert market.client.get("/api/v1/audit/verify").json()["valid"]
    derived = market.client.get(
        path + "/sample",
        params={**params, "layer": "derived", "decision_at": "2024-01-02T00:05:00Z"},
    )
    assert derived.status_code == 200 and len(derived.json()["items"]) == 1
    assert derived.json()["items"][0]["volume"] == "50.000000000000"
    before_close = market.client.get(
        path + "/sample",
        params={**params, "layer": "derived", "decision_at": "2024-01-02T00:04:00Z"},
    )
    assert before_close.json()["items"] == []
    result = market.post(
        "/api/v1/market/asof",
        {
            "account_id": spec["account_id"],
            "dataset_ids": [job["dataset_id"]],
            "start": spec["start"],
            "decision_at": "2024-01-02T00:03:00Z",
        },
    )
    assert result.status_code == 200
    assert result.json()["observations"][job["dataset_id"]]["event_time"].endswith("00:02:00Z")


def test_quality_rejection_and_version_provenance(market: System) -> None:
    spec = setup_import(market)
    first = submit(market, spec)
    run_worker(market)
    second = submit(market, spec, csv_content(bad=True))
    run_worker(market)
    path = f"/api/v1/market/datasets/{second['dataset_id']}"
    result = market.client.get(path).json()
    assert result["version"] == 2 and result["status"] == "REJECTED"
    assert "NONPOSITIVE_PRICE" in result["quality"]["counts"]
    query = {
        "start": spec["start"],
        "end": spec["end"],
        "decision_at": "2024-01-03T00:00:00Z",
        "preview": True,
    }
    assert market.client.get(path + "/sample", params=query).status_code == 409
    comparison = market.client.get(path + f"/compare/{first['dataset_id']}").json()
    assert comparison["same_series"] and not comparison["same_input"]
    assert market.client.get(path + "/provenance").json()["source_revision_warning"]


def test_queue_retries_crash_recovery_cancellation_and_access(
    market: System, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = setup_import(market)
    job = submit(market, spec)
    worker = Worker(market.config)
    original = worker.objects.get

    def fail(artifact: dict[str, object]) -> bytes:
        raise OSError("controlled storage outage")

    monkeypatch.setattr(worker.objects, "get", fail)
    assert worker.once()
    status = market.client.get("/api/v1/market/jobs").json()[0]
    assert (
        status["state"] == "RETRY"
        and status["attempts"] == 1
        and status["error_code"] == "SERVICE_OR_STORAGE_FAILURE"
    )
    monkeypatch.setattr(worker.objects, "get", original)
    engine = create_engine(market.admin_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE ingestion_jobs SET state='RUNNING',lease_until=:past,"
                "next_attempt_at=:past WHERE id=:id"
            ),
            {"past": datetime.now(UTC) - timedelta(seconds=1), "id": job["id"]},
        )
    assert worker.once()
    worker.close()
    engine.dispose()
    assert market.client.get("/api/v1/market/jobs").json()[0]["state"] == "SUCCEEDED"
    next_job = submit(market, {**spec, "transformation_reason": "new explicitly versioned input"})
    assert (
        market.post(f"/api/v1/market/jobs/{next_job['id']}/cancel", {}).json()["state"]
        == "CANCELLED"
    )
    peer, _ = market.peer("market-viewer", "VIEWER")
    try:
        assert peer.get(f"/api/v1/market/datasets/{job['dataset_id']}").status_code == 404
        assert peer.get("/api/v1/market/datasets").json()["total"] == 0
        response = peer.post(
            "/api/v1/market/providers",
            headers=market.csrf(peer),
            json={
                "name": "Denied",
                "adapter": "LOCAL",
                "rights_reference": "test fixture",
                "attribution": "synthetic",
                "usage_rights_acknowledged": True,
            },
        )
        assert response.status_code == 403
    finally:
        cast(FastAPI, peer.app).state.store.engine.dispose()
        peer.close()


def test_market_objects_jobs_and_metadata_survive_actual_restart() -> None:
    isolated = isolated_config()
    database = "p1_market_restart_" + isolated.run_id
    instance = create_system(database, create=isolated.stage == "write")
    try:
        configure_market(instance, "market-restart-" + isolated.run_id)
        if isolated.stage == "write":
            instance.bootstrap()
            instance.secret, instance.recovery = instance.enroll()
            spec = setup_import(instance)
            submit(instance, spec)
            redis = Redis.from_url(isolated.redis_url)
            try:
                assert int(cast(int, redis.llen(QUEUE))) > 0
            finally:
                redis.close()
        else:
            run_worker(instance)
            engine = create_engine(instance.admin_url)
            try:
                with engine.connect() as connection:
                    assert (
                        connection.scalar(text("SELECT state FROM ingestion_jobs")) == "SUCCEEDED"
                    )
                    artifacts = connection.scalar(text("SELECT artifacts FROM market_datasets"))
                assert isinstance(artifacts, list)
                store = ObjectStore(instance.config)
                assert all(store.get(a).startswith(b"PAR1") for a in artifacts)
            finally:
                engine.dispose()
    finally:
        close_system(instance, drop=isolated.stage == "verify")


def test_actual_ecb_provider_download_has_conservative_availability(market: System) -> None:
    from packages.market.providers import ECB_RIGHTS

    spec = setup_import(market)
    provider = market.post(
        "/api/v1/market/providers",
        {
            "name": "Actual ECB reference-rate service",
            "adapter": "ECB",
            "rights_reference": ECB_RIGHTS,
            "attribution": "Source: ECB statistics. Unmodified reference observations.",
            "usage_rights_acknowledged": True,
        },
    )
    assert provider.status_code == 201
    spec.update(
        provider_id=provider.json()["id"],
        source_symbol="D.USD.EUR.SP00.A",
        data_type="REFERENCE",
        timeframe="D1",
        start="2026-10-19T00:00:00Z",
        end="2026-10-24T00:00:00Z",
        provenance="PUBLIC_PROVIDER",
        calendar={
            "verified_until": "2026-10-25T00:00:00Z",
            "source": "ECB daily reference dates; observation count unknown",
        },
    )
    response = market.post("/api/v1/market/jobs", spec)
    assert response.status_code == 202
    run_worker(market)
    path = "/api/v1/market/datasets/" + response.json()["dataset_id"]
    data = market.client.get(path).json()
    assert data["status"] == "VALID" and data["record_count"] > 0 and data["coverage_pct"] is None
    manifest = market.client.get(path + "/provenance").json()
    assert manifest["provider"]["adapter"] == "ECB" and manifest["downloaded_at"] is not None
    query = {"start": spec["start"], "end": spec["end"], "decision_at": "2026-10-24T00:00:00Z"}
    assert market.client.get(path + "/sample", params=query).json()["items"] == []
    rows = market.client.get(
        path + "/sample", params={**query, "decision_at": datetime.now(UTC).isoformat()}
    ).json()["items"]
    assert (
        rows
        and rows[0]["price"] is not None
        and rows[0]["bid"] is None
        and rows[0]["volume"] is None
    )


def test_actual_worker_process_crash_recovers_with_expired_lease(
    market: System, tmp_path: Any
) -> None:
    import subprocess
    import sys
    import time
    from pathlib import Path

    spec = setup_import(market)
    start = datetime(2024, 1, 2, tzinfo=UTC)
    rows = 30000
    end = start + timedelta(minutes=rows)
    spec["end"] = end.isoformat()
    spec["calendar"] = {
        "weekdays": list(range(7)),
        "verified_until": end.isoformat(),
        "source": "Synthetic continuous acceptance grid",
    }
    content = ["event_time,observed_at,available_at,open,high,low,close,sequence"]
    for number in range(rows):
        t = start + timedelta(minutes=number)
        content.append(
            f"{t.isoformat()},{(t + timedelta(minutes=1)).isoformat()},"
            f"{(t + timedelta(minutes=1)).isoformat()},1.1,1.2,1.0,1.15,{number}"
        )
    requested = time.perf_counter()
    job = submit(market, spec, ("\n".join(content) + "\n").encode())
    import_seconds = time.perf_counter() - requested
    config = market.config.model_dump(mode="json")
    for name in type(market.config).model_fields:
        item = getattr(market.config, name)
        if isinstance(item, SecretStr):
            config[name] = item.get_secret_value()
    config_path = Path(tmp_path) / "worker.json"
    config_path.touch(mode=0o600)
    config_path.write_text(json.dumps(config))
    script = (
        "from pathlib import Path;import sys;from apps.api.config import Settings;"
        "from packages.market.jobs import Worker;"
        "w=Worker(Settings.model_validate_json(Path(sys.argv[1]).read_text()));"
        "w.once();w.close()"
    )
    process = subprocess.Popen(  # noqa: S603 - fixed trusted data worker, private fixture config
        [sys.executable, "-c", script, str(config_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )  # noqa: S603 - fixed trusted worker fault test
    engine = create_engine(market.admin_url)
    try:
        deadline = time.monotonic() + 15
        claimed = False
        while time.monotonic() < deadline and process.poll() is None:
            with engine.connect() as connection:
                state = connection.scalar(
                    text("SELECT state FROM ingestion_jobs WHERE id=:id"), {"id": job["id"]}
                )
            if state == "RUNNING":
                claimed = True
                break
            time.sleep(0.01)
        assert claimed, "Worker did not claim before fault injection"
        process.kill()
        process.wait(timeout=10)
        assert process.returncode != 0
        with engine.begin() as connection:
            assert (
                connection.scalar(
                    text("SELECT published_at FROM market_datasets WHERE id=:id"),
                    {"id": job["dataset_id"]},
                )
                is None
            )
            # Advance lease time without sleeping 90 seconds. The worker process really was killed.
            connection.execute(
                text("UPDATE ingestion_jobs SET lease_until=:past WHERE id=:id"),
                {"past": datetime.now(UTC) - timedelta(seconds=1), "id": job["id"]},
            )
        began = time.perf_counter()
        run_worker(market)
        recovery_seconds = time.perf_counter() - began
        result = market.client.get("/api/v1/market/datasets/" + job["dataset_id"]).json()
        assert result["status"] == "VALID" and result["record_count"] == rows
        began = time.perf_counter()
        response = market.client.get(
            "/api/v1/market/datasets/" + job["dataset_id"] + "/sample",
            params={
                "start": start.isoformat(),
                "end": end.isoformat(),
                "decision_at": end.isoformat(),
                "limit": 2000,
            },
        )
        retrieval_seconds = time.perf_counter() - began
        assert (
            response.status_code == 200
            and len(response.json()["items"]) == 2000
            and response.json()["truncated"]
        )
        out = Path(".cache/phase2")
        out.mkdir(exist_ok=True)
        (out / f"benchmark-{isolated_config().stage}.json").write_text(
            json.dumps(
                {
                    "provenance": "SYNTHETIC_TEST_FIXTURE",
                    "actual_services": ["PostgreSQL", "Redis", "MinIO"],
                    "rows": rows,
                    "input_bytes": len(("\n".join(content) + "\n").encode()),
                    "upload_seconds": import_seconds,
                    "recovery_ingestion_seconds": recovery_seconds,
                    "retrieval_2000_seconds": retrieval_seconds,
                    "python": sys.version.split()[0],
                    "platform": sys.platform,
                    "actual_worker_sigkill": True,
                    "run_id": isolated_config().run_id,
                    "stage": isolated_config().stage,
                    "measured_at_utc": datetime.now(UTC).isoformat(),
                },
                indent=2,
            )
            + "\n"
        )
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        engine.dispose()
        config_path.unlink(missing_ok=True)


def test_tick_parquet_zero_sequence_month_pruning_and_root_retention(
    market: System, monkeypatch: pytest.MonkeyPatch
) -> None:
    from decimal import Decimal

    import pyarrow as pa  # type: ignore[import-untyped]
    import pyarrow.parquet as pq  # type: ignore[import-untyped]
    from minio import Minio

    from packages.market.processing import read_rows

    spec = setup_import(market)
    spec.update(
        data_type="TICK",
        timeframe="TICK",
        format="PARQUET",
        start="2024-01-31T23:59:00Z",
        end="2024-02-01T00:02:00Z",
        calendar={
            "weekdays": list(range(7)),
            "verified_until": "2024-02-02T00:00:00Z",
            "source": "Synthetic 24/7 quote fixture",
        },
    )
    times = ["2024-01-31T23:59:00Z", "2024-01-31T23:59:00Z", "2024-02-01T00:00:00Z"]
    rows = [
        {
            "event_time": t,
            "observed_at": t,
            "available_at": t,
            "sequence": i,
            "bid": Decimal("1.10000") + Decimal(i) / 100000,
            "ask": Decimal("1.10010") + Decimal(i) / 100000,
        }
        for i, t in enumerate(times)
    ]
    buffer = io.BytesIO()
    pq.write_table(pa.Table.from_pylist(rows), buffer)
    job = submit(market, spec, buffer.getvalue())
    run_worker(market)
    path = "/api/v1/market/datasets/" + job["dataset_id"]
    record = market.client.get(path).json()
    assert record["status"] == "VALID" and record["coverage_pct"] is None
    manifest = market.client.get(path + "/provenance").json()
    artifacts = manifest["artifacts"]
    assert {a["period"] for a in artifacts if a["layer"] == "normalized"} == {"2024-01", "2024-02"}
    store = ObjectStore(market.config)
    calls = []
    original = store.get

    def counted(artifact: dict[str, object]) -> bytes:
        calls.append(str(artifact["key"]))
        return original(artifact)

    monkeypatch.setattr(store, "get", counted)
    selected = list(read_rows(store, artifacts, start=datetime(2024, 2, 1, tzinfo=UTC)))
    assert len(selected) == 1 and selected[0].sequence == 2
    assert all("/2024-02/" in key for key in calls)
    response = market.client.get(
        path + "/sample",
        params={"start": spec["start"], "end": spec["end"], "decision_at": "2024-02-02T00:00:00Z"},
    )
    assert response.status_code == 200 and [r["sequence"] for r in response.json()["items"]] == [
        0,
        1,
        2,
    ]
    assert response.json()["provenance"] == "SYNTHETIC_TEST_FIXTURE"
    config = isolated_config()
    root = Minio(
        config.storage_endpoint,
        access_key="phase0-test",
        secret_key=config.storage_password.get_secret_value(),
        secure=False,
    )
    artifact = next(a for a in artifacts if a["layer"] == "raw")
    retention = root.get_object_retention(
        store.bucket, artifact["key"], version_id=artifact["version"]
    )
    assert retention is not None and retention.mode == "COMPLIANCE"
    with pytest.raises(S3Error):
        root.remove_object(store.bucket, artifact["key"], version_id=artifact["version"])
