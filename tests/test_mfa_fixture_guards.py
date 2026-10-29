"""The browser fixture may only reduce authorization in a disposable database."""

import sys
from pathlib import Path
from unittest.mock import Mock

import psycopg
import pytest

from testing import mfa_state


@pytest.mark.parametrize("database", ["research", "p1_browser_invalid", ""])
def test_browser_aging_refuses_ambient_databases(
    monkeypatch: pytest.MonkeyPatch, database: str
) -> None:
    monkeypatch.setattr(
        sys, "argv", ["mfa_state", "expire", "11111111-1111-4111-8111-111111111111"]
    )
    monkeypatch.setenv("E2E_PHASE1_ISOLATED", "1")
    monkeypatch.setenv("E2E_AUTH_DATABASE", database)
    monkeypatch.setenv("PHASE0_TEST_CONFIG", "/nonexistent-no-connection")
    connection = Mock()
    monkeypatch.setattr(psycopg, "connect", connection)
    with pytest.raises(RuntimeError, match="Disposable browser harness"):
        mfa_state.main()
    connection.assert_not_called()


def test_browser_aging_requires_private_owned_regular_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "config"
    path.write_text("not a credential file")
    path.chmod(0o644)
    monkeypatch.setattr(
        sys, "argv", ["mfa_state", "stale-mfa", "11111111-1111-4111-8111-111111111111"]
    )
    monkeypatch.setenv("E2E_PHASE1_ISOLATED", "1")
    monkeypatch.setenv("E2E_AUTH_DATABASE", "p1_browser_" + "a" * 32)
    monkeypatch.setenv("PHASE0_TEST_CONFIG", str(path))
    with pytest.raises(RuntimeError, match="Private disposable"):
        mfa_state.main()
