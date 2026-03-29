"""CheckBox — scrollable checkbox list with multi-select and single-select modes."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd

from ._helpers import scroll_offset


class CheckBox(Interaction):
    """Scrollable checkbox list.

    ``get_value()``         → ``dict[str, bool]`` — label → checked state.
    ``set_value(mapping)``  → replace the full checked-state dict.
    ``signal_return()``     → always ``(False, None)``; CheckBox does not
                              signal return by default.

    Keys: ``KEY_UP`` / ``KEY_DOWN`` to move, ``Space`` to toggle.

    In ``mode="single"`` toggling a checkbox unchecks all others first.
    """

    def __init__(self, items: dict, mode: str = "multi") -> None:
        self._labels = list(items.keys())
        self._checked = {k: bool(v) for k, v in items.items()}
        self._mode = mode
        self._cursor = 0 if self._labels else None

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
            mark = "[x]" if self._checked[label] else "[ ]"
            text = f"{mark} {label}"[: context.width].ljust(context.width)
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
        if key == " ":
            label = self._labels[self._cursor]
            if self._mode == "single":
                for k in self._checked:
                    self._checked[k] = False
                self._checked[label] = True
            else:
                self._checked[label] = not self._checked[label]
            return True, self.get_value()
        return False, self.get_value()

    def get_value(self) -> dict:
        return dict(self._checked)

    def set_value(self, mapping) -> None:
        for label in self._labels:
            if label in mapping:
                self._checked[label] = bool(mapping[label])

    def signal_return(self) -> tuple:
        return False, None
