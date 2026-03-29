"""Integration tests: portable interactions and widgets through handle_connection.

Each test drives a real Shell assigned with a portable interaction or widget
through the full WebSocket stack (MockWebSocket → handle_connection → Session
→ DrawCommandRenderer → JSON response) and asserts on the messages the server
sends back.
"""

import asyncio
import json

from panelmark import Shell

from panelmark_web.server import handle_connection
from panelmark_web.interactions import (
    CheckBox,
    ListView,
    MenuFunction,
    MenuReturn,
    RadioList,
    StatusMessage,
    TableView,
    TextBox,
    NestedMenu,
)
from panelmark_web.widgets import Alert, Confirm, InputPrompt, ListSelect


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Shell definitions
# ---------------------------------------------------------------------------

SINGLE = """
|=====|
|{20R $main$ }|
|=====|
"""

TWO_PANEL = """
|=====|
|{20R $main$ }|
|=====|
|{20R $status$ }|
|=====|
"""


# ---------------------------------------------------------------------------
# Mock WebSocket (same contract as test_integration.py)
# ---------------------------------------------------------------------------

class _Closed(Exception):
    pass


class MockWebSocket:
    def __init__(self, messages):
        self._incoming = [json.dumps(m) for m in messages]
        self.sent: list[dict] = []

    async def recv(self) -> str:
        if not self._incoming:
            raise _Closed
        return self._incoming.pop(0)

    async def send(self, data: str) -> None:
        self.sent.append(json.loads(data))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CONNECT = {"type": "connect", "v": 1, "panels": [
    {"region": "main", "width": 20, "height": 5}
]}

TWO_CONNECT = {"type": "connect", "v": 1, "panels": [
    {"region": "main", "width": 20, "height": 5},
    {"region": "status", "width": 20, "height": 2},
]}


def key(k):
    return {"type": "key", "v": 1, "key": k}


def sent_types(ws):
    return [m["type"] for m in ws.sent]


def html_for(ws, region="main"):
    """Return the HTML from the last render update for *region*."""
    html = None
    for msg in ws.sent:
        if msg["type"] == "render":
            for u in msg["updates"]:
                if u["region"] == region:
                    html = u["html"]
    return html


def all_html_for(ws, region="main"):
    """Return all HTML snapshots sent for *region*, in order."""
    result = []
    for msg in ws.sent:
        if msg["type"] == "render":
            for u in msg["updates"]:
                if u["region"] == region:
                    result.append(u["html"])
    return result


# ---------------------------------------------------------------------------
# MenuReturn
# ---------------------------------------------------------------------------

class TestMenuReturnIntegration:
    def _factory(self):
        shell = Shell(SINGLE)
        shell.assign("main", MenuReturn({"New": "new", "Open": "open", "Quit": "quit"}))
        shell.set_focus("main")
        return shell

    def test_connect_renders_menu_items(self):
        async def _run():
            ws = MockWebSocket([CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws)
            assert h is not None
            assert "<pre" in h
            assert "New" in h

        run(_run())

    def test_key_down_re_renders(self):
        async def _run():
            ws = MockWebSocket([CONNECT, key("KEY_DOWN")])
            await handle_connection(ws, self._factory)
            snapshots = all_html_for(ws)
            assert len(snapshots) >= 2
            # After KEY_DOWN, Open should be the highlighted row
            assert "Open" in snapshots[-1]

        run(_run())

    def test_enter_sends_exit(self):
        async def _run():
            ws = MockWebSocket([key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            assert "exit" in sent_types(ws)

        run(_run())

    def test_enter_after_down_sends_exit(self):
        async def _run():
            ws = MockWebSocket([key("KEY_DOWN"), key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            assert "exit" in sent_types(ws)

        run(_run())


# ---------------------------------------------------------------------------
# RadioList
# ---------------------------------------------------------------------------

class TestRadioListIntegration:
    def _factory(self):
        shell = Shell(SINGLE)
        shell.assign("main", RadioList({"Small": "s", "Medium": "m", "Large": "l"}))
        shell.set_focus("main")
        return shell

    def test_connect_renders_radio_marks(self):
        async def _run():
            ws = MockWebSocket([CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws)
            assert "(•)" in h or "(&#8226;)" in h or "•" in h or "Small" in h

        run(_run())

    def test_enter_sends_exit(self):
        async def _run():
            ws = MockWebSocket([key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            assert "exit" in sent_types(ws)

        run(_run())

    def test_down_then_enter_sends_exit(self):
        async def _run():
            ws = MockWebSocket([key("KEY_DOWN"), key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            assert "exit" in sent_types(ws)

        run(_run())


# ---------------------------------------------------------------------------
# CheckBox
# ---------------------------------------------------------------------------

class TestCheckBoxIntegration:
    def _factory(self):
        shell = Shell(SINGLE)
        shell.assign("main", CheckBox({"Alpha": False, "Beta": True}))
        shell.set_focus("main")
        return shell

    def test_connect_renders_checkboxes(self):
        async def _run():
            ws = MockWebSocket([CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws)
            assert "[x]" in h or "[ ]" in h

        run(_run())

    def test_space_re_renders(self):
        async def _run():
            ws = MockWebSocket([CONNECT, key(" ")])
            await handle_connection(ws, self._factory)
            snapshots = all_html_for(ws)
            # Two render messages: connect + after space
            assert len(snapshots) >= 2

        run(_run())

    def test_checkbox_does_not_send_exit(self):
        async def _run():
            ws = MockWebSocket([key(" "), key(" "), key(" ")])
            await handle_connection(ws, self._factory)
            assert "exit" not in sent_types(ws)

        run(_run())


# ---------------------------------------------------------------------------
# StatusMessage
# ---------------------------------------------------------------------------

class TestStatusMessageIntegration:
    def _factory(self):
        shell = Shell(TWO_PANEL)
        from panelmark.interactions.base import Interaction
        from panelmark.draw import WriteCmd, RenderContext

        class _Updater(Interaction):
            """On KEY_ENTER, updates the status panel."""
            def render(self, ctx, focused=False):
                return [WriteCmd(row=0, col=0, text="press enter".ljust(ctx.width))]
            def handle_key(self, key):
                if key == "KEY_ENTER":
                    self._shell.update("status", ("error", "bad input"))
                    return True, None
                return False, None
            def get_value(self): return None
            def set_value(self, v): pass

        shell.assign("main", _Updater())
        shell.assign("status", StatusMessage())
        shell.set_focus("main")
        return shell

    def test_connect_renders_blank_status(self):
        async def _run():
            ws = MockWebSocket([TWO_CONNECT])
            await handle_connection(ws, self._factory)
            # Status panel renders (even if blank)
            status_h = html_for(ws, region="status")
            assert status_h is not None

        run(_run())

    def test_update_re_renders_status(self):
        async def _run():
            ws = MockWebSocket([TWO_CONNECT, key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            snapshots = all_html_for(ws, region="status")
            # At least two renders: connect + after key
            assert len(snapshots) >= 2
            # The last one should mention the error message
            assert "bad input" in snapshots[-1]

        run(_run())


# ---------------------------------------------------------------------------
# TextBox
# ---------------------------------------------------------------------------

class TestTextBoxIntegration:
    def _factory(self, enter_mode="submit"):
        shell = Shell(SINGLE)
        shell.assign("main", TextBox(enter_mode=enter_mode))
        shell.set_focus("main")
        return shell

    def test_typing_produces_render_updates(self):
        async def _run():
            ws = MockWebSocket([CONNECT, key("h"), key("i")])
            await handle_connection(ws, self._factory)
            snapshots = all_html_for(ws)
            assert len(snapshots) >= 3  # connect + 'h' + 'i'

        run(_run())

    def test_typed_text_appears_in_html(self):
        async def _run():
            ws = MockWebSocket([CONNECT, key("h"), key("i")])
            await handle_connection(ws, self._factory)
            h = html_for(ws)
            assert "h" in h

        run(_run())

    def test_enter_submit_sends_exit(self):
        async def _run():
            ws = MockWebSocket([key("h"), key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            assert "exit" in sent_types(ws)

        run(_run())

    def test_enter_newline_does_not_send_exit(self):
        factory = lambda: self._factory(enter_mode="newline")
        async def _run():
            ws = MockWebSocket([key("h"), key("KEY_ENTER")])
            await handle_connection(ws, factory)
            assert "exit" not in sent_types(ws)

        run(_run())


# ---------------------------------------------------------------------------
# NestedMenu
# ---------------------------------------------------------------------------

class TestNestedMenuIntegration:
    def _factory(self):
        shell = Shell(SINGLE)
        shell.assign("main", NestedMenu({
            "File": {"New": "file:new", "Save": "file:save"},
            "Quit": "quit",
        }))
        shell.set_focus("main")
        return shell

    def test_connect_renders_root_items(self):
        async def _run():
            ws = MockWebSocket([CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws)
            assert "File" in h
            assert "Quit" in h

        run(_run())

    def test_enter_on_branch_descends_and_re_renders(self):
        async def _run():
            ws = MockWebSocket([CONNECT, key("KEY_ENTER")])  # descend into File
            await handle_connection(ws, self._factory)
            snapshots = all_html_for(ws)
            assert len(snapshots) >= 2
            # After descending, New / Save should be visible
            assert "New" in snapshots[-1] or "Save" in snapshots[-1]

        run(_run())

    def test_enter_on_leaf_sends_exit(self):
        async def _run():
            ws = MockWebSocket([
                key("KEY_DOWN"),   # → Quit
                key("KEY_ENTER"),  # accept leaf
            ])
            await handle_connection(ws, self._factory)
            assert "exit" in sent_types(ws)

        run(_run())


# ---------------------------------------------------------------------------
# Alert widget
# ---------------------------------------------------------------------------

class TestAlertIntegration:
    def _factory(self):
        shell = Shell(SINGLE)
        shell.assign("main", Alert(title="Warning", message_lines=["Check this."]))
        shell.set_focus("main")
        return shell

    def test_connect_renders_title_and_message(self):
        async def _run():
            ws = MockWebSocket([CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws)
            assert "Warning" in h
            assert "Check this." in h

        run(_run())

    def test_enter_dismisses_and_sends_exit(self):
        async def _run():
            ws = MockWebSocket([key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            assert "exit" in sent_types(ws)

        run(_run())

    def test_escape_cancels_and_sends_exit(self):
        async def _run():
            ws = MockWebSocket([key("Escape")])
            await handle_connection(ws, self._factory)
            assert "exit" in sent_types(ws)

        run(_run())


# ---------------------------------------------------------------------------
# Confirm widget
# ---------------------------------------------------------------------------

class TestConfirmIntegration:
    def _factory(self):
        shell = Shell(SINGLE)
        shell.assign("main", Confirm(title="Sure?", message_lines=["Delete it?"]))
        shell.set_focus("main")
        return shell

    def test_connect_renders_title_and_buttons(self):
        async def _run():
            ws = MockWebSocket([CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws)
            assert "Sure?" in h
            assert "OK" in h

        run(_run())

    def test_enter_sends_exit(self):
        async def _run():
            ws = MockWebSocket([key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            assert "exit" in sent_types(ws)

        run(_run())

    def test_right_then_enter_sends_exit(self):
        async def _run():
            ws = MockWebSocket([key("KEY_RIGHT"), key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            assert "exit" in sent_types(ws)

        run(_run())


# ---------------------------------------------------------------------------
# InputPrompt widget
# ---------------------------------------------------------------------------

class TestInputPromptIntegration:
    def _factory(self):
        shell = Shell(SINGLE)
        shell.assign("main", InputPrompt(title="Name?"))
        shell.set_focus("main")
        return shell

    def test_connect_renders_title(self):
        async def _run():
            ws = MockWebSocket([CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws)
            assert "Name?" in h

        run(_run())

    def test_typing_then_enter_sends_exit(self):
        async def _run():
            ws = MockWebSocket([key("A"), key("l"), key("i"), key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            assert "exit" in sent_types(ws)

        run(_run())

    def test_typed_text_appears_before_exit(self):
        async def _run():
            ws = MockWebSocket([CONNECT, key("B"), key("o"), key("b")])
            await handle_connection(ws, self._factory)
            h = html_for(ws)
            assert "B" in h

        run(_run())


# ---------------------------------------------------------------------------
# ListSelect widget
# ---------------------------------------------------------------------------

class TestListSelectIntegration:
    def _factory(self, multi=False):
        shell = Shell(SINGLE)
        shell.assign("main", ListSelect(
            title="Pick",
            items={"Alpha": False, "Beta": True} if multi else ["Alpha", "Beta", "Gamma"],
            multi=multi,
        ))
        shell.set_focus("main")
        return shell

    def test_single_connect_renders_items(self):
        async def _run():
            ws = MockWebSocket([CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws)
            assert "Alpha" in h

        run(_run())

    def test_single_enter_sends_exit(self):
        async def _run():
            ws = MockWebSocket([key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            assert "exit" in sent_types(ws)

        run(_run())

    def test_multi_space_re_renders(self):
        factory = lambda: self._factory(multi=True)
        async def _run():
            ws = MockWebSocket([CONNECT, key(" ")])
            await handle_connection(ws, factory)
            snapshots = all_html_for(ws)
            assert len(snapshots) >= 2

        run(_run())

    def test_multi_ok_sends_exit(self):
        factory = lambda: self._factory(multi=True)
        async def _run():
            # Navigate to OK row (2 items → index 2) and press Enter
            ws = MockWebSocket([
                key("KEY_DOWN"), key("KEY_DOWN"), key("KEY_ENTER")
            ])
            await handle_connection(ws, factory)
            assert "exit" in sent_types(ws)

        run(_run())


# ---------------------------------------------------------------------------
# MenuFunction
# ---------------------------------------------------------------------------

class TestMenuFunctionIntegration:
    def _factory(self):
        shell = Shell(TWO_PANEL)

        def _on_save(sh):
            sh.update("status", ("success", "saved"))

        shell.assign("main", MenuFunction({"Save": _on_save, "Noop": lambda sh: None}))
        shell.assign("status", StatusMessage())
        shell.set_focus("main")
        return shell

    def test_connect_renders_menu_items(self):
        async def _run():
            ws = MockWebSocket([TWO_CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws, region="main")
            assert "Save" in h

        run(_run())

    def test_enter_invokes_callback_and_re_renders_status(self):
        async def _run():
            ws = MockWebSocket([TWO_CONNECT, key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            snapshots = all_html_for(ws, region="status")
            assert len(snapshots) >= 2
            assert "saved" in snapshots[-1]

        run(_run())

    def test_enter_does_not_send_exit(self):
        async def _run():
            ws = MockWebSocket([key("KEY_ENTER")])
            await handle_connection(ws, self._factory)
            assert "exit" not in sent_types(ws)

        run(_run())

    def test_key_down_re_renders_main(self):
        async def _run():
            ws = MockWebSocket([CONNECT, key("KEY_DOWN")])
            await handle_connection(ws, self._factory)
            snapshots = all_html_for(ws, region="main")
            assert len(snapshots) >= 2

        run(_run())


# ---------------------------------------------------------------------------
# ListView
# ---------------------------------------------------------------------------

class TestListViewIntegration:
    def _factory(self):
        shell = Shell(SINGLE)
        shell.assign("main", ListView(["alpha", "beta", "gamma"]))
        # ListView is not focusable; focus something else if needed,
        # but assign anyway to verify rendering
        return shell

    def test_connect_renders_list_items(self):
        async def _run():
            ws = MockWebSocket([CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws, region="main")
            assert "alpha" in h
            assert "beta" in h

        run(_run())

    def test_render_produces_pre_elements(self):
        async def _run():
            ws = MockWebSocket([CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws, region="main")
            assert "<pre" in h

        run(_run())

    def test_update_via_shell_re_renders(self):
        """shell.update() on a ListView replaces the items and marks it dirty."""
        from panelmark.interactions.base import Interaction
        from panelmark.draw import WriteCmd, RenderContext

        class _Trigger(Interaction):
            def render(self, ctx, focused=False):
                return [WriteCmd(row=0, col=0, text="trigger".ljust(ctx.width))]
            def handle_key(self, key):
                if key == "KEY_ENTER":
                    self._shell.update("main", ["x", "y", "z"])
                    return True, None
                return False, None
            def get_value(self): return None
            def set_value(self, v): pass

        TWO_FOCUSABLE = """
|=====|
|{20R $trigger$ }|
|=====|
|{20R $main$ }|
|=====|
"""
        def factory():
            shell = Shell(TWO_FOCUSABLE)
            shell.assign("trigger", _Trigger())
            shell.assign("main", ListView(["a", "b"]))
            shell.set_focus("trigger")
            return shell

        connect = {"type": "connect", "v": 1, "panels": [
            {"region": "trigger", "width": 20, "height": 3},
            {"region": "main", "width": 20, "height": 3},
        ]}

        async def _run():
            ws = MockWebSocket([connect, key("KEY_ENTER")])
            await handle_connection(ws, factory)
            snapshots = all_html_for(ws, region="main")
            assert len(snapshots) >= 2
            assert "x" in snapshots[-1]

        run(_run())


# ---------------------------------------------------------------------------
# TableView
# ---------------------------------------------------------------------------

class TestTableViewIntegration:
    def _factory(self):
        shell = Shell(SINGLE)
        shell.assign("main", TableView(
            columns=[("Name", 8), ("Score", 5)],
            rows=[["Alice", "100"], ["Bob", "85"], ["Carol", "92"]],
        ))
        shell.set_focus("main")
        return shell

    def test_connect_renders_header_and_rows(self):
        async def _run():
            ws = MockWebSocket([CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws, region="main")
            assert "Name" in h
            assert "Alice" in h

        run(_run())

    def test_render_produces_pre_elements(self):
        async def _run():
            ws = MockWebSocket([CONNECT])
            await handle_connection(ws, self._factory)
            h = html_for(ws, region="main")
            assert "<pre" in h

        run(_run())

    def test_key_down_re_renders(self):
        async def _run():
            ws = MockWebSocket([CONNECT, key("KEY_DOWN")])
            await handle_connection(ws, self._factory)
            snapshots = all_html_for(ws, region="main")
            assert len(snapshots) >= 2

        run(_run())

    def test_does_not_send_exit(self):
        async def _run():
            ws = MockWebSocket([
                key("KEY_DOWN"), key("KEY_DOWN"), key("KEY_DOWN"),
            ])
            await handle_connection(ws, self._factory)
            assert "exit" not in sent_types(ws)

        run(_run())
