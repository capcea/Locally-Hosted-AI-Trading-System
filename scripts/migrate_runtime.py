"""Migration entry point with admin credentials, never used by the API runtime."""

from alembic import command
from alembic.config import Config
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from apps.api.config import Settings
from scripts.provision_market import provision_storage
from scripts.provision_runtime import provision_runtime


class StorageAdministrator(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
    minio_root_user: SecretStr | None = None
    minio_root_password: SecretStr | None = None


def main() -> None:
    settings = Settings()
    storage_admin = StorageAdministrator()
    admin = settings.migration_database_url or settings.database_url
    if not admin or not settings.auth_database_password:
        raise RuntimeError("Migration identity and separate runtime password required")
    config = Config("alembic.ini")
    config.attributes["database_url"] = admin.get_secret_value()
    command.upgrade(config, "head")
    provision_runtime(admin.get_secret_value(), settings.auth_database_password.get_secret_value())
    if (
        settings.object_store_url
        and storage_admin.minio_root_user
        and storage_admin.minio_root_password
        and settings.market_storage_user
        and settings.market_storage_password
    ):
        provision_storage(
            settings.object_store_url,
            storage_admin.minio_root_user.get_secret_value(),
            storage_admin.minio_root_password.get_secret_value(),
            settings.market_storage_user.get_secret_value(),
            settings.market_storage_password.get_secret_value(),
            settings.market_bucket,
        )
    print("Schema migrated and restricted runtime role granted; credentials not printed.")


if __name__ == "__main__":
    main()
