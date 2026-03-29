"""Confirm — asks the user to confirm or deny with caller-defined buttons."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd


class Confirm(Interaction):
    """Confirmation dialog with configurable buttons.

    ``get_value()``    → mapped value of the currently highlighted button;
                         ``None`` before any submission.
    ``signal_return()``→ ``(True, mapped_value)`` when a button is confirmed;
                         ``(True, None)`` on Escape/cancel;
                         ``(False, None)`` while still open.

    Keys: ``KEY_LEFT`` / ``KEY_RIGHT`` to move between buttons;
          ``KEY_ENTER`` to accept; ``Escape`` to cancel.

    Parameters
    ----------
    title:
        Heading line shown at the top.
    message_lines:
        Lines of body text displayed below the title.
    buttons:
        Mapping of button labels to return values.  Defaults to
        ``{"OK": True, "Cancel": False}``.
    """

    def __init__(
        self,
        title: str = "Confirm",
        message_lines: list = None,
        buttons: dict = None,
    ) -> None:
        self._title = title
        self._message_lines = message_lines or []
        self._buttons = buttons if buttons is not None else {"OK": True, "Cancel": False}
        self._btn_labels = list(self._buttons.keys())
        self._cursor = 0
        self._submitted = False
        self._cancelled = False
        self._return_value = None

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
        for line in self._message_lines:
            if row >= context.height:
                break
            cmds.append(WriteCmd(
                row=row, col=0,
                text=line[: context.width].ljust(context.width),
            ))
            row += 1
        if row < context.height:
            # Show all buttons on one line, highlighting the active one
            parts = []
            for i, lbl in enumerate(self._btn_labels):
                if focused and i == self._cursor:
                    parts.append(f"[{lbl}]")
                else:
                    parts.append(f" {lbl} ")
            btn_line = "  ".join(parts)
            cmds.append(WriteCmd(
                row=row, col=0,
                text=btn_line[: context.width].ljust(context.width),
                style={"reverse": True} if focused else None,
            ))
        return cmds

    def handle_key(self, key: str) -> tuple:
        if key == "KEY_LEFT" and self._cursor > 0:
            self._cursor -= 1
            return True, self.get_value()
        if key == "KEY_RIGHT" and self._cursor < len(self._btn_labels) - 1:
            self._cursor += 1
            return True, self.get_value()
        if key == "KEY_ENTER":
            label = self._btn_labels[self._cursor]
            self._return_value = self._buttons[label]
            self._submitted = True
            return True, self.get_value()
        if key == "\x1b":
            self._cancelled = True
            return True, None
        return False, self.get_value()

    def get_value(self):
        if self._submitted:
            return self._return_value
        return None

    def set_value(self, value) -> None:
        pass  # Confirm has no settable value

    def signal_return(self) -> tuple:
        if self._submitted:
            return True, self._return_value
        if self._cancelled:
            return True, None
        return False, None
