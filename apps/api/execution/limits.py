"""Bound execution JSON before parsing untrusted snapshots or simulation commands."""

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class ExecutionLimit:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope.get("method") != "POST"
            or not scope.get("path", "").startswith(
                ("/api/v1/execution/", "/api/v1/risk/", "/api/v1/research/")
            )
        ):
            await self.app(scope, receive, send)
            return
        length = dict(scope.get("headers", [])).get(b"content-length", b"")
        if not length.isdigit() or int(length) > 1048576:
            await JSONResponse(status_code=413, content={"detail": "Bounded JSON required"})(
                scope, receive, send
            )
            return
        consumed = 0

        async def limited() -> Message:
            nonlocal consumed
            message = await receive()
            consumed += len(message.get("body", b""))
            if consumed > 1048576:
                raise HTTPException(413, "Execution request quota exceeded")
            return message

        await self.app(scope, limited, send)
