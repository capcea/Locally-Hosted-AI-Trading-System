"""Bounded dependency probes. Errors never expose DSNs, tokens or exception contents."""

import asyncio
import time
from collections.abc import Awaitable, Callable

import httpx
from redis.asyncio import Redis
from sqlalchemy import create_engine, text

from apps.api.config import Settings
from packages.domain.contracts import ServiceHealth, ServiceStatus

SCHEMA_REVISION = "0006_research_engine"


def probe_database(url: str) -> None:
    options = {"connect_timeout": 2} if url.startswith("postgresql") else {}
    engine = create_engine(url, connect_args=options)
    try:
        with engine.connect() as connection:
            if connection.dialect.name == "postgresql":
                connection.execute(text("SET statement_timeout = '2000ms'"))
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
            if revision != SCHEMA_REVISION:
                raise RuntimeError("Database requires migrations")
    finally:
        engine.dispose()


async def probe_redis(url: str) -> None:
    async with Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2) as client:
        await client.ping()


async def probe_object_store(url: str) -> None:
    async with httpx.AsyncClient(timeout=2, follow_redirects=False) as client:
        response = await client.get(f"{url.rstrip('/')}/minio/health/ready")
        response.raise_for_status()


async def check_service(
    service_id: str,
    name: str,
    configured: bool,
    probe: Callable[[], Awaitable[None]],
) -> ServiceHealth:
    if not configured:
        return ServiceHealth(
            id=service_id,
            name=name,
            status=ServiceStatus.NOT_CONFIGURED,
            detail="Configurarea lipsește. Rulează make bootstrap pentru mediul local.",
        )
    started = time.monotonic()
    try:
        async with asyncio.timeout(3):
            await probe()
        status = ServiceStatus.HEALTHY
        detail = "Verificare directă reușită."
    except Exception:
        status = ServiceStatus.UNAVAILABLE
        detail = "Serviciul nu răspunde sau schema nu este actualizată. Verifică make doctor."
    return ServiceHealth(
        id=service_id,
        name=name,
        status=status,
        detail=detail,
        latency_ms=round((time.monotonic() - started) * 1000),
    )


async def infrastructure_health(settings: Settings) -> list[ServiceHealth]:
    database = settings.database_url.get_secret_value() if settings.database_url else ""
    redis = settings.redis_url.get_secret_value() if settings.redis_url else ""
    object_store = settings.object_store_url or ""
    return list(
        await asyncio.gather(
            check_service(
                "postgres",
                "PostgreSQL",
                bool(database),
                lambda: asyncio.to_thread(probe_database, database),
            ),
            check_service("redis", "Redis", bool(redis), lambda: probe_redis(redis)),
            check_service(
                "storage",
                "Stocare obiecte",
                bool(object_store),
                lambda: probe_object_store(object_store),
            ),
        )
    )
