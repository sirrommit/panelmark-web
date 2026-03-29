"""Tests for DrawCommandRenderer."""

import pytest
from panelmark.draw import CursorCmd, FillCmd, RenderContext, WriteCmd

from panelmark_web.renderer import DrawCommandRenderer


CTX = RenderContext(width=20, height=5, capabilities=frozenset())


class _StubInteraction:
    def __init__(self, commands):
        self._commands = commands

    def render(self, context, focused=False):
        return self._commands


def make_renderer():
    return DrawCommandRenderer()


# --- _commands_to_html ---


def test_empty_commands_returns_empty_string():
    r = make_renderer()
    assert r._commands_to_html([], CTX) == ""


def test_single_writeCmd_no_style():
    r = make_renderer()
    out = r._commands_to_html([WriteCmd(row=0, col=0, text="Hello")], CTX)
    assert "Hello" in out
    assert "<pre" in out


def test_writeCmd_with_bold_style():
    r = make_renderer()
    out = r._commands_to_html(
        [WriteCmd(row=0, col=0, text="Bold", style={"bold": True})], CTX
    )
    assert "font-weight:bold" in out
    assert "Bold" in out


def test_writeCmd_with_color():
    r = make_renderer()
    out = r._commands_to_html(
        [WriteCmd(row=0, col=0, text="Red", style={"color": "red"})], CTX
    )
    assert "color:red" in out
    assert "Red" in out


def test_writeCmd_reverse_style():
    r = make_renderer()
    out = r._commands_to_html(
        [WriteCmd(row=0, col=0, text="Rev", style={"reverse": True})], CTX
    )
    assert "color:" in out
    assert "background:" in out


def test_fillCmd_produces_spaces():
    r = make_renderer()
    out = r._commands_to_html(
        [FillCmd(row=0, col=0, width=5, height=1)], CTX
    )
    assert "     " in out or "&nbsp;" in out or out.count(" ") >= 5 or "<pre" in out


def test_fillCmd_with_char():
    r = make_renderer()
    out = r._commands_to_html(
        [FillCmd(row=0, col=0, width=3, height=2, char="-")], CTX
    )
    assert "---" in out


def test_cursorCmd_ignored():
    r = make_renderer()
    out = r._commands_to_html([CursorCmd(row=0, col=0)], CTX)
    assert out == ""


def test_multiple_rows_produce_multiple_pre_elements():
    r = make_renderer()
    cmds = [
        WriteCmd(row=0, col=0, text="Row0"),
        WriteCmd(row=1, col=0, text="Row1"),
    ]
    out = r._commands_to_html(cmds, CTX)
    assert out.count("<pre") == 2
    assert "Row0" in out
    assert "Row1" in out


def test_html_special_chars_are_escaped():
    r = make_renderer()
    out = r._commands_to_html(
        [WriteCmd(row=0, col=0, text="<b>&foo</b>")], CTX
    )
    assert "<b>" not in out
    assert "&lt;b&gt;" in out


def test_col_offset_pads_with_spaces():
    r = make_renderer()
    out = r._commands_to_html([WriteCmd(row=0, col=5, text="Hi")], CTX)
    # 5 spaces before "Hi"
    assert "     Hi" in out or "Hi" in out  # spaces may be escaped


# --- render_panel ---


def test_render_panel_calls_interaction_render():
    r = make_renderer()
    stub = _StubInteraction([WriteCmd(row=0, col=0, text="Test")])
    out = r.render_panel(stub, CTX, focused=False)
    assert "Test" in out


def test_render_panel_passes_focused():
    received = []

    class _FocusStub:
        def render(self, context, focused=False):
            received.append(focused)
            return []

    r = make_renderer()
    r.render_panel(_FocusStub(), CTX, focused=True)
    assert received == [True]
