"""Scan Git-selected regular source files, including untracked initial-commit contents."""

import shutil
import subprocess
import tempfile
from pathlib import Path

from scripts.repository_check import inspect_repository


def main() -> int:
    local = Path(".tools/bin/gitleaks").resolve()
    executable = str(local) if local.is_file() else shutil.which("gitleaks")
    if executable is None:
        print("BLOCKED: install a checksum-verified Gitleaks CLI; see docs/GITHUB_PREPARATION.md.")
        return 1
    files = inspect_repository()
    cache = Path(".cache")
    cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="source-scan-", dir=cache) as temporary:
        destination = Path(temporary)
        for path in files:
            target = destination / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        print(
            f"Scanning {len(files)} Git-selected files; ignored runtime state is excluded.",
            flush=True,
        )
        result = subprocess.run(  # noqa: S603
            [executable, "dir", str(destination), "--redact", "--no-banner"], check=False
        )
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
