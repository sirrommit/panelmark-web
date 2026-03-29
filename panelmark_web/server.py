"""Framework-agnostic WebSocket server handler for panelmark-web."""

import json

from .keymap import BROWSER_TO_PM
from .protocol import PROTOCOL_VERSION
from .session import Session


def _dispatch(session: Session, raw: str) -> tuple[str | None, str | None]:
    """Process one raw JSON message against a session.

    Returns (outgoing_json, action) where action is 'exit' or None.
    outgoing_json is None if no reply should be sent.
    """
    msg = json.loads(raw)
    match msg.get("type"):
        case "connect" | "resize":
            session.set_panel_sizes(msg.get("panels", []))
            updates = session.render_all()
            return (
                json.dumps({"v": PROTOCOL_VERSION, "type": "render", "updates": updates}),
                None,
            )
        case "key":
            raw_key = msg.get("key", "")
            pm_key = BROWSER_TO_PM.get(raw_key, raw_key)
            result, updates, focus_region = session.process_key(pm_key)

            if updates:
                reply = json.dumps(
                    {"v": PROTOCOL_VERSION, "type": "render", "updates": updates}
                )
            elif focus_region is not None:
                reply = json.dumps(
                    {"v": PROTOCOL_VERSION, "type": "focus", "region": focus_region}
                )
            else:
                reply = None

            if result == "exit":
                exit_msg = json.dumps({"v": PROTOCOL_VERSION, "type": "exit"})
                # Send render/focus update first (if any), then exit
                return reply, "exit"

            return reply, None
        case _:
            return (
                json.dumps(
                    {
                        "v": PROTOCOL_VERSION,
                        "type": "error",
                        "message": f"unknown message type: {msg.get('type')!r}",
                    }
                ),
                None,
            )


async def handle_connection(websocket, shell_factory):
    """Async WebSocket connection handler.

    websocket must support:
        await websocket.recv() -> str   -- raises or returns None on close
        await websocket.send(str)

    This matches the ``websockets`` library interface.  For FastAPI / Starlette
    use ``StarletteAdapter`` from ``panelmark_web.adapters``.

    shell_factory() -> Shell is called once per connection.
    """
    shell = shell_factory()
    session = Session(shell)

    while True:
        try:
            raw = await websocket.recv()
        except Exception:
            break
        if raw is None:
            break
        reply, action = _dispatch(session, raw)
        if reply is not None:
            await websocket.send(reply)
        if action == "exit":
            await websocket.send(json.dumps({"v": PROTOCOL_VERSION, "type": "exit"}))
            return


def handle_connection_sync(websocket, shell_factory):
    """Sync WebSocket connection handler (Flask / flask-sock).

    websocket must support:
        websocket.receive() -> str | None
            Returns the next message, or None when the connection is closed.
            Any exception raised is also treated as a closed connection.
        websocket.send(str)

    shell_factory() -> Shell is called once per connection.
    """
    shell = shell_factory()
    session = Session(shell)

    while True:
        try:
            raw = websocket.receive()
        except Exception:
            break
        if raw is None:
            break
        reply, action = _dispatch(session, raw)
        if reply is not None:
            websocket.send(reply)
        if action == "exit":
            websocket.send(json.dumps({"v": PROTOCOL_VERSION, "type": "exit"}))
            return
