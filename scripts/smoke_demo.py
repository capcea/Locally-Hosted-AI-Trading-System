"""Smoke the running API; fail if any order or live activation is accepted."""

import argparse
from urllib.parse import urlsplit

import httpx
from pydantic import TypeAdapter

from packages.domain.contracts import Overview, SafetyState, ServiceHealth, ServiceStatus


def validate_local_target(base_url: str) -> None:
    url = urlsplit(base_url)
    if (
        url.scheme != "http"
        or url.hostname not in {"127.0.0.1", "::1"}
        or url.username
        or url.password
        or url.query
        or url.fragment
        or url.path not in {"", "/"}
    ):
        raise ValueError("Smoke checks require a literal HTTP loopback address without credentials")


def smoke(base_url: str, require_ready: bool) -> None:
    validate_local_target(base_url)
    with httpx.Client(
        base_url=base_url, timeout=15, trust_env=False, follow_redirects=False
    ) as client:
        live = client.get("/health/live")
        live.raise_for_status()
        if live.json() != {"status": "ok", "mode": "SIMULATED", "version": "0.1.0"}:
            raise RuntimeError("Unexpected application or execution environment")
        safety_response = client.get("/api/v1/safety")
        safety_response.raise_for_status()
        safety_data = safety_response.json()
        if not isinstance(safety_data, dict) or set(safety_data) != set(SafetyState.model_fields):
            raise RuntimeError("Incomplete safety contract; no denial probes will be sent")
        SafetyState.model_validate_json(safety_response.content, strict=True)
        for flag in (
            "live_trading_enabled",
            "order_submission_enabled",
            "generated_code_execution",
        ):
            if safety_data[flag] is not False:
                raise RuntimeError("Execution is not explicitly disabled")
        overview = client.get("/api/v1/overview")
        overview.raise_for_status()
        snapshot = Overview.model_validate_json(overview.content)
        if (
            snapshot.phase not in {0, 1, 2, 3, 4, 5, 6}
            or snapshot.application != "AI Trading Research Platform"
        ):
            raise RuntimeError("Unexpected application; denial probes refused")
        for endpoint in ("/api/v1/orders", "/api/v1/live/activate"):
            if (
                client.post(endpoint, json={"mode": "SIMULATED", "audit_probe": True}).status_code
                != 403
            ):
                raise RuntimeError(f"Execution was not refused at {endpoint}")
        ready = client.get("/health/ready")
        if ready.status_code not in {200, 503}:
            raise RuntimeError(f"Unexpected readiness HTTP status: {ready.status_code}")
        services = TypeAdapter(list[ServiceHealth]).validate_json(ready.content)
        if len(services) != 3 or {item.id for item in services} != {"postgres", "redis", "storage"}:
            raise RuntimeError("Incomplete readiness contract")
        healthy = all(item.status == ServiceStatus.HEALTHY for item in services)
        if (ready.status_code == 200) != healthy:
            raise RuntimeError("Inconsistent readiness status and dependency states")
        if require_ready and not healthy:
            raise RuntimeError("Infrastructure readiness failed (HTTP 503)")
        print(f"API + execution-denial smoke: PASS. Infrastructure readiness: {ready.status_code}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18000")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    smoke(args.base_url, args.require_ready)
