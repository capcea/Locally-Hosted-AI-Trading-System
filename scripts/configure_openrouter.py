"""Review/apply exact cloud egress opt-in, without API keys or provider calls."""

import argparse
import json
import os
import stat
import tempfile
from pathlib import Path

from packages.ai.cloud_contracts import CLOUD_POLICY
from services.ai_egress.proxy import destinations


def private_config(path: Path) -> str:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077:
        raise ValueError("Existing AI configuration must be a private regular mode0600 file")
    return path.read_text()


def proposal(original: str) -> str:
    lines = original.splitlines()
    changes = {"AI_OPENROUTER_ENABLED": "true"}
    matches = [
        line.partition("=")[2].strip()
        for line in lines
        if line.startswith("AI_EGRESS_DESTINATIONS=")
    ]
    if len(matches) > 1 or sum(line.startswith("AI_OPENROUTER_ENABLED=") for line in lines) > 1:
        raise ValueError("Duplicate AI operator configuration refused")
    raw = matches[0] if matches else "[]"
    if raw[:1] in {"'", '"'} and raw[-1:] == raw[:1]:
        raw = raw[1:-1]
    allowed = json.loads(raw)
    destinations(json.dumps(allowed))  # Refuse malformed existing configuration, never broaden it.
    cloud = {"host": "openrouter.ai", "port": 443, "cloud_policy": CLOUD_POLICY}
    if cloud not in allowed:
        allowed.append(cloud)
    changes["AI_EGRESS_DESTINATIONS"] = "'" + json.dumps(allowed, separators=(",", ":")) + "'"
    result = []
    for line in lines:
        name = line.partition("=")[0]
        result.append(name + "=" + changes.pop(name) if name in changes else line)
    result.extend(name + "=" + value for name, value in changes.items())
    return "\n".join(result) + "\n"


def apply(path: Path, original: str, updated: str) -> None:
    if private_config(path) != original:
        raise ValueError("AI configuration changed during review; retry without overwriting it")
    descriptor, name = tempfile.mkstemp(prefix=".env.ai-openrouter-", dir=path.parent)
    temporary = Path(name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--reviewed-policy", choices=[CLOUD_POLICY])
    args = parser.parse_args()
    path = Path(".env.ai")
    original = private_config(path)
    updated = proposal(original)
    if args.apply:
        if args.reviewed_policy != CLOUD_POLICY:
            parser.error("Explicit --reviewed-policy openrouter-public-v1 is required")
        apply(path, original, updated)
    print(
        json.dumps(
            {
                "mode": "APPLIED" if args.apply else "REVIEW_ONLY",
                "destination": "https://openrouter.ai/api/v1",
                "policy": CLOUD_POLICY,
                "preserved": "Existing private destinations, keys and queue/database identities",
                "services_restarted": False,
                "provider_requests": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
