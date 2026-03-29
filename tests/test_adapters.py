"""Tests for framework adapters."""

import asyncio
import json

from panelmark_web.adapters import StarletteAdapter


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class _FakeStarletteWS:
    """Minimal stub of a Starlette WebSocket."""

    def __init__(self, messages: list[str]):
        self._incoming = list(messages)
        self.sent: list[str] = []

    async def receive_text(self) -> str:
        if not self._incoming:
            # Simulate WebSocketDisconnect
            raise Exception("WebSocketDisconnect")
        return self._incoming.pop(0)

    async def send_text(self, data: str) -> None:
        self.sent.append(data)


def test_recv_returns_text():
    async def _run():
        ws = _FakeStarletteWS(['{"type":"ping"}'])
        adapter = StarletteAdapter(ws)
        result = await adapter.recv()
        assert result == '{"type":"ping"}'

    run(_run())


def test_send_calls_send_text():
    async def _run():
        ws = _FakeStarletteWS([])
        adapter = StarletteAdapter(ws)
        await adapter.send('{"type":"render"}')
        assert ws.sent == ['{"type":"render"}']

    run(_run())


def test_recv_propagates_disconnect_exception():
    async def _run():
        ws = _FakeStarletteWS([])   # empty — raises on recv
        adapter = StarletteAdapter(ws)
        try:
            await adapter.recv()
            assert False, "should have raised"
        except Exception:
            pass  # expected

    run(_run())


def test_adapter_with_handle_connection():
    """End-to-end: adapter feeds into handle_connection correctly."""
    import json as _json
    from panelmark.shell import Shell
    from panelmark.interactions.base import Interaction
    from panelmark.draw import WriteCmd
    from panelmark_web.server import handle_connection

    class Stub(Interaction):
        def render(self, ctx, focused=False):
            return [WriteCmd(row=0, col=0, text="hi")]
        def handle_key(self, key): return False, None
        def get_value(self): return None
        def set_value(self, v): pass

    SHELL_DEF = """
|=====|
|{12R $main$ }|
|=====|
"""

    class FakeStarletteWS:
        def __init__(self, messages):
            self._incoming = [_json.dumps(m) for m in messages]
            self.sent = []

        async def receive_text(self):
            if not self._incoming:
                raise Exception("disconnected")
            return self._incoming.pop(0)

        async def send_text(self, data):
            self.sent.append(_json.loads(data))

    async def _run():
        raw_ws = FakeStarletteWS([
            {"type": "connect", "v": 1, "panels": [
                {"region": "main", "width": 20, "height": 5}
            ]},
        ])
        def factory():
            shell = Shell(SHELL_DEF)
            shell.assign("main", Stub())
            return shell
        await handle_connection(StarletteAdapter(raw_ws), factory)
        assert raw_ws.sent[0]["type"] == "render"

    run(_run())
