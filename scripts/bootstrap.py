"""Generate local-only secrets once. Never print secret values or overwrite configuration."""

import os
import secrets
import stat
from pathlib import Path


def bootstrap(destination: Path = Path(".env")) -> bool:
    try:
        existing = destination.lstat()
    except FileNotFoundError:
        pass
    else:
        if (
            not stat.S_ISREG(existing.st_mode)
            or stat.S_IMODE(existing.st_mode) & 0o077
            or existing.st_uid != os.getuid()
        ):
            raise PermissionError(
                "Existing configuration must be a private, owner-owned regular file"
            )
        return False
    database_password = secrets.token_hex(24)
    values = {
        "APP_ENVIRONMENT": "development",
        "BROKER_ENVIRONMENT": "SIMULATED",
        "LIVE_TRADING_ENABLED": "false",
        "WORKER_EXECUTION_ENABLED": "false",
        "EXECUTOR_CAPABILITY": "DENY_ALL",
        "POSTGRES_PASSWORD": database_password,
        "DATABASE_URL": (
            f"postgresql+psycopg://research:{database_password}@127.0.0.1:15432/research"
        ),
        "REDIS_URL": "redis://127.0.0.1:16379/0",
        "OBJECT_STORE_URL": "http://127.0.0.1:19000",
        "MINIO_ROOT_USER": f"dev-{secrets.token_hex(8)}",
        "MINIO_ROOT_PASSWORD": secrets.token_hex(32),
    }
    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w") as file:
        file.write("# Generated local development configuration. Never commit.\n")
        file.writelines(f"{key}={value}\n" for key, value in values.items())
    return True


if __name__ == "__main__":
    created = bootstrap()
    print("Created private local .env (0600)." if created else "Kept existing .env unchanged.")
