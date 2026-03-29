"""Session model: one Shell instance per browser tab."""

from panelmark.draw import RenderContext
from panelmark.shell import Shell

from .renderer import DrawCommandRenderer

_DEFAULT_WIDTH = 80
_DEFAULT_HEIGHT = 24
_CAPABILITIES = frozenset({"color", "256color", "truecolor", "unicode"})


class Session:
    """One Shell instance per browser tab."""

    def __init__(self, shell: Shell):
        self.shell = shell
        self.panel_sizes: dict[str, tuple[int, int]] = {}
        self._renderer = DrawCommandRenderer()

    def set_panel_sizes(self, panels: list[dict]) -> None:
        """Update cached dimensions from a connect or resize message."""
        for p in panels:
            region = p.get("region")
            width = p.get("width", _DEFAULT_WIDTH)
            height = p.get("height", _DEFAULT_HEIGHT)
            if region:
                self.panel_sizes[region] = (int(width), int(height))

    def process_key(self, key: str) -> tuple[str, list[dict], str | None]:
        """Feed key to shell; return (result, render_updates, focus_region).

        result        -- 'exit' or 'continue'
        render_updates -- list of {region, html, focused} dicts for dirty regions
        focus_region  -- focused region name when focus changed but no regions
                         were dirty (i.e. only a focus message is needed);
                         None otherwise
        """
        focus_before = self.shell.focus
        result, _value = self.shell.handle_key(key)
        dirty = self.shell.dirty_regions
        updates = [self._render_region(name) for name in dirty]
        self.shell.mark_all_clean()

        # If focus changed but nothing was rendered, surface a focus-only signal
        focus_region = None
        if not updates and self.shell.focus != focus_before:
            focus_region = self.shell.focus

        return result, updates, focus_region

    def render_all(self) -> list[dict]:
        """Render every named panel; used on initial connect."""
        updates = [
            self._render_region(name) for name in self.shell.interactions
        ]
        self.shell.mark_all_clean()
        return updates

    def _render_region(self, region: str) -> dict:
        """Return {region, html, focused} for one panel."""
        interaction = self.shell.interactions.get(region)
        if interaction is None:
            return {"region": region, "html": "", "focused": False}

        width, height = self.panel_sizes.get(region, (_DEFAULT_WIDTH, _DEFAULT_HEIGHT))
        context = RenderContext(
            width=width,
            height=height,
            capabilities=_CAPABILITIES,
        )
        focused = self.shell.focus == region
        html = self._renderer.render_panel(interaction, context, focused=focused)
        return {"region": region, "html": html, "focused": focused}
