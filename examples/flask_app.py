"""
Example Flask application using panelmark-web.

Requires:
    pip install flask flask-sock

Run with:
    flask --app examples.flask_app run

Then open http://localhost:5000/ in a browser.
"""

import pathlib

from flask import Flask, render_template_string
from flask_sock import Sock

from panelmark import Shell
from panelmark.interactions.base import Interaction
from panelmark.draw import WriteCmd, FillCmd, RenderContext
from panelmark_html import render_document

from panelmark_web.server import handle_connection_sync
from panelmark_web.page import prepare_page


# ---------------------------------------------------------------------------
# Shell definition and interactions (same as fastapi_app.py)
# ---------------------------------------------------------------------------

SHELL_DEF = """
|===========|
|{40R $editor$ }|
|===========|
|{40R $status$ }|
|===========|
"""


class EchoEditor(Interaction):
    def __init__(self):
        self._text = ""

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
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)
sock = Sock(app)

_static_dir = pathlib.Path(__file__).parent.parent / "panelmark_web" / "static"


@app.get("/")
def index():
    shell = make_shell()
    page_html = render_document(shell)
    return prepare_page(page_html, ws_url="/ws", script_src="/static/client.js")


@app.get("/static/client.js")
def client_js():
    js_path = _static_dir / "client.js"
    return js_path.read_text(), 200, {"Content-Type": "application/javascript"}


@sock.route("/ws")
def ws_endpoint(ws):
    handle_connection_sync(ws, shell_factory=make_shell)
