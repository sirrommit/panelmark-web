# Interaction Coverage

This document tracks which interactions and widgets from the
[panelmark portable-library spec](https://github.com/sirrommit/panelmark/blob/main/docs/renderer-spec/portable-library.md)
are implemented in `panelmark-web`.

---

## Current status

`panelmark-web` is a **core-renderer-compatible** runtime.  It hosts any
`Interaction` object whose `render()` method returns standard draw commands
(`WriteCmd`, `FillCmd`).  It does not currently ship built-in implementations
of the portable interaction or widget library.

Application code must supply its own interactions.  See
[docs/getting-started.md](getting-started.md) for how to define and wire them.

---

## Required interactions

These are required for `portable-library-compatible` status.

| Interaction | Status | Notes |
|-------------|--------|-------|
| `StatusMessage` | Not implemented | — |
| `MenuReturn` | Not implemented | — |
| `NestedMenu` | Not implemented | — |
| `RadioList` | Not implemented | — |
| `CheckBox` | Not implemented | — |
| `TextBox` | Not implemented | — |
| `FormInput` | Not implemented | — |
| `DataclassFormInteraction` | Not implemented | — |

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

Implementation of the required interactions and widgets is planned.  Suggested
order (from the project TODO):

1. `StatusMessage`
2. `MenuReturn`
3. `RadioList`
4. `CheckBox`
5. `TextBox`
6. `NestedMenu`
7. `FormInput`
8. `DataclassFormInteraction`

Followed by required widgets, then frequently-implemented extras.

This document will be updated as items are completed.
