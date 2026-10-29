"""Real Playwright acceptance with disposable databases and loopback-only API/Web processes.

Run only where browser execution is permitted. No browser-policy bypass or fallback is implemented.
"""

import base64
import hashlib
import itertools
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
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
from scripts.provision_ai import provision_database, provision_queue
from scripts.provision_market import provision_storage
from scripts.provision_runtime import provision_runtime
from testing.ai_fixture import Fixture

ROOT = Path(__file__).resolve().parents[1]


def safe_server_failures(path: Path) -> list[dict[str, str | None]]:
    """Keep only bounded structured DB diagnostics, never raw server/exception output."""
    with path.open("rb") as source:
        source.seek(max(0, path.stat().st_size - 262144))
        lines = source.read().decode(errors="replace").splitlines()
    failures: list[dict[str, str | None]] = []
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if (
            not isinstance(record, dict)
            or record.get("event") != "persistence_failure"
            or record.get("category") != "PERSISTENCE_TRANSACTION_FAILED"
        ):
            continue
        request_id, sqlstate = record.get("request_id"), record.get("sqlstate")
        if not isinstance(request_id, str) or not re.fullmatch(r"[0-9a-f-]{36}", request_id):
            continue
        failures.append(
            {
                "category": "PERSISTENCE_TRANSACTION_FAILED",
                "request_id": request_id,
                "sqlstate": sqlstate
                if isinstance(sqlstate, str) and re.fullmatch(r"[0-9A-Z]{5}", sqlstate)
                else None,
            }
        )
    return failures[-50:]


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
        "ux",
        "ai",
        "redesign",
        "campaigns",
        "auth",
    }:
        raise RuntimeError(
            "E2E_ONLY_SCENARIO must be foundation, market, broker, risk, research, "
            "ux, ai, redesign, campaigns or auth"
        )
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
        else (
            "foundation",
            "market",
            "broker",
            "risk",
            "research",
            "ux",
            "ai",
            "redesign",
            "campaigns",
            "auth",
        ),
    ):
        database = f"p1_browser_{uuid4().hex}"
        with psycopg.connect(admin_dsn, autocommit=True) as connection:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
        processes: list[subprocess.Popen[bytes]] = []
        ai_fixture: Fixture | None = None
        ai_thread: threading.Thread | None = None
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
            ai_env: dict[str, str] = {}
            if scenario == "auth":
                # Fixed-destination registration only: no worker, provider key or inference.
                api_env.update(
                    {
                        "AI_OPENROUTER_ENABLED": "true",
                        "AI_DATA_KEY": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
                    }
                )
            if scenario == "ai":
                # Real HTTP protocol fixture, never reported as a real model or benchmark.
                ai_fixture = Fixture()
                ai_thread = threading.Thread(target=ai_fixture.serve_forever, daemon=True)
                ai_thread.start()
                ai_password = hashlib.sha256(
                    ("ai-browser:" + isolated.storage_password.get_secret_value()).encode()
                ).hexdigest()
                ai_database = provision_database(url, ai_password)
                provision_queue(isolated.redis_url, "ai_api", ai_password)
                provision_queue(isolated.redis_url, "ai_worker", ai_password)
                ai_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
                ai_shared = {
                    "AI_DATA_KEY": ai_key,
                    "AI_ENDPOINTS": json.dumps(
                        [
                            {
                                "id": "fixture",
                                "label": "SYNTHETIC_HTTP_FIXTURE",
                                "url": ai_fixture.url,
                                "transport": "LOOPBACK",
                                "private_only_attested": True,
                            }
                        ]
                    ),
                }
                api_env.update(
                    {
                        **ai_shared,
                        "AI_REDIS_URL": f"redis://ai_api:{ai_password}@127.0.0.1:{isolated.redis_port}/0",
                    }
                )
                # Whitelist only: never inherit the API's auth/risk key or storage credentials.
                ai_env = {
                    **common,
                    **ai_shared,
                    "AI_DATABASE_URL": ai_database,
                    "AI_REDIS_URL": f"redis://ai_worker:{ai_password}@127.0.0.1:{isolated.redis_port}/0",
                }
            with (
                tempfile.TemporaryDirectory(
                    prefix="phase1-browser-", dir=ROOT / ".cache"
                ) as directory,
                open(Path(directory) / "servers.txt", "xb") as log,
            ):
                os.chmod(log.name, 0o600)
                if scenario == "ai":
                    processes.append(
                        subprocess.Popen(  # noqa: S603 -- fixed inference-only worker
                            [sys.executable, "-m", "scripts.ai_worker"],
                            cwd=ROOT,
                            env=ai_env,
                            stdout=log,
                            stderr=subprocess.STDOUT,
                            start_new_session=True,
                        )
                    )
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
                if scenario == "campaigns":
                    processes.append(
                        subprocess.Popen(  # noqa: S603 - fixed campaign metadata worker
                            [sys.executable, "-m", "scripts.campaign_worker"],
                            cwd=ROOT,
                            env={
                                k: v
                                for k, v in api_env.items()
                                if k
                                not in {
                                    "AUTH_BOOTSTRAP_TOKEN",
                                    "AUTH_COOKIE_SECURE",
                                    "AUTH_ORIGINS",
                                }
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
                        ["e2e/auth-session.spec.ts"]
                        if scenario == "auth"
                        else ["e2e/platform.spec.ts", "e2e/phase1.spec.ts"]
                        if scenario == "foundation"
                        else ["e2e/phase2.spec.ts"]
                        if scenario == "market"
                        else ["e2e/phase3.spec.ts"]
                        if scenario == "broker"
                        else ["e2e/phase4.spec.ts"]
                        if scenario == "risk"
                        else ["e2e/phase5.spec.ts"]
                        if scenario == "research"
                        else ["e2e/phase6.spec.ts"]
                        if scenario == "ai"
                        else ["e2e/phase7a.spec.ts"]
                        if scenario == "campaigns"
                        else ["e2e/redesign-v1.spec.ts"]
                        if scenario == "redesign"
                        else ["e2e/ux-workflows.spec.ts", "e2e/ux-visual.spec.ts"]
                    ),
                    *(
                        ["--update-snapshots"]
                        if os.environ.get("E2E_UPDATE_SNAPSHOTS") == "1" and scenario == "ux"
                        else []
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
                        "PHASE0_TEST_CONFIG": str(config_file),
                        "E2E_AUTH_DATABASE": database if scenario == "auth" else "",
                        "E2E_V1_CAPTURES": "1"
                        if scenario == "redesign" and os.environ.get("V1_CAPTURE_CANDIDATES") == "1"
                        else "0",
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
                    log.flush()
                    print(
                        json.dumps({"backend_failures": safe_server_failures(Path(log.name))}),
                        flush=True,
                    )
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
            if ai_fixture:
                ai_fixture.release.set()
                ai_fixture.shutdown()
                ai_fixture.server_close()
            if ai_thread:
                ai_thread.join(3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
