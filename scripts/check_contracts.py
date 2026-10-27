"""Fail on stale generated contracts, including in an uncommitted repository."""

import shutil
import subprocess
from pathlib import Path

from scripts.export_openapi import export

PATHS = (Path("docs/openapi.json"), Path("apps/web/src/generated/api.ts"))


def main() -> int:
    before = {path: path.read_bytes() for path in PATHS}
    npm = shutil.which("npm")
    if npm is None:
        raise RuntimeError("npm is required")
    try:
        export()
        subprocess.run(  # noqa: S603
            [npm, "--prefix", "apps/web", "run", "generate:api"], check=True
        )
        changed = [str(path) for path in PATHS if path.read_bytes() != before[path]]
    finally:
        # Verification must not silently fix a stale checked-in contract.
        for path, data in before.items():
            path.write_bytes(data)
    if changed:
        print("FAILED: stale generated contracts: " + ", ".join(changed))
        return 1
    print("PASSED: generated contracts match the source byte-for-byte.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
