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

    def process_key(self, key: str) -> tuple[str, list[dict]]:
        """Feed key to shell; return (result, list of render-update dicts).

        result is 'exit' or 'continue'.
        """
        result, value = self.shell.handle_key(key)
        updates = [self._render_region(name) for name in self.shell.dirty_regions]
        self.shell.mark_all_clean()
        return result, updates

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
