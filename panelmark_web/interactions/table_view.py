"""TableView — multi-column read-only display table with a sticky header."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd

from ._helpers import scroll_offset


def _format_row(values: list, widths: list[int]) -> str:
    """Join *values* into a fixed-width row string using *widths* per column."""
    cells = []
    for i, w in enumerate(widths):
        val = str(values[i]) if i < len(values) else ""
        cells.append(val[:w].ljust(w))
    return " ".join(cells)


class TableView(Interaction):
    """Multi-column read-only display table with a sticky header row.

    The first visible row is always the column header; data rows scroll
    beneath it while keeping the cursor visible.

    ``get_value()``      → 0-based active row index (``int``).
    ``set_value(index)`` → move the cursor to the given row index.
    ``signal_return()``  → always ``(False, None)``.

    Parameters
    ----------
    columns:
        ``[(header_label, width_in_chars), ...]`` — column definitions.
        Each column is rendered at exactly *width_in_chars* characters,
        truncating or padding as needed.
    rows:
        List of rows; each row is a list of values (converted to ``str``
        during render).

    Keys: ``KEY_UP`` / ``KEY_DOWN`` to move the cursor.
    """

    def __init__(self, columns: list, rows: list) -> None:
        self._columns = list(columns)   # [(header, width), ...]
        self._rows = list(rows)
        self._cursor: int = 0

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, context: RenderContext, focused: bool = False) -> list:
        cmds = [FillCmd(row=0, col=0, width=context.width, height=context.height)]
        if not self._columns:
            return cmds

        headers = [h for h, _ in self._columns]
        widths = [w for _, w in self._columns]

        # Row 0: sticky header
        header_text = _format_row(headers, widths)[: context.width].ljust(context.width)
        cmds.append(WriteCmd(row=0, col=0, text=header_text, style={"bold": True}))

        if not self._rows or context.height < 2:
            return cmds

        # Rows 1+: scrollable data
        data_height = context.height - 1
        offset = scroll_offset(self._cursor, data_height, len(self._rows))

        for display_row in range(data_height):
            idx = offset + display_row
            if idx >= len(self._rows):
                break
            row_text = _format_row(self._rows[idx], widths)[: context.width].ljust(
                context.width
            )
            style = {"reverse": True} if (focused and idx == self._cursor) else None
            cmds.append(
                WriteCmd(row=display_row + 1, col=0, text=row_text, style=style)
            )

        return cmds

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def handle_key(self, key: str) -> tuple:
        if not self._rows:
            return False, self.get_value()
        if key == "KEY_UP" and self._cursor > 0:
            self._cursor -= 1
            return True, self.get_value()
        if key == "KEY_DOWN" and self._cursor < len(self._rows) - 1:
            self._cursor += 1
            return True, self.get_value()
        return False, self.get_value()

    # ------------------------------------------------------------------
    # Value contract
    # ------------------------------------------------------------------

    def get_value(self) -> int:
        return self._cursor

    def set_value(self, index) -> None:
        if self._rows and 0 <= index < len(self._rows):
            self._cursor = index

    def signal_return(self) -> tuple:
        return False, None
