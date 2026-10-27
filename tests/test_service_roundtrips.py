"""Real service tests. Only the disposable harness may supply their configuration."""

import hashlib
import io
import os
import stat
from pathlib import Path

import pytest
import urllib3
from alembic import command
from alembic.config import Config
from minio import Minio
from minio.error import S3Error
from redis import Redis
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from scripts.integration_services import IsolatedServices

pytestmark = pytest.mark.isolated_services


@pytest.fixture
def isolated() -> IsolatedServices:
    name = os.environ.get("PHASE0_TEST_CONFIG")
    if not name:
        pytest.fail("BLOCKED: use make integration-services; ambient service URLs are forbidden")
    path = Path(name)
    metadata = path.lstat()
    assert stat.S_ISREG(metadata.st_mode) and stat.S_IMODE(metadata.st_mode) == 0o600
    assert metadata.st_uid == os.getuid()
    config = IsolatedServices.model_validate_json(path.read_bytes())
    # Derivation validates credential form; no DATABASE_URL from developer configuration is used.
    assert config.database_url.endswith("/" + config.database_name)
    return config


def test_postgres_isolated_migration_transaction_and_persistence(
    isolated: IsolatedServices,
) -> None:
    url = isolated.database_url
    engine = create_engine(url, connect_args={"connect_timeout": 3})
    config = Config("alembic.ini")
    config.attributes["database_url"] = url
    try:
        if isolated.stage == "write":
            command.upgrade(config, "head")
            with pytest.raises(IntegrityError), engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO platform_metadata (key, value, environment) "
                        "VALUES (:key, :value, :mode)"
                    ),
                    {"key": "unsafe", "value": "TEST_FIXTURE", "mode": "LIVE"},
                )
            command.downgrade(config, "base")
            assert "platform_metadata" not in inspect(engine).get_table_names()
            command.upgrade(config, "head")
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO platform_metadata (key, value, environment) "
                        "VALUES (:key, :value, :mode)"
                    ),
                    {"key": "roundtrip", "value": isolated.run_id, "mode": "SIMULATED"},
                )
            with engine.connect() as connection:
                transaction = connection.begin()
                connection.execute(
                    text("UPDATE platform_metadata SET value=:value WHERE key=:key"),
                    {"value": "ROLLED_BACK_TEST_VALUE", "key": "roundtrip"},
                )
                transaction.rollback()
        # New DB connection, also checked after all service containers stop/start.
        with engine.connect() as connection:
            row = connection.execute(
                text("SELECT value, environment FROM platform_metadata WHERE key=:key"),
                {"key": "roundtrip"},
            ).one()
            assert tuple(row) == (isolated.run_id, "SIMULATED")
    finally:
        engine.dispose()


def test_redis_queue_pending_redelivery_ack_and_persistence(isolated: IsolatedServices) -> None:
    client = Redis.from_url(isolated.redis_url, socket_connect_timeout=3, socket_timeout=3)
    stream = f"phase0:{isolated.run_id}:queue"
    try:
        if isolated.stage == "write":
            persistence = client.config_get("appendonly")
            assert isinstance(persistence, dict) and persistence.get("appendonly") == "yes"
            client.xadd(stream, {"source": "SYNTHETIC_TEST_FIXTURE", "run": isolated.run_id})
            client.expire(stream, 3600)
            client.xgroup_create(stream, "phase0", id="0")
            delivered = client.xreadgroup("phase0", "test-consumer", {stream: ">"}, count=1)
            assert isinstance(delivered, list)
            assert len(delivered) == 1 and len(delivered[0][1]) == 1
            state = client.xpending(stream, "phase0")
            assert isinstance(state, dict) and state["pending"] == 1
        else:
            pending = client.xreadgroup("phase0", "test-consumer", {stream: "0"}, count=1)
            assert isinstance(pending, list)
            assert len(pending) == 1 and len(pending[0][1]) == 1
            message_id, fields = pending[0][1][0]
            assert fields == {
                b"source": b"SYNTHETIC_TEST_FIXTURE",
                b"run": isolated.run_id.encode(),
            }
            assert client.xack(stream, "phase0", message_id) == 1
            state = client.xpending(stream, "phase0")
            assert isinstance(state, dict) and state["pending"] == 0
            assert client.xreadgroup("phase0", "test-consumer", {stream: ">"}, count=1) == []
            client.delete(stream)
    finally:
        client.close()


def test_minio_authenticated_object_integrity_and_persistence(isolated: IsolatedServices) -> None:
    pool = urllib3.PoolManager(timeout=urllib3.Timeout(connect=3, read=5), retries=False)
    client = Minio(
        isolated.storage_endpoint,
        access_key="phase0-test",
        secret_key=isolated.storage_password.get_secret_value(),
        secure=False,
        region="us-east-1",
        http_client=pool,
    )
    bucket = f"phase0-{isolated.run_id}"
    payload = f"SYNTHETIC_TEST_FIXTURE:SIMULATED:{isolated.run_id}".encode()
    try:
        if isolated.stage == "write":
            client.make_bucket(bucket)
            client.put_object(bucket, "fixture.txt", io.BytesIO(payload), len(payload))
            anonymous = Minio(
                isolated.storage_endpoint, secure=False, region="us-east-1", http_client=pool
            )
            with pytest.raises(S3Error) as denied:
                anonymous.get_object(bucket, "fixture.txt")
            assert denied.value.code == "AccessDenied"
        response = client.get_object(bucket, "fixture.txt")
        try:
            actual = response.read()
        finally:
            response.close()
            response.release_conn()
        assert hashlib.sha256(actual).digest() == hashlib.sha256(payload).digest()
        if isolated.stage == "verify":
            client.remove_object(bucket, "fixture.txt")
            client.remove_bucket(bucket)
    finally:
        pool.clear()
