# TODO — panelmark-web

This file is a step-by-step work order for a coding agent. It converts the
current audit findings into an execution sequence that can be checked off as
work is completed.

The goal is to make `panelmark-web` truthful, usable, and internally coherent
without overreaching into features it does not yet implement.


## Working rules

- Treat this as a code review follow-up, not a greenfield design exercise.
- Fix correctness and contract issues before adding new features.
- Keep `panelmark-web` honest about its current scope.
- Do not claim `portable-library-compatible` status unless the required
  interactions/widgets are actually implemented.
- Prefer small, test-backed fixes over speculative refactors.


## Summary of current issues

The audit found these main problems:

- `DrawCommandRenderer` does not correctly handle overlapping draw commands.
- The documented FastAPI/Starlette async WebSocket integration likely does not
  match the actual framework API.
- Documentation does not clearly state that `panelmark-web` currently provides
  transport/runtime infrastructure, not a built-in interaction standard library.
- The browser client hardcodes the WebSocket URL to `/ws`.
- There is minor dead code in the server message path.
- There is no explicit interaction coverage matrix documenting what is and is
  not implemented.


## Phase 1 — Fix renderer correctness first

### 1.1 Repair overlapping draw-command handling

- [x] Read [panelmark_web/renderer.py](/home/sirrommit/claude_play/panelmark-web/panelmark_web/renderer.py).
- [x] Confirm the current bug:
  - `FillCmd` and `WriteCmd` are appended in row/column order
  - later commands do not overwrite earlier cells
  - overlapping command sequences therefore render incorrectly
- [x] Rework `_commands_to_html()` so later commands overwrite earlier cells at
  the cell level.
- [x] Preserve style information per cell or merged run.
- [x] Keep `CursorCmd` ignored.
- [x] Keep output HTML simple and deterministic.

Implementation guidance:

- Build a per-row cell buffer of length `context.width`.
- Apply commands in input order so later commands overwrite earlier content.
- After the buffer is built, collapse adjacent cells with the same style into
  `<span>` runs.
- Continue emitting one `<pre>` per visible row.

Required tests:

- [x] Add a test where `FillCmd` paints a row and a later `WriteCmd` overlays
  text at the same columns.
- [x] Add a test where two `WriteCmd`s overlap and the later one wins.
- [x] Add a test where styled text overwrites previously unstyled fill.
- [x] Keep existing renderer tests passing.


## Phase 2 — Fix async WebSocket integration

### 2.1 Verify the async handler contract

- [x] Read [panelmark_web/server.py](/home/sirrommit/claude_play/panelmark-web/panelmark_web/server.py).
- [x] Read the documented FastAPI usage in
  [docs/getting-started.md](/home/sirrommit/claude_play/panelmark-web/docs/getting-started.md).
- [x] Check whether FastAPI / Starlette `WebSocket` objects actually support the
  iterator/send API assumed by `handle_connection()`.

Expected likely outcome:

- The current docs and handler are mismatched.
- FastAPI usually exposes `receive_text()` and `send_text()`, not `async for raw
  in websocket` plus `await websocket.send(str)`.

### 2.2 Make the async handler truthful

Choose one of these paths and implement it consistently:

- Preferred: adapt `handle_connection()` to work directly with FastAPI /
  Starlette `WebSocket`.
- Acceptable fallback: keep the generic handler but add a framework adapter and
  update docs/examples to use that adapter.

Required outcome:

- [x] The documented FastAPI example must actually work with the public API.
- [x] The code and docs must describe the same async interface.

Required tests:

- [x] Add or update tests for the actual async handler contract.
- [x] If using adapters, test both the internal generic path and the adapter.


## Phase 3 — Clean up server message flow

### 3.1 Remove dead code in exit path

- [x] Remove the unused `exit_msg` variable in
  [panelmark_web/server.py](/home/sirrommit/claude_play/panelmark-web/panelmark_web/server.py).
- [x] Keep the behavior unchanged unless another test-driven fix is needed.

### 3.2 Review exit ordering

- [x] Verify the intended behavior when a key causes both:
  - a render/focus update
  - and an exit
- [x] Ensure the implementation and docs agree that render/focus is sent before
  exit if both exist.
- [x] Add or update tests if this ordering is intended API.


## Phase 4 — Make the scope explicit in docs

### 4.1 Add a top-level package README

There is currently no top-level `README.md` in `panelmark-web`.

- [x] Create [README.md](/home/sirrommit/claude_play/panelmark-web/README.md).

The README should clearly state:

- what `panelmark-web` is
- what it depends on from `panelmark-html`
- that it currently hosts arbitrary server-side `Interaction` objects through
  the core draw-command path
- that it does **not yet** ship a built-in portable interaction/widget library
- whether it currently claims only core renderer hosting behavior or some
  narrower helper/runtime status

Do not claim:

- full portable-library compatibility
- built-in support for standard interactions that are not implemented


### 4.2 Update `docs/getting-started.md`

- [x] Revise the opening section to clarify the current scope:
  - live transport/runtime + browser client
  - not yet a full built-in interaction library
- [x] Fix the FastAPI example so it matches the actual async handler API.
- [x] Keep the “define your own Interaction” example, because that matches the
  current implementation reality.
- [x] Add one short note explaining that current interaction support depends on
  the draw-command renderer and that more complex interactions may need further
  renderer work.


### 4.3 Update `docs/hook-contract-web.md`

- [x] Keep this doc focused on how `panelmark-web` uses `panelmark-html` hooks.
- [x] Add one brief note that panel body HTML is generated from core draw
  commands, not from a renderer-specific interaction catalog.
- [x] Do not imply that `panelmark-web` implements the full portable standard
  library today.


## Phase 5 — Document interaction coverage honestly

### 5.1 Add an interaction coverage section

- [x] In `README.md` or a dedicated doc, add a simple coverage matrix.

It should distinguish:

- implemented in `panelmark-web` today:
  - generic hosting of arbitrary `Interaction.render()` output via draw commands
- not implemented as built-in web interaction/library components:
  - `MenuReturn`
  - `NestedMenu`
  - `RadioList`
  - `CheckBox`
  - `TextBox`
  - `FormInput`
  - `DataclassFormInteraction`
  - `StatusMessage`
  - required widgets like `Alert`, `Confirm`, `InputPrompt`, `ListSelect`,
    `FilePicker`, `DataclassForm`
- additional not-yet-implemented “frequently implemented” interactions:
  - `MenuFunction`
  - `ListView`
  - `TreeView`
  - `TableView`
  - `DatePicker`

Required editorial stance:

- `panelmark-web` currently runs arbitrary draw-command interactions.
- It does not yet provide a blessed-style standard library equivalent.


## Phase 6 — Make WebSocket URL configurable

### 6.1 Remove the `/ws` hardcoding

- [x] Read [panelmark_web/static/client.js](/home/sirrommit/claude_play/panelmark-web/panelmark_web/static/client.js).
- [x] Replace the hardcoded `/ws` connection path with a configurable hook.

Recommended approaches:

- read from `data-pm-ws-url` on the shell root
- or read from a small global config object injected before `client.js`

Preferred approach:

- use a DOM-based hook on the shell root or a nearby container so the server can
  configure the URL without rebuilding the client script

Required outcome:

- [x] Default behavior can still use `/ws`.
- [x] Apps mounted under subpaths or alternate websocket routes can override it.

Required follow-up:

- [x] Update examples and docs to show the configuration mechanism.
- [x] Add tests if there is a testable JS hook path already in the repo; if not,
  document the mechanism clearly in examples/docs.


## Phase 7 — Re-check example truthfulness

### 7.1 FastAPI example

- [x] Update [examples/fastapi_app.py](/home/sirrommit/claude_play/panelmark-web/examples/fastapi_app.py)
  to match the real async API and configurable websocket path.
- [x] Make sure the static asset path logic is still correct.

### 7.2 Flask example

- [x] Update [examples/flask_app.py](/home/sirrommit/claude_play/panelmark-web/examples/flask_app.py)
  if websocket URL configuration changes.
- [x] Keep the example aligned with the docs.

### 7.3 Generated example output

- [x] Review whether files under `examples/out/` need regeneration.
- [x] If they are intended as checked-in artifacts, make sure they reflect the
  current behavior and docs.


## Phase 8 — Optional but recommended cleanup

### 8.1 Add explicit compatibility language

- [x] Add a short statement in docs about renderer-spec status.

Suggested wording direction:

- `panelmark-web` currently provides a live web session/runtime built on top of
  `panelmark-html`
- it does not yet claim full portable-library compatibility
- built-in standard interaction/widget support is future work

This should appear somewhere easy to find:

- top-level README preferred
- docs intro acceptable as backup


## Phase 9 — Implement required portable interactions

Do not start this phase until Phases 1 through 5 are complete. The current
package first needs to be truthful and technically correct as a generic live web
runtime before it can claim more.

Goal of this phase:

- add built-in web implementations for the required portable interaction set
- keep constructor signatures and value semantics aligned with
  `panelmark/docs/renderer-spec/portable-library.md`
- expose these interactions from `panelmark-web` as renderer-provided standard
  components rather than relying only on arbitrary custom `Interaction` classes

### 9.1 Create an interaction module structure

- [x] Add a package such as `panelmark_web/interactions/`.
- [x] Add `__init__.py` exports.
- [x] Keep naming aligned with the portable library:
  - `MenuReturn`
  - `NestedMenu`
  - `RadioList`
  - `CheckBox`
  - `TextBox`
  - `FormInput`
  - `DataclassFormInteraction`
  - `StatusMessage`

Implementation guidance:

- The implementation may be browser/web-native in shape.
- The API and semantics must match the portable-library spec even if the
  presentation differs from `panelmark-tui`.
- Reuse shared helpers where possible instead of duplicating selection/editing
  logic blindly across controls.


### 9.2 Implement required interactions one by one

Suggested order:

1. `StatusMessage`
2. `MenuReturn`
3. `RadioList`
4. `CheckBox`
5. `TextBox`
6. `NestedMenu`
7. `FormInput`
8. `DataclassFormInteraction`

For each interaction:

- [x] match constructor signature and parameter names
- [x] implement `get_value()` semantics from the portable-library spec
- [x] implement `set_value()` semantics from the portable-library spec
- [x] implement `signal_return()` semantics from the portable-library spec
- [x] add renderer tests
- [x] add session/integration coverage where the browser transport matters
- [x] document it

Required interaction-specific notes:

- `MenuReturn`
  - [x] current highlighted label via `get_value()`
  - [x] mapped payload via `signal_return()`
- `NestedMenu`
  - [x] support shorthand nested dict form
  - [x] support `Leaf(value)`
  - [x] preserve ordering
  - [x] enforce malformed-input rules from the spec
- `RadioList`
  - [x] selected mapped value via `get_value()`
  - [x] accept returns same selected value
- `CheckBox`
  - [x] full checked-state mapping via `get_value()`
  - [x] support `”multi”` and `”single”`
- `TextBox`
  - [x] support `wrap`
  - [x] support `readonly`
  - [x] support `enter_mode`
- `FormInput`
  - [x] support portable field types and validation contract
- `DataclassFormInteraction`
  - [x] introspect dataclass instance
  - [x] support action list semantics


### 9.3 Document interaction coverage after implementation

- [x] Update the interaction coverage section added in Phase 5.
- [x] Move each completed interaction from “not implemented” to “implemented.”
- [x] If any interaction still diverges from the portable spec, document the gap
  explicitly instead of silently claiming support.


## Phase 10 — Implement required portable widgets

Do not start this phase until the required interaction layer is in place or at
least far enough along that widget composition is practical.

Goal of this phase:

- add the required portable widget set
- keep calling syntax and return semantics aligned with the portable-library spec
- allow the browser renderer to present these widgets in a web-appropriate way

Required widgets from the current portable-library spec:

- `Alert`
- `Confirm`
- `InputPrompt`
- `ListSelect`
- `FilePicker`
- `DataclassForm`

### 10.1 Add widget module structure

- [x] Add a package such as `panelmark_web/widgets/`.
- [x] Add `__init__.py` exports for the required widgets.
- [x] Keep naming aligned with the portable library.

Implementation guidance:

- These do not need to mimic the TUI shape.
- They do need to preserve call syntax and return semantics.
- Prefer implementing widgets as compositions over the required interactions and
  shell/runtime mechanisms rather than as unrelated one-off code paths.


### 10.2 Implement widgets in recommended order

Suggested order:

1. `Alert`
2. `Confirm`
3. `InputPrompt`
4. `ListSelect`
5. `DataclassForm`
6. `FilePicker`

For each widget:

- [x] match portable constructor signature as closely as the current spec allows
- [x] implement portable return semantics
- [x] add tests
- [x] add browser/session integration coverage if applicable
- [x] document it

Widget-specific notes:

- `Alert`
  - [x] returns `True` when dismissed, `None` on cancel/close if applicable
- `Confirm`
  - [x] returns mapped button value
- `InputPrompt`
  - [x] returns entered text or `None`
- `ListSelect`
  - [x] support single and multi modes with specified semantics
- `DataclassForm`
  - [x] wrap `DataclassFormInteraction`
- `FilePicker`
  - [x] decide whether the first implementation uses browser-native file
    selection or a panelmark-managed picker
  - [x] whichever path is chosen, keep the portable return contract honest


### 10.3 Re-evaluate portability claim after widgets land

- [x] Only after required interactions and widgets are implemented, decide
  whether `panelmark-web` can claim `portable-library-compatible`.
- [x] If yes, add that claim explicitly in docs.
- [x] If not, document the remaining gaps clearly.


## Verification checklist

Before considering this work done, verify all of the following:

- [x] Overlapping draw commands now render correctly.
- [x] The async FastAPI/Starlette path is real, not just documented.
- [x] There is no dead unused exit-path code in `server.py`.
- [x] `panelmark-web` has a top-level `README.md`.
- [x] Docs no longer imply built-in interaction coverage that does not exist.
- [x] Interaction coverage is explicitly documented.
- [x] The websocket URL is configurable instead of being hardcoded to `/ws`.
- [x] Examples match the actual public API.
- [x] Tests cover the renderer overlap fix and the async server contract.
- [x] If Phase 9 was completed, required interactions match the portable spec.
- [x] If Phase 10 was completed, required widgets match the portable spec.


## Do not do in this pass

- Do not implement the full portable interaction/widget library in this cleanup.
- Do not redesign the `panelmark-html` hook contract.
- Do not add framework-specific abstractions beyond what is needed to make the
  documented FastAPI/Flask paths truthful.
- Do not silently widen the public API without updating docs and examples.
