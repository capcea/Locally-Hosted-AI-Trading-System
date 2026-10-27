"""Real Playwright acceptance with disposable databases and loopback-only API/Web processes.

Run only where browser execution is permitted. No browser-policy bypass or fallback is implemented.
"""

import base64
import hashlib
import itertools
import json
import os
import secrets
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy.engine import make_url

from scripts.integration_services import IsolatedServices
from scripts.provision_market import provision_storage
from scripts.provision_runtime import provision_runtime

ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = int(listener.getsockname()[1])
        if port < 1024:
            raise RuntimeError("Non-privileged loopback port required")
        return port


def ready(url: str, processes: list[subprocess.Popen[bytes]]) -> None:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if any(process.poll() is not None for process in processes):
            raise RuntimeError("Isolated application process stopped before readiness")
        try:
            if httpx.get(url, timeout=2).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    raise RuntimeError("Isolated application readiness timed out")


def main() -> int:
    config_file = os.environ.get("PHASE0_TEST_CONFIG")
    if not config_file:
        raise RuntimeError("Use make browser-integration; ambient databases are prohibited")
    # Explicit focused runs keep the same isolated services and authentication workflow.
    # With no selection, every desktop/mobile foundation and market case still runs.
    only_project = os.environ.get("E2E_ONLY_PROJECT")
    only_scenario = os.environ.get("E2E_ONLY_SCENARIO")
    if only_project is not None and only_project not in {"desktop", "mobile"}:
        raise RuntimeError("E2E_ONLY_PROJECT must be desktop or mobile")
    if only_scenario is not None and only_scenario not in {
        "foundation",
        "market",
        "broker",
        "risk",
        "research",
    }:
        raise RuntimeError("E2E_ONLY_SCENARIO must be foundation, market, broker, risk or research")
    isolated = IsolatedServices.model_validate_json(Path(config_file).read_bytes())
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("npm is required")
    admin = make_url(isolated.database_url)
    admin_dsn = admin.set(drivername="postgresql", database="postgres").render_as_string(
        hide_password=False
    )
    # A fresh database per viewport/scenario exercises owner setup through the real UI.
    for project, scenario in itertools.product(
        (only_project,) if only_project else ("desktop", "mobile"),
        (only_scenario,)
        if only_scenario
        else ("foundation", "market", "broker", "risk", "research"),
    ):
        database = f"p1_browser_{uuid4().hex}"
        with psycopg.connect(admin_dsn, autocommit=True) as connection:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
        processes: list[subprocess.Popen[bytes]] = []
        try:
            url = admin.set(database=database).render_as_string(hide_password=False)
            migration = Config(str(ROOT / "alembic.ini"))
            migration.attributes["database_url"] = url
            command.upgrade(migration, "head")
            runtime = provision_runtime(url, isolated.storage_password.get_secret_value())
            storage_user = "browser-" + uuid4().hex[:20]
            storage_password = secrets.token_hex(32)
            bucket = "browser-market-" + uuid4().hex
            provision_storage(
                "http://" + isolated.storage_endpoint,
                "phase0-test",
                isolated.storage_password.get_secret_value(),
                storage_user,
                storage_password,
                bucket,
            )
            key = base64.urlsafe_b64encode(
                hashlib.sha256(secrets.token_bytes(32)).digest()
            ).decode()
            setup_token, password = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
            api_port, web_port = free_port(), free_port()
            while api_port == web_port:
                web_port = free_port()
            base_url = f"http://127.0.0.1:{web_port}"
            common = {
                key: value
                for key, value in os.environ.items()
                if key
                in {
                    "PATH",
                    "HOME",
                    "TMPDIR",
                    "LANG",
                    "LC_ALL",
                    "PLAYWRIGHT_BROWSERS_PATH",
                    "CI",
                }
            }
            common["npm_config_cache"] = str(ROOT / ".cache/npm")
            api_env = {
                **common,
                "APP_ENVIRONMENT": "test",
                "DATABASE_URL": runtime,
                "REDIS_URL": isolated.redis_url,
                "OBJECT_STORE_URL": f"http://{isolated.storage_endpoint}",
                "AUTH_ENCRYPTION_KEY": key,
                "MARKET_STORAGE_USER": storage_user,
                "MARKET_STORAGE_PASSWORD": storage_password,
                "MARKET_BUCKET": bucket,
                "AUTH_BOOTSTRAP_TOKEN": setup_token,
                "AUTH_COOKIE_SECURE": "false",
                "AUTH_ORIGINS": json.dumps([base_url]),
                "BROKER_ENVIRONMENT": "SIMULATED",
                "EXECUTOR_CAPABILITY": "DENY_ALL",
                "LIVE_TRADING_ENABLED": "false",
                "WORKER_EXECUTION_ENABLED": "false",
            }
            with (
                tempfile.TemporaryDirectory(
                    prefix="phase1-browser-", dir=ROOT / ".cache"
                ) as directory,
                open(Path(directory) / "servers.txt", "xb") as log,
            ):
                os.chmod(log.name, 0o600)
                processes.append(
                    subprocess.Popen(  # noqa: S603 - fixed local application command
                        [
                            sys.executable,
                            "-m",
                            "uvicorn",
                            "apps.api.main:create_app",
                            "--factory",
                            "--host",
                            "127.0.0.1",
                            "--port",
                            str(api_port),
                            "--no-access-log",
                            "--no-proxy-headers",
                        ],
                        cwd=ROOT,
                        env=api_env,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                )
                ready(f"http://127.0.0.1:{api_port}/health/ready", processes)
                processes.append(
                    subprocess.Popen(  # noqa: S603 - fixed trusted data worker
                        [sys.executable, "-m", "scripts.market_worker"],
                        cwd=ROOT,
                        env=api_env,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                )
                processes.append(
                    subprocess.Popen(  # noqa: S603 - fixed reviewed research registry only
                        [sys.executable, "-m", "scripts.research_worker"],
                        cwd=ROOT,
                        env={
                            key: value
                            for key, value in api_env.items()
                            if key
                            not in {"AUTH_BOOTSTRAP_TOKEN", "AUTH_COOKIE_SECURE", "AUTH_ORIGINS"}
                        },
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                )
                processes.append(
                    subprocess.Popen(  # noqa: S603 - fixed independent risk monitor
                        [sys.executable, "-m", "scripts.risk_monitor"],
                        cwd=ROOT,
                        env={
                            **common,
                            "APP_ENVIRONMENT": "test",
                            "DATABASE_URL": runtime,
                            "AUTH_ENCRYPTION_KEY": key,
                            "BROKER_ENVIRONMENT": "SIMULATED",
                            "EXECUTOR_CAPABILITY": "DENY_ALL",
                            "LIVE_TRADING_ENABLED": "false",
                            "WORKER_EXECUTION_ENABLED": "false",
                        },
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                )
                processes.append(
                    subprocess.Popen(  # noqa: S603 - fixed local application command
                        [npm, "run", "dev", "--", "--port", str(web_port)],
                        cwd=ROOT / "apps/web",
                        env={**common, "PHASE1_E2E_API_PORT": str(api_port)},
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                )
                ready(base_url, processes)
                test_command = [
                    npm,
                    "run",
                    "test:e2e",
                    "--",
                    *(
                        ["e2e/platform.spec.ts", "e2e/phase1.spec.ts"]
                        if scenario == "foundation"
                        else ["e2e/phase2.spec.ts"]
                        if scenario == "market"
                        else ["e2e/phase3.spec.ts"]
                        if scenario == "broker"
                        else ["e2e/phase4.spec.ts"]
                        if scenario == "risk"
                        else ["e2e/phase5.spec.ts"]
                    ),
                    f"--project={project}",
                    "--workers=1",
                ]
                print(
                    "+ " + shlex.join(test_command),
                    flush=True,
                )
                runner = subprocess.Popen(  # noqa: S603 - fixed Playwright command and project names
                    test_command,
                    cwd=ROOT / "apps/web",
                    env={
                        **common,
                        "E2E_EXTERNAL_SERVERS": "1",
                        "E2E_BASE_URL": base_url,
                        "E2E_PHASE1_ISOLATED": "1",
                        "E2E_SETUP_TOKEN": setup_token,
                        "E2E_OWNER_PASSWORD": password,
                    },
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                processes.append(runner)
                output = runner.communicate(timeout=300)[0].decode(errors="replace")
                for value in (
                    setup_token,
                    storage_password,
                    password,
                    key,
                    isolated.storage_password.get_secret_value(),
                ):
                    output = output.replace(value, "[REDACTED]")
                print(output, flush=True)
                if runner.returncode:
                    return runner.returncode
        finally:
            for process in reversed(processes):
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    with suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            with psycopg.connect(admin_dsn, autocommit=True) as connection:
                connection.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database))
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
