"""Built-in portable interactions for panelmark-web.

All interactions in this package implement the portable-library-compatible API
defined in ``panelmark/docs/renderer-spec/portable-library.md``.

Required interactions
---------------------
.. list-table::
   :header-rows: 1

   * - Class
     - Description
   * - :class:`StatusMessage`
     - Display-only single-line status and feedback area
   * - :class:`MenuReturn`
     - Scrollable single-select list; returns mapped value on accept
   * - :class:`RadioList`
     - Single-select list with radio-button visuals
   * - :class:`CheckBox`
     - Scrollable checkbox list (multi-select and single-select modes)
   * - :class:`TextBox`
     - Text-input area with configurable wrap and Enter behaviour
   * - :class:`NestedMenu`
     - Hierarchical drill-down menu
   * - :class:`FormInput`
     - Structured form with typed fields and validation
   * - :class:`DataclassFormInteraction`
     - Structured form driven by a Python dataclass instance

Supporting types
----------------
:class:`Leaf`
    Explicit leaf marker for :class:`NestedMenu`.  Use ``Leaf(value)`` when a
    leaf payload is itself a ``dict``.
"""

from .checkbox import CheckBox
from .dataclass_form import DataclassFormInteraction
from .form_input import FormInput
from .list_view import ListView
from .menu_function import MenuFunction
from .menu_return import MenuReturn
from .nested_menu import Leaf, NestedMenu
from .radio_list import RadioList
from .status_message import StatusMessage
from .table_view import TableView
from .textbox import TextBox

__all__ = [
    "CheckBox",
    "DataclassFormInteraction",
    "FormInput",
    "Leaf",
    "ListView",
    "MenuFunction",
    "MenuReturn",
    "NestedMenu",
    "RadioList",
    "StatusMessage",
    "TableView",
    "TextBox",
]
