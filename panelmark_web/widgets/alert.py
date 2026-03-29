"""Alert — informational popup that blocks until dismissed."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd


class Alert(Interaction):
    """Informational popup that displays a message and waits for dismissal.

    ``get_value()``    → ``True`` after dismissal; ``None`` otherwise.
    ``signal_return()``→ ``(True, True)`` when dismissed;
                         ``(True, None)`` on Escape/cancel;
                         ``(False, None)`` while still open.

    Keys: ``KEY_ENTER`` or ``Space`` to dismiss; ``Escape`` to cancel.

    Parameters
    ----------
    title:
        Heading line shown at the top.
    message_lines:
        Lines of body text displayed below the title.
    """

    def __init__(
        self,
        title: str = "Alert",
        message_lines: list = None,
    ) -> None:
        self._title = title
        self._message_lines = message_lines or []
        self._dismissed = False
        self._cancelled = False

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
            btn = "[ OK ]"
            cmds.append(WriteCmd(
                row=row, col=0,
                text=btn[: context.width].ljust(context.width),
                style={"reverse": True} if focused else {"bold": True},
            ))
        return cmds

    def handle_key(self, key: str) -> tuple:
        if key in ("KEY_ENTER", " "):
            self._dismissed = True
            return True, True
        if key == "\x1b":
            self._cancelled = True
            return True, None
        return False, self.get_value()

    def get_value(self):
        if self._dismissed:
            return True
        return None

    def set_value(self, value) -> None:
        pass  # Alert has no settable value

    def signal_return(self) -> tuple:
        if self._dismissed:
            return True, True
        if self._cancelled:
            return True, None
        return False, None
