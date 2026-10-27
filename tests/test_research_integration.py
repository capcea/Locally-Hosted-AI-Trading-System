"""Actual disposable research registry, MinIO results, risk journal and holdout boundaries."""

from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_execution_engine import START
from test_execution_integration import make_run
from test_market_integration import market as market
from test_market_integration import run_worker, setup_import, submit
from test_phase1_integration import System

from packages.research.jobs import Worker
from packages.research.models import ResearchAccount, ResearchJob, ResearchResult

pytestmark = pytest.mark.isolated_services


def prepared(system: System) -> dict[str, Any]:
    spec = setup_import(system)
    spec.update(
        data_type="TICK", timeframe="TICK", end=(START + timedelta(seconds=101)).isoformat()
    )
    lines = ["event_time,observed_at,available_at,bid,ask,sequence"]
    for i in range(101):
        at = (START + timedelta(seconds=i)).isoformat()
        bid = 11000 + i
        lines.append(f"{at},{at},{at},{bid / 10000:.4f},{(bid + 2) / 10000:.4f},{i}")
    imported = submit(system, spec, ("\n".join(lines) + "\n").encode())
    run_worker(system)
    dataset = system.client.get(f"/api/v1/market/datasets/{imported['dataset_id']}").json()
    assert dataset["status"] == "VALID", dataset
    source = make_run(system, account_id=spec["account_id"], instrument_id=spec["instrument_id"])
    context = system.client.get(f"/api/v1/risk/runs/{source['id']}/contexts").json()[0]["context"]
    import hashlib
    import json

    from risk_setup import clear_stop

    previous = system.client.get(f"/api/v1/risk/accounts/{spec['account_id']}/policies").json()[0]
    terms = {**previous["terms"], "automation_permitted": True}
    document = hashlib.sha256(json.dumps(terms, sort_keys=True).encode()).hexdigest()
    created = system.post(
        f"/api/v1/risk/accounts/{spec['account_id']}/policies",
        {
            "kind": "PERSONAL",
            "terms": terms,
            "effective_at": previous["effective_at"],
            "expires_at": previous["expires_at"],
            "document_digest": document,
            "source_references": ["owner://explicit-synthetic-automated-research-policy"],
        },
    )
    assert created.status_code == 201, created.text
    attested = system.post(
        f"/api/v1/risk/policies/{created.json()['id']}/attest",
        {
            "document_digest": document,
            "action": "VERIFY",
            "acknowledged_exact_program_and_effective_dates": True,
        },
    )
    assert attested.status_code == 200, attested.text
    clear_stop(system, spec["account_id"])
    context["financial"].update(automated=True, execution_style="INTRADAY_BENCHMARK")
    registry = system.client.get("/api/v1/research/strategies").json()
    strategy = next(s for s in registry if s["id"] == "EMA_TREND")
    symbol = dict(source["state"]["spec"])
    symbol["symbol"] = spec["source_symbol"]
    return {
        "key": "research-" + uuid4().hex,
        "name": "Explicit synthetic research fixture",
        "source_account_id": spec["account_id"],
        "strategy": "EMA_TREND",
        "strategy_digest": strategy["digest"],
        "datasets": [
            {
                "dataset_id": dataset["id"],
                "manifest_sha256": dataset["manifest_sha256"],
                "symbol": symbol,
                "context": context,
            }
        ],
        "parameters": [
            {
                "fast": 2,
                "slow": 3,
                "lookback": 2,
                "stop_ticks": 20,
                "max_hold_seconds": 5,
                "volume": ".01",
            }
        ],
        "chronology": {
            "start": START.isoformat(),
            "discovery_end": (START + timedelta(seconds=30)).isoformat(),
            "calibration_end": (START + timedelta(seconds=50)).isoformat(),
            "validation_end": (START + timedelta(seconds=75)).isoformat(),
            "end": (START + timedelta(seconds=101)).isoformat(),
            "purge_seconds": 5,
            "embargo_seconds": 1,
            "walk_forward_folds": 2,
        },
        "phase": "DISCOVERY",
        "engine": "EVENT",
        "assumptions": source["state"]["model"],
        "seed": 7,
        "max_rows": 200,
        "max_seconds": 120,
        "bootstrap_samples": 100,
        "acknowledged_clone_policy_to_isolated_accounts": True,
        "acknowledged_research_only": True,
        "acknowledged_cost_and_bar_assumptions": True,
    }


def submitted(system: System, plan: dict[str, Any]) -> dict[str, Any]:
    response = system.post("/api/v1/research/experiments", plan)
    assert response.status_code == 202, response.text
    return dict(response.json())


def work(system: System) -> None:
    worker = Worker(system.config)
    try:
        assert worker.once()
    finally:
        worker.close()


def test_actual_event_research_persists_risk_fills_and_reproduces_without_source_cash_change(
    market: System,
) -> None:
    plan = prepared(market)
    run = submitted(market, plan)
    assert submitted(market, plan)["id"] == run["id"]
    work(market)
    path = f"/api/v1/research/experiments/{run['id']}"
    report = market.client.get(path).json()
    assert report["job"]["state"] == "SUCCEEDED", report
    result = market.client.get(path + "/results").json()
    trial = result["trials"][0]
    assert trial["risk_validated"] and trial["metrics"]["trade_count"] > 0, trial
    replay = market.client.get(path + "/results", params={"section": "replay"}).json()["items"]
    assert any(row["risk"] and row["risk"]["decision"] == "ALLOW" for row in replay)
    account = market.client.get(f"/api/v1/records/accounts/{plan['source_account_id']}").json()
    assert account["data"]["initial_capital"] == plan["assumptions"]["synthetic_initial_balance"]
    second = submitted(market, {**plan, "key": "repeat-" + uuid4().hex})
    work(market)
    actual = market.client.get(f"/api/v1/research/experiments/{second['id']}").json()
    assert actual["result"]["semantic_digest"] == report["result"]["semantic_digest"]
    engine = create_engine(market.runtime_url)
    with Session(engine) as db:
        bindings = list(db.scalars(select(ResearchAccount)))
        assert len(bindings) == 2 and bindings[0].account_id != bindings[1].account_id
        with pytest.raises(DBAPIError):
            db.execute(
                text("UPDATE research_results SET semantic_digest=:value"), {"value": "0" * 64}
            )
            db.commit()
        db.rollback()
    engine.dispose()
    audit = market.client.get(
        "/api/v1/audit?event_type=research.simulated_command&limit=100"
    ).json()
    assert any(event["event_type"] == "research.simulated_command" for event in audit)
    assert market.client.get("/api/v1/audit/verify").json()["valid"]


def test_exploratory_screen_random_control_and_cancel_never_publish_execution_authority(
    market: System,
) -> None:
    plan = prepared(market)
    plan["engine"] = "SCREEN"
    plan["parameters"][0]["random_keep_pct"] = 0
    run = submitted(market, plan)
    work(market)
    report = market.client.get(f"/api/v1/research/experiments/{run['id']}").json()
    assert report["job"]["state"] == "SUCCEEDED", report
    result = market.client.get(f"/api/v1/research/experiments/{run['id']}/results").json()[
        "trials"
    ][0]
    assert (
        result["approximate_net"] == "0.0"
        and result["risk_validated"] is False
        and result["paper_eligible"] is False
    )
    cancelled = submitted(market, {**plan, "key": "cancel-" + uuid4().hex})
    assert (
        market.post(f"/api/v1/research/experiments/{cancelled['id']}/cancel", {}).status_code == 200
    )
    assert (
        market.client.get(f"/api/v1/research/experiments/{cancelled['id']}/results").status_code
        == 409
    )
    changed = {**plan, "strategy_digest": "0" * 64, "key": "mutated-" + uuid4().hex}
    assert market.post("/api/v1/research/experiments", changed).status_code == 409


def test_sealed_holdout_blocks_ordinary_reads_and_allows_one_frozen_audited_release(
    market: System,
) -> None:
    plan = prepared(market)
    dataset = plan["datasets"][0]["dataset_id"]
    seal = market.post(
        "/api/v1/research/holdouts",
        {
            "dataset_id": dataset,
            "reason": "Separate synthetic final evaluation boundary",
            "acknowledged_prior_exposure_unknown": True,
        },
    )
    assert seal.status_code == 201, seal.text
    assert market.client.get(f"/api/v1/market/datasets/{dataset}/provenance").status_code == 403
    assert market.post("/api/v1/research/experiments", plan).status_code == 409
    final = {**plan, "phase": "FINAL_HOLDOUT", "key": "final-" + uuid4().hex}
    released = market.post(
        f"/api/v1/research/holdouts/{seal.json()['id']}/release",
        {
            "experiment": final,
            "acknowledged_single_final_evaluation": True,
            "acknowledged_not_certified_untouched": True,
        },
    )
    assert released.status_code == 201, released.text
    final["holdout_release_id"] = released.json()["id"]
    run = submitted(market, final)
    work(market)
    report = market.client.get(f"/api/v1/research/experiments/{run['id']}").json()
    assert report["job"]["state"] == "SUCCEEDED", report
    assert (
        market.post(
            f"/api/v1/research/holdouts/{seal.json()['id']}/release",
            {
                "experiment": final,
                "acknowledged_single_final_evaluation": True,
                "acknowledged_not_certified_untouched": True,
            },
        ).status_code
        == 409
    )
    final["key"] = "illegal-repeat-" + uuid4().hex
    assert market.post("/api/v1/research/experiments", final).status_code == 409
    assert market.client.get("/api/v1/audit/verify").json()["valid"]


def test_walk_forward_selects_on_train_only_and_uses_independent_oos_accounts(
    market: System,
) -> None:
    plan = prepared(market)
    plan.update(phase="VALIDATION", validation_mode="WALK_FORWARD")
    run = submitted(market, plan)
    work(market)
    path = f"/api/v1/research/experiments/{run['id']}"
    report = market.client.get(path).json()
    assert report["job"]["state"] == "SUCCEEDED", report
    result = market.client.get(path + "/results", params={"section": "walk_forward"}).json()[
        "items"
    ]
    assert len(result) == 1 and result[0]["train_end"] < result[0]["oos_start"]
    engine = create_engine(market.runtime_url)
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(ResearchAccount)) == 4
    engine.dispose()


def test_unverified_margin_and_mutated_contract_are_refused_without_orders(market: System) -> None:
    plan = prepared(market)
    plan["datasets"][0]["context"]["financial"]["margin_per_unit"] = None
    response = market.post("/api/v1/research/experiments", plan)
    assert response.status_code == 409, response.text
    plan["datasets"][0]["context"]["financial"]["margin_per_unit"] = "1000"
    plan["datasets"][0]["symbol"]["canonical_symbol"] = "GBPUSD"
    assert market.post("/api/v1/research/experiments", plan).status_code == 409
    plan["datasets"][0]["dataset_id"] = str(uuid4())
    assert market.post("/api/v1/research/experiments", plan).status_code == 409


def test_queued_job_cannot_clone_superseded_risk_profile(market: System) -> None:
    plan = prepared(market)
    run = submitted(market, plan)
    updated = market.post(
        f"/api/v1/risk/accounts/{plan['source_account_id']}/profiles",
        {
            "name": "Stricter owner-reviewed revision",
            "scope": "ACCOUNT",
            "limits": {"per_trade_pct": ".1"},
            "acknowledged_internal_defaults": True,
        },
    )
    assert updated.status_code == 201, updated.text
    work(market)
    report = market.client.get(f"/api/v1/research/experiments/{run['id']}").json()
    assert report["job"]["state"] == "FAILED"
    assert market.client.get(f"/api/v1/research/experiments/{run['id']}/results").status_code == 409


def test_actual_minio_upload_then_cancel_cannot_publish_result(
    market: System, monkeypatch: pytest.MonkeyPatch
) -> None:
    from packages.market.storage import ObjectStore

    plan = prepared(market)
    plan["engine"] = "SCREEN"
    run = submitted(market, plan)
    original = ObjectStore.put

    def cancel_after_put(self: ObjectStore, path: str, content: bytes) -> dict[str, object]:
        artifact = original(self, path, content)
        if path.startswith("research/"):
            engine = create_engine(market.runtime_url)
            with engine.begin() as db:
                db.execute(
                    text("UPDATE research_jobs SET cancel_requested=true WHERE run_id=:id"),
                    {"id": run["id"]},
                )
            engine.dispose()
        return artifact

    monkeypatch.setattr(ObjectStore, "put", cancel_after_put)
    work(market)
    report = market.client.get(f"/api/v1/research/experiments/{run['id']}").json()
    assert report["job"]["state"] == "CANCELLED", report
    assert market.client.get(f"/api/v1/research/experiments/{run['id']}/results").status_code == 409


def test_actual_worker_sigkill_retries_frozen_inputs_without_publishing_partial_result(
    market: System, tmp_path: Any
) -> None:
    import json
    import os
    import signal
    import subprocess
    import sys
    import time
    from pathlib import Path

    from pydantic import SecretStr

    plan = prepared(market)
    run = submitted(market, plan)
    values = market.config.model_dump(mode="json")
    for field in type(market.config).model_fields:
        item = getattr(market.config, field)
        if isinstance(item, SecretStr):
            values[field] = item.get_secret_value()
    private = Path(tmp_path) / "private-config.json"
    private.write_text(json.dumps(values))
    private.chmod(0o600)
    script = (
        "from pathlib import Path; import sys; from apps.api.config import Settings; "
        "from packages.research.jobs import Worker; "
        "w=Worker(Settings.model_validate_json(Path(sys.argv[1]).read_bytes())); "
        "w.once(); w.close()"
    )
    child = subprocess.Popen(  # noqa: S603 - fixed trusted worker, private fixture config
        [sys.executable, "-c", script, str(private)],
        env={**os.environ, "APP_ENVIRONMENT": "test"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )  # noqa: S603 - fixed trusted worker, private fixture config
    engine = create_engine(market.runtime_url)
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            with Session(engine) as db:
                state = db.scalar(
                    select(ResearchJob.state).where(ResearchJob.run_id == UUID(run["id"]))
                )
            if state == "RUNNING":
                break
            if child.poll() is not None:
                raise AssertionError("Worker exited before controlled kill")
            time.sleep(0.02)
        else:
            raise AssertionError("Worker never claimed the durable job")
        child.send_signal(signal.SIGKILL)
        child.wait(timeout=10)
        assert child.returncode == -signal.SIGKILL
        with Session(engine) as db:
            assert db.get(ResearchResult, UUID(run["id"])) is None
        with engine.begin() as db:
            db.execute(
                text("UPDATE research_jobs SET lease_until=:at WHERE run_id=:id"),
                {"at": START, "id": run["id"]},
            )
        work(market)
        report = market.client.get(f"/api/v1/research/experiments/{run['id']}").json()
        assert report["job"]["state"] == "SUCCEEDED" and report["job"]["attempts"] == 2, report
        assert market.client.get("/api/v1/audit/verify").json()["valid"]
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)
        engine.dispose()
        private.unlink(missing_ok=True)


def test_netting_round_trips_include_actual_funding_and_roundtrip_fees(market: System) -> None:
    from decimal import Decimal

    plan = prepared(market)
    plan["datasets"][0]["symbol"]["account_mode"] = "NETTING"
    plan["assumptions"]["swap_per_unit_per_day"] = "-1"
    plan["assumptions"]["commission_per_unit"] = "3.5"
    run = submitted(market, plan)
    work(market)
    path = f"/api/v1/research/experiments/{run['id']}"
    report = market.client.get(path).json()
    assert report["job"]["state"] == "SUCCEEDED", report
    trades = market.client.get(path + "/results", params={"section": "trades"}).json()["items"]
    curve = market.client.get(path + "/results", params={"section": "equity"}).json()["items"]
    assert len(trades) >= 3 and all(t["realized_r"] is not None for t in trades)
    assert sum(Decimal(t["funding"]) for t in trades) < 0
    assert sum(Decimal(t["net"]) for t in trades) == Decimal(curve[-1]["equity"]) - Decimal(
        plan["assumptions"]["synthetic_initial_balance"]
    )
    assert all(Decimal(t["fees"]) > 0 for t in trades)


def bar_plan(system: System, *, ambiguous: bool = False) -> dict[str, Any]:
    from decimal import Decimal

    from packages.market.models import MarketDataset

    plan = prepared(system)
    engine = create_engine(system.runtime_url)
    with Session(engine) as db:
        stored = db.get(MarketDataset, UUID(plan["datasets"][0]["dataset_id"]))
        assert stored is not None
        spec = dict(stored.spec)
    engine.dispose()
    spec.update(data_type="BAR", timeframe="M1", end=(START + timedelta(minutes=101)).isoformat())
    lines = ["event_time,observed_at,available_at,open,high,low,close,sequence"]
    for i in range(101):
        begin = (START + timedelta(minutes=i)).isoformat()
        end = (START + timedelta(minutes=i + 1)).isoformat()
        price = Decimal("1.1000") + Decimal(".0001") * i
        extreme = Decimal(".01") if ambiguous and i == 9 else Decimal(".0003")
        lines.append(
            f"{begin},{end},{end},{price},{price + extreme},{price - extreme},"
            f"{price + Decimal('.0001')},{i}"
        )
    imported = submit(system, spec, ("\n".join(lines) + "\n").encode())
    run_worker(system)
    data = system.client.get(f"/api/v1/market/datasets/{imported['dataset_id']}").json()
    assert data["status"] == "VALID", data
    plan["datasets"][0].update(dataset_id=data["id"], manifest_sha256=data["manifest_sha256"])
    plan["chronology"].update(
        discovery_end=(START + timedelta(minutes=30)).isoformat(),
        calibration_end=(START + timedelta(minutes=50)).isoformat(),
        validation_end=(START + timedelta(minutes=75)).isoformat(),
        end=(START + timedelta(minutes=101)).isoformat(),
        purge_seconds=120,
        embargo_seconds=60,
    )
    plan["parameters"][0]["max_hold_seconds"] = 120
    plan["bar_spread"] = ".0002"
    return plan


def test_real_admitted_ohlc_replay_defers_signals_and_uses_next_bar(market: System) -> None:
    from datetime import datetime

    plan = bar_plan(market)
    run = submitted(market, plan)
    work(market)
    path = f"/api/v1/research/experiments/{run['id']}"
    report = market.client.get(path).json()
    assert report["job"]["state"] == "SUCCEEDED", report
    signals = market.client.get(path + "/results", params={"section": "signals"}).json()["items"]
    fills = market.client.get(path + "/results", params={"section": "fills"}).json()["items"]
    assert fills and signals
    assert datetime.fromisoformat(fills[0]["timestamp"]) > datetime.fromisoformat(signals[0]["at"])
    assert all(
        (datetime.fromisoformat(f["timestamp"]) - START).total_seconds() % 60 == 0 for f in fills
    )


def test_both_touched_ohlc_protection_refuses_unknown_path_instead_of_optimistic_profit(
    market: System,
) -> None:
    plan = bar_plan(market, ambiguous=True)
    run = submitted(market, plan)
    work(market)
    path = f"/api/v1/research/experiments/{run['id']}"
    report = market.client.get(path).json()
    assert report["job"]["state"] == "FAILED" and "AMBIGUOUS_OHLC" in report["job"]["error"], report
    assert market.client.get(path + "/results").status_code == 409


def test_holdout_alias_cannot_escape_ordinary_or_research_read_restrictions(market: System) -> None:
    from packages.market.models import MarketDataset

    plan = prepared(market)
    original = plan["datasets"][0]["dataset_id"]
    engine = create_engine(market.runtime_url)
    with Session(engine) as db:
        initial = db.get(MarketDataset, UUID(original))
        assert initial is not None
        spec = dict(initial.spec)
    spec["source_symbol"] = "EURUSD.sealed_alias"
    lines = ["event_time,observed_at,available_at,bid,ask,sequence"]
    for i in range(101):
        at = (START + timedelta(seconds=i)).isoformat()
        lines.append(f"{at},{at},{at},1.1000,1.1002,{i}")
    alias = submit(market, spec, ("\n".join(lines) + "\n").encode())
    run_worker(market)
    alias_data = market.client.get(f"/api/v1/market/datasets/{alias['dataset_id']}").json()
    assert alias_data["status"] == "VALID"
    assert (
        market.post(
            "/api/v1/research/holdouts",
            {
                "dataset_id": original,
                "reason": "Sealed final interval includes aliases",
                "acknowledged_prior_exposure_unknown": True,
            },
        ).status_code
        == 201
    )
    assert (
        market.client.get(f"/api/v1/market/datasets/{alias['dataset_id']}/provenance").status_code
        == 403
    )
    listed = market.client.get("/api/v1/market/datasets").json()
    assert listed["total"] == 0
    plan["datasets"][0].update(
        dataset_id=alias_data["id"], manifest_sha256=alias_data["manifest_sha256"]
    )
    plan["datasets"][0]["symbol"]["symbol"] = spec["source_symbol"]
    assert market.post("/api/v1/research/experiments", plan).status_code == 409
    engine.dispose()


def test_pending_entries_and_partial_liquidity_reuse_actual_order_lifecycle(market: System) -> None:
    from decimal import Decimal

    from packages.execution.models import ExecutionEvent

    plan = prepared(market)
    plan["parameters"][0].update(
        entry_order_type="STOP", entry_offset_ticks=1, pending_expiry_seconds=10, volume=".02"
    )
    plan["assumptions"]["liquidity_per_tick"] = ".01"
    plan["chronology"]["discovery_end"] = (START + timedelta(seconds=24)).isoformat()
    run = submitted(market, plan)
    work(market)
    path = f"/api/v1/research/experiments/{run['id']}"
    report = market.client.get(path).json()
    assert report["job"]["state"] == "SUCCEEDED", report
    fills = market.client.get(path + "/results", params={"section": "fills"}).json()["items"]
    assert fills and all(Decimal(f["volume"]) <= Decimal(".01") for f in fills)
    engine = create_engine(market.runtime_url)
    with Session(engine) as db:
        events = list(
            db.scalars(select(ExecutionEvent).where(ExecutionEvent.kind == "ORDER_STATE"))
        )
        partial = False
        for event in events:
            body = event.payload.get("payload")
            if isinstance(body, dict) and body.get("after") == "PARTIALLY_FILLED":
                partial = True
        assert partial
    engine.dispose()
