"""Report development prerequisites without disclosing environment contents."""

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    failures = 0
    for command in ("python3", "node", "npm", "docker", "make"):
        found = shutil.which(command) is not None
        print(f"{'OK' if found else 'MISSING'}: {command}")
        failures += int(not found)
    for filename in (".env", ".venv/bin/python", "apps/web/node_modules"):
        found = Path(filename).exists()
        print(f"{'OK' if found else 'MISSING'}: {filename}")
        failures += int(not found)
    executable = shutil.which("docker")
    if executable:
        try:
            result = subprocess.run(  # noqa: S603
                [executable, "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                timeout=10,
                check=False,
            )
            available = result.returncode == 0
        except subprocess.TimeoutExpired:
            available = False
        print(
            "OK: Docker engine" if available else "UNAVAILABLE: Start Docker Desktop for Compose."
        )
        failures += int(not available)
    print("Safety: SIMULATED only; no live executor, model runner or broker connectors shipped.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
