"""Framework-agnostic WebSocket server handler for panelmark-web."""

import json

from .keymap import BROWSER_TO_PM
from .protocol import PROTOCOL_VERSION
from .session import Session


async def handle_connection(websocket, shell_factory):
    """Core connection handler.

    websocket must support:
        await websocket.recv() -> str
        await websocket.send(str)

    shell_factory() -> Shell is called once per connection.
    """
    shell = shell_factory()
    session = Session(shell)

    async for raw in websocket:
        msg = json.loads(raw)
        match msg.get("type"):
            case "connect":
                session.set_panel_sizes(msg.get("panels", []))
                updates = session.render_all()
                await websocket.send(
                    json.dumps(
                        {"v": PROTOCOL_VERSION, "type": "render", "updates": updates}
                    )
                )
            case "resize":
                session.set_panel_sizes(msg.get("panels", []))
                updates = session.render_all()
                await websocket.send(
                    json.dumps(
                        {"v": PROTOCOL_VERSION, "type": "render", "updates": updates}
                    )
                )
            case "key":
                raw_key = msg.get("key", "")
                pm_key = BROWSER_TO_PM.get(raw_key, raw_key)
                result, updates, focus_region = session.process_key(pm_key)
                if updates:
                    await websocket.send(
                        json.dumps(
                            {
                                "v": PROTOCOL_VERSION,
                                "type": "render",
                                "updates": updates,
                            }
                        )
                    )
                elif focus_region is not None:
                    await websocket.send(
                        json.dumps(
                            {
                                "v": PROTOCOL_VERSION,
                                "type": "focus",
                                "region": focus_region,
                            }
                        )
                    )
                if result == "exit":
                    await websocket.send(
                        json.dumps({"v": PROTOCOL_VERSION, "type": "exit"})
                    )
                    return
            case _:
                await websocket.send(
                    json.dumps(
                        {
                            "v": PROTOCOL_VERSION,
                            "type": "error",
                            "message": f"unknown message type: {msg.get('type')!r}",
                        }
                    )
                )
