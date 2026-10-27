from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from apps.api.health import probe_database


def test_migrations_up_down_and_simulation_constraint(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'migration-test.db'}"
    config = Config("alembic.ini")
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    probe_database(url)
    engine = create_engine(url)
    with engine.begin() as connection:
        row = connection.execute(text("SELECT environment FROM platform_metadata")).scalar()
        assert row == "SIMULATED"
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO platform_metadata (key, value, environment) "
                "VALUES (:key, :value, :mode)"
            ),
            {"key": "forbidden", "value": "test", "mode": "LIVE"},
        )
    command.downgrade(config, "base")
    assert "platform_metadata" not in inspect(engine).get_table_names()
    command.upgrade(config, "head")
    probe_database(url)
    engine.dispose()


def test_unmigrated_database_is_not_ready(tmp_path: Path) -> None:
    with pytest.raises(Exception, match="alembic_version"):
        probe_database(f"sqlite:///{tmp_path / 'empty.db'}")
