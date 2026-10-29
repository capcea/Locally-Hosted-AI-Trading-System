"""Simulation-only status and authenticated Phase 1 management API."""

import json
import logging
import os
import re
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from minio.error import S3Error
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware
from urllib3.exceptions import HTTPError as StorageHTTPError

from apps.api.ai.cloud_routes import router as ai_cloud_router
from apps.api.ai.routes import router as ai_router
from apps.api.campaigns.routes import router as campaign_router
from apps.api.catalog import PLANNED_SERVICES, ROADMAP
from apps.api.config import Settings
from apps.api.execution.limits import ExecutionLimit
from apps.api.execution.routes import router as execution_router
from apps.api.governance.routes import router as governance_router
from apps.api.health import infrastructure_health
from apps.api.identity.routes import router as identity_router
from apps.api.market.limits import ImportLimit
from apps.api.market.routes import router as market_router
from apps.api.research.routes import router as research_router
from apps.api.risk.routes import router as risk_router
from packages.ai.settings import GatewaySettings
from packages.domain.contracts import (
    Overview,
    ReferenceProfile,
    SafetyState,
    ServiceHealth,
    ServiceStatus,
)
from packages.domain.safety import ExecutionDisabledError, deny_order_submission
from packages.market.storage import DataIntegrityError
from packages.persistence.store import Store

logger = logging.getLogger("research.requests")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())


def create_app(
    settings: Settings | None = None, ai_config: GatewaySettings | None = None
) -> FastAPI:
    config = settings or Settings(
        _env_file=None if os.environ.get("APP_ENVIRONMENT") == "test" else ".env"
    )
    store = Store(config.database_url.get_secret_value()) if config.database_url else None

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            if store:
                store.engine.dispose()

    started = time.monotonic()
    app = FastAPI(
        title="AI Trading Research Platform",
        version="0.1.0",
        description=(
            "Local simulation-only status and authenticated governance. No trading capability."
        ),
        lifespan=lifespan,
    )
    app.state.settings = config
    app.state.store = store
    app.state.ai_error = None
    try:
        ai_settings = ai_config or GatewaySettings()
        if (
            (ai_settings.data_key or ai_settings.data_key_file)
            and config.auth_encryption_key
            and ai_settings.key_value() == config.auth_encryption_key.get_secret_value()
        ):
            raise ValueError("AI key reuse refused")
        app.state.ai_config = ai_settings
    except (ValueError, OSError):
        # Invalid/unreadable optional AI configuration must not unmount authenticated safety.
        # Construct trusted empty defaults without re-reading the malformed AI environment.
        app.state.ai_config = GatewaySettings.model_construct()
        app.state.ai_error = "AI_CONFIGURATION_INVALID"
        logger.warning('{"event":"AI_CONFIGURATION_INVALID","action":"AI_DISABLED"}')
    app.include_router(identity_router)
    app.include_router(governance_router)
    app.include_router(market_router)
    app.include_router(execution_router)
    app.include_router(risk_router)
    app.include_router(research_router)
    app.include_router(ai_router)
    app.include_router(ai_cloud_router)
    app.include_router(campaign_router)
    allowed_hosts = ["127.0.0.1", "localhost", "api", "web"]
    if config.app_environment == "test":
        allowed_hosts.append("testserver")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts, www_redirect=False)
    app.add_middleware(ImportLimit, max_bytes=config.market_upload_bytes + 250000)
    app.add_middleware(ExecutionLimit)

    @app.middleware("http")
    async def secure_response(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid4())
        request.state.correlation_id = UUID(request_id)
        begin = time.monotonic()
        response = await call_next(request)
        response.headers.update(
            {
                "X-Request-ID": request_id,
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Cache-Control": "no-store",
                "X-Frame-Options": "DENY",
            }
        )
        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "request_id": request_id,
                    "method": request.method,
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - begin) * 1000),
                }
            )
        )
        return response

    @app.get("/health/live")
    def liveness() -> dict[str, str]:
        return {"status": "ok", "mode": "SIMULATED", "version": "0.1.0"}

    @app.get("/health/ready", response_model=list[ServiceHealth])
    async def readiness(response: Response) -> list[ServiceHealth]:
        health = await infrastructure_health(config)
        if not all(item.status == ServiceStatus.HEALTHY for item in health):
            response.status_code = 503
        return health

    @app.get("/api/v1/safety", response_model=SafetyState)
    def safety() -> SafetyState:
        return SafetyState()

    @app.get("/api/v1/overview", response_model=Overview)
    async def overview() -> Overview:
        return Overview(
            timestamp=datetime.now(UTC),
            uptime_seconds=int(time.monotonic() - started),
            safety=SafetyState(),
            services=[
                ServiceHealth(
                    id="api",
                    name="API de control",
                    status=ServiceStatus.HEALTHY,
                    detail="FastAPI · status public local și administrare autentificată.",
                ),
                *await infrastructure_health(config),
                *PLANNED_SERVICES,
            ],
            reference_profile=ReferenceProfile(),
            roadmap=ROADMAP,
        )

    @app.post("/api/v1/live/activate", status_code=403)
    def refuse_live_activation() -> None:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "LIVE_EXECUTION_NOT_IMPLEMENTED",
                "message": "Live activation is unavailable, regardless of credentials.",
            },
        )

    @app.post("/api/v1/orders", status_code=403)
    def refuse_order_submission() -> None:
        deny_order_submission()

    @app.exception_handler(ExecutionDisabledError)
    async def disabled_execution(_: Request, exc: ExecutionDisabledError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={
                "detail": {"code": "ORDER_SUBMISSION_DISABLED", "message": str(exc)},
            },
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        # FastAPI's default error includes the raw rejected input, including credential fields.
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {
                        "loc": list(error["loc"]),
                        "type": error["type"],
                        "msg": "Invalid request value",
                    }
                    for error in exc.errors()
                ]
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_failure(_: Request, __: IntegrityError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "Record conflicts with an existing identity, version or constraint"},
        )

    @app.exception_handler(SQLAlchemyError)
    async def storage_failure(request: Request, error: SQLAlchemyError) -> JSONResponse:
        # Never stringify database exceptions: their statements/parameters can contain secrets.
        sqlstate = getattr(getattr(error, "orig", None), "sqlstate", None)
        logger.error(
            json.dumps(
                {
                    "event": "persistence_failure",
                    "request_id": str(request.state.correlation_id),
                    "category": "PERSISTENCE_TRANSACTION_FAILED",
                    "sqlstate": sqlstate
                    if isinstance(sqlstate, str) and re.fullmatch(r"[0-9A-Z]{5}", sqlstate)
                    else None,
                }
            )
        )
        return JSONResponse(
            status_code=503,
            content={"detail": "Persistent service unavailable; no change accepted"},
            headers={"X-Error-Category": "PERSISTENCE_TRANSACTION_FAILED"},
        )

    @app.exception_handler(DataIntegrityError)
    async def invalid_data(_: Request, __: DataIntegrityError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "Dataset integrity check failed"})

    @app.exception_handler(S3Error)
    @app.exception_handler(StorageHTTPError)
    async def unavailable_storage(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "Object storage unavailable"})

    return app
