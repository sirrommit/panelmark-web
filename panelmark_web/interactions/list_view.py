"""ListView — display-only scrollable list."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd


class ListView(Interaction):
    """Display-only scrollable list.  Not focusable by default.

    Renders items top-to-bottom, clipped to the available height.  Because
    ``is_focusable`` is ``False``, Tab does not cycle focus to this region.
    Update the list programmatically via ``set_value(items)`` or
    ``shell.update(name, items)``.

    ``get_value()``      → current items list (``list[str]``).
    ``set_value(items)`` → replace the full items list.
    ``signal_return()``  → always ``(False, None)``.
    """

    def __init__(self, items: list) -> None:
        self._items: list[str] = list(items)

    @property
    def is_focusable(self) -> bool:
        return False

    def render(self, context: RenderContext, focused: bool = False) -> list:
        cmds = [FillCmd(row=0, col=0, width=context.width, height=context.height)]
        for row, item in enumerate(self._items[: context.height]):
            text = str(item)[: context.width].ljust(context.width)
            cmds.append(WriteCmd(row=row, col=0, text=text))
        return cmds

    def handle_key(self, key: str) -> tuple:
        return False, self.get_value()

    def get_value(self) -> list:
        return list(self._items)

    def set_value(self, items) -> None:
        self._items = list(items)

    def signal_return(self) -> tuple:
        return False, None
