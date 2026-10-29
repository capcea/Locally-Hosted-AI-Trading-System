"""Inspect effective Compose boundaries without printing secrets or starting services."""

import json
import os
import shutil
import subprocess


def main() -> None:
    docker = shutil.which("docker")
    if not docker:
        raise RuntimeError("Docker Compose CLI unavailable")
    # Configuration-only stand-ins; never used to connect or overwrite owner configuration.
    environment = {
        **os.environ,
        "AI_API_REDIS_URL": "redis://ai_api:configuration-only@ai-redis:6379/0",
        "AI_WORKER_REDIS_URL": "redis://ai_worker:configuration-only@ai-redis:6379/0",
        "AI_WORKER_DATABASE_URL": "postgresql+psycopg://research_ai:configuration-only@172.30.61.2:5432/research",
    }
    result = subprocess.run(  # noqa: S603 -- fixed read-only Compose config command
        [
            docker,
            "compose",
            "-f",
            "compose.yaml",
            "-f",
            "compose.ai.yaml",
            "--profile",
            "ai",
            "config",
            "--format",
            "json",
        ],
        env=environment,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            "AI Compose configuration invalid; raw interpolated configuration withheld"
        )
    config = json.loads(result.stdout)
    worker = config["services"]["ai-worker"]
    networks = config["networks"]
    invalid = (
        not worker["read_only"]
        or "ALL" not in worker["cap_drop"]
        or worker.get("ports")
        or worker.get("volumes")
        or any(not key.startswith("AI_") for key in worker["environment"])
        or any(not networks[name].get("internal") for name in worker["networks"])
        or "control" in worker["networks"]
        or "ai_database" not in config["services"]["postgres"]["networks"]
        or "ai_api_queue" not in config["services"]["api"]["networks"]
        or bool(set(worker["networks"]) & set(config["services"]["api"]["networks"]))
        or config["services"]["ai-egress"].get("ports")
        or config["services"]["ai-redis"].get("ports")
    )
    if invalid:
        raise RuntimeError("AI deployment boundary failed")
    print(
        json.dumps(
            {
                "result": "PASSED_CONFIGURATION_ONLY",
                "worker_networks": sorted(worker["networks"]),
                "external_worker_network": False,
                "public_ai_ports": False,
                "worker_environment_names": sorted(worker["environment"]),
                "live_firewall_and_real_provider_acceptance": "NOT_VERIFIED",
            }
        )
    )


if __name__ == "__main__":
    main()
