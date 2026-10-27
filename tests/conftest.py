"""Unit tests never load .env or know broker credentials."""

import pytest
from fastapi.testclient import TestClient

from apps.api.config import Settings
from apps.api.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, app_environment="test")


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))
