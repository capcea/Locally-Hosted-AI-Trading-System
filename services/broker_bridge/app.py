"""Independently launched mTLS + bearer read-only bridge, never included in the main image."""

import asyncio
import hmac
import json
import multiprocessing
import ssl
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Literal
from uuid import UUID

import uvicorn
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from packages.brokers.contracts import BrokerSnapshot, SignedObservation, SnapshotRequest
from packages.domain.serialization import canonical
from services.broker_bridge.limits import BridgeLimit
from services.broker_bridge.security import OAuth, TokenVault, private_file


class BridgeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    provider: Literal["MT5", "CTRADER"]
    authorized_demo_reads: Literal[True]
    connection_id: UUID
    account_id: str = Field(min_length=1, max_length=100)
    server: str = Field(min_length=1, max_length=120)
    authorization_token_file: Path
    signing_key_file: Path
    tls_cert: Path
    tls_key: Path
    client_ca: Path
    client_id: str | None = None
    client_secret: SecretStr | None = None
    oauth_redirect: str | None = None
    token_file: Path | None = None
    token_key_file: Path | None = None


def oauth_for(config: BridgeConfig) -> OAuth:
    if (
        not config.client_id
        or not config.client_secret
        or not config.oauth_redirect
        or not config.token_file
        or not config.token_key_file
    ):
        raise PermissionError("Private cTrader OAuth configuration required")
    return OAuth(
        config.client_id,
        config.client_secret,
        config.oauth_redirect,
        TokenVault(config.token_file, config.token_key_file),
    )


def child_read(config_bytes: bytes, request_bytes: bytes, output: object) -> None:
    from services.broker_bridge.ctrader import CTraderAdapter
    from services.broker_bridge.mt5 import MT5Adapter

    try:
        if __import__("sys").platform != "win32":
            import resource

            resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024, 768 * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
        config = BridgeConfig.model_validate_json(config_bytes)
        request = SnapshotRequest.model_validate_json(request_bytes)
        if config.provider == "MT5":
            snapshot = MT5Adapter(True).snapshot(request)
        else:
            tokens = oauth_for(config).current()
            snapshot = CTraderAdapter(
                config.client_id or "",
                config.client_secret.get_secret_value() if config.client_secret else "",
                tokens.access.get_secret_value(),
                True,
            ).snapshot(request)
        output.send_bytes(snapshot.model_dump_json().encode())  # type: ignore[attr-defined]
    except Exception:
        output.send_bytes(b'{"error":"BROKER_READ_UNAVAILABLE"}')  # type: ignore[attr-defined]
    finally:
        output.close()  # type: ignore[attr-defined]


def bounded_read(config: BridgeConfig, request: SnapshotRequest) -> BrokerSnapshot:
    # A spawned process permits terminating a hung native SDK call.
    context = multiprocessing.get_context("spawn")
    receiving, sending = context.Pipe(duplex=False)
    config_data = config.model_dump(mode="json")
    if config.client_secret:
        config_data["client_secret"] = config.client_secret.get_secret_value()
    process = context.Process(
        target=child_read,
        args=(json.dumps(config_data).encode(), request.model_dump_json().encode(), sending),
    )
    process.start()
    sending.close()
    try:
        if not receiving.poll(30):
            raise TimeoutError("Broker read exceeded the process deadline")
        return BrokerSnapshot.model_validate_json(receiving.recv_bytes(1048576))
    finally:
        receiving.close()
        if process.is_alive():
            process.terminate()
        process.join(timeout=3)
        if process.is_alive():
            process.kill()
            process.join(timeout=3)


def create_bridge(
    config: BridgeConfig, reader: Callable[[SnapshotRequest], BrokerSnapshot] | None = None
) -> FastAPI:
    token = private_file(config.authorization_token_file).strip().decode()
    if len(token) < 43:
        raise PermissionError("Generated 256-bit service identity required")
    signing = Ed25519PrivateKey.from_private_bytes(private_file(config.signing_key_file))
    busy = threading.BoundedSemaphore(1)
    oauth = oauth_for(config) if config.provider == "CTRADER" else None

    def authenticated(authorization: str = Header(default="")) -> None:
        if not hmac.compare_digest(authorization, "Bearer " + token):
            raise HTTPException(403, "Private bridge authentication required")

    app = FastAPI(
        title="Private demo read-only broker bridge",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(BridgeLimit)

    @app.get("/health", dependencies=[Depends(authenticated)])
    def health() -> dict[str, object]:
        return {
            "mode": "DEMO_READ_ONLY",
            "provider": config.provider,
            "external_execution": False,
            "connected": False,
            "status": "SNAPSHOT_CONNECTION_ONLY",
        }

    @app.get("/public-key", dependencies=[Depends(authenticated)])
    def public_key() -> dict[str, str]:
        return {"public_key": signing.public_key().public_bytes_raw().hex()}

    @app.post("/snapshot", response_model=SignedObservation, dependencies=[Depends(authenticated)])
    async def snapshot(request: SnapshotRequest) -> SignedObservation:
        if request.account_id != config.account_id or request.server != config.server:
            raise HTTPException(403, "Pinned account/server mismatch")
        if not busy.acquire(blocking=False):
            raise HTTPException(429, "One bounded broker read at a time")
        try:
            started = time.monotonic()
            data = (
                await asyncio.to_thread(reader, request)
                if reader
                else await asyncio.to_thread(bounded_read, config, request)
            )
            if (
                data.account_id != config.account_id
                or data.server != config.server
                or data.provider != config.provider
            ):
                raise PermissionError("Broker response identity mismatch")
            data.latency_ms = round((time.monotonic() - started) * 1000)
            body = {
                "connection_id": str(config.connection_id),
                "snapshot": data.model_dump(mode="json"),
            }
            return SignedObservation(
                connection_id=config.connection_id,
                snapshot=data,
                signature=signing.sign(canonical(body)).hex(),
            )
        except Exception:
            raise HTTPException(
                503, "Read-only broker snapshot unavailable; no execution attempted"
            ) from None
        finally:
            busy.release()

    @app.post("/oauth/start", dependencies=[Depends(authenticated)])
    def oauth_start() -> dict[str, str]:
        if oauth is None:
            raise HTTPException(404, "OAuth unavailable for this provider")
        return {"authorization_url": oauth.start(), "scope": "accounts"}

    @app.get("/oauth/callback")
    def oauth_callback(code: str, state: str) -> dict[str, bool]:
        if oauth is None:
            raise HTTPException(404, "OAuth unavailable for this provider")
        if not busy.acquire(blocking=False):
            raise HTTPException(429, "OAuth must wait for the bounded broker read")
        try:
            oauth.callback(code, state)
        except Exception:
            raise HTTPException(403, "OAuth callback refused") from None
        finally:
            busy.release()
        return {
            "stored_privately": True,
            "read_only_scope_still_requires_protocol_verification": True,
        }

    return app


def server_for(config: BridgeConfig, port: int = 18443) -> uvicorn.Server:
    if not 1024 <= port <= 65535:
        raise ValueError("Non-privileged private listener required")
    private_file(config.tls_key)
    return uvicorn.Server(
        uvicorn.Config(
            create_bridge(config),
            host="127.0.0.1",
            port=port,
            ssl_certfile=str(config.tls_cert),
            ssl_keyfile=str(config.tls_key),
            ssl_ca_certs=str(config.client_ca),
            ssl_cert_reqs=ssl.CERT_REQUIRED,
            access_log=False,
            log_level="warning",
        )
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Private mTLS + bearer demo-read bridge; no orders"
    )
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = BridgeConfig.model_validate_json(private_file(args.config))
    server_for(config).run()


if __name__ == "__main__":
    main()
