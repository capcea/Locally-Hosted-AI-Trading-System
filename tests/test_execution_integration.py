"""Actual disposable PostgreSQL execution journal, MinIO replay and process-kill tests."""

import json
import signal
import subprocess
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from risk_setup import clear_stop, configure_run
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_execution_engine import START, initial
from test_market_integration import market as market
from test_market_integration import run_worker, setup_import
from test_market_integration import submit as import_rows
from test_phase1_integration import System, close_system, create_system, isolated_config

from packages.brokers.contracts import BrokerSnapshot
from packages.execution.contracts import Command, SimState
from packages.execution.journal import canonical, execute, verify
from packages.execution.models import SimulationRun
from packages.persistence.audit import append_event
from packages.persistence.models import User, utcnow
from packages.risk.ledger import lock_account

pytestmark = pytest.mark.isolated_services


@pytest.fixture
def execution() -> Any:
    system = create_system("p1_execution_" + uuid4().hex)
    system.bootstrap()
    system.secret, system.recovery = system.enroll()
    try:
        yield system
    finally:
        close_system(system)


def post(system: System, path: str, body: dict[str, Any], status: int = 201) -> dict[str, Any]:
    response = system.post(path, body)
    assert response.status_code == status, response.text
    return dict(response.json())


def make_run(
    system: System,
    *,
    account_id: str | None = None,
    instrument_id: str | None = None,
    dataset_id: str | None = None,
    simulation: SimState | None = None,
) -> dict[str, Any]:
    account_id = account_id or system.account()["id"]
    state = simulation or initial()
    if not instrument_id:
        venue = post(
            system,
            "/api/v1/records/venues",
            {"kind": "venues", "name": "Synthetic venue", "venue_type": "CUSTOM"},
        )
        instrument_id = post(
            system,
            "/api/v1/records/instruments",
            {
                "kind": "instruments",
                "name": state.spec.canonical_symbol,
                "symbol": state.spec.canonical_symbol,
                "asset_class": state.spec.asset_class,
                "venue_id": venue["id"],
            },
        )["id"]
    metadata = post(
        system,
        "/api/v1/records/brokers",
        {
            "kind": "brokers",
            "name": "Synthetic broker",
            "account_id": account_id,
            "adapter": "CUSTOM",
            "source": "SYNTHETIC_TEST_FIXTURE",
        },
    )
    post(
        system,
        "/api/v1/execution/connections",
        {"broker_connection_id": metadata["id"], "provider": "SIMULATOR", "mode": "SIMULATED"},
    )
    account_data = system.client.get(f"/api/v1/records/accounts/{account_id}").json()["data"]
    state.model.synthetic_initial_balance = Decimal(account_data["initial_capital"])
    state.spec.stop_distance = Decimal(0)
    if dataset_id:
        state.spec.symbol = "EURUSD.fixture"
    result = post(
        system,
        "/api/v1/execution/simulations",
        {
            "connection_id": metadata["id"],
            "instrument_id": instrument_id,
            "name": "Synthetic acceptance",
            "start_at": START.isoformat(),
            "spec": state.spec.model_dump(mode="json"),
            "assumptions": state.model.model_dump(mode="json"),
            "dataset_id": dataset_id,
        },
    )

    configure_run(system, result)
    return result


def cmd(
    system: System, run: dict[str, Any], action: str, seconds: int, **fields: Any
) -> dict[str, Any]:
    if action == "SUBMIT" and "order" in fields:
        request = fields["order"]
        buying = request["side"] == "BUY"
        request.setdefault("stop_loss", "1.0990" if buying else "1.1012")
        request.setdefault("take_profit", "1.1030" if buying else "1.0980")
    check = system.post(f"/api/v1/risk/accounts/{run['account_id']}/monitor", {})
    assert check.status_code == 200, check.text
    return post(
        system,
        f"/api/v1/execution/simulations/{run['id']}/commands",
        {
            "key": f"{action}-{seconds}-integration",
            "at": (START + timedelta(seconds=seconds)).isoformat(),
            "action": action,
            **fields,
        },
        200,
    )


def tick(system: System, run: dict[str, Any], seconds: int) -> dict[str, Any]:
    at = (START + timedelta(seconds=seconds)).isoformat()
    return cmd(
        system,
        run,
        "TICK",
        seconds,
        quote={
            "symbol": "EURUSD.test",
            "bid": "1.1000",
            "ask": "1.1002",
            "sequence": seconds,
            "event_time": at,
            "available_at": at,
        },
    )


def test_journal_exact_fills_idempotency_integrity_and_account_isolation(execution: System) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    submitted = cmd(
        execution, run, "SUBMIT", 0, order={"side": "BUY", "order_type": "MARKET", "volume": "0.1"}
    )
    assert not submitted["state"]["fills"]
    assert (
        cmd(
            execution,
            run,
            "SUBMIT",
            0,
            order={"side": "BUY", "order_type": "MARKET", "volume": "0.1"},
        )
        == submitted
    )
    result = tick(execution, run, 1)
    assert len(result["state"]["fills"]) == 1
    assert (
        result["state"]["fills"][0]["price"] == "1.100200000000"
        or result["state"]["fills"][0]["price"] == "1.1002"
    )
    assert tick(execution, run, 1) == result
    conflict = execution.post(
        f"/api/v1/execution/simulations/{run['id']}/commands",
        {
            "key": "SUBMIT-0-integration",
            "at": START.isoformat(),
            "action": "SUBMIT",
            "order": {"side": "BUY", "order_type": "MARKET", "volume": "0.2"},
        },
    )
    assert conflict.status_code == 409
    assert execution.client.get("/api/v1/audit/verify").json()["valid"]
    events = execution.client.get(f"/api/v1/execution/simulations/{run['id']}/events").json()
    assert any(e["event"]["kind"] == "FILL" for e in events)
    engine = create_engine(execution.runtime_url)
    with Session(engine) as db:
        persisted = db.get(SimulationRun, UUID(run["id"]))
        assert persisted is not None and verify(db, persisted)
    for table in ("execution_events", "simulation_commands"):
        for sql in (
            f"UPDATE {table} SET owner_id=owner_id",  # noqa: S608 - fixed test table allowlist
            f"DELETE FROM {table}",  # noqa: S608 - fixed test table allowlist
            f"TRUNCATE {table}",
        ):
            with pytest.raises(DBAPIError), engine.begin() as connection:
                connection.execute(text(sql))
    engine.dispose()
    viewer, _ = execution.peer("execution-viewer", "VIEWER")
    assert viewer.get(f"/api/v1/execution/simulations/{run['id']}").status_code == 404
    assert (
        execution.post(
            f"/api/v1/execution/simulations/{run['id']}/commands",
            {"key": "viewer-command", "at": START.isoformat(), "action": "RECONCILE"},
            viewer,
        ).status_code
        == 403
    )
    unauthenticated = execution.client.get(
        "/api/v1/execution/simulations", headers={"Cookie": "research_session=invalid"}
    )
    assert unauthenticated.status_code == 401


def test_ambiguous_submit_fails_closed_and_reconciliation_uses_persisted_truth(
    execution: System,
) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    cmd(execution, run, "FAULT", 0, fault="AFTER_SUBMIT")
    ambiguous = cmd(
        execution, run, "SUBMIT", 0, order={"side": "BUY", "order_type": "MARKET", "volume": "0.1"}
    )
    assert list(ambiguous["state"]["orders"].values())[0]["state"] == "UNKNOWN"
    assert not ambiguous["state"]["fills"]
    denied = execution.post(
        f"/api/v1/execution/simulations/{run['id']}/commands",
        {
            "key": "blind-retry-denied",
            "action": "SUBMIT",
            "at": (START + timedelta(seconds=1)).isoformat(),
            "order": {"side": "BUY", "order_type": "MARKET", "volume": "0.1"},
        },
    )
    assert denied.status_code == 409
    assert execution.client.get("/api/v1/records/incidents").json()["items"]
    reconciled = cmd(execution, run, "RECONCILE", 1)
    assert list(reconciled["state"]["orders"].values())[0]["state"] == "ACKNOWLEDGED"
    clear_stop(execution, run["account_id"])
    assert len(tick(execution, run, 2)["state"]["fills"]) == 1


def test_signed_external_observations_are_fixture_only_and_never_order_capable(
    execution: System,
) -> None:
    account = execution.account()
    meta = post(
        execution,
        "/api/v1/records/brokers",
        {
            "kind": "brokers",
            "name": "MT5 contract fixture",
            "account_id": account["id"],
            "adapter": "MT5",
        },
    )
    key = Ed25519PrivateKey.generate()
    post(
        execution,
        "/api/v1/execution/connections",
        {
            "broker_connection_id": meta["id"],
            "provider": "MT5",
            "mode": "DEMO_READ_ONLY",
            "external_account": "fixture-demo",
            "server": "fixture-server",
            "public_key": key.public_key().public_bytes_raw().hex(),
        },
    )
    snapshot = BrokerSnapshot(
        provider="MT5",
        environment="DEMO_READ_ONLY",
        account_id="fixture-demo",
        server="fixture-server",
        currency="USD",
        observed_at=utcnow(),
        source_sequence=0,
        source="CONTRACT_FIXTURE",
        healthy=True,
        authorization="READ_ONLY",
    )

    def packet(data: BrokerSnapshot) -> dict[str, Any]:
        body = {"connection_id": meta["id"], "snapshot": data.model_dump(mode="json")}
        return {**body, "signature": key.sign(canonical(body)).hex()}

    url = f"/api/v1/execution/connections/{meta['id']}/observations"
    first = packet(snapshot)
    assert post(execution, url, first, 200)["duplicate"] is False
    assert post(execution, url, first, 200)["duplicate"] is True
    assert execution.post(url, {**first, "signature": "0" * 128}).status_code == 403
    assert (
        execution.post(url, packet(snapshot.model_copy(update={"account_id": "other"}))).status_code
        == 409
    )
    assert (
        execution.post(
            url,
            packet(
                snapshot.model_copy(
                    update={"observed_at": utcnow() - timedelta(minutes=2), "source_sequence": 1}
                )
            ),
        ).status_code
        == 409
    )
    gap = snapshot.model_copy(update={"source_sequence": 3, "observed_at": utcnow()})
    assert post(execution, url, packet(gap), 200)["reconciliation"] == "UNKNOWN"
    assert (
        execution.client.get("/api/v1/execution/connections").json()[0]["status"] == "FIXTURE_ONLY"
    )
    for suffix in ("orders", "orders/cancel", "orders/modify"):
        assert (
            execution.post(f"/api/v1/execution/connections/{meta['id']}/{suffix}", {}).status_code
            == 403
        )
    unsafe = {"broker_connection_id": str(uuid4()), "provider": "MT5", "mode": "LIVE"}
    assert execution.post("/api/v1/execution/connections", unsafe).status_code == 422
    assert (
        execution.post(
            "/api/v1/execution/connections", {**unsafe, "mode": "DEMO_EXECUTION"}
        ).status_code
        == 422
    )


@pytest.mark.parametrize("point", ["before_commit", "after_commit"])
def test_actual_process_kill_rolls_back_or_recovers_without_duplicate_fill(
    execution: System, tmp_path: Path, point: str
) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    cmd(execution, run, "SUBMIT", 0, order={"side": "BUY", "order_type": "MARKET", "volume": "0.1"})
    secret_file = tmp_path / "runtime.json"
    secret_file.touch(mode=0o600)
    secret_file.write_text(
        json.dumps(
            {
                "url": execution.runtime_url,
                "run": run["id"],
                "point": point,
                "key": execution.config.auth_encryption_key.get_secret_value()
                if execution.config.auth_encryption_key
                else "",
            }
        )
    )
    program = """
import json,sys,os,signal
from pathlib import Path
from uuid import UUID,uuid4
from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session
from packages.execution.models import SimulationRun
from packages.execution.contracts import Command, SimState
from packages.execution.journal import execute
from packages.persistence.audit import append_event
from packages.risk.ledger import lock_account
from packages.persistence.models import User
config=json.loads(Path(sys.argv[1]).read_text())
engine=create_engine(config['url'])
with Session(engine) as db:
    with db.begin():
        account=db.scalar(select(SimulationRun.account_id).where(SimulationRun.id==UUID(config['run'])))
        lock_account(db,account)
        run=db.scalar(select(SimulationRun).where(SimulationRun.id==UUID(config['run'])).with_for_update())
        execute(db,run,Command.model_validate({'key':'-'.join(('TICK','1','integration')),'at':'2024-01-02T00:00:01Z','action':'TICK','quote':{'symbol':'EURUSD.test','event_time':'2024-01-02T00:00:01Z','available_at':'2024-01-02T00:00:01Z','sequence':1,'bid':'1.1000','ask':'1.1002'}}),uuid4(),risk_key=config['key'])
        append_event(db,config['key'],'simulation.crash_probe',actor=db.get(User,run.owner_id),mfa=True,entity_id=run.id,after={'head':run.digest,'source':'SIMULATED'})
        if config['point']=='before_commit':os.kill(os.getpid(),signal.SIGKILL)
    os.kill(os.getpid(),signal.SIGKILL)
"""
    child = subprocess.run(  # noqa: S603 - fixed crash program; disposable config path only
        [sys.executable, "-c", program, str(secret_file)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert child.returncode == -signal.SIGKILL, child.stderr
    before = execution.client.get(f"/api/v1/execution/simulations/{run['id']}").json()
    assert len(before["state"]["fills"]) == (1 if point == "after_commit" else 0)
    recovered = tick(execution, run, 1)
    assert len(recovered["state"]["fills"]) == 1
    assert len(tick(execution, run, 1)["state"]["fills"]) == 1
    assert execution.client.get("/api/v1/audit/verify").json()["valid"]


def test_simulation_journal_survives_real_database_restart() -> None:
    isolated = isolated_config()
    database = "p1_exec_persist_" + isolated.run_id
    if isolated.stage == "write":
        system = create_system(database)
        system.bootstrap()
        system.secret, system.recovery = system.enroll()
        try:
            run = make_run(system)
            tick(system, run, 0)
            cmd(
                system,
                run,
                "SUBMIT",
                0,
                order={"side": "BUY", "order_type": "MARKET", "volume": "0.1"},
            )
            tick(system, run, 1)
        finally:
            close_system(system, drop=False)
    else:
        system = create_system(database, create=False)
        try:
            engine = create_engine(system.runtime_url)
            with Session(engine) as db:
                persisted = db.scalar(select(SimulationRun))
                assert persisted is not None and verify(db, persisted)
                fills = persisted.state["fills"]
                assert isinstance(fills, list) and len(fills) == 1
            engine.dispose()
        finally:
            close_system(system)


def test_concurrent_processors_commit_one_tick_and_one_fill(execution: System) -> None:
    from concurrent.futures import ThreadPoolExecutor

    run = make_run(execution)
    tick(execution, run, 0)
    cmd(execution, run, "SUBMIT", 0, order={"side": "BUY", "order_type": "MARKET", "volume": "0.1"})
    engine = create_engine(execution.runtime_url)
    key = execution.config.auth_encryption_key
    assert key is not None
    body = Command.model_validate(
        {
            "key": "parallel-tick-probe",
            "action": "TICK",
            "at": "2024-01-02T00:00:01Z",
            "quote": {
                "symbol": "EURUSD.test",
                "event_time": "2024-01-02T00:00:01Z",
                "available_at": "2024-01-02T00:00:01Z",
                "sequence": 1,
                "bid": "1.1000",
                "ask": "1.1002",
            },
        }
    )

    def process(_: int) -> bool:
        with Session(engine) as db, db.begin():
            lock_account(db, UUID(run["account_id"]))
            row = db.scalar(
                select(SimulationRun).where(SimulationRun.id == UUID(run["id"])).with_for_update()
            )
            assert row is not None
            _response, changed = execute(db, row, body, uuid4(), risk_key=key.get_secret_value())
            if changed:
                append_event(
                    db,
                    key.get_secret_value(),
                    "simulation.parallel_probe",
                    actor=db.get(User, row.owner_id),
                    mfa=True,
                    entity_id=row.id,
                    after={"head": row.digest},
                )
            return changed

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(process, range(2))) == [False, True]
        current = execution.client.get(f"/api/v1/execution/simulations/{run['id']}").json()
        assert len(current["state"]["fills"]) == 1
        assert execution.client.get("/api/v1/audit/verify").json()["valid"]
    finally:
        engine.dispose()


def test_phase2_valid_tick_replay_uses_actual_pinned_minio_data(market: System) -> None:
    spec = setup_import(market)
    spec.update(data_type="TICK", timeframe="TICK")
    csv = (
        b"event_time,observed_at,available_at,bid,ask,sequence\n"
        b"2024-01-02T00:00:01Z,2024-01-02T00:00:01Z,2024-01-02T00:00:01Z,1.1000,1.1002,0\n"
        b"2024-01-02T00:00:02Z,2024-01-02T00:00:02Z,2024-01-02T00:00:02Z,1.1001,1.1003,1\n"
    )
    job = import_rows(market, spec, csv)
    run_worker(market)
    run = make_run(
        market,
        account_id=spec["account_id"],
        instrument_id=spec["instrument_id"],
        dataset_id=job["dataset_id"],
    )
    base = f"/api/v1/execution/simulations/{run['id']}"
    first = {
        "key": "verified-first-tick",
        "start": START.isoformat(),
        "end": (START + timedelta(seconds=2)).isoformat(),
        "decision_at": (START + timedelta(seconds=1)).isoformat(),
    }
    assert not post(market, base + "/replay", first, 200)["state"]["fills"]
    cmd(market, run, "SUBMIT", 1, order={"side": "BUY", "order_type": "MARKET", "volume": "0.1"})
    second = {
        **first,
        "key": "verified-second-tick",
        "start": (START + timedelta(seconds=2)).isoformat(),
        "end": (START + timedelta(seconds=3)).isoformat(),
        "decision_at": (START + timedelta(seconds=2)).isoformat(),
    }
    executed = post(market, base + "/replay", second, 200)
    assert len(executed["state"]["fills"]) == 1
    assert (
        executed["state"]["fills"][0]["price"] == "1.100300000000"
        or executed["state"]["fills"][0]["price"] == "1.1003"
    )
    assert post(market, base + "/replay", second, 200)["state"] == executed["state"]
    assert (
        market.post(
            base + "/commands",
            {"key": "no-injected-quotes", "at": START.isoformat(), "action": "TICK"},
        ).status_code
        == 409
    )
