"""Explicit local AI identity provisioning. No model, remote account or broker is connected."""

import hashlib
import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet

from apps.api.config import Settings
from scripts.provision_ai import provision_database


def write_private(path: Path, value: str, mode: int = 0o600) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(value)


def main() -> None:
    config = Settings()
    admin = config.migration_database_url or config.database_url
    if not admin:
        raise ValueError("Migration database identity required; run migrations first")
    target = Path(".env.ai")
    root = Path(".secrets/ai")
    if target.exists() or root.exists():
        raise ValueError("AI setup already exists; do not overwrite or rotate active identities")
    # Private parent prevents traversal by other host users; read-only container mounts can
    # read individual files without running the worker as root.
    root.mkdir(parents=True, mode=0o700)
    os.chmod(root, 0o700)
    key, db_password, queue_password = (
        Fernet.generate_key().decode(),
        secrets.token_hex(32),
        secrets.token_hex(32),
    )
    database = provision_database(admin.get_secret_value(), db_password)
    from sqlalchemy.engine import make_url

    worker_url = (
        make_url(database).set(host="172.30.61.2", port=5432).render_as_string(hide_password=False)
    )
    write_private(root / "ai-content-key", key + "\n", 0o644)
    queue_hash = hashlib.sha256(queue_password.encode()).hexdigest()
    write_private(
        root / "ai-redis-acl",
        "\n".join(
            [
                "user default reset on nopass -@all +ping",
                f"user ai_api reset on #{queue_hash} ~ai:* -@all +ping +get +lpush +ltrim",
                f"user ai_worker reset on #{queue_hash} ~ai:* -@all "
                "+ping +get +set +lpush +ltrim +rpop",
            ]
        )
        + "\n",
        0o644,
    )
    write_private(
        target,
        "\n".join(
            [
                f"AI_WORKER_DATABASE_URL={worker_url}",
                f"AI_WORKER_REDIS_URL=redis://ai_worker:{queue_password}@ai-redis:6379/0",
                f"AI_API_REDIS_URL=redis://ai_api:{queue_password}@ai-redis:6379/0",
                "AI_ENDPOINTS=[]",
                "AI_EGRESS_DESTINATIONS=[]",
                "",
            ]
        ),
    )
    print("AI-only identities prepared. No models configured; secrets not printed.")


if __name__ == "__main__":
    main()
