"""Bound AI JSON before parsing; never inspect or log request contents."""

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class AIJSONLimit:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope.get("method") not in {"POST", "PATCH"}
            or not scope.get("path", "").startswith("/api/v1/ai/")
        ):
            await self.app(scope, receive, send)
            return
        length = dict(scope.get("headers", [])).get(b"content-length")
        if length is not None and (not length.isdigit() or int(length) > 65536):
            await JSONResponse(status_code=413, content={"detail": "AI_REQUEST_BYTE_LIMIT"})(
                scope, receive, send
            )
            return
        consumed = 0

        async def limited() -> Message:
            nonlocal consumed
            message = await receive()
            consumed += len(message.get("body", b""))
            if consumed > 65536:
                raise HTTPException(413, "AI_REQUEST_BYTE_LIMIT")
            return message

        await self.app(scope, limited, send)
