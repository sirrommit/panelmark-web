"""NestedMenu — hierarchical action menu with drill-down navigation."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd

from ._helpers import scroll_offset


class Leaf:
    """Explicit leaf marker for NestedMenu.

    Use ``Leaf(value)`` when a leaf payload is itself a dict (to prevent
    it from being interpreted as a branch).

    ``None`` is not a valid leaf payload.
    """

    def __init__(self, value) -> None:
        if value is None:
            raise ValueError("Leaf payload may not be None")
        self.value = value


def _make_level(items_dict: dict) -> tuple:
    """Convert a branch dict to ``([(label, payload), ...], cursor=0)``."""
    return (list(items_dict.items()), 0)


class NestedMenu(Interaction):
    """Hierarchical action menu.

    ``get_value()``      → current highlighted path tuple ``(str, ...)``,
                           or ``()`` if nothing is highlighted.
    ``set_value(path)``  → highlight the item at the given label path;
                           invalid or empty paths are ignored.
    ``signal_return()``  → ``(True, mapped_value)`` when a leaf is accepted;
                           ``(False, None)`` otherwise.

    Navigation keys:

    - ``KEY_UP`` / ``KEY_DOWN``  — move within the current branch
    - ``KEY_ENTER``              — descend into a branch or accept a leaf
    - ``KEY_LEFT`` / ``Escape``  — go back to the parent branch

    Ordering follows the provided mapping order at each branch level.
    Sibling labels must be unique within the same branch level.
    """

    def __init__(self, items: dict) -> None:
        self._root = items
        # Stack of ([(label, payload), ...], cursor_idx)
        self._stack: list[tuple[list, int]] = [_make_level(items)]
        self._submitted = False
        self._return_value = None

    # ------------------------------------------------------------------
    # Stack helpers
    # ------------------------------------------------------------------

    def _items(self) -> list:
        return self._stack[-1][0]

    def _cursor(self) -> int:
        return self._stack[-1][1]

    def _set_cursor(self, idx: int) -> None:
        items, _ = self._stack[-1]
        self._stack[-1] = (items, idx)

    # ------------------------------------------------------------------
    # Interaction contract
    # ------------------------------------------------------------------

    def render(self, context: RenderContext, focused: bool = False) -> list:
        cmds = [FillCmd(row=0, col=0, width=context.width, height=context.height)]
        items = self._items()
        cursor = self._cursor()
        if not items:
            return cmds
        offset = scroll_offset(cursor, context.height, len(items))
        for row in range(context.height):
            idx = offset + row
            if idx >= len(items):
                break
            label, val = items[idx]
            # Branch indicator
            is_branch = isinstance(val, dict)
            suffix = " >" if is_branch else "  "
            text = (label + suffix)[: context.width].ljust(context.width)
            style = {"reverse": True} if (focused and idx == cursor) else None
            cmds.append(WriteCmd(row=row, col=0, text=text, style=style))
        return cmds

    def handle_key(self, key: str) -> tuple:
        items = self._items()
        cursor = self._cursor()
        n = len(items)
        if not items:
            return False, self.get_value()

        if key == "KEY_UP":
            if cursor > 0:
                self._set_cursor(cursor - 1)
                return True, self.get_value()
            return False, self.get_value()

        if key == "KEY_DOWN":
            if cursor < n - 1:
                self._set_cursor(cursor + 1)
                return True, self.get_value()
            return False, self.get_value()

        if key == "KEY_ENTER":
            label, val = items[cursor]
            if isinstance(val, Leaf):
                self._submitted = True
                self._return_value = val.value
                return True, self.get_value()
            if isinstance(val, dict):
                self._stack.append(_make_level(val))
                return True, self.get_value()
            # Plain leaf value
            self._submitted = True
            self._return_value = val
            return True, self.get_value()

        if key in ("KEY_LEFT", "\x1b") and len(self._stack) > 1:
            self._stack.pop()
            return True, self.get_value()

        return False, self.get_value()

    def get_value(self) -> tuple:
        path = []
        for items, cursor in self._stack:
            if not items or cursor >= len(items):
                break
            path.append(items[cursor][0])
        return tuple(path)

    def set_value(self, path) -> None:
        if not path:
            return
        self._stack = [_make_level(self._root)]
        current_dict = self._root
        for i, label in enumerate(path):
            items = list(current_dict.items())
            labels = [lbl for lbl, _ in items]
            if label not in labels:
                return
            idx = labels.index(label)
            self._stack[-1] = (items, idx)
            if i < len(path) - 1:
                _, val = items[idx]
                if isinstance(val, dict):
                    current_dict = val
                    self._stack.append(_make_level(val))
                else:
                    return  # path goes deeper than the tree allows

    def signal_return(self) -> tuple:
        if self._submitted:
            return True, self._return_value
        return False, None
