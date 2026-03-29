"""
Example FastAPI application using panelmark-web.

Run with:
    uvicorn examples.fastapi_app:app --reload

Then open http://localhost:8000/ in a browser.
"""

import pathlib

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from panelmark import Shell
from panelmark.interactions.base import Interaction
from panelmark.draw import WriteCmd, FillCmd, RenderContext
from panelmark_html import render_document

from panelmark_web.server import handle_connection


# ---------------------------------------------------------------------------
# Shell definition and interactions
# ---------------------------------------------------------------------------

SHELL_DEF = """
|===========|
|{40R $editor$ }|
|===========|
|{40R $status$ }|
|===========|
"""


class EchoEditor(Interaction):
    """Simple line editor that echoes typed characters."""

    def __init__(self):
        self._text = ""
        self._cursor = 0

    def render(self, context: RenderContext, focused: bool = False) -> list:
        cursor_char = "_" if focused else " "
        display = self._text + cursor_char
        line = display[: context.width].ljust(context.width)
        return [
            FillCmd(row=0, col=0, width=context.width, height=context.height),
            WriteCmd(row=0, col=0, text=line, style={"reverse": focused} if focused else None),
        ]

    def handle_key(self, key: str) -> tuple:
        if key == "KEY_BACKSPACE" and self._text:
            self._text = self._text[:-1]
            return True, self._text
        if key == "KEY_ENTER":
            self._text = ""
            return True, self._text
        if len(key) == 1 and key.isprintable():
            self._text += key
            return True, self._text
        return False, self._text

    def get_value(self) -> str:
        return self._text

    def set_value(self, value) -> None:
        self._text = str(value)


class StatusBar(Interaction):
    """Display-only status bar."""

    def __init__(self):
        self._message = "Type something — press Escape to exit"

    @property
    def is_focusable(self) -> bool:
        return False

    def render(self, context: RenderContext, focused: bool = False) -> list:
        line = self._message[: context.width].ljust(context.width)
        return [WriteCmd(row=0, col=0, text=line, style={"reverse": True})]

    def handle_key(self, key: str) -> tuple:
        return False, self._message

    def get_value(self) -> str:
        return self._message

    def set_value(self, value) -> None:
        self._message = str(value)


def make_shell() -> Shell:
    shell = Shell(SHELL_DEF)
    shell.assign("editor", EchoEditor())
    shell.assign("status", StatusBar())
    shell.set_focus("editor")
    return shell


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI()

_static_dir = pathlib.Path(__file__).parent.parent / "panelmark_web" / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    shell = make_shell()
    page_html = render_document(shell)
    # Inject the client script before </body>
    script_tag = '<script src="/static/client.js"></script>'
    if "</body>" in page_html:
        page_html = page_html.replace("</body>", script_tag + "\n</body>")
    else:
        page_html += "\n" + script_tag
    return page_html


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    await handle_connection(websocket, shell_factory=make_shell)
