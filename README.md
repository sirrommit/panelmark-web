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

## What it is not

**`panelmark-web` does not yet ship a built-in interaction or widget library.**

It provides the transport and rendering infrastructure to host any
`panelmark.Interaction` object in a browser.  The interactions themselves —
`MenuReturn`, `TextBox`, `RadioList`, `CheckBox`, `FormInput`, and so on — are
defined in the [panelmark portable-library spec](https://github.com/sirrommit/panelmark/blob/main/docs/renderer-spec/portable-library.md)
but are not yet implemented in this package.

The current package hosts arbitrary server-side `Interaction` objects through
the core draw-command path.  Application code must supply its own interactions,
or wait for a future release that implements the portable standard library.

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

`panelmark-web` currently implements the **core renderer contract** defined in
`panelmark/docs/renderer-spec/contract.md`:

- shell hosting via WebSocket session
- draw-command execution (`WriteCmd`, `FillCmd`; `CursorCmd` ignored)
- focus routing and dirty-region tracking
- exit signal handling

It does **not** currently claim `portable-library-compatible` status.  That
requires a built-in implementation of the required interactions and widgets,
which is planned for a future phase.

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
