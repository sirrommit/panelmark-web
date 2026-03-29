"""Draw command to HTML renderer."""

import html
from panelmark.draw import DrawCommand, FillCmd, RenderContext, WriteCmd


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
        # swap fg/bg; default fg=inherit, bg=inherit
        fg, bg = bg or "var(--pm-fg,inherit)", fg or "var(--pm-bg,inherit)"
        parts.append(f"color:{fg};background:{bg}")
    else:
        if fg:
            parts.append(f"color:{fg}")
        if bg:
            parts.append(f"background:{bg}")
    return ";".join(parts)


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
        # Line-oriented approach: build a grid of (text, style) cells per row.
        # rows[r] = list of (col, text, style) segments
        rows: dict[int, list[tuple[int, str, dict | None]]] = {}

        for cmd in commands:
            if isinstance(cmd, WriteCmd):
                rows.setdefault(cmd.row, []).append((cmd.col, cmd.text, cmd.style))
            elif isinstance(cmd, FillCmd):
                for r in range(cmd.row, cmd.row + cmd.height):
                    rows.setdefault(r, []).append(
                        (cmd.col, cmd.char * cmd.width, cmd.style)
                    )
            # CursorCmd is ignored

        if not rows:
            return ""

        lines = []
        for r in range(max(rows) + 1):
            segs = rows.get(r)
            if not segs:
                lines.append("<pre></pre>")
                continue
            # Sort segments by column
            segs = sorted(segs, key=lambda s: s[0])
            line_html = '<pre style="margin:0;padding:0">'
            cursor = 0
            for col, text, style in segs:
                if col > cursor:
                    line_html += html.escape(" " * (col - cursor))
                css = _style_to_css(style)
                escaped = html.escape(text)
                if css:
                    line_html += f'<span style="{css}">{escaped}</span>'
                else:
                    line_html += escaped
                cursor = col + len(text)
            line_html += "</pre>"
            lines.append(line_html)

        return "\n".join(lines)
