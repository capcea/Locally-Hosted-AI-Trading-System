"""Apply the bounded context envelope only, without provisioning roles, secrets or storage."""

from alembic import command
from alembic.config import Config

from apps.api.config import Settings


def main() -> None:
    settings = Settings()
    admin = settings.migration_database_url or settings.database_url
    if admin is None:
        raise RuntimeError("Migration database configuration required")
    config = Config("alembic.ini")
    config.attributes["database_url"] = admin.get_secret_value()
    command.upgrade(config, "0013_ai_context_capacity")
    print("Context envelope migration applied; existing records and credentials are retained.")


if __name__ == "__main__":
    main()
