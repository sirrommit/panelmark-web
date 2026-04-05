# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- PyPI packaging metadata (`pyproject.toml`, `LICENSE`, `AUTHORS`, keywords,
  classifiers).
- `MenuFunction`, `ListView`, and `TableView` frequently-implemented
  interactions (beyond the required portable library).
- Browser/session integration tests for the full portable interaction and
  widget library.
- `protocol.md` mirrored from panelmark-docs.

### Changed

- `hook-contract-web.md` renamed to `hook-usage.md`; mirror header added.
- `prepare_page()` now accepts a configurable WebSocket URL parameter.
- README updated: expanded "What it includes", added "Not Implemented" section,
  fixed links, added documentation table.

### Fixed

- Stale "no built-in library" claims removed from docs.
- Stale Roadmap section and portable-library spec link fixed in
  `interaction-coverage.md`.
- Renderer cell buffer ensures later draw commands overwrite earlier cells at
  the same position.
- Async handler updated to use `recv()`/`send()` interface; `StarletteAdapter`
  added.
- `license = { text = "MIT" }` form used to avoid hatchling metadata issue
  with PyPI upload.

---

## [0.1.0] — 2026-03-28

Initial release.

### Added

- WebSocket-based live renderer: browser sends key events, server dispatches
  through the panelmark shell, changed regions are re-rendered and pushed as
  HTML patches.
- `prepare_page(shell)` — injects the panelmark-html fragment and the client
  JS bootstrap into a host page.
- Client-side JS (`panelmark_web/static/panelmark.js`) handling WebSocket
  connection, key capture, and DOM patching.
- Sync handler (`handle_connection`) and async handler
  (`async_handle_connection`) for Flask and ASGI (Starlette/FastAPI) servers.
- `StarletteAdapter` for ASGI WebSocket compatibility.
- Exit-ordering guarantees: documented and tested clean shutdown sequence.
- All 8 required portable interactions: `MenuReturn`, `NestedMenu`,
  `RadioList`, `CheckBox`, `TextBox`, `FormInput`, `DataclassFormInteraction`,
  `StatusMessage`.
- All 6 required portable widgets: `Alert`, `Confirm`, `InputPrompt`,
  `ListSelect`, `FilePicker`, `DataclassForm`.
- Interaction coverage matrix (`docs/interaction-coverage.md`).
- Getting-started guide, hook-usage docs, and README.
- Snapshot tests and example application.

[Unreleased]: https://github.com/sirrommit/panelmark-web/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sirrommit/panelmark-web/releases/tag/v0.1.0
