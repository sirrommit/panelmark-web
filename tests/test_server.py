"""Tests for the WebSocket server handler."""

import asyncio
import json
import pytest
from panelmark.shell import Shell
from panelmark.interactions.base import Interaction
from panelmark.draw import WriteCmd, RenderContext

from panelmark_web.server import handle_connection, handle_connection_sync


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


SHELL_DEF = """
|=====|
|{12R $main$ }|
|=====|
"""


class StubInteraction(Interaction):
    def render(self, context, focused=False):
        return [WriteCmd(row=0, col=0, text="content")]

    def handle_key(self, key):
        return False, None

    def get_value(self):
        return None

    def set_value(self, value):
        pass


class ExitInteraction(Interaction):
    def render(self, context, focused=False):
        return [WriteCmd(row=0, col=0, text="bye")]

    def handle_key(self, key):
        return False, None

    def get_value(self):
        return None

    def set_value(self, value):
        pass

    def signal_return(self):
        return True, "done"


class _ConnectionClosed(Exception):
    pass


class MockWebSocket:
    """In-memory WebSocket stub matching the handle_connection interface.

    Supports:
        await ws.recv() -> str  (raises _ConnectionClosed when queue is empty)
        await ws.send(str)
    """

    def __init__(self, messages: list[dict]):
        self._incoming = [json.dumps(m) for m in messages]
        self.sent: list[dict] = []

    async def recv(self) -> str:
        if not self._incoming:
            raise _ConnectionClosed
        return self._incoming.pop(0)

    async def send(self, data: str):
        self.sent.append(json.loads(data))


def make_shell_factory(interaction_class=StubInteraction):
    def factory():
        shell = Shell(SHELL_DEF)
        shell.assign("main", interaction_class())
        shell.set_focus("main")
        return shell

    return factory


# --- connect ---


def test_connect_sends_render():
    async def _run():
        ws = MockWebSocket([
            {"type": "connect", "v": 1, "panels": [{"region": "main", "width": 40, "height": 10}]},
        ])
        await handle_connection(ws, make_shell_factory())
        assert len(ws.sent) == 1
        msg = ws.sent[0]
        assert msg["type"] == "render"
        assert msg["v"] == 1
        assert len(msg["updates"]) == 1
        assert msg["updates"][0]["region"] == "main"

    run(_run())


def test_connect_render_update_has_correct_shape():
    async def _run():
        ws = MockWebSocket([
            {"type": "connect", "v": 1, "panels": [{"region": "main", "width": 40, "height": 10}]},
        ])
        await handle_connection(ws, make_shell_factory())
        u = ws.sent[0]["updates"][0]
        assert "region" in u
        assert "html" in u
        assert "focused" in u

    run(_run())


# --- resize ---


def test_resize_sends_render():
    async def _run():
        ws = MockWebSocket([
            {"type": "resize", "v": 1, "panels": [{"region": "main", "width": 60, "height": 20}]},
        ])
        await handle_connection(ws, make_shell_factory())
        assert ws.sent[0]["type"] == "render"

    run(_run())


# --- key ---


def test_key_tab_sends_render_for_both_panels():
    TWO_REGION = """
|=====|
|{12R $left$ }|{12R $right$ }|
|=====|
"""

    def factory():
        shell = Shell(TWO_REGION)
        for name in shell.regions:
            shell.assign(name, StubInteraction())
        shell.set_focus("left")
        shell.mark_all_clean()
        return shell

    async def _run():
        ws = MockWebSocket([
            {"type": "key", "v": 1, "key": "Tab"},
        ])
        await handle_connection(ws, factory)
        assert len(ws.sent) == 1
        msg = ws.sent[0]
        assert msg["type"] == "render"
        regions = {u["region"] for u in msg["updates"]}
        assert regions == {"left", "right"}

    run(_run())


def test_key_sends_render_when_dirty():
    async def _run():
        ws = MockWebSocket([
            {"type": "connect", "v": 1, "panels": []},
            {"type": "key", "v": 1, "key": "a"},
        ])
        await handle_connection(ws, make_shell_factory())
        types = [m["type"] for m in ws.sent]
        assert "render" in types

    run(_run())


def test_key_arrow_is_mapped():
    received_keys = []

    class TrackingInteraction(Interaction):
        def render(self, context, focused=False):
            return [WriteCmd(row=0, col=0, text="x")]

        def handle_key(self, key):
            received_keys.append(key)
            return False, None

        def get_value(self):
            return None

        def set_value(self, value):
            pass

    def factory():
        shell = Shell(SHELL_DEF)
        shell.assign("main", TrackingInteraction())
        shell.set_focus("main")
        return shell

    async def _run():
        ws = MockWebSocket([
            {"type": "key", "v": 1, "key": "ArrowUp"},
        ])
        await handle_connection(ws, factory)
        assert received_keys == ["KEY_UP"]

    run(_run())


def test_key_exit_sends_exit_message():
    async def _run():
        ws = MockWebSocket([
            {"type": "key", "v": 1, "key": "Escape"},
        ])
        await handle_connection(ws, make_shell_factory())
        types = [m["type"] for m in ws.sent]
        assert "exit" in types

    run(_run())


def test_key_signal_return_sends_exit():
    async def _run():
        ws = MockWebSocket([
            {"type": "key", "v": 1, "key": "KEY_ENTER"},
        ])
        await handle_connection(ws, make_shell_factory(ExitInteraction))
        types = [m["type"] for m in ws.sent]
        assert "exit" in types

    run(_run())


# --- unknown message type ---


def test_unknown_message_type_sends_error():
    async def _run():
        ws = MockWebSocket([
            {"type": "bogus", "v": 1},
        ])
        await handle_connection(ws, make_shell_factory())
        assert ws.sent[0]["type"] == "error"
        assert "bogus" in ws.sent[0]["message"]

    run(_run())


# ---------------------------------------------------------------------------
# Sync handler tests (handle_connection_sync)
# ---------------------------------------------------------------------------


class SyncMockWebSocket:
    """Synchronous in-memory WebSocket stub."""

    def __init__(self, messages: list[dict]):
        self._incoming = [json.dumps(m) for m in messages]
        self.sent: list[dict] = []

    def send(self, data: str):
        self.sent.append(json.loads(data))

    def receive(self):
        if not self._incoming:
            return None
        return self._incoming.pop(0)


class SyncMockWebSocketRaisesOnClose:
    """Stub that raises ConnectionError when the queue is empty."""

    class ConnectionClosed(Exception):
        pass

    def __init__(self, messages: list[dict]):
        self._incoming = [json.dumps(m) for m in messages]
        self.sent: list[dict] = []

    def send(self, data: str):
        self.sent.append(json.loads(data))

    def receive(self):
        if not self._incoming:
            raise self.ConnectionClosed("closed")
        return self._incoming.pop(0)


def test_sync_connect_sends_render():
    ws = SyncMockWebSocket([
        {"type": "connect", "v": 1, "panels": [{"region": "main", "width": 40, "height": 10}]},
    ])
    handle_connection_sync(ws, make_shell_factory())
    assert ws.sent[0]["type"] == "render"
    assert ws.sent[0]["updates"][0]["region"] == "main"


def test_sync_resize_sends_render():
    ws = SyncMockWebSocket([
        {"type": "resize", "v": 1, "panels": [{"region": "main", "width": 60, "height": 20}]},
    ])
    handle_connection_sync(ws, make_shell_factory())
    assert ws.sent[0]["type"] == "render"


def test_sync_key_arrow_is_mapped():
    received_keys = []

    class TrackingInteraction(Interaction):
        def render(self, context, focused=False):
            return [WriteCmd(row=0, col=0, text="x")]

        def handle_key(self, key):
            received_keys.append(key)
            return False, None

        def get_value(self):
            return None

        def set_value(self, value):
            pass

    def factory():
        shell = Shell(SHELL_DEF)
        shell.assign("main", TrackingInteraction())
        shell.set_focus("main")
        return shell

    ws = SyncMockWebSocket([{"type": "key", "v": 1, "key": "ArrowUp"}])
    handle_connection_sync(ws, factory)
    assert received_keys == ["KEY_UP"]


def test_sync_escape_sends_exit():
    ws = SyncMockWebSocket([{"type": "key", "v": 1, "key": "Escape"}])
    handle_connection_sync(ws, make_shell_factory())
    types = [m["type"] for m in ws.sent]
    assert "exit" in types


def test_sync_signal_return_sends_exit():
    ws = SyncMockWebSocket([{"type": "key", "v": 1, "key": "KEY_ENTER"}])
    handle_connection_sync(ws, make_shell_factory(ExitInteraction))
    types = [m["type"] for m in ws.sent]
    assert "exit" in types


def test_sync_unknown_type_sends_error():
    ws = SyncMockWebSocket([{"type": "bogus", "v": 1}])
    handle_connection_sync(ws, make_shell_factory())
    assert ws.sent[0]["type"] == "error"


def test_sync_none_receive_closes_gracefully():
    ws = SyncMockWebSocket([])  # empty — receive() returns None immediately
    handle_connection_sync(ws, make_shell_factory())  # must not raise


def test_sync_exception_on_receive_closes_gracefully():
    ws = SyncMockWebSocketRaisesOnClose([])
    handle_connection_sync(ws, make_shell_factory())  # must not raise
