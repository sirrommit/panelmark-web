"""ListSelect — single or multi-select list dialog."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd

from panelmark_web.interactions._helpers import scroll_offset


class ListSelect(Interaction):
    """List-selection dialog supporting single and multi-select modes.

    **Single mode** (``multi=False``):
    ``KEY_ENTER`` accepts the highlighted item.
    ``get_value()`` → selected label (``list`` items) or mapped value
    (``dict`` items); ``None`` before submission.
    ``signal_return()`` → ``(True, label_or_value)`` on accept.

    **Multi mode** (``multi=True``):
    ``Space`` toggles the highlighted item.  ``KEY_ENTER`` on the
    ``[ OK ]`` row (or on a checked item) submits.
    ``get_value()`` → ``dict[str, bool]`` at all times.
    ``signal_return()`` → ``(True, dict[str, bool])`` on OK.

    Both modes: ``Escape`` → ``(True, None)``.

    Parameters
    ----------
    title:
        Heading line.
    prompt_lines:
        Lines of instructional text shown between the title and the list.
    items:
        A ``list`` of label strings, or a ``dict`` mapping labels to return
        values.  In multi mode, pass ``dict[str, bool]`` to set initial
        checked states (or a ``list`` to start all unchecked).
    multi:
        ``False`` (default) for single-select; ``True`` for multi-select.
    """

    def __init__(
        self,
        title: str = "Select",
        prompt_lines: list = None,
        items=None,
        multi: bool = False,
    ) -> None:
        self._title = title
        self._prompt_lines = prompt_lines or []
        self._multi = multi
        items = items if items is not None else []

        if isinstance(items, dict):
            self._labels = list(items.keys())
            if multi:
                # dict[str, bool] — initial checked states
                self._checked = {k: bool(v) for k, v in items.items()}
                self._payloads = None
            else:
                # dict[str, value] — label → return value
                self._payloads = dict(items)
                self._checked = None
        else:
            self._labels = list(items)
            self._payloads = None
            self._checked = {lbl: False for lbl in self._labels} if multi else None

        # In multi mode the last navigable row is the OK button
        self._cursor = 0 if self._labels else None
        self._submitted = False
        self._cancelled = False
        self._return_value = None

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def _header_rows(self) -> list:
        return [self._title] + self._prompt_lines

    def render(self, context: RenderContext, focused: bool = False) -> list:
        cmds = [FillCmd(row=0, col=0, width=context.width, height=context.height)]
        display_row = 0

        # Header
        for i, line in enumerate(self._header_rows()):
            if display_row >= context.height:
                break
            cmds.append(WriteCmd(
                row=display_row, col=0,
                text=line[: context.width].ljust(context.width),
                style={"bold": True} if i == 0 else None,
            ))
            display_row += 1

        # Reserve one row for the OK button in multi mode
        footer_height = 1 if self._multi else 0
        list_height = context.height - display_row - footer_height

        if list_height > 0 and self._labels:
            cursor = self._cursor if self._cursor is not None else 0
            # Clamp cursor to list area for scroll calculation (not the OK row)
            list_cursor = min(cursor, len(self._labels) - 1)
            offset = scroll_offset(list_cursor, list_height, len(self._labels))
            for i in range(list_height):
                idx = offset + i
                if idx >= len(self._labels):
                    break
                if display_row >= context.height - footer_height:
                    break
                label = self._labels[idx]
                if self._multi:
                    mark = "[x]" if self._checked.get(label) else "[ ]"
                    item_text = f"{mark} {label}"
                else:
                    item_text = label
                is_active = focused and self._cursor == idx
                cmds.append(WriteCmd(
                    row=display_row, col=0,
                    text=item_text[: context.width].ljust(context.width),
                    style={"reverse": True} if is_active else None,
                ))
                display_row += 1

        # OK button (multi mode only)
        if self._multi and display_row < context.height:
            ok_row = len(self._labels)  # virtual index of OK button
            is_ok = focused and self._cursor == ok_row
            cmds.append(WriteCmd(
                row=display_row, col=0,
                text="[ OK ]"[: context.width].ljust(context.width),
                style={"reverse": True} if is_ok else {"bold": True},
            ))

        return cmds

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def handle_key(self, key: str) -> tuple:
        # Total navigable rows: list items + optional OK button
        n = len(self._labels) + (1 if self._multi else 0)
        if not n:
            return False, self.get_value()
        cursor = self._cursor if self._cursor is not None else 0

        if key == "KEY_UP":
            if cursor > 0:
                self._cursor = cursor - 1
                return True, self.get_value()
            return False, self.get_value()

        if key == "KEY_DOWN":
            if cursor < n - 1:
                self._cursor = cursor + 1
                return True, self.get_value()
            return False, self.get_value()

        if key == " " and self._multi and cursor < len(self._labels):
            label = self._labels[cursor]
            self._checked[label] = not self._checked.get(label, False)
            return True, self.get_value()

        if key == "KEY_ENTER":
            if self._multi:
                if cursor == len(self._labels):
                    # OK button
                    self._return_value = dict(self._checked)
                    self._submitted = True
                else:
                    # Toggle on enter too
                    label = self._labels[cursor]
                    self._checked[label] = not self._checked.get(label, False)
                return True, self.get_value()
            else:
                # Single mode: accept highlighted item
                label = self._labels[cursor]
                self._return_value = (
                    self._payloads[label] if self._payloads is not None else label
                )
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
            return self._return_value
        if self._multi:
            return dict(self._checked) if self._checked is not None else {}
        # Single mode: current highlighted item
        cursor = self._cursor if self._cursor is not None else 0
        if not self._labels or cursor >= len(self._labels):
            return None
        label = self._labels[cursor]
        return self._payloads[label] if self._payloads is not None else label

    def set_value(self, value) -> None:
        if self._multi and isinstance(value, dict):
            for label in self._labels:
                if label in value:
                    self._checked[label] = bool(value[label])
        elif not self._multi:
            if self._payloads is not None:
                for i, label in enumerate(self._labels):
                    if self._payloads[label] == value:
                        self._cursor = i
                        return
            elif value in self._labels:
                self._cursor = self._labels.index(value)

    def signal_return(self) -> tuple:
        if self._submitted:
            return True, self._return_value
        if self._cancelled:
            return True, None
        return False, None
