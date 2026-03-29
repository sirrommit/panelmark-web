"""Integration tests: real Shell driven through handle_connection."""

import asyncio
import json

from panelmark import Shell
from panelmark.interactions.base import Interaction
from panelmark.draw import WriteCmd, FillCmd, RenderContext

from panelmark_web.server import handle_connection


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Shell definitions and interactions
# ---------------------------------------------------------------------------

SINGLE_PANEL = """
|=====|
|{20R $main$ }|
|=====|
"""

TWO_PANEL = """
|=====|
|{20R $editor$ }|
|=====|
|{20R $status$ }|
|=====|
"""


class EchoInteraction(Interaction):
    """Types characters and echoes them."""

    def __init__(self):
        self._text = ""

    def render(self, context: RenderContext, focused: bool = False) -> list:
        line = self._text[: context.width].ljust(context.width)
        style = {"reverse": True} if focused else None
        return [WriteCmd(row=0, col=0, text=line, style=style)]

    def handle_key(self, key: str) -> tuple:
        if key == "KEY_BACKSPACE" and self._text:
            self._text = self._text[:-1]
            return True, self._text
        if len(key) == 1 and key.isprintable():
            self._text += key
            return True, self._text
        return False, self._text

    def get_value(self) -> str:
        return self._text

    def set_value(self, value) -> None:
        self._text = str(value)


class DisplayInteraction(Interaction):
    """Display-only; not focusable."""

    @property
    def is_focusable(self) -> bool:
        return False

    def render(self, context: RenderContext, focused: bool = False) -> list:
        msg = "ready"
        return [WriteCmd(row=0, col=0, text=msg.ljust(context.width))]

    def handle_key(self, key: str) -> tuple:
        return False, None

    def get_value(self):
        return None

    def set_value(self, value) -> None:
        pass


class ExitOnEnterInteraction(Interaction):
    def __init__(self):
        self._done = False

    def render(self, context: RenderContext, focused: bool = False) -> list:
        return [WriteCmd(row=0, col=0, text="press enter")]

    def handle_key(self, key: str) -> tuple:
        if key == "KEY_ENTER":
            self._done = True
        return False, None

    def get_value(self):
        return None

    def set_value(self, value) -> None:
        pass

    def signal_return(self) -> tuple:
        return self._done, None


# ---------------------------------------------------------------------------
# Mock WebSocket
# ---------------------------------------------------------------------------


class MockWebSocket:
    def __init__(self, messages: list[dict]):
        self._incoming = [json.dumps(m) for m in messages]
        self.sent: list[dict] = []

    async def send(self, data: str):
        self.sent.append(json.loads(data))

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._incoming:
            raise StopAsyncIteration
        return self._incoming.pop(0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def first_render(sent: list[dict]) -> dict:
    return next(m for m in sent if m["type"] == "render")


def update_for(sent: list[dict], region: str) -> dict | None:
    for msg in sent:
        if msg.get("type") == "render":
            for u in msg["updates"]:
                if u["region"] == region:
                    return u
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_connect_renders_all_panels():
    def factory():
        shell = Shell(SINGLE_PANEL)
        shell.assign("main", EchoInteraction())
        shell.set_focus("main")
        return shell

    async def _run():
        ws = MockWebSocket([
            {"type": "connect", "v": 1, "panels": [
                {"region": "main", "width": 20, "height": 5}
            ]},
        ])
        await handle_connection(ws, factory)
        msg = first_render(ws.sent)
        assert len(msg["updates"]) == 1
        assert msg["updates"][0]["region"] == "main"

    run(_run())


def test_typed_text_appears_in_render():
    def factory():
        shell = Shell(SINGLE_PANEL)
        shell.assign("main", EchoInteraction())
        shell.set_focus("main")
        return shell

    async def _run():
        ws = MockWebSocket([
            {"type": "connect", "v": 1, "panels": [
                {"region": "main", "width": 20, "height": 5}
            ]},
            {"type": "key", "v": 1, "key": "h"},
            {"type": "key", "v": 1, "key": "i"},
        ])
        await handle_connection(ws, factory)
        # Find last render for 'main'
        u = update_for(ws.sent, "main")
        assert u is not None
        assert "h" in u["html"] or "hi" in u["html"]

    run(_run())


def test_focused_flag_true_for_focused_panel():
    def factory():
        shell = Shell(SINGLE_PANEL)
        shell.assign("main", EchoInteraction())
        shell.set_focus("main")
        return shell

    async def _run():
        ws = MockWebSocket([
            {"type": "connect", "v": 1, "panels": [
                {"region": "main", "width": 20, "height": 5}
            ]},
        ])
        await handle_connection(ws, factory)
        u = update_for(ws.sent, "main")
        assert u["focused"] is True

    run(_run())


def test_tab_between_two_focusable_panels():
    TWO_FOCUSABLE = """
|=====|
|{20R $left$ }|{20R $right$ }|
|=====|
"""

    def factory():
        shell = Shell(TWO_FOCUSABLE)
        shell.assign("left", EchoInteraction())
        shell.assign("right", EchoInteraction())
        shell.set_focus("left")
        shell.mark_all_clean()
        return shell

    async def _run():
        ws = MockWebSocket([
            {"type": "key", "v": 1, "key": "Tab"},
        ])
        await handle_connection(ws, factory)
        # Both regions are marked dirty; a render message is sent for both
        assert len(ws.sent) == 1
        msg = ws.sent[0]
        assert msg["type"] == "render"
        regions = {u["region"] for u in msg["updates"]}
        assert regions == {"left", "right"}
        # right is now focused
        right_update = next(u for u in msg["updates"] if u["region"] == "right")
        assert right_update["focused"] is True

    run(_run())


def test_resize_rerenders_panels():
    def factory():
        shell = Shell(SINGLE_PANEL)
        shell.assign("main", EchoInteraction())
        shell.set_focus("main")
        return shell

    async def _run():
        ws = MockWebSocket([
            {"type": "connect", "v": 1, "panels": [
                {"region": "main", "width": 20, "height": 5}
            ]},
            {"type": "resize", "v": 1, "panels": [
                {"region": "main", "width": 40, "height": 10}
            ]},
        ])
        await handle_connection(ws, factory)
        renders = [m for m in ws.sent if m["type"] == "render"]
        assert len(renders) == 2

    run(_run())


def test_escape_sends_exit():
    def factory():
        shell = Shell(SINGLE_PANEL)
        shell.assign("main", EchoInteraction())
        shell.set_focus("main")
        return shell

    async def _run():
        ws = MockWebSocket([
            {"type": "key", "v": 1, "key": "Escape"},
        ])
        await handle_connection(ws, factory)
        types = [m["type"] for m in ws.sent]
        assert "exit" in types

    run(_run())


def test_signal_return_sends_exit():
    def factory():
        shell = Shell(SINGLE_PANEL)
        shell.assign("main", ExitOnEnterInteraction())
        shell.set_focus("main")
        return shell

    async def _run():
        ws = MockWebSocket([
            {"type": "key", "v": 1, "key": "KEY_ENTER"},
        ])
        await handle_connection(ws, factory)
        types = [m["type"] for m in ws.sent]
        assert "exit" in types

    run(_run())


def test_html_contains_pre_elements():
    def factory():
        shell = Shell(SINGLE_PANEL)
        shell.assign("main", EchoInteraction())
        shell.set_focus("main")
        return shell

    async def _run():
        ws = MockWebSocket([
            {"type": "connect", "v": 1, "panels": [
                {"region": "main", "width": 20, "height": 5}
            ]},
        ])
        await handle_connection(ws, factory)
        u = update_for(ws.sent, "main")
        assert "<pre" in u["html"]

    run(_run())


def test_two_panel_connect_renders_both():
    def factory():
        shell = Shell(TWO_PANEL)
        shell.assign("editor", EchoInteraction())
        shell.assign("status", DisplayInteraction())
        shell.set_focus("editor")
        return shell

    async def _run():
        ws = MockWebSocket([
            {"type": "connect", "v": 1, "panels": [
                {"region": "editor", "width": 20, "height": 5},
                {"region": "status", "width": 20, "height": 2},
            ]},
        ])
        await handle_connection(ws, factory)
        msg = first_render(ws.sent)
        regions = {u["region"] for u in msg["updates"]}
        assert "editor" in regions
        assert "status" in regions

    run(_run())
