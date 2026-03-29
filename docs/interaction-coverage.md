# Interaction Coverage

This document tracks which interactions and widgets from the
[panelmark portable-library spec](https://github.com/sirrommit/panelmark/blob/main/docs/renderer-spec/portable-library.md)
are implemented in `panelmark-web`.

---

## Current status

`panelmark-web` is a **core-renderer-compatible** runtime.  All eight required
portable interactions are now implemented in `panelmark_web.interactions`.
Required widgets are not yet implemented.

```python
from panelmark_web.interactions import (
    StatusMessage, MenuReturn, RadioList, CheckBox,
    TextBox, NestedMenu, FormInput, DataclassFormInteraction,
    Leaf,  # explicit leaf marker for NestedMenu
)
```

---

## Required interactions

These are required for `portable-library-compatible` status.

| Interaction | Status | Notes |
|-------------|--------|-------|
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

These modal widgets are also required for `portable-library-compatible` status.

| Widget | Status | Notes |
|--------|--------|-------|
| `Alert` | Not implemented | — |
| `Confirm` | Not implemented | — |
| `InputPrompt` | Not implemented | — |
| `ListSelect` | Not implemented | — |
| `DataclassForm` | Not implemented | — |
| `FilePicker` | Not implemented | — |

---

## Frequently implemented (optional)

These are not required but renderers that provide them should follow the
portable-library API contracts.

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

## What is implemented

The draw-command renderer handles:

| Draw command | Support |
|--------------|---------|
| `WriteCmd` | Full — text, position, style (bold, italic, underline, color, bg, reverse) |
| `FillCmd` | Full — rectangular fill with character and style |
| `CursorCmd` | Ignored — HTML renderers do not render a text cursor |

Any custom `Interaction` whose `render()` produces only `WriteCmd` and
`FillCmd` commands will work out of the box.  Interactions that rely on
renderer-specific behaviour beyond the draw-command set (e.g. native input
elements, browser file pickers) require additional work outside the current
scope of `panelmark-web`.

---

## Roadmap

Required widgets remain:

1. `Alert`
2. `Confirm`
3. `InputPrompt`
4. `ListSelect`
5. `DataclassForm`
6. `FilePicker`

Followed by frequently-implemented extras.

`portable-library-compatible` status will be evaluated after the required
widget set is implemented.

This document will be updated as items are completed.
