"""Tests for Session model."""

import pytest
from panelmark.shell import Shell
from panelmark.interactions.base import Interaction
from panelmark.draw import WriteCmd, RenderContext

from panelmark_web.session import Session


SINGLE_REGION = """
|=====|
|{12R $main$ }|
|=====|
"""

TWO_REGION = """
|=====|
|{12R $left$ }|{12R $right$ }|
|=====|
"""


class StubInteraction(Interaction):
    def __init__(self, text="stub"):
        self._text = text
        self._keys_received = []

    def render(self, context, focused=False):
        return [WriteCmd(row=0, col=0, text=self._text)]

    def handle_key(self, key):
        self._keys_received.append(key)
        return False, self._text

    def get_value(self):
        return self._text

    def set_value(self, value):
        self._text = str(value)


class ExitInteraction(Interaction):
    """Interaction that signals exit on any key."""

    def render(self, context, focused=False):
        return [WriteCmd(row=0, col=0, text="exit")]

    def handle_key(self, key):
        return False, None

    def get_value(self):
        return None

    def set_value(self, value):
        pass

    def signal_return(self):
        return True, "done"


def make_session(definition=SINGLE_REGION, interaction_class=StubInteraction):
    shell = Shell(definition)
    session = Session(shell)
    for name in shell.regions:
        shell.assign(name, interaction_class())
    return session


# --- set_panel_sizes ---


def test_set_panel_sizes_stores_dimensions():
    session = make_session()
    session.set_panel_sizes([{"region": "main", "width": 40, "height": 10}])
    assert session.panel_sizes["main"] == (40, 10)


def test_set_panel_sizes_multiple():
    shell = Shell(TWO_REGION)
    for name in shell.regions:
        shell.assign(name, StubInteraction())
    session = Session(shell)
    session.set_panel_sizes([
        {"region": "left", "width": 30, "height": 8},
        {"region": "right", "width": 30, "height": 8},
    ])
    assert session.panel_sizes["left"] == (30, 8)
    assert session.panel_sizes["right"] == (30, 8)


def test_set_panel_sizes_skips_missing_region_key():
    session = make_session()
    session.set_panel_sizes([{"width": 40, "height": 10}])
    assert session.panel_sizes == {}


# --- render_all ---


def test_render_all_returns_update_dicts():
    session = make_session()
    updates = session.render_all()
    assert len(updates) == 1
    u = updates[0]
    assert u["region"] == "main"
    assert "stub" in u["html"]
    assert isinstance(u["focused"], bool)


def test_render_all_marks_clean():
    session = make_session()
    session.render_all()
    assert session.shell.dirty_regions == set()


def test_render_all_uses_stored_sizes():
    session = make_session()
    session.set_panel_sizes([{"region": "main", "width": 10, "height": 3}])
    updates = session.render_all()
    # Just verify it succeeds with the stored size
    assert updates[0]["region"] == "main"


# --- process_key ---


def test_process_key_returns_continue():
    session = make_session()
    result, updates, _focus = session.process_key("a")
    assert result == "continue"


def test_process_key_returns_update_dicts():
    session = make_session()
    result, updates, _focus = session.process_key("a")
    # dirty_regions may or may not be populated depending on shell internals
    assert isinstance(updates, list)
    for u in updates:
        assert "region" in u
        assert "html" in u
        assert "focused" in u


def test_process_key_marks_clean():
    session = make_session()
    session.process_key("a")
    assert session.shell.dirty_regions == set()


def test_process_key_exit_result():
    shell = Shell(SINGLE_REGION)
    shell.assign("main", ExitInteraction())
    shell.set_focus("main")
    session = Session(shell)
    result, updates, _focus = session.process_key("KEY_ENTER")
    assert result == "exit"


# --- _render_region ---


def test_render_region_returns_correct_shape():
    session = make_session()
    u = session._render_region("main")
    assert u["region"] == "main"
    assert isinstance(u["html"], str)
    assert isinstance(u["focused"], bool)


def test_render_region_unassigned_returns_empty_html():
    shell = Shell(SINGLE_REGION)
    session = Session(shell)
    u = session._render_region("main")
    assert u["html"] == ""
    assert u["focused"] is False


def test_process_key_focus_region_none_when_dirty():
    shell = Shell(TWO_REGION)
    for name in shell.regions:
        shell.assign(name, StubInteraction())
    shell.set_focus("left")
    shell.mark_all_clean()
    session = Session(shell)
    # Tab marks both regions dirty, so focus_region should be None
    _result, updates, focus_region = session.process_key("KEY_TAB")
    assert focus_region is None
    assert len(updates) == 2


def test_render_region_focused_flag():
    shell = Shell(SINGLE_REGION)
    stub = StubInteraction()
    shell.assign("main", stub)
    shell.set_focus("main")
    session = Session(shell)
    u = session._render_region("main")
    assert u["focused"] is True
