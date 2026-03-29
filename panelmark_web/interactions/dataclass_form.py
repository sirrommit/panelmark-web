"""DataclassFormInteraction — structured form driven by a dataclass instance."""

import dataclasses

from panelmark.interactions.base import Interaction
from panelmark.draw import FillCmd, RenderContext, WriteCmd

from ._helpers import scroll_offset


def _py_type_to_str(annotation) -> str:
    """Map a Python type annotation to a simple type name."""
    _map = {int: "int", float: "float", bool: "bool", str: "str"}
    return _map.get(annotation, "str")


def _coerce_field(raw: str, ftype: str):
    """Coerce *raw* edit string to *ftype*. Returns coerced value or *raw* on error."""
    try:
        if ftype == "int":
            return int(raw)
        if ftype == "float":
            return float(raw)
        if ftype == "bool":
            return raw.strip().lower() in ("true", "1", "yes")
    except (ValueError, TypeError):
        pass
    return raw


class DataclassFormInteraction(Interaction):
    """Structured form interaction driven by a Python dataclass instance.

    Field types and labels are derived from the dataclass's field annotations
    and names.

    ``get_value()``        → current field-state dict.
    ``set_value(mapping)`` → replace field-state dict.
    ``signal_return()``    → ``(True, action_result)`` when an action fires;
                             ``(False, None)`` otherwise.

    Parameters
    ----------
    dataclass_instance:
        An instance of a ``@dataclasses.dataclass`` class.
    actions:
        Optional list of action dicts, each with ``"label"`` and ``"action"``
        keys.  ``"action"`` is a callable that receives the current
        field-value dict and returns the shell exit value.
    on_change:
        Optional callable invoked with the current field-value dict after any
        field changes.
    """

    def __init__(self, dataclass_instance, actions=None, on_change=None) -> None:
        dc_fields = dataclasses.fields(dataclass_instance)
        self._field_names = [f.name for f in dc_fields]
        self._field_types = {
            f.name: _py_type_to_str(f.type) for f in dc_fields
        }
        self._values = {f.name: getattr(dataclass_instance, f.name) for f in dc_fields}
        self._actions = actions or []
        self._on_change = on_change

        # All navigable rows: fields + action buttons
        self._all_rows = self._field_names + [a["label"] for a in self._actions]

        self._cursor = 0
        self._edit_buf: dict[str, str] = {}
        self._submitted = False
        self._return_value = None

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, context: RenderContext, focused: bool = False) -> list:
        cmds = [FillCmd(row=0, col=0, width=context.width, height=context.height)]
        n = len(self._all_rows)
        if not n:
            return cmds
        offset = scroll_offset(self._cursor, context.height, n)
        for display_row in range(context.height):
            item_idx = offset + display_row
            if item_idx >= n:
                break
            row_name = self._all_rows[item_idx]
            is_active = focused and item_idx == self._cursor

            if row_name in self._field_names:
                value_str = self._edit_buf.get(
                    row_name, str(self._values.get(row_name, ""))
                )
                text = f"{row_name}: {value_str}"[: context.width].ljust(context.width)
                style = {"reverse": True} if is_active else None
            else:
                text = f"[ {row_name} ]"[: context.width].ljust(context.width)
                style = {"reverse": True} if is_active else {"bold": True}

            cmds.append(WriteCmd(row=display_row, col=0, text=text, style=style))
        return cmds

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def handle_key(self, key: str) -> tuple:
        n = len(self._all_rows)
        if not self._all_rows:
            return False, self.get_value()

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

        # Action button
        if current not in self._field_names:
            if key == "KEY_ENTER":
                for action in self._actions:
                    if action["label"] == current:
                        self._commit_edits()
                        result = action["action"](dict(self._values))
                        self._submitted = True
                        self._return_value = result
                        return True, self.get_value()
            return False, self.get_value()

        ftype = self._field_types.get(current, "str")

        # bool: toggle with space/enter
        if ftype == "bool":
            if key in (" ", "KEY_ENTER"):
                self._values[current] = not bool(self._values.get(current, False))
                if self._on_change:
                    self._on_change(dict(self._values))
                return True, self.get_value()
            return False, self.get_value()

        # Text-like field: edit buffer
        if current not in self._edit_buf:
            self._edit_buf[current] = str(self._values.get(current, ""))

        if key == "KEY_BACKSPACE":
            if self._edit_buf[current]:
                self._edit_buf[current] = self._edit_buf[current][:-1]
                return True, self.get_value()
            return False, self.get_value()

        if key == "KEY_ENTER":
            raw = self._edit_buf[current]
            self._values[current] = _coerce_field(raw, ftype)
            del self._edit_buf[current]
            if self._on_change:
                self._on_change(dict(self._values))
            if self._cursor < n - 1:
                self._cursor += 1
            return True, self.get_value()

        if len(key) == 1 and key.isprintable():
            self._edit_buf[current] += key
            return True, self.get_value()

        return False, self.get_value()

    def _commit_edits(self) -> None:
        """Commit all pending edit buffers before an action fires."""
        for name in list(self._edit_buf):
            ftype = self._field_types.get(name, "str")
            self._values[name] = _coerce_field(self._edit_buf[name], ftype)
            del self._edit_buf[name]

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
            return True, self._return_value
        return False, None
