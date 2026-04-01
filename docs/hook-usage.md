> **Note:** This document is also mirrored at
> [panelmark-docs](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-web/hook-usage.md).

# panelmark-web DOM Hook Usage

This document describes how `panelmark-web` reads and writes the stable DOM
hooks defined in `panelmark-html/docs/hook-contract.md`.

---

## Hooks panelmark-web reads

### Locating panels

`client.js` uses `[data-pm-region]` to discover all named panels at startup
and on resize:

```js
const panels = document.querySelectorAll('[data-pm-region]');
panels.forEach(panel => {
    const region = panel.dataset.pmRegion;   // e.g. "sidebar"
    const body = panel.querySelector('.pm-panel-body');
    // measure body dimensions in character units
});
```

The `data-pm-region` attribute is a **stable** hook (see
`panelmark-html/docs/hook-contract.md`).

### Reading focus state at page load

`data-pm-focused` is emitted by `panelmark-html` as a static snapshot.
`panelmark-web` ignores it on load; the server sends a `render` message on
connect that carries the authoritative `focused` value for each panel.

---

## Hooks panelmark-web writes

### Panel body content — `.pm-panel-body`

On every `render` message from the server, `client.js` replaces the
`innerHTML` of the panel body:

```js
const body = panel.querySelector('.pm-panel-body');
body.innerHTML = update.html;
```

`panelmark-web` **never** replaces the `.pm-panel-body` element itself —
only its inner content.  This preserves the structural CSS that depends on
the element's presence in the flex layout.

### Focus state — `data-pm-focused`

After each `render` message, `client.js` updates `data-pm-focused` on the
panel element:

```js
panel.dataset.pmFocused = update.focused ? 'true' : 'false';
```

After a `focus`-only message (focus changed, no content change), all panels
are updated:

```js
document.querySelectorAll('[data-pm-region]').forEach(panel => {
    panel.dataset.pmFocused =
        (panel.dataset.pmRegion === focusedRegion) ? 'true' : 'false';
});
```

The `[data-pm-focused="true"]` CSS rule is provided by `panelmark-html`'s
base stylesheet (added in the focused-state-css PR).  `panelmark-web` does
not embed its own focused-state CSS.

---

## Hooks panelmark-web does not touch

| Hook | Reason |
|------|--------|
| `class="pm-panel-heading"` / `<header>` | Owned by `panelmark-html`; never modified |
| `data-pm-interaction` | Metadata only; read-only for `panelmark-web` |
| `data-pm-focusable` | Metadata only; focus routing happens server-side |
| `data-pm-empty` | Panels with this attribute have no server-side interaction; `panelmark-web` skips them |
| `.pm-split`, `.pm-split-h`, `.pm-split-v` | Structural; `panelmark-web` does not attach behavior to splits |

---

## Server-side rendering flow

The Python side (`Session`, `DrawCommandRenderer`) produces HTML strings from
the draw commands returned by `Interaction.render()`.  These are sent to the
browser as the `html` field in `render` update objects and assigned directly
to `.pm-panel-body` innerHTML.

The HTML is generated from the core `panelmark` draw-command types (`WriteCmd`,
`FillCmd`).  The built-in interactions in `panelmark_web.interactions` and
widgets in `panelmark_web.widgets` all render through this same draw-command
pipeline.  Any custom `Interaction` subclass whose `render()` method returns
standard draw commands will also work without additional renderer changes.

The HTML format produced by `DrawCommandRenderer` is intentionally simple:
one `<pre>` element per row, with inline `<span style="...">` elements for
styled text segments.  This format is an internal detail of `panelmark-web`
and is not part of the `panelmark-html` hook contract.
