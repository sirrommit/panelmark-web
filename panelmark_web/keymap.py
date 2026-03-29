"""Browser KeyboardEvent.key to panelmark key string mapping."""

BROWSER_TO_PM: dict[str, str] = {
    "ArrowUp": "KEY_UP",
    "ArrowDown": "KEY_DOWN",
    "ArrowLeft": "KEY_LEFT",
    "ArrowRight": "KEY_RIGHT",
    "Enter": "KEY_ENTER",
    "Escape": "\x1b",
    "Tab": "KEY_TAB",
    "Backspace": "KEY_BACKSPACE",
    "Delete": "KEY_DELETE",
    "Home": "KEY_HOME",
    "End": "KEY_END",
    "PageUp": "KEY_PGUP",
    "PageDown": "KEY_PGDN",
    "F1": "KEY_F1",
    "F2": "KEY_F2",
    "F3": "KEY_F3",
    "F4": "KEY_F4",
    "F5": "KEY_F5",
    "F6": "KEY_F6",
    "F7": "KEY_F7",
    "F8": "KEY_F8",
    "F9": "KEY_F9",
    "F10": "KEY_F10",
    "F11": "KEY_F11",
    "F12": "KEY_F12",
}

# Shift+Tab arrives as key="Tab" with shiftKey=True; the client sends "ShiftTab"
# as a convention to distinguish it.
BROWSER_TO_PM["ShiftTab"] = "KEY_BTAB"
