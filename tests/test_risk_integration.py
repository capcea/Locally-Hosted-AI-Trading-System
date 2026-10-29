"""Actual disposable PostgreSQL risk, process concurrency, crash and safety acceptance."""

import json
import signal
import subprocess
import sys
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from risk_setup import clear_stop, post
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_execution_engine import START, initial
from test_execution_integration import cmd, make_run, tick
from test_execution_integration import execution as execution
from test_phase1_integration import System, close_system, create_system, isolated_config

from packages.execution.contracts import Command
from packages.execution.journal import execute
from packages.execution.models import SimulationRun
from packages.persistence.audit import append_event
from packages.persistence.models import LoginSession, User, utcnow
from packages.risk.authorization import consume
from packages.risk.contracts import AuthorizationScope
from packages.risk.models import (
    AccountControl,
    AuthorizationUse,
    Reservation,
    RiskAuthorization,
)

pytestmark = pytest.mark.isolated_services
D = Decimal


def test_independent_monitor_recovers_real_connection_loss_without_clearing_stop(
    execution: System, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Terminate only this disposable client's connection, never development PostgreSQL."""
    from threading import Event

    from packages.persistence.store import Store
    from scripts import risk_monitor

    run = make_run(execution)
    tick(execution, run, 0)
    report = status(execution, run)
    post(
        execution,
        f"/api/v1/risk/accounts/{run['account_id']}/emergency",
        {
            "key": "reconnect-owner-stop",
            "action": "STOP_NEW_ENTRIES",
            "expected_revision": report["revision"],
            "acknowledged_simulated_only": True,
        },
    )
    store = Store(execution.runtime_url)
    ready = tmp_path / "monitor-ready"
    original = risk_monitor.once
    calls = 0
    observations: list[bool] = []

    def interrupted_once(current: Store, secret: str) -> int:
        nonlocal calls
        calls += 1
        if calls == 2:
            with current.engine.connect() as connection:
                # A real PostgreSQL connection termination raises the actual driver exception.
                connection.scalar(text("SELECT pg_terminate_backend(pg_backend_pid())"))
            pytest.fail("Disposable PostgreSQL did not terminate its own connection")
        return original(current, secret)

    class Observe(Event):
        def wait(self, timeout: float | None = None) -> bool:
            observations.append(ready.exists())
            if calls == 3:
                self.set()
            assert calls <= 3, "Monitor failed to recover within the controlled fault sequence"
            return self.is_set()

    monkeypatch.setattr(risk_monitor, "once", interrupted_once)
    try:
        risk_monitor.monitor(store, key(execution), Observe(), ready=ready)
        assert observations == [True, False, True]
        assert not ready.exists(), "Shutdown must withdraw daemon readiness"
        state = status(execution, run)
        assert state["manual_stop"]
        denied = raw_order(execution, run)
        assert denied.status_code == 409 and not denied.json()["state"]["orders"]
        assert execution.client.get("/api/v1/audit/verify").json()["valid"]
    finally:
        store.engine.dispose()


def key(system: System) -> str:
    assert system.config.auth_encryption_key
    return system.config.auth_encryption_key.get_secret_value()


def status(system: System, run: dict[str, Any]) -> dict[str, Any]:
    response = system.client.get(f"/api/v1/risk/accounts/{run['account_id']}/status")
    assert response.status_code == 200
    return dict(response.json())


def raw_order(system: System, run: dict[str, Any], **changes: Any) -> Any:
    body = {
        "key": "risk-command-" + uuid4().hex,
        "at": START.isoformat(),
        "action": "SUBMIT",
        "order": {
            "side": "BUY",
            "order_type": "MARKET",
            "volume": ".1",
            "stop_loss": "1.0990",
            "take_profit": "1.1030",
        },
    }
    body.update(changes)
    return system.post(f"/api/v1/execution/simulations/{run['id']}/commands", body)


def test_full_simulated_order_has_one_atomic_reservation_and_consumed_scope(
    execution: System,
) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    submitted = raw_order(execution, run, key="risk-exact-idempotency")
    assert submitted.status_code == 200
    assert submitted.json()["risk"]["decision"] == "ALLOW"
    duplicate = raw_order(execution, run, key="risk-exact-idempotency")
    assert duplicate.json() == submitted.json()
    engine = create_engine(execution.runtime_url)
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Reservation)) == 1
        assert db.scalar(select(func.count()).select_from(AuthorizationUse)) == 1
    filled = tick(execution, run, 1)
    assert len(filled["state"]["fills"]) == 1
    with Session(engine) as db:
        reservation = db.scalar(select(Reservation))
        assert reservation is not None and reservation.state == "OPEN" and reservation.amount > 0
        assert db.scalar(select(func.count()).select_from(AuthorizationUse)) == 2
    assert execution.client.get("/api/v1/audit/verify").json()["valid"]
    engine.dispose()


def test_direct_journal_call_without_service_identity_cannot_create_order(
    execution: System,
) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    engine = create_engine(execution.runtime_url)
    with Session(engine) as db, db.begin():
        row = db.get(SimulationRun, UUID(run["id"]))
        assert row is not None
        result, _ = execute(
            db,
            row,
            Command.model_validate(
                {
                    "key": "direct-bypass-denied",
                    "at": START,
                    "action": "SUBMIT",
                    "order": {
                        "side": "BUY",
                        "order_type": "MARKET",
                        "volume": ".1",
                        "stop_loss": "1.0990",
                        "take_profit": "1.1030",
                    },
                }
            ),
            uuid4(),
        )
        assert result["risk"]["decision"] != "ALLOW"
        assert result["state"]["orders"] == {}
        assert db.scalar(select(func.count()).select_from(Reservation)) == 0
        append_event(
            db,
            key(execution),
            "risk.direct_bypass_refused",
            actor=db.get(User, row.owner_id),
            mfa=True,
            entity_id=row.id,
            after={"source": "SIMULATED"},
        )
    engine.dispose()
    assert execution.client.get("/api/v1/audit/verify").json()["valid"]


@pytest.mark.parametrize("fault", ["stale_monitor", "missing_sl", "excess_volume"])
def test_missing_safety_inputs_and_oversizing_return_durable_denial(
    execution: System,
    fault: str,
) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    if fault == "stale_monitor":
        engine = create_engine(execution.runtime_url)
        with Session(engine) as db, db.begin():
            control = db.get(AccountControl, UUID(run["account_id"]))
            assert control
            control.monitor_at = utcnow() - timedelta(seconds=31)
        engine.dispose()
    order = {
        "side": "BUY",
        "order_type": "MARKET",
        "volume": "100" if fault == "excess_volume" else ".1",
        "stop_loss": None if fault == "missing_sl" else "1.0990",
        "take_profit": "1.1030",
    }
    refused = raw_order(execution, run, order=order)
    assert refused.status_code == 409
    assert refused.json()["risk"]["decision"] != "ALLOW"
    assert not refused.json()["state"]["orders"]
    history = execution.client.get(f"/api/v1/risk/accounts/{run['account_id']}/decisions").json()
    assert history[0]["result"]["decision"] != "ALLOW"
    assert execution.client.get("/api/v1/audit/verify").json()["valid"]


def test_unknown_retains_reservation_and_clear_requires_reconciliation(execution: System) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    cmd(execution, run, "FAULT", 0, fault="AFTER_SUBMIT")
    cmd(execution, run, "SUBMIT", 0, order={"side": "BUY", "order_type": "MARKET", "volume": ".1"})
    entries = execution.client.get(f"/api/v1/risk/accounts/{run['account_id']}/reservations").json()
    assert entries[0]["state"] == "UNKNOWN" and D(entries[0]["amount"]) > 0
    report = status(execution, run)
    assert report["automatic_stop"]
    refused = execution.post(
        f"/api/v1/risk/accounts/{run['account_id']}/emergency",
        {
            "key": "cannot-clear-unknown",
            "action": "CLEAR_STOP",
            "expected_revision": report["revision"],
            "acknowledged_simulated_only": True,
        },
    )
    assert refused.status_code == 409 and not refused.json()["completed"]
    assert raw_order(execution, run).status_code == 409
    cmd(execution, run, "RECONCILE", 1)
    assert clear_stop(execution, run["account_id"])["completed"]
    assert len(tick(execution, run, 2)["state"]["fills"]) == 1


def test_stop_and_flatten_are_distinct_and_require_fresh_owner_mfa(execution: System) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    cmd(execution, run, "SUBMIT", 0, order={"side": "BUY", "order_type": "MARKET", "volume": ".1"})
    tick(execution, run, 1)
    base = f"/api/v1/risk/accounts/{run['account_id']}"
    report = status(execution, run)
    stopped = post(
        execution,
        base + "/emergency",
        {
            "key": "persistent-owner-stop",
            "action": "STOP_NEW_ENTRIES",
            "expected_revision": report["revision"],
            "acknowledged_simulated_only": True,
        },
    )
    current = execution.client.get(f"/api/v1/execution/simulations/{run['id']}").json()
    assert sum(D(p["volume"]) for p in current["state"]["positions"].values()) == D(".1")
    assert (
        raw_order(execution, run, at=(START + timedelta(seconds=1)).isoformat()).status_code == 409
    )
    flattened = post(
        execution,
        base + "/emergency",
        {
            "key": "separate-simulated-flatten",
            "action": "FLATTEN",
            "expected_revision": stopped["revision"],
            "acknowledged_simulated_only": True,
        },
    )
    assert flattened["completed"] and flattened["remaining_positions"] == 0
    assert flattened["external_positions_closed"] is False
    assert status(execution, run)["manual_stop"]
    viewer, _ = execution.peer("risk-foreign-viewer", "VIEWER")
    assert viewer.get(base + "/status").status_code == 404
    assert (
        execution.post(
            base + "/emergency",
            {
                "key": "viewer-cannot-stop",
                "action": "STOP_NEW_ENTRIES",
                "expected_revision": 1,
                "acknowledged_simulated_only": True,
            },
            viewer,
        ).status_code
        == 403
    )
    engine = create_engine(execution.runtime_url)
    session_id = execution.client.get("/api/v1/auth/me").json()["session_id"]
    with Session(engine) as db, db.begin():
        login = db.get(LoginSession, UUID(session_id))
        assert login
        login.mfa_at = utcnow() - timedelta(minutes=6)
    engine.dispose()
    assert (
        execution.post(
            base + "/emergency",
            {
                "key": "stale-mfa-cannot-clear",
                "action": "CLEAR_STOP",
                "expected_revision": flattened["revision"],
                "acknowledged_simulated_only": True,
            },
        ).status_code
        == 403
    )


def test_authorization_tamper_replay_and_sql_rewrite_are_refused(execution: System) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    assert raw_order(execution, run).status_code == 200
    engine = create_engine(execution.runtime_url)
    with Session(engine) as db, db.begin():
        original = db.scalar(select(RiskAuthorization))
        assert original
        scope = AuthorizationScope.model_validate(original.scope)
        with pytest.raises(ValueError, match="TAMPER_EXPIRED_OR_REPLAYED"):
            consume(db, original.id, key(execution), scope, START)
        forged = RiskAuthorization(
            owner_id=original.owner_id,
            account_id=original.account_id,
            run_id=original.run_id,
            decision_id=original.decision_id,
            scope=original.scope,
            signature="0" * 64,
        )
        db.add(forged)
        db.flush()
        with pytest.raises(ValueError, match="TAMPER_EXPIRED_OR_REPLAYED"):
            consume(db, forged.id, key(execution), scope, START)
        assert db.scalar(select(func.count()).select_from(AuthorizationUse)) == 1
        db.rollback()
    for table in (
        "risk_authorizations",
        "risk_authorization_uses",
        "risk_decisions",
        "risk_ledger",
        "risk_profile_versions",
        "risk_run_contexts",
        "risk_emergency_commands",
    ):
        for query in (f"DELETE FROM {table}", f"TRUNCATE {table}"):  # noqa: S608 - fixed table allowlist
            with pytest.raises(DBAPIError), engine.begin() as connection:
                connection.execute(text(query))
    engine.dispose()


def test_adverse_gap_triggers_durable_daily_total_stop(execution: System) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    cmd(execution, run, "SUBMIT", 0, order={"side": "BUY", "order_type": "MARKET", "volume": ".1"})
    tick(execution, run, 1)
    at = (START + timedelta(seconds=2)).isoformat()
    result = cmd(
        execution,
        run,
        "TICK",
        2,
        quote={
            "symbol": "EURUSD.test",
            "event_time": at,
            "available_at": at,
            "sequence": 2,
            "bid": "1.0000",
            "ask": "1.0002",
        },
    )
    assert D(result["state"]["fills"][-1]["realized_pnl"]) == D("-1002")
    report = status(execution, run)
    assert report["automatic_stop"]
    assert {"DAILY_DRAWDOWN_LIMIT", "TOTAL_DRAWDOWN_LIMIT"} <= set(report["reasons"])
    assert D(report["daily_headroom"]) < 0 and D(report["total_headroom"]) < 0
    assert execution.client.get("/api/v1/audit/verify").json()["valid"]


def test_multiple_actual_processes_cannot_overreserve_same_correlated_account(
    execution: System,
    tmp_path: Path,
) -> None:
    first = make_run(execution)
    runs = [
        first,
        make_run(execution, account_id=first["account_id"]),
        make_run(execution, account_id=first["account_id"]),
    ]
    for run in runs:
        tick(execution, run, 0)
    config = tmp_path / "private.json"
    config.touch(mode=0o600)
    config.write_text(
        json.dumps(
            {
                "url": execution.runtime_url,
                "key": key(execution),
                "account": first["account_id"],
                "runs": [r["id"] for r in runs],
            }
        )
    )
    program = """
import json,sys,time
from pathlib import Path
from uuid import UUID,uuid4
from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session
from packages.execution.contracts import Command
from packages.execution.models import SimulationRun
from packages.execution.journal import execute
from packages.risk.ledger import lock_account
from packages.persistence.audit import append_event
from packages.persistence.models import User
config=json.loads(Path(sys.argv[1]).read_text()); index=int(sys.argv[2])
folder=Path(sys.argv[1]).parent; (folder/('ready'+str(index))).touch()
deadline=time.monotonic()+15
while not (folder/'release').exists():
 if time.monotonic()>deadline:raise RuntimeError('test barrier deadline')
 time.sleep(.01)
engine=create_engine(config['url'])
with Session(engine) as db,db.begin():
 lock_account(db,UUID(config['account']))
 run=db.scalar(select(SimulationRun).where(SimulationRun.id==UUID(config['runs'][index])).with_for_update())
 command=Command.model_validate({'key':'worker-'+str(index)+'-reservation','at':'2024-01-02T00:00:00Z','action':'SUBMIT','order':{'side':'BUY','order_type':'MARKET','volume':'.35','stop_loss':'1.0990','take_profit':'1.1030'}})
 result,_=execute(db,run,command,uuid4(),risk_key=config['key'])
 append_event(db,config['key'],'risk.concurrent_worker',actor=db.get(User,run.owner_id),mfa=True,entity_id=run.id,after={'source':'SIMULATED'})
 print(result['risk']['decision'])
engine.dispose()
"""
    children = [
        subprocess.Popen(  # noqa: S603 - fixed test program and private local config
            [sys.executable, "-c", program, str(config), str(i)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for i in range(3)
    ]
    try:
        deadline = time.monotonic() + 15
        while not all((tmp_path / f"ready{i}").exists() for i in range(3)):
            assert time.monotonic() < deadline, "process barrier readiness timeout"
            assert all(child.poll() is None for child in children)
            time.sleep(0.01)
        (tmp_path / "release").touch()
        outcomes = []
        for child in children:
            out, err = child.communicate(timeout=30)
            assert child.returncode == 0, err
            outcomes.append(out.strip())
        assert sorted(outcomes) == ["ALLOW", "ALLOW", "DENY"]
        engine = create_engine(execution.runtime_url)
        with Session(engine) as db:
            reserved = db.scalar(select(func.sum(Reservation.amount)))
            assert reserved == D("112") and reserved <= D("125")
            assert db.scalar(select(func.count()).select_from(AuthorizationUse)) == 2
        engine.dispose()
        assert execution.client.get("/api/v1/audit/verify").json()["valid"]
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)


@pytest.mark.parametrize("point", ["before_commit", "after_commit"])
def test_actual_risk_process_kill_has_no_unreserved_approved_order(
    execution: System,
    tmp_path: Path,
    point: str,
) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    config = tmp_path / "private-crash.json"
    config.touch(mode=0o600)
    command = {
        "key": "atomic-risk-crash",
        "at": START.isoformat(),
        "action": "SUBMIT",
        "order": {
            "side": "BUY",
            "order_type": "MARKET",
            "volume": ".1",
            "stop_loss": "1.0990",
            "take_profit": "1.1030",
        },
    }
    config.write_text(
        json.dumps(
            {
                "url": execution.runtime_url,
                "key": key(execution),
                "run": run["id"],
                "point": point,
                "command": command,
            }
        )
    )
    program = """
import json,os,signal,sys
from pathlib import Path
from uuid import UUID,uuid4
from sqlalchemy.orm import Session
from sqlalchemy import create_engine,select
from packages.execution.models import SimulationRun
from packages.execution.contracts import Command
from packages.execution.journal import execute
from packages.risk.ledger import lock_account
from packages.persistence.audit import append_event
from packages.persistence.models import User
config=json.loads(Path(sys.argv[1]).read_text());engine=create_engine(config['url'])
with Session(engine) as db:
 with db.begin():
  account=db.scalar(select(SimulationRun.account_id).where(SimulationRun.id==UUID(config['run'])))
  lock_account(db,account)
  run=db.scalar(select(SimulationRun).where(SimulationRun.id==UUID(config['run'])).with_for_update())
  execute(db,run,Command.model_validate(config['command']),uuid4(),risk_key=config['key'])
  append_event(db,config['key'],'risk.actual_crash_probe',actor=db.get(User,run.owner_id),mfa=True,entity_id=run.id,after={'source':'SIMULATED'})
  if config['point']=='before_commit':os.kill(os.getpid(),signal.SIGKILL)
 os.kill(os.getpid(),signal.SIGKILL)
"""
    child = subprocess.run(  # noqa: S603 - fixed crash probe, never strategy code
        [sys.executable, "-c", program, str(config)], capture_output=True, text=True, timeout=30
    )
    assert child.returncode == -signal.SIGKILL, child.stderr
    engine = create_engine(execution.runtime_url)
    with Session(engine) as db:
        expected = 1 if point == "after_commit" else 0
        assert db.scalar(select(func.count()).select_from(Reservation)) == expected
        assert db.scalar(select(func.count()).select_from(AuthorizationUse)) == expected
        state = db.get(SimulationRun, UUID(run["id"]))
        assert state
        orders = state.state["orders"]
        assert isinstance(orders, dict) and len(orders) == expected
    result = execution.post(f"/api/v1/execution/simulations/{run['id']}/commands", command)
    assert result.status_code == 200
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Reservation)) == 1
        assert db.scalar(select(func.count()).select_from(AuthorizationUse)) == 1
    engine.dispose()
    assert execution.client.get("/api/v1/audit/verify").json()["valid"]


def test_stop_state_survives_actual_service_restart() -> None:
    isolated = isolated_config()
    database = "p1_risk_stop_" + isolated.run_id
    if isolated.stage == "write":
        system = create_system(database)
        system.bootstrap()
        system.secret, system.recovery = system.enroll()
        try:
            run = make_run(system)
            tick(system, run, 0)
            report = status(system, run)
            post(
                system,
                f"/api/v1/risk/accounts/{run['account_id']}/emergency",
                {
                    "key": "durable-stop-restart",
                    "action": "STOP_NEW_ENTRIES",
                    "expected_revision": report["revision"],
                    "acknowledged_simulated_only": True,
                },
            )
        finally:
            close_system(system, drop=False)
    else:
        system = create_system(database, create=False)
        try:
            engine = create_engine(system.runtime_url)
            with Session(engine) as db:
                controls = list(db.scalars(select(AccountControl)))
                assert len(controls) == 1 and controls[0].manual_stop
                assert controls[0].sequence > 0 and len(controls[0].digest) == 64
            engine.dispose()
        finally:
            close_system(system)


def quote(
    system: System, run: dict[str, Any], second: int, bid: str = "1.1000", ask: str = "1.1002"
) -> dict[str, Any]:
    at = (START + timedelta(seconds=second)).isoformat()
    return cmd(
        system,
        run,
        "TICK",
        second,
        quote={
            "symbol": run["state"]["spec"]["symbol"],
            "event_time": at,
            "available_at": at,
            "sequence": second,
            "bid": bid,
            "ask": ask,
        },
    )


def context_data(system: System, run: dict[str, Any]) -> dict[str, Any]:
    return dict(system.client.get(f"/api/v1/risk/runs/{run['id']}/contexts").json()[0]["context"])


def policy_version(
    system: System,
    run: dict[str, Any],
    *,
    terms: dict[str, Any] | None = None,
    expires: str | None = None,
) -> dict[str, Any]:
    previous = system.client.get(f"/api/v1/risk/accounts/{run['account_id']}/policies").json()[0]
    body = {
        k: previous[k]
        for k in (
            "kind",
            "firm_policy_id",
            "terms",
            "effective_at",
            "expires_at",
            "document_digest",
            "source_references",
        )
    }
    if terms:
        body["terms"] = {**body["terms"], **terms}
    if expires:
        body["expires_at"] = expires
    created = post(system, f"/api/v1/risk/accounts/{run['account_id']}/policies", body, 201)
    post(
        system,
        f"/api/v1/risk/policies/{created['id']}/attest",
        {
            "document_digest": created["document_digest"],
            "action": "VERIFY",
            "acknowledged_exact_program_and_effective_dates": True,
        },
    )
    return created


def test_partial_fill_cancel_and_partial_close_release_only_verified_risk(
    execution: System,
) -> None:
    run = make_run(execution, simulation=initial(liquidity_per_tick=".04"))
    tick(execution, run, 0)
    submitted = cmd(
        execution, run, "SUBMIT", 0, order={"side": "BUY", "order_type": "MARKET", "volume": ".1"}
    )
    order_id = next(iter(submitted["state"]["orders"]))
    partial = tick(execution, run, 1)
    assert D(partial["state"]["fills"][0]["volume"]) == D(".04")
    path = f"/api/v1/risk/accounts/{run['account_id']}/reservations"
    before = execution.client.get(path).json()[0]
    cmd(execution, run, "CANCEL", 1, target_id=order_id)
    after = execution.client.get(path).json()[0]
    assert D(after["amount"]) == D(before["amount"]) * D(".4")
    assert after["state"] == "OPEN"
    position_id = next(iter(partial["state"]["positions"]))
    cmd(execution, run, "CLOSE", 1, target_id=position_id, volume=".02")
    reduced = execution.client.get(path).json()[0]
    assert D(reduced["amount"]) == D(after["amount"]) / 2
    cmd(execution, run, "CLOSE", 2, target_id=position_id, volume=".02")
    released = execution.client.get(path).json()[0]
    assert released["state"] == "RELEASED" and D(released["amount"]) == 0


def test_policy_expiry_between_reservation_and_fill_refuses_authority(execution: System) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    policy_version(execution, run, expires=(START + timedelta(seconds=1)).isoformat())
    clear_stop(execution, run["account_id"])
    assert raw_order(execution, run).status_code == 200
    after = tick(execution, run, 2)
    assert not after["state"]["fills"]
    assert next(iter(after["state"]["orders"].values()))["state"] == "REJECTED"
    assert status(execution, run)["automatic_stop"]
    assert all(
        r["state"] == "RELEASED"
        for r in execution.client.get(
            f"/api/v1/risk/accounts/{run['account_id']}/reservations"
        ).json()
    )


def test_profile_revision_cannot_reuse_old_risk_authority(execution: System) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    binding = execution.client.get(f"/api/v1/risk/accounts/{run['account_id']}/profiles").json()[0]
    record = execution.client.get(f"/api/v1/records/risk-profiles/{binding['profile_id']}").json()
    updated = execution.client.put(
        f"/api/v1/records/risk-profiles/{record['id']}?expected_revision={record['revision']}",
        json={**record["data"], "per_trade_pct": ".2"},
        headers=execution.csrf(),
    )
    assert updated.status_code == 200
    refused = raw_order(execution, run)
    assert refused.status_code == 409
    assert "RISK_PROFILE_REVISION_CHANGED" in refused.json()["risk"]["reasons"]
    assert not refused.json()["state"]["orders"]


def test_calendar_outage_and_news_blackout_fail_closed(execution: System) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    policy_version(
        execution,
        run,
        terms={
            "news_required": True,
            "news_scope": "NEW_ENTRIES",
            "news_before_seconds": 0,
            "news_after_seconds": 0,
        },
    )
    context = context_data(execution, run)
    context["calendar"] = {
        "observed_at": START.isoformat(),
        "available_at": START.isoformat(),
        "valid_until": (START + timedelta(seconds=5)).isoformat(),
        "events": [
            {
                "timestamp": START.isoformat(),
                "currencies": ["USD"],
                "severity": "HIGH",
                "reference": "Known synthetic release",
            }
        ],
        "source_reference": "Synthetic owner calendar snapshot",
        "source": "SIMULATED",
    }
    post(execution, f"/api/v1/risk/runs/{run['id']}/contexts", context, 201)
    clear_stop(execution, run["account_id"])
    blackout = raw_order(execution, run)
    assert blackout.status_code == 409
    assert "ECONOMIC_NEWS_BLACKOUT" in blackout.json()["risk"]["reasons"]
    quote(execution, run, 6)
    report = status(execution, run)
    assert report["automatic_stop"]
    assert "ECONOMIC_CALENDAR_MISSING_OR_STALE" in report["reasons"]
    assert (
        raw_order(execution, run, at=(START + timedelta(seconds=6)).isoformat()).status_code == 409
    )


def test_what_if_denial_cannot_create_authorization_or_change_emergency_state(
    execution: System,
) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    before = status(execution, run)
    computed = post(
        execution,
        "/api/v1/risk/what-if",
        {
            "run_id": run["id"],
            "at": (START + timedelta(seconds=60)).isoformat(),
            "order": {
                "side": "BUY",
                "order_type": "MARKET",
                "volume": ".1",
                "stop_loss": "1.0990",
                "take_profit": "1.1030",
            },
        },
    )
    assert computed["decision"] == "INDETERMINATE"
    after = status(execution, run)
    assert (after["manual_stop"], after["automatic_stop"]) == (
        before["manual_stop"],
        before["automatic_stop"],
    )
    engine = create_engine(execution.runtime_url)
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(RiskAuthorization)) == 0
        assert db.scalar(select(func.count()).select_from(Reservation)) == 0
    engine.dispose()


def test_cross_currency_simulated_pnl_and_data_only_fx_refresh(execution: System) -> None:
    state = initial()
    state.spec.symbol = "USDJPY.test"
    state.spec.canonical_symbol = "USDJPY"
    state.spec.profit_currency = "JPY"
    state.spec.tick_size = D(".001")
    state.spec.digits = 3
    run = make_run(execution, simulation=state)
    context = context_data(execution, run)
    context["financial"]["base_currency"] = "USD"
    context["financial"]["fx"] = [
        {
            "base": "USD",
            "quote": "JPY",
            "bid": "150",
            "ask": "150.1",
            "observed_at": START.isoformat(),
            "available_at": START.isoformat(),
            "valid_until": (START + timedelta(seconds=30)).isoformat(),
            "source_reference": "Declared synthetic USDJPY FX snapshot",
        }
    ]
    post(execution, f"/api/v1/risk/runs/{run['id']}/contexts", context, 201)
    clear_stop(execution, run["account_id"])
    quote(execution, run, 0, "150", "150.002")
    placed = raw_order(
        execution,
        run,
        order={
            "side": "BUY",
            "order_type": "MARKET",
            "volume": ".1",
            "stop_loss": "149.900",
            "take_profit": "151.000",
        },
    )
    assert placed.status_code == 200, placed.text
    quote(execution, run, 1, "150", "150.002")
    # New observed FX is data; changing payoff, margin or correlation while held is refused.
    context["financial"]["fx"][0].update(
        observed_at=(START + timedelta(seconds=1)).isoformat(),
        available_at=(START + timedelta(seconds=1)).isoformat(),
    )
    post(execution, f"/api/v1/risk/runs/{run['id']}/contexts", context, 201)
    bad = json.loads(json.dumps(context))
    bad["financial"]["margin_per_unit"] = "1"
    assert execution.post(f"/api/v1/risk/runs/{run['id']}/contexts", bad).status_code == 409
    closed = quote(execution, run, 2, "149.900", "149.902")
    assert D(closed["state"]["fills"][-1]["realized_pnl"]) == D("-6.8")
    report = status(execution, run)
    assert D(report["values"]["balance"]) == D(run["state"]["cash"]) - D("6.8")
    assert report["source"] == "SIMULATED"
    assert execution.client.get("/api/v1/audit/verify").json()["valid"]


def test_ledger_admin_tamper_is_detected_without_inventing_trusted_equity(
    execution: System,
) -> None:
    run = make_run(execution)
    tick(execution, run, 0)
    engine = create_engine(execution.admin_url)
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE risk_ledger DISABLE TRIGGER USER"))
        connection.execute(text("UPDATE risk_ledger SET payload='{}'::json WHERE sequence=1"))
        connection.execute(text("ALTER TABLE risk_ledger ENABLE TRIGGER USER"))
    engine.dispose()
    checked = post(execution, f"/api/v1/risk/accounts/{run['account_id']}/monitor", {})
    assert checked["automatic_stop"] and not checked["ledger_verified"]
    assert checked["values"] is None
    refused = raw_order(execution, run)
    assert refused.status_code == 409
    assert not refused.json()["state"]["orders"]
    assert execution.client.get("/api/v1/audit/verify").json()["valid"]


@pytest.mark.parametrize("firm_index", [0, 1, 2])
def test_exact_prop_program_policy_and_stricter_verified_caps(
    execution: System,
    firm_index: int,
) -> None:
    from test_risk_math import policy as internal_policy

    firms = execution.client.get("/api/v1/records/firms").json()["items"]
    firm = firms[firm_index]
    program = post(
        execution,
        "/api/v1/records/programs",
        {
            "kind": "programs",
            "name": "Synthetic program, not actual firm rules",
            "firm_id": firm["id"],
            "phase": "SYNTHETIC_CHALLENGE",
            "platform": "SYNTHETIC_TERMINAL",
        },
        201,
    )
    account = post(
        execution,
        "/api/v1/records/accounts",
        {
            "kind": "accounts",
            "name": "Synthetic prop account",
            "currency": "USD",
            "initial_capital": "25000",
            "program_id": program["id"],
            "source": "SYNTHETIC_TEST_FIXTURE",
        },
        201,
    )
    document = {
        "kind": "policies",
        "name": "Synthetic source, not verified official firm rules",
        "source": "SYNTHETIC_TEST_FIXTURE",
        "program_id": program["id"],
        "account_id": account["id"],
        "version": 1,
        "source_references": ["https://example.invalid/synthetic-policy"],
        "document_digest": "a" * 64,
        "effective_at": "2020-01-01T00:00:00Z",
        "expires_at": "2035-01-01T00:00:00Z",
    }
    base = post(execution, "/api/v1/records/policies", document, 201)
    post(
        execution,
        f"/api/v1/policies/{base['id']}/verify",
        {"decision": "VERIFIED", "source_review_acknowledged": True, "expected_revision": 1},
    )
    post(
        execution,
        f"/api/v1/risk/accounts/{account['id']}/profiles",
        {
            "name": "Conservative synthetic account cap",
            "scope": "ACCOUNT",
            "acknowledged_internal_defaults": True,
        },
        201,
    )
    policy = post(
        execution,
        f"/api/v1/risk/accounts/{account['id']}/policies",
        {
            "kind": "PROP",
            "firm_policy_id": base["id"],
            "terms": internal_policy().model_dump(mode="json"),
            "effective_at": document["effective_at"],
            "expires_at": document["expires_at"],
            "source_references": document["source_references"],
            "document_digest": document["document_digest"],
        },
        201,
    )
    post(
        execution,
        f"/api/v1/risk/policies/{policy['id']}/attest",
        {
            "document_digest": policy["document_digest"],
            "action": "VERIFY",
            "acknowledged_exact_program_and_effective_dates": True,
        },
    )
    rejected = execution.post(
        f"/api/v1/risk/accounts/{account['id']}/profiles",
        {
            "name": "Cannot exceed verified policy",
            "scope": "ACCOUNT",
            "limits": {"daily_loss_pct": "2"},
            "acknowledged_internal_defaults": True,
        },
    )
    assert rejected.status_code == 409
    run = make_run(execution, account_id=account["id"])
    tick(execution, run, 0)
    assert raw_order(execution, run).status_code == 200
    # Latest UNVERIFIED program version blocks old numeric policy even if it was verified.
    post(execution, "/api/v1/records/policies", {**document, "version": 2}, 201)
    later = raw_order(execution, run)
    assert later.status_code == 409
    assert "EXACT_PROP_PROGRAM_POLICY_NOT_VERIFIED" in later.json()["risk"]["reasons"]


def test_midnight_stop_gap_uses_balance_before_the_fill_as_daily_reference(
    execution: System,
) -> None:
    run = make_run(execution)
    quote(execution, run, 86398)
    submitted = raw_order(execution, run, at=(START + timedelta(seconds=86398)).isoformat())
    assert submitted.status_code == 200
    quote(execution, run, 86399)
    stopped = quote(execution, run, 86400, "1.0000", "1.0002")
    assert D(stopped["state"]["fills"][-1]["realized_pnl"]) == D("-1002")
    report = status(execution, run)
    assert report["automatic_stop"] and D(report["daily_headroom"]) < D("-750")
    rows = execution.client.get(f"/api/v1/risk/accounts/{run['account_id']}/ledger").json()
    current = rows[0]["payload"]
    assert D(current["day_balance"]) == D(run["state"]["cash"])
    assert current["period"] == (START + timedelta(days=1)).isoformat()
    assert "DAILY_DRAWDOWN_LIMIT" in report["reasons"]


def test_funding_is_advanced_once_before_assessment_and_retry_is_idempotent(
    execution: System,
) -> None:
    run = make_run(execution, simulation=initial(swap_per_unit_per_day="-1"))
    tick(execution, run, 0)
    cmd(execution, run, "SUBMIT", 0, order={"side": "BUY", "order_type": "MARKET", "volume": ".1"})
    tick(execution, run, 1)
    funded = tick(execution, run, 2)
    assert D(funded["state"]["swap"]) == D("-.000001157407")
    duplicate = tick(execution, run, 2)
    assert duplicate["state"]["cash"] == funded["state"]["cash"]
    computed = post(
        execution,
        "/api/v1/risk/what-if",
        {
            "run_id": run["id"],
            "at": (START + timedelta(seconds=3)).isoformat(),
            "order": {
                "side": "BUY",
                "order_type": "MARKET",
                "volume": ".1",
                "stop_loss": "1.0990",
                "take_profit": "1.1030",
            },
        },
    )
    assert computed["decision"] == "ALLOW"
    assert D(computed["evidence"]["account_exposure"]["funding"]) == D("-.000002314814")
    current = execution.client.get(f"/api/v1/execution/simulations/{run['id']}").json()
    assert current["state"]["swap"] == funded["state"]["swap"]


def test_policy_creation_concurrent_with_independent_monitor_preserves_both_transactions(
    execution: System, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real monitor incident must not deadlock authenticated owner policy persistence."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from sqlalchemy import event
    from sqlalchemy.exc import SQLAlchemyError

    from packages.persistence.store import Store
    from packages.risk.ledger import lock_account
    from packages.risk.monitor import poll
    from scripts import risk_monitor

    run = make_run(execution)
    account_id = run["account_id"]
    path = f"/api/v1/risk/accounts/{account_id}/policies"
    previous = execution.client.get(path).json()[0]
    post(
        execution,
        f"/api/v1/risk/policies/{previous['id']}/attest",
        {
            "document_digest": previous["document_digest"],
            "action": "REVOKE",
            "acknowledged_exact_program_and_effective_dates": True,
        },
    )
    body = {
        field: previous[field]
        for field in (
            "kind",
            "firm_policy_id",
            "terms",
            "effective_at",
            "expires_at",
            "document_digest",
            "source_references",
        )
    }
    headers = execution.csrf()
    held, release = Event(), Event()
    monitor_store = Store(execution.runtime_url)
    sqlstates: list[str] = []

    def database_error(context: Any) -> None:
        code = getattr(context.original_exception, "sqlstate", None)
        if isinstance(code, str):
            sqlstates.append(code)

    def paused_poll(db: Session, account: Any) -> list[str]:
        lock_account(db, account.id)
        held.set()
        assert release.wait(8), "Test did not release monitor transaction"
        return poll(db, account)

    def monitor() -> str:
        try:
            risk_monitor.once(monitor_store, key(execution))
            return "COMMITTED"
        except SQLAlchemyError:
            return "DATABASE_ERROR"

    monkeypatch.setattr(risk_monitor, "poll", paused_poll)
    event.listen(monitor_store.engine, "handle_error", database_error)
    api_store = cast(FastAPI, execution.client.app).state.store
    event.listen(api_store.engine, "handle_error", database_error)
    admin = create_engine(execution.admin_url)
    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            monitor_future = workers.submit(monitor)
            assert held.wait(5), "Independent monitor did not reach account serialization"
            request = workers.submit(execution.client.post, path, json=body, headers=headers)
            try:
                # Release only after PostgreSQL reports real lock contention, not a timed sleep.
                deadline = time.monotonic() + 5
                with admin.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
                    while time.monotonic() < deadline:
                        blocked = connection.scalar(
                            text(
                                "SELECT count(*) FROM pg_stat_activity "
                                "WHERE datname = current_database() AND wait_event_type = 'Lock' "
                                "AND cardinality(pg_blocking_pids(pid)) > 0"
                            )
                        )
                        if blocked:
                            break
                    else:
                        pytest.fail("No real database lock contention was observed")
            finally:
                release.set()
            response = request.result(timeout=15)
            monitor_outcome = monitor_future.result(timeout=15)
        diagnostics = {
            "endpoint": "POST /api/v1/risk/accounts/{account_id}/policies",
            "status": response.status_code,
            "request_id": response.headers.get("x-request-id"),
            "monitor": monitor_outcome,
            "sqlstates": sqlstates,
        }
        if response.status_code == 503:
            diagnostics["detail"] = response.json().get("detail")
        print(json.dumps(diagnostics))
        assert response.status_code == 201, diagnostics
        assert monitor_outcome == "COMMITTED", diagnostics
        assert sqlstates == [], diagnostics
        assert response.json()["status"] == "UNVERIFIED"
        assert response.json()["version"] == previous["version"] + 1
        assert response.json()["document_digest"] == previous["document_digest"]
        assert execution.client.get(path).json()[0]["id"] == response.json()["id"]
        report = execution.client.get(f"/api/v1/risk/accounts/{account_id}/status").json()
        assert report["manual_stop"] and report["automatic_stop"]
        assert not report["external_execution_authorized"]
        assert execution.client.get("/api/v1/audit/verify").json()["valid"]
    finally:
        release.set()
        event.remove(api_store.engine, "handle_error", database_error)
        monitor_store.engine.dispose()
        admin.dispose()
