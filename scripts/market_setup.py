"""Generate stable private data-service credentials without rotating existing secrets."""

import os
import secrets
import stat
import tempfile
from pathlib import Path

from dotenv import dotenv_values


def setup(path: Path = Path(".env")) -> bool:
    before = path.lstat()
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_uid != os.getuid()
        or stat.S_IMODE(before.st_mode) & 0o077
    ):
        raise PermissionError("Private owner-owned .env required")
    values = dotenv_values(path)
    required = ("MARKET_STORAGE_USER", "MARKET_STORAGE_PASSWORD")
    if all(values.get(k) for k in required):
        return False
    if any(values.get(k) for k in required):
        raise RuntimeError("Partial market credentials; reconcile without rotating existing keys")
    content = path.read_text() + "\n# Phase 2 private data-service identity; never commit.\n"
    content += f"MARKET_STORAGE_USER=market_{secrets.token_hex(8)}\n"
    content += f"MARKET_STORAGE_PASSWORD={secrets.token_hex(32)}\n"
    descriptor, temporary = tempfile.mkstemp(prefix=".identity-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        after = path.lstat()
        if (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size) != (
            before.st_dev,
            before.st_ino,
            before.st_mtime_ns,
            before.st_size,
        ):
            raise RuntimeError("Concurrent configuration update")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return True


if __name__ == "__main__":
    print(
        "Added private data-service credentials."
        if setup()
        else "Preserved existing data credentials."
    )
