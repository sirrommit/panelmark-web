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

- **Interactions** (`panelmark_web.interactions`): `StatusMessage`,
  `MenuReturn`, `RadioList`, `CheckBox`, `TextBox`, `NestedMenu`,
  `FormInput`, `DataclassFormInteraction`
- **Widgets** (`panelmark_web.widgets`): `Alert`, `Confirm`, `InputPrompt`,
  `ListSelect`, `DataclassForm`, `FilePicker`

Application code can also supply arbitrary custom `Interaction` objects — any
`render()` method that returns `WriteCmd` and `FillCmd` commands works out of
the box.

See [docs/interaction-coverage.md](docs/interaction-coverage.md) for the full
status matrix.

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

See [docs/getting-started.md](docs/getting-started.md) for a step-by-step
guide including interaction definition, server wiring, and browser setup.

See [examples/fastapi_app.py](examples/fastapi_app.py) and
[examples/flask_app.py](examples/flask_app.py) for working server examples.
