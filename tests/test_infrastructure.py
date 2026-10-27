"""Run explicitly against Compose. Failure is not replaced by simulated success."""

import asyncio

import pytest

from apps.api.config import Settings
from apps.api.health import infrastructure_health
from packages.domain.contracts import ServiceStatus


@pytest.mark.infrastructure
def test_compose_dependencies_and_schema_readiness() -> None:
    settings = Settings()
    # A test must not mutate a database selected by ambient developer configuration.
    # Compose's dedicated migration service applies schema changes before this read-only probe.
    assert settings.database_url is not None
    assert settings.database_url.get_secret_value().startswith("postgresql+psycopg://")
    health = asyncio.run(infrastructure_health(settings))
    assert all(item.status == ServiceStatus.HEALTHY for item in health), [
        (item.id, item.status) for item in health
    ]
