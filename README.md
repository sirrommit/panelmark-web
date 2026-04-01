# panelmark-web

Live web session runtime for the [panelmark](https://github.com/sirrommit/panelmark) ecosystem.

---

## What it is

`panelmark-web` sits on top of `panelmark-html`'s static structure and adds a
real-time browser interface:

- A WebSocket server handler that drives a `panelmark.Shell` instance
- A draw-command-to-HTML renderer that populates `.pm-panel-body` elements
- A vanilla-JS browser client that relays keyboard input and applies DOM updates
- Framework adapters for FastAPI/Starlette (async) and Flask/flask-sock (sync)

Each browser tab corresponds to one `Shell` instance on the server.  The
WebSocket connection is the session lifetime.

---

## What it includes

Beyond the transport and rendering infrastructure, `panelmark-web` ships
built-in implementations of the full portable standard library:

- **Interactions** (`panelmark_web.interactions`): all 8 required portable
  interactions — `StatusMessage`, `MenuReturn`, `RadioList`, `CheckBox`,
  `TextBox`, `NestedMenu`, `FormInput`, `DataclassFormInteraction` — plus
  `MenuFunction`, `ListView`, `TableView`.
  See [portable library spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/portable-library.md)
  for the full normative specification.

- **Widgets** (`panelmark_web.widgets`): all 6 required portable widgets —
  `Alert`, `Confirm`, `InputPrompt`, `ListSelect`, `DataclassForm`, `FilePicker`.
  Web-specific note: widgets are async/non-blocking; see
  [overview](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-web/overview.md)
  for the async widget model.

Application code can also supply arbitrary custom `Interaction` objects — any
`render()` method that returns `WriteCmd` and `FillCmd` commands works out of
the box.

See [docs/interaction-coverage.md](docs/interaction-coverage.md) for the full
status matrix.

## What is not implemented

The following optional interactions and widgets from the portable library are
**not** implemented in this version:

| Item | Type | Notes |
|------|------|-------|
| `TreeView` | Interaction | Not implemented |
| `DatePicker` | Widget | Not implemented |
| `Progress` | Widget | Not implemented |
| `Spinner` | Widget | Not implemented |
| `Toast` | Widget | Not implemented |

See the [interaction coverage matrix](docs/interaction-coverage.md) for the full
status of every portable interaction, widget, and draw command.

---

## Dependencies

| Package | Role |
|---------|------|
| `panelmark` | Shell, Interaction ABC, draw commands |
| `panelmark-html` | Static page structure and base CSS |
| `fastapi` / `starlette` *(optional)* | Async ASGI server adapter |
| `flask` + `flask-sock` *(optional)* | Sync WSGI server adapter |

---

## Compatibility status

`panelmark-web` implements the **core renderer contract** and claims
**`portable-library-compatible`** status:

- shell hosting via WebSocket session
- draw-command execution (`WriteCmd`, `FillCmd`; `CursorCmd` ignored)
- focus routing and dirty-region tracking
- exit signal handling
- all 8 required portable interactions (`panelmark_web.interactions`)
- all 6 required portable widgets (`panelmark_web.widgets`)

**Web note:** The portable-library spec describes widgets as blocking
(`widget.show(sh)` returns after the user acts).  In `panelmark-web` the
session is async — assign the widget to a panel region and `signal_return()`
delivers the result when the user acts.  Constructor signatures and value
semantics match the spec exactly.

See [docs/interaction-coverage.md](docs/interaction-coverage.md) for the
full status matrix.

---

## Install

```bash
pip install panelmark-web[fastapi]   # FastAPI / Starlette
pip install panelmark-web[flask]     # Flask + flask-sock
```

---

## Quick start

See [docs/getting-started.md](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-web/getting-started.md) for a step-by-step
guide including interaction definition, server wiring, and browser setup.

See [examples/fastapi_app.py](examples/fastapi_app.py) and
[examples/flask_app.py](examples/flask_app.py) for working server examples.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-web/getting-started.md) | Step-by-step guide: interaction definition, FastAPI/Flask wiring, browser setup |
| [Interaction Coverage](docs/interaction-coverage.md) | Status matrix: every portable interaction, widget, and draw command |
| [WebSocket Protocol](docs/protocol.md) | Client→server and server→client message format; key mapping reference |
| [Hook Usage](docs/hook-usage.md) | How panelmark-web reads and writes the panelmark-html DOM hook contract |
| [DOM Hook Contract](https://github.com/sirrommit/panelmark-html/blob/main/docs/hook-contract.md) | Stable DOM interface defined by panelmark-html that this package depends on |
| [Portable Library Spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/portable-library.md) | Normative spec for all 8 portable interactions and 6 portable widgets |
| [Renderer Spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/overview.md) | Core renderer contract; compatibility levels; extension policy |
| [Shell Language](https://github.com/sirrommit/panelmark-docs/blob/main/docs/shell-language/overview.md) | ASCII-art layout syntax reference |
| [Ecosystem Overview](https://github.com/sirrommit/panelmark-docs/blob/main/docs/ecosystem.md) | How panelmark-web fits into the panelmark package ecosystem |
