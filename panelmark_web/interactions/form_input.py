"""FormInput — structured data-entry form with typed fields and validation."""

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd

from ._helpers import scroll_offset

_SUBMIT_LABEL = "[ Submit ]"


def _coerce(raw: str, ftype: str, options: list) -> tuple:
    """Try to coerce *raw* string to *ftype*. Returns ``(value, error_str|None)``."""
    try:
        if ftype == "str":
            return raw, None
        if ftype == "int":
            return int(raw), None
        if ftype == "float":
            return float(raw), None
        if ftype == "bool":
            return raw.strip().lower() in ("true", "1", "yes"), None
        if ftype == "choices":
            if raw in options:
                return raw, None
            return raw, f"Must be one of: {', '.join(options)}"
    except (ValueError, TypeError):
        return None, f"Invalid {ftype}"
    return raw, None


def _default_for_type(ftype: str):
    if ftype == "bool":
        return False
    if ftype in ("int", "float"):
        return 0
    return ""


class FormInput(Interaction):
    """Structured data-entry form.

    ``get_value()``        → current field-state dict (values coerced to their
                             declared types).
    ``set_value(mapping)`` → replace field-state dict.
    ``signal_return()``    → ``(True, field_dict)`` on successful Submit;
                             ``(False, None)`` otherwise.

    Navigation: ``KEY_UP`` / ``KEY_DOWN`` / ``KEY_TAB`` between rows.
    Editing: type to fill the edit buffer; ``KEY_BACKSPACE`` to delete;
    ``KEY_ENTER`` to commit a text field and advance.
    ``bool`` / ``choices`` fields cycle with ``Space`` / ``KEY_LEFT`` /
    ``KEY_RIGHT``.
    """

    def __init__(self, fields: dict) -> None:
        self._field_names = list(fields.keys())
        self._field_defs = dict(fields)
        # All navigable rows: one per field + a Submit row
        self._all_rows = self._field_names + ["__submit__"]

        # Initialise values from defaults
        self._values: dict = {}
        for name, defn in fields.items():
            ftype = defn.get("type", "str")
            default = defn.get("default", _default_for_type(ftype))
            self._values[name] = default

        self._cursor = 0
        self._edit_buf: dict[str, str] = {}  # name → in-progress edit string
        self._errors: dict[str, str] = {}
        self._submitted = False
        self._submit_value = None

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, context: RenderContext, focused: bool = False) -> list:
        cmds = [FillCmd(row=0, col=0, width=context.width, height=context.height)]
        n = len(self._all_rows)
        offset = scroll_offset(self._cursor, context.height, n)
        for display_row in range(context.height):
            item_idx = offset + display_row
            if item_idx >= n:
                break
            field_name = self._all_rows[item_idx]
            is_active = focused and item_idx == self._cursor

            if field_name == "__submit__":
                text = _SUBMIT_LABEL[: context.width].ljust(context.width)
                style = {"reverse": True} if is_active else {"bold": True}
            else:
                defn = self._field_defs[field_name]
                descriptor = defn.get("descriptor", field_name)
                value_str = self._edit_buf.get(
                    field_name, str(self._values.get(field_name, ""))
                )
                error = self._errors.get(field_name, "")
                if error:
                    label = f"{descriptor}: {value_str}  [{error}]"
                else:
                    label = f"{descriptor}: {value_str}"
                text = label[: context.width].ljust(context.width)
                style = {"reverse": True} if is_active else None

            cmds.append(WriteCmd(row=display_row, col=0, text=text, style=style))
        return cmds

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def handle_key(self, key: str) -> tuple:
        n = len(self._all_rows)

        if key == "KEY_UP":
            if self._cursor > 0:
                self._cursor -= 1
                return True, self.get_value()
            return False, self.get_value()

        if key in ("KEY_DOWN", "KEY_TAB"):
            if self._cursor < n - 1:
                self._cursor += 1
                return True, self.get_value()
            return False, self.get_value()

        current = self._all_rows[self._cursor]

        if current == "__submit__":
            if key == "KEY_ENTER":
                return self._try_submit()
            return False, self.get_value()

        defn = self._field_defs[current]
        ftype = defn.get("type", "str")
        options = defn.get("options", [])

        # bool: space/enter toggles
        if ftype == "bool":
            if key in (" ", "KEY_ENTER"):
                self._values[current] = not bool(self._values.get(current, False))
                return True, self.get_value()
            return False, self.get_value()

        # choices: cycle with space/arrows
        if ftype == "choices":
            cur_val = self._values.get(current, options[0] if options else "")
            if key in (" ", "KEY_LEFT", "KEY_RIGHT") and options:
                idx = options.index(cur_val) if cur_val in options else 0
                if key == "KEY_LEFT":
                    idx = (idx - 1) % len(options)
                else:
                    idx = (idx + 1) % len(options)
                self._values[current] = options[idx]
                return True, self.get_value()
            return False, self.get_value()

        # Text-like fields: edit buffer
        if current not in self._edit_buf:
            self._edit_buf[current] = str(self._values.get(current, ""))

        if key == "KEY_BACKSPACE":
            if self._edit_buf[current]:
                self._edit_buf[current] = self._edit_buf[current][:-1]
                self._errors.pop(current, None)
                return True, self.get_value()
            return False, self.get_value()

        if key == "KEY_ENTER":
            coerced, error = _coerce(self._edit_buf[current], ftype, options)
            if error:
                self._errors[current] = error
            else:
                self._values[current] = coerced
                self._errors.pop(current, None)
                del self._edit_buf[current]
                if self._cursor < n - 1:
                    self._cursor += 1
            return True, self.get_value()

        if len(key) == 1 and key.isprintable():
            self._edit_buf[current] += key
            self._errors.pop(current, None)
            return True, self.get_value()

        return False, self.get_value()

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------

    def _try_submit(self) -> tuple:
        # Commit pending edit buffers
        for name in list(self._edit_buf):
            defn = self._field_defs[name]
            ftype = defn.get("type", "str")
            options = defn.get("options", [])
            coerced, error = _coerce(self._edit_buf[name], ftype, options)
            if error:
                self._errors[name] = error
            else:
                self._values[name] = coerced
                del self._edit_buf[name]

        # Validate all fields
        for name in self._field_names:
            defn = self._field_defs[name]
            ftype = defn.get("type", "str")
            value = self._values.get(name)
            if defn.get("required"):
                if ftype != "bool" and (value is None or value == ""):
                    self._errors[name] = "Required"
                    continue
            validator = defn.get("validator")
            if validator and value is not None:
                result = validator(value)
                if result is not True:
                    self._errors[name] = str(result)

        if self._errors:
            return True, self.get_value()

        self._submitted = True
        self._submit_value = dict(self._values)
        return True, self.get_value()

    # ------------------------------------------------------------------
    # Value contract
    # ------------------------------------------------------------------

    def get_value(self) -> dict:
        return dict(self._values)

    def set_value(self, mapping) -> None:
        for name in self._field_names:
            if name in mapping:
                self._values[name] = mapping[name]
                self._edit_buf.pop(name, None)

    def signal_return(self) -> tuple:
        if self._submitted:
            return True, self._submit_value
        return False, None
