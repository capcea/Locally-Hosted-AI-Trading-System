"""Add private Phase 1 configuration without changing existing data-store credentials."""

import os
import secrets
import stat
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet
from dotenv import dotenv_values
from sqlalchemy.engine import make_url


def setup(destination: Path = Path(".env")) -> bool:
    metadata = destination.lstat()
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) & 0o077
        or metadata.st_uid != os.getuid()
    ):
        raise PermissionError("Identity configuration requires a private owner-owned regular .env")
    values = dotenv_values(destination)
    required = (
        "AUTH_ENCRYPTION_KEY",
        "AUTH_BOOTSTRAP_TOKEN",
        "AUTH_DATABASE_PASSWORD",
        "MIGRATION_DATABASE_URL",
    )
    if all(values.get(key) for key in required):
        return False
    if any(values.get(key) for key in required):
        raise RuntimeError(
            "Partial identity configuration exists; reconcile it manually without rotating keys"
        )
    old_url = values.get("DATABASE_URL")
    if not old_url or not old_url.startswith("postgresql+psycopg://"):
        raise RuntimeError("Existing local PostgreSQL URL required")
    runtime_password = secrets.token_hex(32)
    runtime_url = (
        make_url(old_url)
        .set(username="research_app", password=runtime_password)
        .render_as_string(hide_password=False)
    )
    added = {
        "MIGRATION_DATABASE_URL": old_url,
        "AUTH_DATABASE_PASSWORD": runtime_password,
        "AUTH_ENCRYPTION_KEY": Fernet.generate_key().decode(),
        "AUTH_BOOTSTRAP_TOKEN": secrets.token_urlsafe(32),
        "AUTH_COOKIE_SECURE": "false",  # Only the current loopback HTTP development deployment.
    }
    content = destination.read_text()
    lines = [
        f"DATABASE_URL={runtime_url}" if line.startswith("DATABASE_URL=") else line
        for line in content.splitlines()
    ]
    lines.extend(
        ["", "# Phase 1 local identity. Back up the encryption key privately; never commit."]
    )
    lines.extend(f"{key}={value}" for key, value in added.items())
    descriptor, temporary = tempfile.mkstemp(prefix=".identity-", dir=destination.parent)
    try:
        with os.fdopen(descriptor, "w") as file:
            file.write("\n".join(lines) + "\n")
            file.flush()
            os.fsync(file.fileno())
        current = destination.lstat()
        if (
            current.st_dev,
            current.st_ino,
            current.st_mode,
            current.st_size,
            current.st_mtime_ns,
        ) != (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_mode,
            metadata.st_size,
            metadata.st_mtime_ns,
        ):
            raise RuntimeError("Configuration changed concurrently; no replacement made")
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return True


if __name__ == "__main__":
    changed = setup()
    print(
        "Added private Phase 1 keys and separate runtime DB identity."
        if changed
        else "Kept existing identity keys unchanged."
    )
    print("The owner setup token is in private .env; no credentials were printed.")
