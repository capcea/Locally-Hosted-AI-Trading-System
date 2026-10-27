"""Small read requests only; enforce real body bytes before JSON decoding."""

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class BridgeLimit:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") != "POST":
            await self.app(scope, receive, send)
            return
        length = dict(scope.get("headers", [])).get(b"content-length", b"")
        if not length.isdigit() or int(length) > 16384:
            await JSONResponse(
                status_code=413, content={"detail": "Bounded read request required"}
            )(scope, receive, send)
            return
        count = 0

        async def limited() -> Message:
            nonlocal count
            message = await receive()
            count += len(message.get("body", b""))
            if count > 16384:
                raise HTTPException(413, "Bridge read request limit exceeded")
            return message

        await self.app(scope, limited, send)
