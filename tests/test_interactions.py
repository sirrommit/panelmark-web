"""Tests for panelmark_web.interactions — portable interaction library."""

import dataclasses

import pytest

from panelmark.draw import RenderContext, WriteCmd, FillCmd

from panelmark_web.interactions import (
    CheckBox,
    DataclassFormInteraction,
    FormInput,
    Leaf,
    MenuReturn,
    NestedMenu,
    RadioList,
    StatusMessage,
    TextBox,
)

CTX = RenderContext(width=20, height=5)


# ---------------------------------------------------------------------------
# StatusMessage
# ---------------------------------------------------------------------------

class TestStatusMessage:
    def test_initial_value_is_none(self):
        s = StatusMessage()
        assert s.get_value() is None

    def test_not_focusable(self):
        assert StatusMessage().is_focusable is False

    def test_set_none_clears(self):
        s = StatusMessage()
        s.set_value(("error", "oops"))
        s.set_value(None)
        assert s.get_value() is None

    def test_set_empty_string_clears(self):
        s = StatusMessage()
        s.set_value("")
        assert s.get_value() is None

    def test_set_plain_string_becomes_info(self):
        s = StatusMessage()
        s.set_value("hello")
        assert s.get_value() == ("info", "hello")

    def test_set_error_tuple(self):
        s = StatusMessage()
        s.set_value(("error", "bad"))
        assert s.get_value() == ("error", "bad")

    def test_set_success_tuple(self):
        s = StatusMessage()
        s.set_value(("success", "ok"))
        assert s.get_value() == ("success", "ok")

    def test_signal_return_always_false(self):
        s = StatusMessage()
        s.set_value("msg")
        assert s.signal_return() == (False, None)

    def test_handle_key_ignored(self):
        s = StatusMessage()
        changed, _ = s.handle_key("a")
        assert changed is False

    def test_render_blank_returns_fill(self):
        s = StatusMessage()
        cmds = s.render(CTX)
        assert any(isinstance(c, FillCmd) for c in cmds)

    def test_render_message_includes_write(self):
        s = StatusMessage()
        s.set_value(("error", "boom"))
        cmds = s.render(CTX)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert any("boom" in t for t in texts)


# ---------------------------------------------------------------------------
# MenuReturn
# ---------------------------------------------------------------------------

class TestMenuReturn:
    def _menu(self):
        return MenuReturn({"New": "new", "Open": "open", "Quit": "quit"})

    def test_initial_value_is_first_label(self):
        m = self._menu()
        assert m.get_value() == "New"

    def test_key_down_moves_cursor(self):
        m = self._menu()
        changed, val = m.handle_key("KEY_DOWN")
        assert changed is True
        assert m.get_value() == "Open"

    def test_key_up_does_not_go_before_first(self):
        m = self._menu()
        changed, _ = m.handle_key("KEY_UP")
        assert changed is False
        assert m.get_value() == "New"

    def test_key_down_does_not_go_past_last(self):
        m = self._menu()
        m.handle_key("KEY_DOWN")
        m.handle_key("KEY_DOWN")
        changed, _ = m.handle_key("KEY_DOWN")
        assert changed is False
        assert m.get_value() == "Quit"

    def test_signal_return_false_before_enter(self):
        m = self._menu()
        assert m.signal_return() == (False, None)

    def test_enter_sets_signal_return(self):
        m = self._menu()
        m.handle_key("KEY_DOWN")  # → Open
        m.handle_key("KEY_ENTER")
        ok, val = m.signal_return()
        assert ok is True
        assert val == "open"

    def test_set_value_moves_cursor(self):
        m = self._menu()
        m.set_value("Quit")
        assert m.get_value() == "Quit"

    def test_set_value_unknown_label_ignored(self):
        m = self._menu()
        m.set_value("Missing")
        assert m.get_value() == "New"

    def test_render_produces_write_cmds(self):
        m = self._menu()
        cmds = m.render(CTX, focused=True)
        write_cmds = [c for c in cmds if isinstance(c, WriteCmd)]
        assert len(write_cmds) >= 1


# ---------------------------------------------------------------------------
# RadioList
# ---------------------------------------------------------------------------

class TestRadioList:
    def _radio(self):
        return RadioList({"Small": "s", "Medium": "m", "Large": "l"})

    def test_initial_get_value_is_mapped_value(self):
        r = self._radio()
        assert r.get_value() == "s"

    def test_key_down_changes_mapped_value(self):
        r = self._radio()
        r.handle_key("KEY_DOWN")
        assert r.get_value() == "m"

    def test_set_value_by_mapped_value(self):
        r = self._radio()
        r.set_value("l")
        assert r.get_value() == "l"

    def test_set_value_unknown_ignored(self):
        r = self._radio()
        r.set_value("x")
        assert r.get_value() == "s"

    def test_signal_return_after_enter(self):
        r = self._radio()
        r.handle_key("KEY_DOWN")
        r.handle_key("KEY_ENTER")
        ok, val = r.signal_return()
        assert ok is True
        assert val == "m"

    def test_signal_return_false_before_enter(self):
        r = self._radio()
        assert r.signal_return() == (False, None)

    def test_render_includes_radio_mark(self):
        r = self._radio()
        cmds = r.render(CTX)
        texts = " ".join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert "(•)" in texts


# ---------------------------------------------------------------------------
# CheckBox
# ---------------------------------------------------------------------------

class TestCheckBox:
    def _cb(self, mode="multi"):
        return CheckBox(
            {"Logging": True, "Dark mode": False, "Auto-save": True}, mode=mode
        )

    def test_get_value_returns_dict(self):
        cb = self._cb()
        v = cb.get_value()
        assert v == {"Logging": True, "Dark mode": False, "Auto-save": True}

    def test_space_toggles_item(self):
        cb = self._cb()
        cb.handle_key(" ")
        assert cb.get_value()["Logging"] is False

    def test_space_in_single_mode_unchecks_others(self):
        cb = self._cb(mode="single")
        cb.handle_key("KEY_DOWN")   # move to Dark mode
        cb.handle_key(" ")          # check Dark mode
        v = cb.get_value()
        assert v["Dark mode"] is True
        assert v["Logging"] is False
        assert v["Auto-save"] is False

    def test_signal_return_always_false(self):
        cb = self._cb()
        cb.handle_key(" ")
        assert cb.signal_return() == (False, None)

    def test_set_value_replaces_states(self):
        cb = self._cb()
        cb.set_value({"Logging": False, "Dark mode": True, "Auto-save": False})
        v = cb.get_value()
        assert v == {"Logging": False, "Dark mode": True, "Auto-save": False}

    def test_render_includes_checkbox_marks(self):
        cb = self._cb()
        cmds = cb.render(CTX)
        texts = " ".join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert "[x]" in texts
        assert "[ ]" in texts


# ---------------------------------------------------------------------------
# TextBox
# ---------------------------------------------------------------------------

class TestTextBox:
    def test_initial_empty(self):
        t = TextBox()
        assert t.get_value() == ""

    def test_initial_value(self):
        t = TextBox(initial="hello")
        assert t.get_value() == "hello"

    def test_typing_appends(self):
        t = TextBox()
        t.handle_key("h")
        t.handle_key("i")
        assert t.get_value() == "hi"

    def test_backspace_removes_last_char(self):
        t = TextBox(initial="abc")
        t.handle_key("KEY_BACKSPACE")
        assert t.get_value() == "ab"

    def test_enter_mode_newline(self):
        t = TextBox(enter_mode="newline")
        t.handle_key("a")
        t.handle_key("KEY_ENTER")
        t.handle_key("b")
        assert t.get_value() == "a\nb"

    def test_enter_mode_submit_fires_signal_return(self):
        t = TextBox(initial="hello", enter_mode="submit")
        t.handle_key("KEY_ENTER")
        ok, val = t.signal_return()
        assert ok is True
        assert val == "hello"

    def test_enter_mode_ignore(self):
        t = TextBox(initial="abc", enter_mode="ignore")
        changed, _ = t.handle_key("KEY_ENTER")
        assert changed is False
        assert t.get_value() == "abc"

    def test_readonly_ignores_keys(self):
        t = TextBox(initial="ro", readonly=True)
        t.handle_key("x")
        t.handle_key("KEY_BACKSPACE")
        assert t.get_value() == "ro"

    def test_signal_return_false_before_submit(self):
        t = TextBox(enter_mode="submit")
        assert t.signal_return() == (False, None)

    def test_set_value_replaces_text(self):
        t = TextBox(initial="old")
        t.set_value("new")
        assert t.get_value() == "new"


# ---------------------------------------------------------------------------
# NestedMenu
# ---------------------------------------------------------------------------

class TestNestedMenu:
    def _menu(self):
        return NestedMenu({
            "File": {
                "New":  "file:new",
                "Save": "file:save",
            },
            "Quit": "quit",
        })

    def test_initial_path_is_first_label(self):
        m = self._menu()
        assert m.get_value() == ("File",)

    def test_key_down_moves_cursor(self):
        m = self._menu()
        m.handle_key("KEY_DOWN")
        assert m.get_value() == ("Quit",)

    def test_enter_on_branch_descends(self):
        m = self._menu()
        m.handle_key("KEY_ENTER")  # descend into File
        path = m.get_value()
        assert path[0] == "File"
        assert len(path) == 2

    def test_enter_on_leaf_submits(self):
        m = self._menu()
        m.handle_key("KEY_DOWN")   # Quit
        m.handle_key("KEY_ENTER")
        ok, val = m.signal_return()
        assert ok is True
        assert val == "quit"

    def test_key_left_ascends(self):
        m = self._menu()
        m.handle_key("KEY_ENTER")  # descend into File
        m.handle_key("KEY_LEFT")   # back to root
        assert m.get_value() == ("File",)

    def test_signal_return_false_before_leaf_accept(self):
        m = self._menu()
        assert m.signal_return() == (False, None)

    def test_set_value_navigates_to_path(self):
        m = self._menu()
        m.set_value(("File", "Save"))
        assert m.get_value() == ("File", "Save")

    def test_set_value_empty_path_ignored(self):
        m = self._menu()
        m.set_value(())
        assert m.get_value() == ("File",)  # unchanged

    def test_leaf_marker(self):
        menu = NestedMenu({"Prefs": Leaf({"theme": "dark"})})
        menu.handle_key("KEY_ENTER")
        ok, val = menu.signal_return()
        assert ok is True
        assert val == {"theme": "dark"}

    def test_leaf_none_rejected(self):
        with pytest.raises(ValueError):
            Leaf(None)

    def test_get_value_empty_menu(self):
        # Malformed empty root — renderer handles gracefully
        m = NestedMenu({})
        assert m.get_value() == ()

    def test_render_shows_branch_indicator(self):
        m = self._menu()
        cmds = m.render(CTX, focused=True)
        texts = " ".join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert ">" in texts


# ---------------------------------------------------------------------------
# FormInput
# ---------------------------------------------------------------------------

class TestFormInput:
    def _form(self):
        return FormInput({
            "name": {"type": "str",   "descriptor": "Name",  "required": True},
            "age":  {"type": "int",   "descriptor": "Age"},
            "role": {"type": "choices", "descriptor": "Role",
                     "options": ["Admin", "User", "Guest"], "default": "User"},
        })

    def test_initial_get_value(self):
        f = self._form()
        v = f.get_value()
        assert v["role"] == "User"

    def test_signal_return_false_initially(self):
        f = self._form()
        assert f.signal_return() == (False, None)

    def test_typing_into_field(self):
        f = self._form()
        f.handle_key("A")
        f.handle_key("l")
        f.handle_key("i")
        f.handle_key("c")
        f.handle_key("e")
        f.handle_key("KEY_ENTER")  # commit name field
        assert f.get_value()["name"] == "Alice"

    def test_required_field_prevents_submit(self):
        f = self._form()
        # Navigate to Submit without filling required name
        for _ in range(10):  # go past all fields to Submit
            f.handle_key("KEY_DOWN")
        f.handle_key("KEY_ENTER")
        # Should not have submitted
        assert f.signal_return() == (False, None)

    def test_submit_with_valid_fields(self):
        f = self._form()
        # Fill name
        for ch in "Bob":
            f.handle_key(ch)
        f.handle_key("KEY_ENTER")  # commit, advance to age
        # age has default 0; navigate to Submit
        for _ in range(10):
            f.handle_key("KEY_DOWN")
        f.handle_key("KEY_ENTER")
        ok, val = f.signal_return()
        assert ok is True
        assert val["name"] == "Bob"

    def test_set_value_updates_fields(self):
        f = self._form()
        f.set_value({"name": "Eve", "age": 30})
        assert f.get_value()["name"] == "Eve"
        assert f.get_value()["age"] == 30

    def test_choices_cycles_with_space(self):
        f = self._form()
        # Navigate down past name and age to role
        f.handle_key("KEY_DOWN")
        f.handle_key("KEY_DOWN")
        # role starts at "User", space advances
        f.handle_key(" ")
        assert f.get_value()["role"] == "Guest"

    def test_render_shows_descriptor(self):
        f = self._form()
        cmds = f.render(CTX, focused=True)
        texts = " ".join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert "Name" in texts


# ---------------------------------------------------------------------------
# DataclassFormInteraction
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class _Config:
    host:  str  = "localhost"
    port:  int  = 8080
    debug: bool = False


class TestDataclassFormInteraction:
    def _form(self, actions=None):
        return DataclassFormInteraction(_Config(), actions=actions)

    def test_initial_values_from_dataclass(self):
        f = self._form()
        v = f.get_value()
        assert v["host"] == "localhost"
        assert v["port"] == 8080
        assert v["debug"] is False

    def test_signal_return_false_initially(self):
        assert self._form().signal_return() == (False, None)

    def test_set_value_replaces_fields(self):
        f = self._form()
        f.set_value({"host": "example.com", "port": 443})
        v = f.get_value()
        assert v["host"] == "example.com"
        assert v["port"] == 443

    def test_action_fires_and_signals_return(self):
        actions = [
            {"label": "Save",   "action": lambda v: v},
            {"label": "Cancel", "action": lambda v: None},
        ]
        f = DataclassFormInteraction(_Config(), actions=actions)
        # Navigate to Save action (3 fields + first action = index 3)
        for _ in range(3):
            f.handle_key("KEY_DOWN")
        f.handle_key("KEY_ENTER")
        ok, val = f.signal_return()
        assert ok is True
        assert val is not None  # got field dict back

    def test_cancel_action_returns_none(self):
        actions = [
            {"label": "Save",   "action": lambda v: v},
            {"label": "Cancel", "action": lambda v: None},
        ]
        f = DataclassFormInteraction(_Config(), actions=actions)
        for _ in range(4):  # past 3 fields + Save → Cancel
            f.handle_key("KEY_DOWN")
        f.handle_key("KEY_ENTER")
        ok, val = f.signal_return()
        assert ok is True
        assert val is None

    def test_bool_field_toggles(self):
        f = self._form()
        # debug is at index 2 (third field)
        f.handle_key("KEY_DOWN")
        f.handle_key("KEY_DOWN")
        f.handle_key(" ")
        assert f.get_value()["debug"] is True

    def test_on_change_called(self):
        calls = []
        f = DataclassFormInteraction(_Config(), on_change=lambda v: calls.append(v))
        f.handle_key("KEY_DOWN")
        f.handle_key("KEY_DOWN")
        f.handle_key(" ")  # toggle debug
        assert len(calls) == 1
        assert calls[0]["debug"] is True

    def test_render_shows_field_name(self):
        f = self._form()
        cmds = f.render(CTX, focused=True)
        texts = " ".join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert "host" in texts
