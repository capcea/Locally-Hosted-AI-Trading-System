import json
import stat
from pathlib import Path

import pytest

from scripts.bootstrap import bootstrap
from scripts.seed_demo_data import seed


def test_bootstrap_is_private_and_never_overwrites_existing_config(tmp_path: Path) -> None:
    destination = tmp_path / ".env"
    assert bootstrap(destination)
    original = destination.read_bytes()
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert b"LIVE_TRADING_ENABLED=false" in original
    assert b"REPLACE_WITH" not in original
    assert not bootstrap(destination)
    assert destination.read_bytes() == original


def test_bootstrap_rejects_public_existing_configuration(tmp_path: Path) -> None:
    destination = tmp_path / ".env"
    destination.write_text("SYNTHETIC_TEST_FIXTURE=true\n")
    destination.chmod(0o644)
    with pytest.raises(PermissionError, match="private"):
        bootstrap(destination)
    assert stat.S_IMODE(destination.stat().st_mode) == 0o644


def test_bootstrap_rejects_symlink_without_touching_target(tmp_path: Path) -> None:
    target = tmp_path / "private"
    target.write_text("SYNTHETIC_TEST_FIXTURE=true\n")
    target.chmod(0o600)
    destination = tmp_path / ".env"
    destination.symlink_to(target)
    with pytest.raises(PermissionError, match="regular file"):
        bootstrap(destination)
    assert target.read_text() == "SYNTHETIC_TEST_FIXTURE=true\n"


def test_seed_has_explicit_test_provenance_and_no_fake_performance(tmp_path: Path) -> None:
    destination = tmp_path / "seed.json"
    seed(destination)
    data = json.loads(destination.read_text())
    assert data["source"] == "SYNTHETIC_TEST_FIXTURE"
    assert data["environment"] == "SIMULATED"
    assert data["market_data"] is False
    assert data["performance_data"] is False
