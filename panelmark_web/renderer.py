"""Draw command to HTML renderer."""

import html
from panelmark.draw import DrawCommand, FillCmd, RenderContext, WriteCmd

# Sentinel style value meaning "no style" (distinct from None which is also
# no style, but used as a typed default in the cell buffer).
_NO_STYLE: dict | None = None


def _style_to_css(style: dict | None) -> str:
    if not style:
        return ""
    parts = []
    if style.get("bold"):
        parts.append("font-weight:bold")
    if style.get("italic"):
        parts.append("font-style:italic")
    if style.get("underline"):
        parts.append("text-decoration:underline")
    fg = style.get("color")
    bg = style.get("bg")
    if style.get("reverse"):
        fg, bg = bg or "var(--pm-fg,inherit)", fg or "var(--pm-bg,inherit)"
        parts.append(f"color:{fg};background:{bg}")
    else:
        if fg:
            parts.append(f"color:{fg}")
        if bg:
            parts.append(f"background:{bg}")
    return ";".join(parts)


def _styles_equal(a: dict | None, b: dict | None) -> bool:
    """Return True if two style dicts produce the same CSS."""
    if a is b:
        return True
    if not a and not b:
        return True
    if not a or not b:
        return False
    return a == b


class DrawCommandRenderer:
    """Converts draw commands to HTML for a .pm-panel-body element."""

    def render_panel(
        self,
        interaction,
        context: RenderContext,
        focused: bool,
    ) -> str:
        """Return HTML string for .pm-panel-body contents."""
        commands = interaction.render(context, focused=focused)
        return self._commands_to_html(commands, context)

    def _commands_to_html(
        self, commands: list[DrawCommand], context: RenderContext
    ) -> str:
        # Build a per-row cell buffer.  Each cell is (char, style).
        # Commands are applied in input order; later commands overwrite earlier cells.
        # Rows outside [0, context.height) are clipped.
        # Columns outside [0, context.width) are clipped per cell.

        # cell_buf[row][col] = (char, style)
        cell_buf: dict[int, list[tuple[str, dict | None]]] = {}

        def _get_row(r: int) -> list[tuple[str, dict | None]]:
            if r not in cell_buf:
                cell_buf[r] = [(" ", None)] * context.width
            return cell_buf[r]

        for cmd in commands:
            if isinstance(cmd, WriteCmd):
                row = cmd.row
                if row < 0 or row >= context.height:
                    continue
                buf = _get_row(row)
                for i, ch in enumerate(cmd.text):
                    col = cmd.col + i
                    if 0 <= col < context.width:
                        buf[col] = (ch, cmd.style)

            elif isinstance(cmd, FillCmd):
                for row in range(cmd.row, cmd.row + cmd.height):
                    if row < 0 or row >= context.height:
                        continue
                    buf = _get_row(row)
                    for i in range(cmd.width):
                        col = cmd.col + i
                        if 0 <= col < context.width:
                            buf[col] = (cmd.char, cmd.style)

            # CursorCmd is ignored

        if not cell_buf:
            return ""

        lines = []
        for r in range(max(cell_buf) + 1):
            if r not in cell_buf:
                lines.append("<pre></pre>")
                continue

            buf = cell_buf[r]
            line_html = '<pre style="margin:0;padding:0">'

            # Collapse adjacent cells with the same style into runs
            run_start = 0
            while run_start < len(buf):
                run_style = buf[run_start][1]
                run_end = run_start + 1
                while run_end < len(buf) and _styles_equal(buf[run_end][1], run_style):
                    run_end += 1

                run_text = "".join(ch for ch, _ in buf[run_start:run_end])
                css = _style_to_css(run_style)
                escaped = html.escape(run_text)
                if css:
                    line_html += f'<span style="{css}">{escaped}</span>'
                else:
                    line_html += escaped

                run_start = run_end

            line_html += "</pre>"
            lines.append(line_html)

        return "\n".join(lines)
