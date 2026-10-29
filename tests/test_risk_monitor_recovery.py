"""Daemon liveness is not risk authority; database failures must never publish readiness."""

import secrets
from pathlib import Path
from threading import Event
from typing import Any, cast
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import OperationalError

from packages.persistence.store import Store
from scripts import risk_monitor


class ImmediateStop(Event):
    def __init__(self, observe: Any):
        super().__init__()
        self.observe = observe
        self.waits: list[float | None] = []

    def wait(self, timeout: float | None = None) -> bool:
        self.waits.append(timeout)
        self.observe(self, timeout)
        return self.is_set()


def test_disconnection_clears_readiness_recovers_and_rechecks_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ready = tmp_path / "ready"
    ready.touch()
    private = secrets.token_hex(24)
    store = Mock()
    identity = Mock()
    tick = Mock(side_effect=[OperationalError("private statement", {}, Exception(private)), 0])
    monkeypatch.setattr(risk_monitor, "restricted_identity", identity)
    monkeypatch.setattr(risk_monitor, "once", tick)

    def observe(stopped: ImmediateStop, timeout: float | None) -> None:
        if tick.call_count == 1:
            assert not ready.exists(), "Disconnected monitor must not advertise readiness"
        else:
            assert ready.exists(), "Only a completed scan can publish readiness"
            stopped.set()

    stopped = ImmediateStop(observe)
    risk_monitor.monitor(cast(Store, store), private, stopped, ready=ready)
    assert tick.call_count == identity.call_count == 2
    store.engine.dispose.assert_called_once()
    assert len(stopped.waits) == 2 and not ready.exists()
    output = capsys.readouterr().out
    assert "Readiness withheld" in output and private not in output


def test_persistent_connection_failure_is_bounded_without_sensitive_exception_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ready = tmp_path / "ready"
    ready.touch()
    private = secrets.token_hex(24)
    tick = Mock(side_effect=OperationalError("private statement", {}, Exception(private)))
    monkeypatch.setattr(risk_monitor, "restricted_identity", Mock())
    monkeypatch.setattr(risk_monitor, "once", tick)
    stopped = ImmediateStop(lambda *args: None)
    with pytest.raises(RuntimeError, match="RISK_MONITOR_DATABASE_UNAVAILABLE") as caught:
        risk_monitor.monitor(cast(Store, Mock()), private, stopped, ready=ready)
    assert tick.call_count == 6 and len(stopped.waits) == 5
    assert all(0 < float(n or 0) <= 8 for n in stopped.waits)
    assert not ready.exists() and private not in str(caught.value) + capsys.readouterr().out


@pytest.mark.parametrize("state", ["28P01", "42501", "57014"])
def test_known_auth_permission_or_statement_failures_do_not_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    original = Mock(sqlstate=state)
    tick = Mock(side_effect=OperationalError("private statement", {}, original))
    monkeypatch.setattr(risk_monitor, "restricted_identity", Mock())
    monkeypatch.setattr(risk_monitor, "once", tick)
    stopped = ImmediateStop(lambda *args: None)
    with pytest.raises(RuntimeError, match="RISK_MONITOR_DATABASE_UNAVAILABLE"):
        risk_monitor.monitor(cast(Store, Mock()), "unused", stopped, ready=tmp_path / "ready")
    assert tick.call_count == 1 and not stopped.waits


def test_privileged_identity_cannot_poll_or_become_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ready = tmp_path / "ready"
    ready.touch()
    monkeypatch.setattr(
        risk_monitor, "restricted_identity", Mock(side_effect=RuntimeError("privileged identity"))
    )
    tick = Mock()
    monkeypatch.setattr(risk_monitor, "once", tick)
    with pytest.raises(RuntimeError, match="privileged identity"):
        risk_monitor.monitor(cast(Store, Mock()), "unused", Event(), ready=ready)
    tick.assert_not_called()
    assert not ready.exists()


def test_once_diagnostic_does_not_retry_or_modify_daemon_heartbeat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ready = tmp_path / "ready"
    ready.write_text("daemon heartbeat")
    tick = Mock(side_effect=OperationalError("private statement", {}, Exception()))
    monkeypatch.setattr(risk_monitor, "restricted_identity", Mock())
    monkeypatch.setattr(risk_monitor, "once", tick)
    stopped = ImmediateStop(lambda *args: None)
    with pytest.raises(RuntimeError, match="RISK_MONITOR_DATABASE_UNAVAILABLE"):
        risk_monitor.monitor(cast(Store, Mock()), "unused", stopped, single=True, ready=ready)
    assert tick.call_count == 1 and not stopped.waits
    assert ready.read_text() == "daemon heartbeat"
