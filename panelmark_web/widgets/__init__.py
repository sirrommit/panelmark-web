"""Built-in portable widgets for panelmark-web.

All widgets in this package implement the portable-library-compatible API
defined in ``panelmark/docs/renderer-spec/portable-library.md``.

Each widget is an ``Interaction`` subclass and can be assigned to a panel
region in a :class:`panelmark.Shell`.  Assign it, then rely on the WebSocket
session lifecycle to deliver the result via ``signal_return()``.

Required widgets
----------------
.. list-table::
   :header-rows: 1

   * - Class
     - Description
   * - :class:`Alert`
     - Informational popup; returns ``True`` on dismiss
   * - :class:`Confirm`
     - Confirmation dialog with caller-defined buttons
   * - :class:`InputPrompt`
     - Single-line text-entry dialog
   * - :class:`ListSelect`
     - Single or multi-select list dialog
   * - :class:`DataclassForm`
     - Modal form driven by a Python dataclass instance
   * - :class:`FilePicker`
     - Server-side filesystem browser

Web note
--------
The portable-library spec describes widgets as blocking (``widget.show(sh)``
returns after the user acts).  In ``panelmark-web`` the session is inherently
async — assign the widget to a panel region and the result arrives via
``signal_return()`` when the user acts.
"""

from .alert import Alert
from .confirm import Confirm
from .dataclass_form import DataclassForm
from .file_picker import FilePicker
from .input_prompt import InputPrompt
from .list_select import ListSelect

__all__ = [
    "Alert",
    "Confirm",
    "DataclassForm",
    "FilePicker",
    "InputPrompt",
    "ListSelect",
]
