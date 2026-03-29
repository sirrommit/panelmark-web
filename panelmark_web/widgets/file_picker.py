"""FilePicker — panelmark-managed server-side filesystem browser."""

import fnmatch
import os

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd

from panelmark_web.interactions._helpers import scroll_offset

_SELECT_HERE = "[Select here]"


class FilePicker(Interaction):
    """Server-side filesystem browser.

    Navigates the server filesystem using draw commands.  The user browses
    directories with ``KEY_UP`` / ``KEY_DOWN``, enters directories with
    ``KEY_ENTER``, and selects a file (or directory in ``dirs_only`` mode)
    with ``KEY_ENTER``.

    ``get_value()``    → absolute path of the currently highlighted entry;
                         ``None`` when the list is empty.
    ``signal_return()``→ ``(True, absolute_path)`` when a file or directory
                         is selected; ``(True, None)`` on Escape/cancel;
                         ``(False, None)`` while still browsing.

    Parameters
    ----------
    start_dir:
        Initial directory.  Defaults to the current working directory.
    title:
        Heading line.
    dirs_only:
        If ``True``, hide regular files and show only directories.  A
        ``[Select here]`` entry is added at the top to select the current
        directory.
    filter:
        Glob pattern applied to file names (e.g. ``"*.py"``).  Ignored
        when ``dirs_only=True``.
    """

    def __init__(
        self,
        start_dir: str | None = None,
        title: str = "Select File",
        dirs_only: bool = False,
        filter: str = "*",
    ) -> None:
        self._title = title
        self._dirs_only = dirs_only
        self._filter = filter
        self._current_dir = os.path.abspath(start_dir or os.getcwd())
        self._entries: list[tuple[str, bool]] = []  # (display_name, is_dir)
        self._cursor = 0
        self._submitted = False
        self._cancelled = False
        self._selected_path: str | None = None
        self._refresh()

    # ------------------------------------------------------------------
    # Filesystem helpers
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        entries: list[tuple[str, bool]] = []

        if self._dirs_only:
            entries.append((_SELECT_HERE, False))

        parent = os.path.dirname(self._current_dir)
        if parent != self._current_dir:
            entries.append(("..", True))

        try:
            names = sorted(os.listdir(self._current_dir))
        except (PermissionError, FileNotFoundError):
            names = []

        for name in names:
            path = os.path.join(self._current_dir, name)
            if os.path.isdir(path):
                entries.append((name + "/", True))
            elif not self._dirs_only:
                if self._filter == "*" or fnmatch.fnmatch(name, self._filter):
                    entries.append((name, False))

        self._entries = entries
        self._cursor = min(self._cursor, max(0, len(entries) - 1))

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, context: RenderContext, focused: bool = False) -> list:
        cmds = [FillCmd(row=0, col=0, width=context.width, height=context.height)]
        row = 0
        if row < context.height:
            cmds.append(WriteCmd(
                row=row, col=0,
                text=self._title[: context.width].ljust(context.width),
                style={"bold": True},
            ))
            row += 1
        if row < context.height:
            cmds.append(WriteCmd(
                row=row, col=0,
                text=self._current_dir[: context.width].ljust(context.width),
            ))
            row += 1

        list_height = context.height - row
        if list_height > 0 and self._entries:
            offset = scroll_offset(self._cursor, list_height, len(self._entries))
            for i in range(list_height):
                idx = offset + i
                if idx >= len(self._entries):
                    break
                if row >= context.height:
                    break
                name, _ = self._entries[idx]
                cmds.append(WriteCmd(
                    row=row, col=0,
                    text=name[: context.width].ljust(context.width),
                    style={"reverse": True} if (focused and idx == self._cursor) else None,
                ))
                row += 1

        return cmds

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def handle_key(self, key: str) -> tuple:
        n = len(self._entries)
        if not n:
            return False, self.get_value()

        if key == "KEY_UP":
            if self._cursor > 0:
                self._cursor -= 1
                return True, self.get_value()
            return False, self.get_value()

        if key == "KEY_DOWN":
            if self._cursor < n - 1:
                self._cursor += 1
                return True, self.get_value()
            return False, self.get_value()

        if key == "KEY_ENTER":
            name, is_dir = self._entries[self._cursor]
            if name == _SELECT_HERE:
                self._selected_path = self._current_dir
                self._submitted = True
                return True, self.get_value()
            if is_dir:
                if name == "..":
                    self._current_dir = os.path.dirname(self._current_dir)
                else:
                    self._current_dir = os.path.join(
                        self._current_dir, name.rstrip("/")
                    )
                self._cursor = 0
                self._refresh()
                return True, self.get_value()
            # Regular file
            self._selected_path = os.path.join(self._current_dir, name)
            self._submitted = True
            return True, self.get_value()

        if key == "\x1b":
            self._cancelled = True
            return True, None

        return False, self.get_value()

    # ------------------------------------------------------------------
    # Value contract
    # ------------------------------------------------------------------

    def get_value(self):
        if self._submitted:
            return self._selected_path
        if not self._entries:
            return None
        name, _ = self._entries[self._cursor]
        if name == _SELECT_HERE:
            return self._current_dir
        if name == "..":
            return os.path.dirname(self._current_dir)
        return os.path.join(self._current_dir, name.rstrip("/"))

    def set_value(self, value) -> None:
        pass  # FilePicker does not support programmatic path injection

    def signal_return(self) -> tuple:
        if self._submitted:
            return True, self._selected_path
        if self._cancelled:
            return True, None
        return False, None
