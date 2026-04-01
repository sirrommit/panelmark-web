> **Note:** This document is also mirrored at
> [panelmark-docs](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-web/protocol.md).

# panelmark-web Protocol

The WebSocket message protocol between the `panelmark-web` server and browser client.
All messages are JSON. Every server-to-client message includes a version field `"v": 1`.

---

## Connection flow

1. Browser opens a WebSocket to the configured `ws_url`.
2. Browser sends a `connect` message with the character dimensions of each panel.
3. Server creates a `Shell` via `shell_factory()`, renders all panels, and replies with a
   `render` message containing HTML for each panel body.
4. Browser sets each `.pm-panel-body` innerHTML and updates `data-pm-focused` on panel
   elements.
5. On every `keydown`, the browser sends a `key` message.
6. Server feeds the key to `Shell.handle_key()`, re-renders dirty panels, and sends back a
   `render` update (or a `focus` message if only focus changed).
7. When the shell signals exit, the server sends an `exit` message and closes the
   connection.

---

## Client-to-server messages

### `connect`

Sent once when the WebSocket opens, and again on browser resize.

```json
{
  "type": "connect",
  "panels": [
    {"region": "menu",    "width": 20, "height": 10},
    {"region": "content", "width": 60, "height": 24}
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"connect"` | Message type |
| `panels` | array | One entry per named region, with character dimensions |
| `panels[].region` | string | Region name (matches `data-pm-region`) |
| `panels[].width` | int | Panel body width in characters |
| `panels[].height` | int | Panel body height in characters |

A `resize` message has the same shape as `connect` and is handled identically.

### `key`

Sent on each keydown event.

```json
{
  "type": "key",
  "key": "KEY_DOWN"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"key"` | Message type |
| `key` | string | panelmark key string (see [Key mapping](#key-mapping) below) |

---

## Server-to-client messages

### `render`

Sent after `connect` / `resize`, and after any key event that modifies panel content.

```json
{
  "v": 1,
  "type": "render",
  "updates": [
    {"region": "menu", "html": "<pre>...</pre>", "focused": true},
    {"region": "content", "html": "<pre>...</pre>", "focused": false}
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `v` | int | Protocol version (`1`) |
| `type` | `"render"` | Message type |
| `updates` | array | One entry per dirty region |
| `updates[].region` | string | Region name |
| `updates[].html` | string | HTML to assign to `.pm-panel-body` innerHTML |
| `updates[].focused` | bool | Whether this region is currently focused |

Only dirty regions are included. The browser replaces `.pm-panel-body` innerHTML and sets
`data-pm-focused` for each entry in `updates`.

### `focus`

Sent when focus changes but no panel content changed. The browser updates `data-pm-focused`
on all panel elements.

```json
{
  "v": 1,
  "type": "focus",
  "region": "content"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `v` | int | Protocol version (`1`) |
| `type` | `"focus"` | Message type |
| `region` | string | Name of the newly focused region |

### `exit`

Sent when the shell signals exit. The browser should close the WebSocket and may redirect
or show a "session ended" state.

```json
{
  "v": 1,
  "type": "exit"
}
```

### `error`

Sent when the server receives a message with an unrecognised type.

```json
{
  "v": 1,
  "type": "error",
  "message": "unknown message type: 'foo'"
}
```

---

## Key mapping

`client.js` maps browser `KeyboardEvent.key` values to panelmark key strings before
sending:

| Browser key | panelmark string |
|-------------|-----------------|
| `ArrowUp` | `KEY_UP` |
| `ArrowDown` | `KEY_DOWN` |
| `ArrowLeft` | `KEY_LEFT` |
| `ArrowRight` | `KEY_RIGHT` |
| `Enter` | `KEY_ENTER` |
| `Escape` | `\x1b` (triggers exit) |
| `Tab` | `KEY_TAB` |
| `Shift+Tab` | `KEY_BTAB` |
| `Backspace` | `KEY_BACKSPACE` |
| Printable char | character itself |

The full mapping is in `panelmark_web/keymap.py`.

---

## Panel body HTML format

The HTML assigned to `.pm-panel-body` by the browser is produced by
`DrawCommandRenderer` on the server. The format is one `<pre>` element per row, with
inline `<span style="...">` elements for styled text segments.

This format is an internal detail of `panelmark-web` — it is not part of the
`panelmark-html` hook contract and may change between versions.

---

## See also

- [Getting Started](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-web/getting-started.md)
- [Hook Usage](hook-usage.md)
- [panelmark-html Hook Contract](https://github.com/sirrommit/panelmark-html/blob/main/docs/hook-contract.md)
