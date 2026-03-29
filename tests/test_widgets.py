"""Tests for panelmark_web.widgets — portable widget library."""

import dataclasses
import os
import tempfile

from panelmark.draw import FillCmd, RenderContext, WriteCmd

from panelmark_web.widgets import (
    Alert,
    Confirm,
    DataclassForm,
    FilePicker,
    InputPrompt,
    ListSelect,
)

CTX = RenderContext(width=24, height=8)


# ---------------------------------------------------------------------------
# Alert
# ---------------------------------------------------------------------------

class TestAlert:
    def test_signal_return_false_initially(self):
        assert Alert().signal_return() == (False, None)

    def test_get_value_none_before_dismiss(self):
        assert Alert().get_value() is None

    def test_enter_dismisses(self):
        a = Alert(title="T", message_lines=["msg"])
        a.handle_key("KEY_ENTER")
        assert a.get_value() is True
        ok, val = a.signal_return()
        assert ok is True and val is True

    def test_space_dismisses(self):
        a = Alert()
        a.handle_key(" ")
        ok, val = a.signal_return()
        assert ok is True and val is True

    def test_escape_cancels(self):
        a = Alert()
        a.handle_key("\x1b")
        ok, val = a.signal_return()
        assert ok is True and val is None

    def test_other_keys_do_nothing(self):
        a = Alert()
        changed, _ = a.handle_key("x")
        assert changed is False
        assert a.signal_return() == (False, None)

    def test_render_includes_title(self):
        a = Alert(title="Warning")
        cmds = a.render(CTX, focused=True)
        texts = " ".join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert "Warning" in texts

    def test_render_includes_message(self):
        a = Alert(message_lines=["All good"])
        cmds = a.render(CTX)
        texts = " ".join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert "All good" in texts


# ---------------------------------------------------------------------------
# Confirm
# ---------------------------------------------------------------------------

class TestConfirm:
    def _confirm(self):
        return Confirm(title="Delete?", message_lines=["Are you sure?"])

    def test_signal_return_false_initially(self):
        assert self._confirm().signal_return() == (False, None)

    def test_enter_returns_first_button_value(self):
        c = self._confirm()  # OK=True, Cancel=False, cursor starts at OK
        c.handle_key("KEY_ENTER")
        ok, val = c.signal_return()
        assert ok is True and val is True

    def test_right_then_enter_returns_second_button(self):
        c = self._confirm()
        c.handle_key("KEY_RIGHT")  # move to Cancel
        c.handle_key("KEY_ENTER")
        ok, val = c.signal_return()
        assert ok is True and val is False

    def test_left_does_not_go_before_first(self):
        c = self._confirm()
        changed, _ = c.handle_key("KEY_LEFT")
        assert changed is False

    def test_escape_cancels(self):
        c = self._confirm()
        c.handle_key("\x1b")
        ok, val = c.signal_return()
        assert ok is True and val is None

    def test_custom_buttons(self):
        c = Confirm(buttons={"Yes": "yes", "No": "no", "Maybe": "maybe"})
        c.handle_key("KEY_RIGHT")
        c.handle_key("KEY_RIGHT")
        c.handle_key("KEY_ENTER")
        ok, val = c.signal_return()
        assert ok is True and val == "maybe"

    def test_render_includes_title(self):
        cmds = self._confirm().render(CTX, focused=True)
        texts = " ".join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert "Delete?" in texts


# ---------------------------------------------------------------------------
# InputPrompt
# ---------------------------------------------------------------------------

class TestInputPrompt:
    def test_get_value_returns_initial(self):
        p = InputPrompt(initial="hello")
        assert p.get_value() == "hello"

    def test_signal_return_false_initially(self):
        assert InputPrompt().signal_return() == (False, None)

    def test_typing_appends(self):
        p = InputPrompt()
        p.handle_key("h")
        p.handle_key("i")
        assert p.get_value() == "hi"

    def test_backspace_deletes(self):
        p = InputPrompt(initial="abc")
        p.handle_key("KEY_BACKSPACE")
        assert p.get_value() == "ab"

    def test_enter_submits(self):
        p = InputPrompt(initial="text")
        p.handle_key("KEY_ENTER")
        ok, val = p.signal_return()
        assert ok is True and val == "text"

    def test_enter_with_empty_string(self):
        p = InputPrompt()
        p.handle_key("KEY_ENTER")
        ok, val = p.signal_return()
        assert ok is True and val == ""

    def test_escape_cancels(self):
        p = InputPrompt()
        p.handle_key("\x1b")
        ok, val = p.signal_return()
        assert ok is True and val is None

    def test_set_value(self):
        p = InputPrompt()
        p.set_value("preset")
        assert p.get_value() == "preset"

    def test_render_shows_text(self):
        p = InputPrompt(title="Name", initial="Bob")
        cmds = p.render(CTX, focused=True)
        texts = " ".join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert "Name" in texts
        assert "Bob" in texts


# ---------------------------------------------------------------------------
# ListSelect — single mode
# ---------------------------------------------------------------------------

class TestListSelectSingle:
    def _ls(self):
        return ListSelect(items=["Apple", "Banana", "Cherry"])

    def test_enter_selects_first(self):
        ls = self._ls()
        ls.handle_key("KEY_ENTER")
        ok, val = ls.signal_return()
        assert ok is True and val == "Apple"

    def test_down_then_enter(self):
        ls = self._ls()
        ls.handle_key("KEY_DOWN")
        ls.handle_key("KEY_ENTER")
        ok, val = ls.signal_return()
        assert ok is True and val == "Banana"

    def test_dict_items_return_mapped_value(self):
        ls = ListSelect(items={"Small": "s", "Large": "l"})
        ls.handle_key("KEY_DOWN")
        ls.handle_key("KEY_ENTER")
        ok, val = ls.signal_return()
        assert ok is True and val == "l"

    def test_escape_cancels(self):
        ls = self._ls()
        ls.handle_key("\x1b")
        ok, val = ls.signal_return()
        assert ok is True and val is None

    def test_signal_return_false_before_action(self):
        assert self._ls().signal_return() == (False, None)

    def test_get_value_returns_highlighted(self):
        ls = self._ls()
        ls.handle_key("KEY_DOWN")
        assert ls.get_value() == "Banana"

    def test_set_value_single_list(self):
        ls = self._ls()
        ls.set_value("Cherry")
        assert ls.get_value() == "Cherry"


# ---------------------------------------------------------------------------
# ListSelect — multi mode
# ---------------------------------------------------------------------------

class TestListSelectMulti:
    def _ls(self):
        return ListSelect(
            items={"Alpha": False, "Beta": False, "Gamma": True},
            multi=True,
        )

    def test_initial_get_value_is_dict(self):
        assert self._ls().get_value() == {"Alpha": False, "Beta": False, "Gamma": True}

    def test_space_toggles(self):
        ls = self._ls()
        ls.handle_key(" ")  # toggle Alpha
        assert ls.get_value()["Alpha"] is True

    def test_ok_button_submits(self):
        ls = self._ls()
        # Navigate past all items to OK button
        ls.handle_key("KEY_DOWN")
        ls.handle_key("KEY_DOWN")
        ls.handle_key("KEY_DOWN")  # now on OK row
        ls.handle_key("KEY_ENTER")
        ok, val = ls.signal_return()
        assert ok is True
        assert isinstance(val, dict)
        assert val["Gamma"] is True

    def test_escape_cancels(self):
        ls = self._ls()
        ls.handle_key("\x1b")
        ok, val = ls.signal_return()
        assert ok is True and val is None

    def test_set_value_multi(self):
        ls = self._ls()
        ls.set_value({"Alpha": True, "Beta": True, "Gamma": False})
        v = ls.get_value()
        assert v == {"Alpha": True, "Beta": True, "Gamma": False}

    def test_render_shows_checkboxes(self):
        ls = self._ls()
        cmds = ls.render(CTX)
        texts = " ".join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert "[ ]" in texts
        assert "[x]" in texts


# ---------------------------------------------------------------------------
# DataclassForm
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class _Profile:
    name: str = "Alice"
    age: int = 30
    active: bool = True


class TestDataclassForm:
    def test_initial_values(self):
        f = DataclassForm(_Profile())
        v = f.get_value()
        assert v["name"] == "Alice"
        assert v["age"] == 30
        assert v["active"] is True

    def test_escape_cancels(self):
        f = DataclassForm(_Profile())
        f.handle_key("\x1b")
        ok, val = f.signal_return()
        assert ok is True and val is None

    def test_action_fires(self):
        f = DataclassForm(
            _Profile(),
            actions=[{"label": "Save", "action": lambda v: v}],
        )
        # Navigate to Save action (index 3 = past name, age, active)
        for _ in range(3):
            f.handle_key("KEY_DOWN")
        f.handle_key("KEY_ENTER")
        ok, val = f.signal_return()
        assert ok is True and val is not None

    def test_title_stored(self):
        f = DataclassForm(_Profile(), title="Edit Profile")
        assert f.title == "Edit Profile"

    def test_signal_return_false_initially(self):
        assert DataclassForm(_Profile()).signal_return() == (False, None)


# ---------------------------------------------------------------------------
# FilePicker
# ---------------------------------------------------------------------------

class TestFilePicker:
    def test_initial_dir_is_cwd(self):
        fp = FilePicker()
        assert fp._current_dir == os.path.abspath(os.getcwd())

    def test_custom_start_dir(self):
        with tempfile.TemporaryDirectory() as d:
            fp = FilePicker(start_dir=d)
            assert fp._current_dir == d

    def test_signal_return_false_initially(self):
        fp = FilePicker()
        assert fp.signal_return() == (False, None)

    def test_escape_cancels(self):
        fp = FilePicker()
        fp.handle_key("\x1b")
        ok, val = fp.signal_return()
        assert ok is True and val is None

    def test_enter_on_file_selects(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.txt")
            open(path, "w").close()
            fp = FilePicker(start_dir=d)
            # Find the test.txt entry
            names = [e[0] for e in fp._entries]
            idx = names.index("test.txt")
            fp._cursor = idx
            fp.handle_key("KEY_ENTER")
            ok, val = fp.signal_return()
            assert ok is True
            assert val == path

    def test_enter_on_dir_navigates(self):
        with tempfile.TemporaryDirectory() as d:
            subdir = os.path.join(d, "sub")
            os.mkdir(subdir)
            fp = FilePicker(start_dir=d)
            names = [e[0] for e in fp._entries]
            idx = names.index("sub/")
            fp._cursor = idx
            fp.handle_key("KEY_ENTER")
            assert fp._current_dir == subdir

    def test_dirs_only_shows_select_here(self):
        fp = FilePicker(dirs_only=True)
        names = [e[0] for e in fp._entries]
        assert "[Select here]" in names

    def test_dirs_only_select_here_submits_current_dir(self):
        with tempfile.TemporaryDirectory() as d:
            fp = FilePicker(start_dir=d, dirs_only=True)
            fp._cursor = 0  # [Select here]
            fp.handle_key("KEY_ENTER")
            ok, val = fp.signal_return()
            assert ok is True and val == d

    def test_filter_hides_non_matching_files(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "a.py"), "w").close()
            open(os.path.join(d, "b.txt"), "w").close()
            fp = FilePicker(start_dir=d, filter="*.py")
            names = [e[0] for e in fp._entries]
            assert "a.py" in names
            assert "b.txt" not in names

    def test_render_shows_title_and_dir(self):
        fp = FilePicker(title="Open")
        cmds = fp.render(CTX)
        texts = " ".join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert "Open" in texts
