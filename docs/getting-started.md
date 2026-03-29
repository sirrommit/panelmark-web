# Getting Started with panelmark-web

`panelmark-web` is a live web renderer for the panelmark ecosystem.  It sits
on top of `panelmark-html`'s static structure and adds a real-time browser
interface: WebSocket-driven keyboard input, focus transitions, and live
rendering of interaction content inside panel bodies.

---

## Prerequisites

- Python 3.11+
- [`panelmark`](https://github.com/sirrommit/panelmark) installed
- [`panelmark-html`](https://github.com/sirrommit/panelmark-html) installed

---

## Install

```bash
pip install panelmark-web[fastapi]   # FastAPI / Starlette
pip install panelmark-web[flask]     # Flask + flask-sock
```

Or from source:

```bash
cd panelmark-web
pip install -e ".[fastapi]"   # or .[flask]
```

---

## Step 1 — Define your interactions

Implement the `Interaction` ABC from `panelmark`:

```python
from panelmark.interactions.base import Interaction
from panelmark.draw import WriteCmd, FillCmd, RenderContext


class EchoEditor(Interaction):
    def __init__(self):
        self._text = ""

    def render(self, context: RenderContext, focused: bool = False) -> list:
        line = (self._text + ("_" if focused else " "))[: context.width]
        line = line.ljust(context.width)
        return [
            FillCmd(row=0, col=0, width=context.width, height=context.height),
            WriteCmd(row=0, col=0, text=line, style={"reverse": True} if focused else None),
        ]

    def handle_key(self, key: str) -> tuple:
        if key == "KEY_BACKSPACE" and self._text:
            self._text = self._text[:-1]
            return True, self._text
        if len(key) == 1 and key.isprintable():
            self._text += key
            return True, self._text
        return False, self._text

    def get_value(self) -> str:
        return self._text

    def set_value(self, value) -> None:
        self._text = str(value)
```

---

## Step 2 — Define a shell and a factory

```python
from panelmark import Shell

SHELL_DEF = """
|===========|
|{40R $editor$ }|
|===========|
"""


def make_shell() -> Shell:
    shell = Shell(SHELL_DEF)
    shell.assign("editor", EchoEditor())
    shell.set_focus("editor")
    return shell
```

`shell_factory` is called once per WebSocket connection, so each browser tab
gets its own independent shell state.

---

## Step 3 — Wire up the server

```python
import pathlib
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from panelmark_html import render_document
from panelmark_web.server import handle_connection

app = FastAPI()

# Serve client.js from panelmark_web/static/
_static = pathlib.Path(__file__).parent / "panelmark_web" / "static"
app.mount("/static", StaticFiles(directory=str(_static)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    shell = make_shell()
    html = render_document(shell)
    # Inject the JS client
    script = '<script src="/static/client.js"></script>'
    if "</body>" in html:
        html = html.replace("</body>", script + "\n</body>")
    return html


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    await handle_connection(websocket, shell_factory=make_shell)
```

---

## Step 4 — Run

```bash
uvicorn myapp:app --reload
```

Open `http://localhost:8000/` in a browser.  The panel body populates on
connect and updates as you type.

---

## How it works

1. On page load, `client.js` opens a WebSocket to `/ws` and sends a `connect`
   message with each panel's character dimensions.
2. The server creates a `Shell`, renders all panels, and sends a `render`
   message with HTML for each panel body.
3. `client.js` sets each `.pm-panel-body` innerHTML and updates
   `data-pm-focused` on the panel element.
4. On every `keydown`, `client.js` sends a `key` message.  The server feeds
   it to `Shell.handle_key`, re-renders dirty panels, and sends back a
   `render` update.
5. When the shell signals exit (Escape / Ctrl+Q by default), the server sends
   an `exit` message and closes the connection.

---

## Key mapping

`client.js` maps browser `KeyboardEvent.key` values to panelmark key strings:

| Browser key | panelmark string |
|-------------|-----------------|
| `ArrowUp` | `KEY_UP` |
| `ArrowDown` | `KEY_DOWN` |
| `Enter` | `KEY_ENTER` |
| `Escape` | `\x1b` (exit signal) |
| `Tab` | `KEY_TAB` |
| `Shift+Tab` | `KEY_BTAB` |
| `Backspace` | `KEY_BACKSPACE` |
| Printable char | character itself |

The full mapping is in `panelmark_web/keymap.py`.

---

## Theming

`panelmark-html` exposes CSS custom properties for theming.  Override them
in your own stylesheet:

```css
:root {
  --pm-border-color: #333;
  --pm-focused-border-color: #00aaff;  /* focus outline colour */
  --pm-focused-border-width: 2px;
}
```

See `panelmark-html/docs/hook-contract.md` for the full property list.

---

## Flask / flask-sock

Use `handle_connection_sync` with `flask-sock`:

```python
from flask import Flask
from flask_sock import Sock
from panelmark_web.server import handle_connection_sync

app = Flask(__name__)
sock = Sock(app)

@sock.route("/ws")
def ws_endpoint(ws):
    handle_connection_sync(ws, shell_factory=make_shell)
```

`handle_connection_sync` expects `ws.receive()` to return `None` (or raise)
when the connection closes — which is exactly what `flask-sock` does.

## Full examples

- [`examples/fastapi_app.py`](../examples/fastapi_app.py) — FastAPI (async)
- [`examples/flask_app.py`](../examples/flask_app.py) — Flask + flask-sock (sync)
