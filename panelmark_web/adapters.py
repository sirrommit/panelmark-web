"""Framework adapters for handle_connection.

These thin wrappers translate framework-specific WebSocket APIs into the
generic interface expected by ``handle_connection``:

    await websocket.recv() -> str
    await websocket.send(str)
"""


class StarletteAdapter:
    """Adapt a FastAPI / Starlette WebSocket to the panelmark-web interface.

    Usage::

        from fastapi import FastAPI, WebSocket
        from panelmark_web.server import handle_connection
        from panelmark_web.adapters import StarletteAdapter

        app = FastAPI()

        @app.websocket("/ws")
        async def ws_endpoint(websocket: WebSocket):
            await websocket.accept()
            await handle_connection(StarletteAdapter(websocket), shell_factory)
    """

    def __init__(self, ws) -> None:
        self._ws = ws

    async def recv(self) -> str:
        """Receive the next text message.

        Raises ``starlette.websockets.WebSocketDisconnect`` when the client
        disconnects; ``handle_connection`` catches this and exits cleanly.
        """
        return await self._ws.receive_text()

    async def send(self, data: str) -> None:
        """Send a text message."""
        await self._ws.send_text(data)
