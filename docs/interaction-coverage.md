# Interaction Coverage

This document tracks which interactions and widgets from the
[panelmark portable-library spec](https://github.com/sirrommit/panelmark/blob/main/docs/renderer-spec/portable-library.md)
are implemented in `panelmark-web`.

---

## Current status

All required portable interactions and widgets are implemented.
`panelmark-web` claims **`portable-library-compatible`** status with one noted
difference from the blocking-modal semantics described in the spec — see
[Web note](#web-note) below.

```python
# Interactions
from panelmark_web.interactions import (
    StatusMessage, MenuReturn, RadioList, CheckBox,
    TextBox, NestedMenu, FormInput, DataclassFormInteraction,
    Leaf,
)

# Widgets
from panelmark_web.widgets import (
    Alert, Confirm, InputPrompt, ListSelect,
    DataclassForm, FilePicker,
)
```

---

## Web note

The portable-library spec describes widgets as blocking: `widget.show(sh)`
returns only after the user acts.  In `panelmark-web` the session is
inherently async — there is no call that blocks a coroutine until a widget
is dismissed.

**Web-appropriate pattern:** assign the widget to a panel region and rely on
`signal_return()` to fire when the user acts.  The WebSocket session
lifecycle delivers the result automatically.

All constructor signatures, `get_value()` / `set_value()` / `signal_return()`
semantics, and return values match the portable spec exactly.

---

## Required interactions

| Interaction | Status | Module |
|-------------|--------|--------|
| `StatusMessage` | **Implemented** | `panelmark_web.interactions.StatusMessage` |
| `MenuReturn` | **Implemented** | `panelmark_web.interactions.MenuReturn` |
| `NestedMenu` | **Implemented** | `panelmark_web.interactions.NestedMenu` |
| `RadioList` | **Implemented** | `panelmark_web.interactions.RadioList` |
| `CheckBox` | **Implemented** | `panelmark_web.interactions.CheckBox` |
| `TextBox` | **Implemented** | `panelmark_web.interactions.TextBox` |
| `FormInput` | **Implemented** | `panelmark_web.interactions.FormInput` |
| `DataclassFormInteraction` | **Implemented** | `panelmark_web.interactions.DataclassFormInteraction` |

---

## Required widgets

| Widget | Status | Module |
|--------|--------|--------|
| `Alert` | **Implemented** | `panelmark_web.widgets.Alert` |
| `Confirm` | **Implemented** | `panelmark_web.widgets.Confirm` |
| `InputPrompt` | **Implemented** | `panelmark_web.widgets.InputPrompt` |
| `ListSelect` | **Implemented** | `panelmark_web.widgets.ListSelect` |
| `DataclassForm` | **Implemented** | `panelmark_web.widgets.DataclassForm` |
| `FilePicker` | **Implemented** (server-side filesystem browser) | `panelmark_web.widgets.FilePicker` |

---

## Frequently implemented (optional)

| Interaction / Widget | Status | Notes |
|----------------------|--------|-------|
| `MenuFunction` | Not implemented | — |
| `ListView` | Not implemented | — |
| `TreeView` | Not implemented | — |
| `TableView` | Not implemented | — |
| `DatePicker` | Not implemented | — |
| `Progress` | Not implemented | — |
| `Spinner` | Not implemented | — |
| `Toast` | Not implemented | — |

---

## Draw-command renderer

| Draw command | Support |
|--------------|---------|
| `WriteCmd` | Full — text, position, style (bold, italic, underline, color, bg, reverse) |
| `FillCmd` | Full — rectangular fill with character and style |
| `CursorCmd` | Ignored — HTML renderers do not render a text cursor |

Any custom `Interaction` whose `render()` produces only `WriteCmd` and
`FillCmd` commands will work out of the box.

---

## Roadmap

Frequently-implemented extras (`MenuFunction`, `ListView`, `TreeView`,
`TableView`, `DatePicker`, `Progress`, `Spinner`, `Toast`) are future work.
