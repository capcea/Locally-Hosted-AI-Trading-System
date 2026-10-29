"""A configuration value can only reduce capabilities, never enable trading."""

from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    campaign_global_concurrency: int = Field(default=2, ge=1, le=2)
    campaign_owner_concurrency: int = Field(default=1, ge=1, le=1)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    app_environment: Literal["development", "test"] = "development"
    broker_environment: Literal["SIMULATED"] = "SIMULATED"
    live_trading_enabled: bool = False
    worker_execution_enabled: bool = False
    executor_capability: Literal["DENY_ALL"] = "DENY_ALL"
    database_url: SecretStr | None = None
    migration_database_url: SecretStr | None = None
    redis_url: SecretStr | None = None
    object_store_url: str | None = None
    auth_encryption_key: SecretStr | None = None
    auth_database_password: SecretStr | None = None
    auth_bootstrap_token: SecretStr | None = None
    auth_cookie_secure: bool = True
    auth_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    session_lifetime_seconds: int = Field(default=28800, ge=60, le=86400)
    session_idle_seconds: int = Field(default=1800, ge=60, le=3600)
    market_storage_user: SecretStr | None = None
    market_storage_password: SecretStr | None = None
    market_bucket: str = Field(default="market-data", pattern=r"^[a-z][a-z0-9-]{2,62}$")
    market_upload_bytes: int = Field(default=20971520, ge=1024, le=20971520)
    market_max_rows: int = Field(default=1000000, ge=1, le=1000000)
    market_max_datasets: int = Field(default=1000, ge=1, le=100000)
    market_retention_days: int = Field(default=30, ge=1, le=3650)

    @field_validator("auth_origins")
    @classmethod
    def safe_origins(cls, values: list[str]) -> list[str]:
        from urllib.parse import urlsplit

        if not values:
            raise ValueError("At least one explicit authentication origin is required")
        for value in values:
            parsed = urlsplit(value)
            local = parsed.hostname in {"127.0.0.1", "localhost", "testserver"}
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or (parsed.scheme == "http" and not local)
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(
                    "Origins must be exact HTTPS origins or explicit local test origins"
                )
        return values

    @field_validator("auth_encryption_key")
    @classmethod
    def encryption_key(cls, value: SecretStr | None) -> SecretStr | None:
        if value:
            from cryptography.fernet import Fernet

            Fernet(value.get_secret_value().encode())
        return value

    @field_validator("auth_bootstrap_token")
    @classmethod
    def bootstrap_strength(cls, value: SecretStr | None) -> SecretStr | None:
        if value and len(value.get_secret_value()) < 43:
            raise ValueError("Bootstrap token must have at least 256 bits of generated entropy")
        return value

    @field_validator("live_trading_enabled", "worker_execution_enabled")
    @classmethod
    def deny_execution(cls, value: bool) -> bool:
        if value:
            raise ValueError("Execution cannot be enabled in this simulation-only release")
        return value

    @field_validator("object_store_url")
    @classmethod
    def validate_object_store(cls, value: str | None) -> str | None:
        if value is not None:
            from urllib.parse import urlsplit

            parsed = urlsplit(value)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("Object store URL must be HTTP(S)")
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError("Object store health URL must not contain secrets or query data")
        return value
