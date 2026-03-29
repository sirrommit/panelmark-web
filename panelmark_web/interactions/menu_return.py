"""MenuReturn — scrollable single-select list that returns a mapped value."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd

from ._helpers import scroll_offset


class MenuReturn(Interaction):
    """Scrollable single-select list.

    ``get_value()``     → currently highlighted label (``str | None``).
    ``set_value(label)`` → highlight the item with that label.
    ``signal_return()`` → ``(True, mapped_value)`` after Enter;
                          ``(False, None)`` otherwise.

    Keys: ``KEY_UP`` / ``KEY_DOWN`` to move, ``KEY_ENTER`` to accept.
    """

    def __init__(self, items: dict) -> None:
        self._labels = list(items.keys())
        self._payloads = dict(items)
        self._cursor = 0 if self._labels else None
        self._submitted = False

    def render(self, context: RenderContext, focused: bool = False) -> list:
        cmds = [FillCmd(row=0, col=0, width=context.width, height=context.height)]
        if not self._labels:
            return cmds
        offset = scroll_offset(self._cursor, context.height, len(self._labels))
        for row in range(context.height):
            idx = offset + row
            if idx >= len(self._labels):
                break
            label = self._labels[idx]
            text = label[: context.width].ljust(context.width)
            style = {"reverse": True} if (focused and idx == self._cursor) else None
            cmds.append(WriteCmd(row=row, col=0, text=text, style=style))
        return cmds

    def handle_key(self, key: str) -> tuple:
        if not self._labels:
            return False, self.get_value()
        if key == "KEY_UP" and self._cursor > 0:
            self._cursor -= 1
            return True, self.get_value()
        if key == "KEY_DOWN" and self._cursor < len(self._labels) - 1:
            self._cursor += 1
            return True, self.get_value()
        if key == "KEY_ENTER":
            self._submitted = True
            return True, self.get_value()
        return False, self.get_value()

    def get_value(self):
        if self._cursor is None:
            return None
        return self._labels[self._cursor]

    def set_value(self, label) -> None:
        if label in self._labels:
            self._cursor = self._labels.index(label)

    def signal_return(self) -> tuple:
        if self._submitted:
            label = self.get_value()
            return True, self._payloads.get(label)
        return False, None
