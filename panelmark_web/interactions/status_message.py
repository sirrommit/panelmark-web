"""StatusMessage — display-only single-line status and feedback area."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd

_STYLE_MAP = {
    "error":   {"color": "#fff", "bg": "#c00"},
    "success": {"color": "#fff", "bg": "#060"},
    "info":    {"color": "#fff", "bg": "#06c"},
}


def _normalize(value):
    """Normalize a status value to ``(kind, message)`` or ``None``."""
    if value is None or value == "":
        return None
    if isinstance(value, str):
        return ("info", value)
    kind, msg = value
    return (kind, str(msg))


class StatusMessage(Interaction):
    """Display-only single-line status and feedback area.

    Accepted value forms for ``set_value()`` / ``shell.update()``:

    - ``None`` or ``""``          → blank
    - ``str``                     → treated as ``("info", str)``
    - ``("error", "message")``    → error-styled
    - ``("success", "message")``  → success-styled
    - ``("info", "message")``     → info-styled

    ``get_value()`` returns ``(style, message)`` or ``None`` when blank.
    ``signal_return()`` always returns ``(False, None)``.
    """

    def __init__(self) -> None:
        self._value = None

    @property
    def is_focusable(self) -> bool:
        return False

    def render(self, context: RenderContext, focused: bool = False) -> list:
        if self._value is None:
            return [FillCmd(row=0, col=0, width=context.width, height=context.height)]
        kind, msg = self._value
        prefix = f"[{kind.upper()}] "
        text = (prefix + msg)[: context.width].ljust(context.width)
        style = _STYLE_MAP.get(kind)
        cmds = [WriteCmd(row=0, col=0, text=text, style=style)]
        if context.height > 1:
            cmds.append(
                FillCmd(row=1, col=0, width=context.width, height=context.height - 1)
            )
        return cmds

    def handle_key(self, key: str) -> tuple:
        return False, self._value

    def get_value(self):
        return self._value

    def set_value(self, value) -> None:
        self._value = _normalize(value)

    def signal_return(self) -> tuple:
        return False, None
