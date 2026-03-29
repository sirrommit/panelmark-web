"""TextBox — text-input area with configurable wrap and Enter behaviour."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd


def _wrap_lines(text: str, width: int, wrap: str) -> list[str]:
    """Wrap *text* into a list of display lines of at most *width* chars."""
    if wrap == "extend":
        # No wrap — treat text as one logical line (ignore embedded newlines
        # for display; show only the last segment after the final newline).
        return [text.split("\n")[-1]]

    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        if wrap == "anywhere":
            while len(paragraph) > width:
                lines.append(paragraph[:width])
                paragraph = paragraph[width:]
            lines.append(paragraph)
        else:  # "word"
            while len(paragraph) > width:
                split_at = paragraph.rfind(" ", 0, width + 1)
                if split_at <= 0:
                    split_at = width
                lines.append(paragraph[:split_at].rstrip())
                paragraph = paragraph[split_at:].lstrip()
            lines.append(paragraph)
    return lines


class TextBox(Interaction):
    """Text-input area.

    ``get_value()``     → current text content (``str``), including newlines.
    ``set_value(text)`` → replace the full text content.
    ``signal_return()`` → ``(True, text)`` when Enter is pressed in
                          ``enter_mode="submit"``; ``(False, None)`` otherwise.

    Parameters
    ----------
    initial:
        Starting text content.
    wrap:
        ``"word"`` (default) — wrap at word boundaries;
        ``"anywhere"`` — wrap mid-word;
        ``"extend"`` — no wrap, suitable for single-line inputs.
    readonly:
        If ``True``, all keys are ignored.
    enter_mode:
        ``"newline"`` (default) — Enter inserts a newline;
        ``"submit"`` — Enter fires ``signal_return()``;
        ``"ignore"`` — Enter is discarded.
    """

    def __init__(
        self,
        initial: str = "",
        wrap: str = "word",
        readonly: bool = False,
        enter_mode: str = "newline",
    ) -> None:
        self._text = initial
        self._wrap = wrap
        self._readonly = readonly
        self._enter_mode = enter_mode
        self._submitted = False

    def render(self, context: RenderContext, focused: bool = False) -> list:
        cmds = [FillCmd(row=0, col=0, width=context.width, height=context.height)]
        lines = _wrap_lines(self._text, context.width, self._wrap)
        # Scroll to the end so the editing point is always visible
        start = max(0, len(lines) - context.height)
        visible = lines[start:]
        for row, line in enumerate(visible[: context.height]):
            # Append a cursor marker on the last visible line when focused
            if focused and row == min(len(visible), context.height) - 1:
                display = (line + "_")[: context.width].ljust(context.width)
            else:
                display = line[: context.width].ljust(context.width)
            style = {"reverse": True} if (focused and self._wrap == "extend") else None
            cmds.append(WriteCmd(row=row, col=0, text=display, style=style))
        return cmds

    def handle_key(self, key: str) -> tuple:
        if self._readonly:
            return False, self.get_value()
        if key == "KEY_BACKSPACE" and self._text:
            self._text = self._text[:-1]
            return True, self.get_value()
        if key == "KEY_ENTER":
            if self._enter_mode == "submit":
                self._submitted = True
                return True, self.get_value()
            if self._enter_mode == "newline":
                self._text += "\n"
                return True, self.get_value()
            # "ignore"
            return False, self.get_value()
        if len(key) == 1 and key.isprintable():
            self._text += key
            return True, self.get_value()
        return False, self.get_value()

    def get_value(self) -> str:
        return self._text

    def set_value(self, text) -> None:
        self._text = str(text)

    def signal_return(self) -> tuple:
        if self._submitted:
            return True, self._text
        return False, None
