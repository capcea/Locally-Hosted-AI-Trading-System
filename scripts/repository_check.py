"""Inspect a prospective commit without modifying Git metadata or contacting a remote."""

import argparse
import shutil
import subprocess
from pathlib import Path

SENSITIVE_EXAMPLES = (
    ".env",
    ".env.local",
    "apps/web/.env.production",
    "secrets/credentials.json",
    "credentials-demo.json",
    "server.key",
    "identity.pem",
    "data/market.parquet",
    "database.sqlite3",
    "backups/database.dump",
    "models/weights.gguf",
    "checkpoints/model.safetensors",
    "artifacts/model.onnx",
    "logs/request.log",
    "request.log",
    "playwright-report/trace.zip",
    "test-results/credentials.har",
    ".cache/runtime.json",
    ".aws/credentials",
)


def git(*args: str, input_data: bytes | None = None) -> bytes:
    executable = shutil.which("git")
    if executable is None:
        raise RuntimeError("Git is required")
    return subprocess.run(  # noqa: S603 -- fixed Git commands, no shell
        [executable, *args], input=input_data, capture_output=True, check=True
    ).stdout


def inspect_repository() -> list[Path]:
    ignored = (
        git(
            "check-ignore",
            "--no-index",
            "--stdin",
            input_data=("\n".join(SENSITIVE_EXAMPLES) + "\n").encode(),
        )
        .decode()
        .splitlines()
    )
    missing = sorted(set(SENSITIVE_EXAMPLES) - set(ignored))
    if missing:
        raise RuntimeError("Sensitive paths are not ignored: " + ", ".join(missing))
    tracked_ignored = git("ls-files", "--cached", "--ignored", "--exclude-standard", "-z")
    if tracked_ignored:
        raise RuntimeError("Ignored files are already tracked; review them before committing")
    paths = sorted(
        {
            Path(name)
            for name in git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
            .decode()
            .split("\0")
            if name
        }
    )
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"Non-regular prospective commit path: {path}")
        if path.stat().st_size > 5_000_000:
            raise RuntimeError(f"Unexpected large prospective commit file: {path}")
    if Path(".env.example") not in paths:
        raise RuntimeError("The placeholder-only .env.example must be included")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    paths = inspect_repository()
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_bytes(b"".join(str(path).encode() + b"\0" for path in paths))
    print(
        f"PASSED: {len(SENSITIVE_EXAMPLES)} sensitive-path exclusions; "
        f"{len(paths)} regular source/evidence files."
    )
    print("No files staged, no commit made, no remote created, no network request.")


if __name__ == "__main__":
    main()
