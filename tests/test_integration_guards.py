"""Unit tests of the harness's boundaries, not evidence of actual service integration."""

import json
import subprocess
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from scripts import browser_acceptance, integration_services
from scripts.integration_services import (
    IsolatedServices,
    inspected_loopback_port,
    mapped_loopback_port,
    require_local_engine,
)
from scripts.repository_check import inspect_repository


@pytest.mark.parametrize(
    ("name", "value"),
    [("E2E_ONLY_PROJECT", "other"), ("E2E_ONLY_SCENARIO", "other")],
)
def test_browser_selection_rejects_invalid_values_before_resources(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv("PHASE0_TEST_CONFIG", "/nonexistent-no-resource-access")
    monkeypatch.delenv("E2E_ONLY_PROJECT", raising=False)
    monkeypatch.delenv("E2E_ONLY_SCENARIO", raising=False)
    monkeypatch.setenv(name, value)
    with pytest.raises(RuntimeError, match=name):
        browser_acceptance.main()


@pytest.mark.parametrize("endpoint", ["tcp://remote:2375", "ssh://remote", "http://localhost"])
def test_remote_engine_is_refused(endpoint: str) -> None:
    with pytest.raises(RuntimeError, match="local Docker"):
        require_local_engine(endpoint)


@pytest.mark.parametrize(
    "port",
    [
        "0.0.0.0:12345",
        "127.0.0.1:80",
        "[::]:12345",
        "127.0.0.1:70000",
        "invalid IP:0",
        "127.0.0.1:0",
        "",
        "127.0.0.1:35432\n0.0.0.0:35432",
    ],
)
def test_nonlocal_or_invalid_port_is_refused(port: str) -> None:
    with pytest.raises(ValueError, match="loopback"):
        mapped_loopback_port(port)


@pytest.mark.parametrize(
    "ports",
    [
        None,
        {},
        {"5432/tcp": None},
        {"5432/tcp": []},
        {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "0"}]},
        {"5432/tcp": [{"HostIp": "0.0.0.0", "HostPort": "35432"}]},  # noqa: S104 - rejection fixture
        {
            "5432/tcp": [
                {"HostIp": "127.0.0.1", "HostPort": "35432"},
                {"HostIp": "::", "HostPort": "35432"},
            ]
        },
        {
            "5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "35432"}],
            "9001/tcp": [{"HostIp": "0.0.0.0", "HostPort": "39001"}],  # noqa: S104 - rejection fixture
        },
    ],
)
def test_missing_or_unsafe_engine_bindings_are_refused(ports: object) -> None:
    with pytest.raises(ValueError, match="loopback"):
        inspected_loopback_port(json.dumps(ports), "5432")


def test_unpublished_image_ports_do_not_count_as_host_bindings() -> None:
    ports = {"9000/tcp": [{"HostIp": "127.0.0.1", "HostPort": "39000"}], "9001/tcp": None}
    assert inspected_loopback_port(json.dumps(ports), "9000") == 39000


def test_disposable_connection_cannot_accept_ambient_database_url() -> None:
    with pytest.raises(ValidationError):
        IsolatedServices.model_validate({"database_url": "postgresql://shared/database"})
    assert mapped_loopback_port("127.0.0.1:35432\n") == 35432


def test_repository_sensitive_files_are_excluded() -> None:
    assert Path(".env.example") in inspect_repository()


@pytest.mark.parametrize("failure", [None, "write", "port", "binding", "tcp", "verify_binding"])
def test_mocked_harness_scopes_cleanup_and_propagates_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure: str | None
) -> None:
    commands: list[list[str]] = []
    stages: list[str] = []
    connections: list[int] = []
    restarted = False
    services = {
        "postgres": ("1" * 64, "5432"),
        "redis": ("2" * 64, "6379"),
        "minio": ("3" * 64, "9000"),
    }

    def host_port(target: str) -> int:
        return int(target) + 30000 + (1000 if restarted else 0)

    monkeypatch.setattr(integration_services, "ROOT", tmp_path)
    monkeypatch.setattr("scripts.integration_services.shutil.which", lambda _: "/test/docker")
    monkeypatch.delenv("DOCKER_HOST", raising=False)

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal restarted
        commands.append(command)
        output = ""
        code = 0
        if command[1:3] == ["context", "inspect"]:
            output = "unix:///test/docker.sock"
        elif "ps" in command:
            output = services[command[-1]][0]
        elif "port" in command:
            output = "invalid IP:0" if failure == "port" else f"127.0.0.1:{host_port(command[-1])}"
        elif command[1] == "inspect":
            target = next(
                target for container, target in services.values() if container == command[-1]
            )
            address = "0.0.0.0" if failure == "binding" else "127.0.0.1"  # noqa: S104 - rejection fixture
            port = host_port(target) + (1 if failure == "verify_binding" and restarted else 0)
            output = json.dumps({f"{target}/tcp": [{"HostIp": address, "HostPort": str(port)}]})
        elif "stop" in command:
            restarted = True
        elif "pytest" in command:
            config = IsolatedServices.model_validate_json(
                Path(kwargs["env"]["PHASE0_TEST_CONFIG"]).read_bytes()
            )
            stages.append(config.stage)
            assert config.database_name.startswith("phase0_")
            assert config.database_port == host_port("5432")
            assert config.redis_port == host_port("6379")
            assert config.storage_port == host_port("9000")
            code = 1 if failure == "write" and config.stage == "write" else 0
        return subprocess.CompletedProcess(command, code, output, "")

    def fake_connect(address: tuple[str, int], timeout: int) -> nullcontext[None]:
        assert address[0] == "127.0.0.1" and timeout == 3
        if failure == "tcp":
            raise ConnectionRefusedError("Fixture: port is unreachable")
        connections.append(address[1])
        return nullcontext()

    monkeypatch.setattr("scripts.integration_services.subprocess.run", fake_run)
    monkeypatch.setattr("scripts.integration_services.socket.create_connection", fake_connect)
    assert integration_services.main() == int(failure is not None)
    compose_commands = [command for command in commands if "--project-name" in command]
    projects = {command[command.index("--project-name") + 1] for command in compose_commands}
    assert len(projects) == 1 and next(iter(projects)).startswith("phase0-test-")
    assert commands[-1][-3:] == ["down", "--volumes", "--remove-orphans"]
    if failure is None:
        assert stages == ["write", "verify"]
        assert len(connections) == 6
    elif failure in {"write", "verify_binding"}:
        assert stages == ["write"]
    else:
        assert stages == []
