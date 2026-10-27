"""Private key provisioning must preserve existing service credentials and be idempotent."""

from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

from scripts.bootstrap import bootstrap
from scripts.identity_setup import setup


def test_identity_setup_preserves_credentials_and_keys(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    bootstrap(path)
    original = dotenv_values(path)
    assert setup(path)
    current = dotenv_values(path)
    assert current["POSTGRES_PASSWORD"] == original["POSTGRES_PASSWORD"]
    assert current["MINIO_ROOT_PASSWORD"] == original["MINIO_ROOT_PASSWORD"]
    assert current["MIGRATION_DATABASE_URL"] == original["DATABASE_URL"]
    assert make_url(current["DATABASE_URL"] or "").username == "research_app"
    assert current["AUTH_ENCRYPTION_KEY"] is not None
    Fernet(current["AUTH_ENCRYPTION_KEY"].encode())
    assert len(current["AUTH_BOOTSTRAP_TOKEN"] or "") == 43
    assert path.stat().st_mode & 0o777 == 0o600
    before = path.read_bytes()
    assert not setup(path)
    assert path.read_bytes() == before


def test_identity_setup_refuses_nonprivate_and_partial_configuration(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    bootstrap(path)
    path.chmod(0o644)
    with pytest.raises(PermissionError):
        setup(path)
    path.chmod(0o600)
    with path.open("a") as stream:
        stream.write("AUTH_ENCRYPTION_KEY=partial-fixture\n")
    before = path.read_bytes()
    with pytest.raises(RuntimeError, match="Partial"):
        setup(path)
    assert path.read_bytes() == before
