"""Own a disposable Compose project; never migrate or restart the development stack."""

import json
import os
import re
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, SecretStr

ROOT = Path(__file__).resolve().parents[1]


class IsolatedServices(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    run_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    stage: Literal["write", "verify"]
    database_port: int = Field(ge=1024, le=65535)
    redis_port: int = Field(ge=1024, le=65535)
    storage_port: int = Field(ge=1024, le=65535)
    database_password: SecretStr
    storage_password: SecretStr

    @property
    def database_name(self) -> str:
        return f"phase0_{self.run_id}"

    @property
    def database_url(self) -> str:
        password = self.database_password.get_secret_value()
        if not re.fullmatch(r"[0-9a-f]{48}", password):
            raise ValueError("Unexpected disposable database credential format")
        return (
            f"postgresql+psycopg://phase0_test:{password}@127.0.0.1:"
            f"{self.database_port}/{self.database_name}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://127.0.0.1:{self.redis_port}/0"

    @property
    def storage_endpoint(self) -> str:
        return f"127.0.0.1:{self.storage_port}"


def mapped_loopback_port(output: str) -> int:
    match = re.fullmatch(r"127\.0\.0\.1:(\d+)", output.strip())
    if match is None or not 1024 <= int(match[1]) <= 65535:
        raise ValueError("Disposable service must expose exactly one non-privileged loopback port")
    return int(match[1])


def require_local_engine(endpoint: str) -> None:
    if not endpoint.startswith(("unix:///", "npipe://")):
        raise RuntimeError("Disposable infrastructure tests require a local Docker engine")


def inspected_loopback_port(output: str, container_port: str) -> int:
    """Check actual Engine bindings, including unintended additional publications."""
    ports = json.loads(output)
    if not isinstance(ports, dict):
        raise ValueError("Missing Docker loopback port bindings")
    published = {key: value for key, value in ports.items() if value is not None}
    bindings = published.get(f"{container_port}/tcp")
    if (
        len(published) != 1
        or not isinstance(bindings, list)
        or len(bindings) != 1
        or not isinstance(bindings[0], dict)
        or set(bindings[0]) != {"HostIp", "HostPort"}
    ):
        raise ValueError("Expected exactly one Docker loopback port binding")
    binding = bindings[0]
    return mapped_loopback_port(f"{binding['HostIp']}:{binding['HostPort']}")


def main(
    *,
    browser: bool = False,
    browser_only: bool = False,
    campaigns_only: bool = False,
    openrouter_only: bool = False,
    risk_only: bool = False,
    auth_only: bool = False,
) -> int:
    docker = shutil.which("docker")
    if docker is None:
        print("BLOCKED: Docker CLI unavailable.", file=sys.stderr)
        return 1
    env = os.environ.copy()
    private_values: list[str] = []

    def run(command: list[str], timeout: int = 600) -> str:
        print("+ " + shlex.join(command), flush=True)
        result = subprocess.run(  # noqa: S603
            command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout, check=False
        )
        output = result.stdout + result.stderr
        for value in private_values:
            output = output.replace(value, "[REDACTED]")
        if output:
            print(output, end="", flush=True)
        if result.returncode:
            raise RuntimeError(f"Command exited {result.returncode}; no service acceptance claimed")
        return result.stdout.strip()

    try:
        if env.get("DOCKER_HOST"):
            require_local_engine(env["DOCKER_HOST"])
        endpoint = run(
            [docker, "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"], timeout=15
        )
        require_local_engine(endpoint)
        run([docker, "info", "--format", "{{.ServerVersion}}"], timeout=15)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1

    run_id = uuid4().hex
    project = f"phase0-test-{run_id}"
    password = secrets.token_hex(24)
    storage_password = secrets.token_hex(32)
    private_values.extend([password, storage_password])
    env.update(
        P0_DATABASE_NAME=f"phase0_{run_id}",
        P0_DATABASE_PASSWORD=password,
        P0_STORAGE_PASSWORD=storage_password,
    )
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    # Keep Buildx's client activity files in the writable workspace, not ~/.docker.
    env.setdefault("BUILDX_CONFIG", str(cache / "buildx"))
    with tempfile.TemporaryDirectory(prefix="phase0-test-", dir=cache) as temporary:
        directory = Path(temporary)
        # Explicit empty env file prevents loading the developer's .env.
        env_file = directory / ".env"
        env_file.touch(mode=0o600)
        compose = [
            docker,
            "compose",
            "--project-name",
            project,
            "--env-file",
            str(env_file),
            "-f",
            str(ROOT / "compose.test.yaml"),
        ]
        config_path = directory / "services.json"
        env["PHASE0_TEST_CONFIG"] = str(config_path)
        code = 0
        try:
            # Exact digest-pinned cached images may be used without registry credential access.
            pull = ["--pull", "never"] if env.get("P0_CACHED_IMAGES") == "1" else []
            run([*compose, "up", "--build", *pull, "-d", "--wait", "--wait-timeout", "180"])
            run(
                [
                    docker,
                    "network",
                    "inspect",
                    f"{project}_default",
                    "--format",
                    '{"driver":{{json .Driver}},"internal":{{json .Internal}}}',
                ]
            )

            def service_ports() -> dict[str, int]:
                verified: dict[str, int] = {}
                for name, service, target in (
                    ("database", "postgres", "5432"),
                    ("redis", "redis", "6379"),
                    ("storage", "minio", "9000"),
                ):
                    container = run([*compose, "ps", "-q", service])
                    if not re.fullmatch(r"[0-9a-f]{64}", container):
                        raise ValueError("Expected exactly one disposable service container")
                    reported = run([*compose, "port", service, target])
                    actual = run(
                        [
                            docker,
                            "inspect",
                            "--format",
                            "{{json .NetworkSettings.Ports}}",
                            container,
                        ]
                    )
                    port = mapped_loopback_port(reported)
                    if inspected_loopback_port(actual, target) != port:
                        raise ValueError("Compose and Docker loopback port bindings disagree")
                    with socket.create_connection(("127.0.0.1", port), timeout=3):
                        print(f"PASSED: {service} 127.0.0.1:{port} -> {target}/tcp; TCP connected.")
                    verified[f"{name}_port"] = port
                return verified

            ports = service_ports()
            config = {
                "run_id": run_id,
                **ports,
                "database_password": password,
                "storage_password": storage_password,
                "stage": "write",
            }
            IsolatedServices.model_validate(config)
            config_path.touch(mode=0o600)

            def test_stage(stage: str) -> None:
                config["stage"] = stage
                config_path.write_text(json.dumps(config))
                run(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        *(
                            [
                                "tests/test_phase1_integration.py",
                                "tests/test_mfa_session_integration.py",
                            ]
                            if auth_only
                            else ["tests/test_risk_integration.py"]
                            if risk_only
                            else ["tests/test_openrouter_integration.py"]
                            if openrouter_only
                            else ["tests/test_campaign_integration.py"]
                            if campaigns_only
                            else [
                                "tests/test_service_roundtrips.py",
                                "tests/test_phase1_integration.py",
                                "tests/test_market_integration.py",
                                "tests/test_execution_integration.py",
                                "tests/test_risk_integration.py",
                                "tests/test_research_integration.py",
                                "tests/test_research_fx_integration.py",
                                "tests/test_ai_integration.py",
                                "tests/test_campaign_integration.py",
                                "tests/test_openrouter_integration.py",
                                "tests/test_mfa_session_integration.py",
                            ]
                        ),
                        "-m",
                        "isolated_services",
                        "-q",
                    ],
                    timeout=600,
                )

            if not browser_only:
                test_stage("write")
                # Verify native-service restart persistence in the full integration mode.
                run([*compose, "stop", "postgres", "redis", "minio"], timeout=60)
                run([*compose, "up", "-d", "--wait", "--wait-timeout", "180"])
                config.update(service_ports())
                test_stage("verify")
            if browser or browser_only:
                run([sys.executable, "-m", "scripts.browser_acceptance"], timeout=900)
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            print(f"FAILED: {error}", file=sys.stderr)
            code = 1
        finally:
            try:
                # Only the unique project owned by this invocation is removed.
                run([*compose, "down", "--volumes", "--remove-orphans"], timeout=120)
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                print(f"FAILED cleanup: inspect disposable project {project}", file=sys.stderr)
                code = 1
        if code == 0:
            print(
                "PASSED: isolated browser acceptance."
                if browser_only
                else "PASSED: isolated migrations, round trips and graceful-restart persistence."
            )
        return code


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Run actual Playwright; requires permitted browser execution",
    )
    parser.add_argument(
        "--browser-only",
        action="store_true",
        help="Run real Playwright with disposable services, without repeating native integration stages",
    )
    parser.add_argument(
        "--campaigns-only", action="store_true", help="Focused real-service campaign suite"
    )
    parser.add_argument(
        "--openrouter-only",
        action="store_true",
        help="Focused cloud policy/secret fixture integration",
    )
    parser.add_argument("--risk-only", action="store_true", help="Focused actual risk services")
    parser.add_argument(
        "--auth-only", action="store_true", help="Focused real identity/session services"
    )
    args = parser.parse_args()
    if (
        sum(
            (
                args.browser,
                args.browser_only,
                args.campaigns_only,
                args.openrouter_only,
                args.risk_only,
                args.auth_only,
            )
        )
        > 1
    ):
        parser.error("Choose one browser or focused native suite")
    raise SystemExit(
        main(
            browser=args.browser,
            browser_only=args.browser_only,
            campaigns_only=args.campaigns_only,
            openrouter_only=args.openrouter_only,
            risk_only=args.risk_only,
            auth_only=args.auth_only,
        )
    )
