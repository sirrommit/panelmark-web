"""MenuFunction — scrollable menu that invokes callbacks without exiting the shell."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd

from ._helpers import scroll_offset


class MenuFunction(Interaction):
    """Scrollable menu that invokes a callback on each selection.

    Unlike :class:`~panelmark_web.interactions.MenuReturn`, ``MenuFunction``
    does **not** exit the shell when an item is accepted.  Instead it calls
    the item's associated callable and keeps running.

    ``get_value()``      → currently highlighted label (``str | None``).
    ``set_value(label)`` → highlight the item with that label.
    ``last_activated``   → read-only property — label most recently invoked,
                           or ``None`` before any invocation.
    ``signal_return()``  → always ``(False, None)``.

    Each callable receives the shell as its first argument::

        menu = MenuFunction({
            "Save": lambda sh: sh.update("status", "Saved"),
            "Reload": lambda sh: reload_data(sh),
        })

    Keys: ``KEY_UP`` / ``KEY_DOWN`` to move; ``KEY_ENTER`` to invoke.
    """

    def __init__(self, items: dict) -> None:
        self._labels = list(items.keys())
        self._callbacks = dict(items)
        self._cursor = 0 if self._labels else None
        self._last_activated: str | None = None

    @property
    def last_activated(self) -> str | None:
        """Label most recently invoked, or ``None``."""
        return self._last_activated

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
            label = self._labels[self._cursor]
            self._last_activated = label
            self._callbacks[label](self._shell)
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
        return False, None
