"""Bound multipart request bodies before untrusted file parsing/spooling."""

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class ImportLimit:
    def __init__(self, app: ASGIApp, max_bytes: int):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") != "/api/v1/market/imports":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        length = headers.get(b"content-length", b"")
        if not length.isdigit() or int(length) > self.max_bytes:
            await JSONResponse(
                status_code=413, content={"detail": "Bounded Content-Length required"}
            )(scope, receive, send)
            return
        consumed = 0

        async def bounded_receive() -> Message:
            nonlocal consumed
            message = await receive()
            consumed += len(message.get("body", b""))
            if consumed > self.max_bytes:
                raise HTTPException(413, "Import request exceeds byte quota")
            return message

        await self.app(scope, bounded_receive, send)
