"""InputPrompt — asks the user to type a single line of text."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd


class InputPrompt(Interaction):
    """Single-line text-entry dialog.

    ``get_value()``    → current text content (``str``).
    ``signal_return()``→ ``(True, text)`` when Enter is pressed (text may be
                         ``""``); ``(True, None)`` on Escape/cancel;
                         ``(False, None)`` while still open.

    Keys: printable chars to type; ``KEY_BACKSPACE`` to delete;
          ``KEY_ENTER`` to submit; ``Escape`` to cancel.

    Parameters
    ----------
    title:
        Heading line shown at the top.
    prompt_lines:
        Lines of instructional text displayed between the title and the
        input field.
    initial:
        Initial content of the input field.
    """

    def __init__(
        self,
        title: str = "Input",
        prompt_lines: list = None,
        initial: str = "",
    ) -> None:
        self._title = title
        self._prompt_lines = prompt_lines or []
        self._text = initial
        self._submitted = False
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
        for line in self._prompt_lines:
            if row >= context.height:
                break
            cmds.append(WriteCmd(
                row=row, col=0,
                text=line[: context.width].ljust(context.width),
            ))
            row += 1
        if row < context.height:
            cursor_char = "_" if focused else ""
            display = (self._text + cursor_char)[: context.width].ljust(context.width)
            cmds.append(WriteCmd(
                row=row, col=0,
                text=display,
                style={"reverse": True} if focused else None,
            ))
        return cmds

    def handle_key(self, key: str) -> tuple:
        if key == "KEY_BACKSPACE" and self._text:
            self._text = self._text[:-1]
            return True, self._text
        if key == "KEY_ENTER":
            self._submitted = True
            return True, self._text
        if key == "\x1b":
            self._cancelled = True
            return True, None
        if len(key) == 1 and key.isprintable():
            self._text += key
            return True, self._text
        return False, self._text

    def get_value(self) -> str:
        return self._text

    def set_value(self, value) -> None:
        self._text = str(value)

    def signal_return(self) -> tuple:
        if self._submitted:
            return True, self._text
        if self._cancelled:
            return True, None
        return False, None
