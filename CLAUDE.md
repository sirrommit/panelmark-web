# Claude Instructions for panelmark-web

This repository is `panelmark-web`, the live web renderer for the panelmark ecosystem.

---

## Scope

The only repositories in scope for this work are:

- `/home/sirrommit/claude_play/panelmark` — read for API docs and contracts
- `/home/sirrommit/claude_play/panelmark-html` — read for DOM hook contract and CSS
- `/home/sirrommit/claude_play/panelmark-web` — the implementation target

`panelmark-tui` is **out of scope**. Do not read, search, or reference it.

Do not read `panelmark` or `panelmark-html` source code unless a doc gap is found.
All information needed is available from the documentation listed below.

---

## Repo initialisation

If this directory does not yet have a `.git` folder, initialise the repo first:

```
cd /home/sirrommit/claude_play/panelmark-web
git init
git remote add origin git@github.com:sirrommit/panelmark-web.git
```

Do this once. Skip if `.git` already exists.

---

## Implementation plan

Read this before starting any work:

- `/home/sirrommit/claude_play/PANELMARK_WEB_IMPLEMENTATION_PLAN.md`

All open questions in the plan are answered. Do not read `panelmark` or `panelmark-html`
source to re-answer them.

---

## Required documentation

All information needed to implement `panelmark-web` is in these doc files.
Read them instead of source code.

| What you need to know | Document | Section |
|-----------------------|----------|---------|
| Renderer contract overview | `panelmark/docs/renderer-spec/contract.md` | — |
| Key string format (`KEY_*` names, control chars, printable chars) | `panelmark/docs/renderer-spec/contract.md` | §"Key string format" |
| `Shell.handle_key` return values | `panelmark/docs/renderer-spec/contract.md` | §"Return value" |
| Dirty-region tracking (`dirty_regions`, `mark_all_clean()`, render loop) | `panelmark/docs/renderer-spec/contract.md` | §"Dirty-region tracking" |
| `Interaction` ABC (`render`, `handle_key`, `get_value`, `set_value`, `is_focusable`) | `panelmark/docs/custom-interactions.md` | — |
| `DrawCommand` types (`WriteCmd`, `FillCmd`, `CursorCmd`) and `RenderContext` | `panelmark/docs/draw-commands.md` | — |
| Stable DOM hooks (`data-pm-region`, `.pm-panel-body`, `data-pm-focused`, etc.) | `panelmark-html/docs/hook-contract.md` | — |
| CSS classes and custom properties provided by `panelmark-html` | `panelmark-html/docs/hook-contract.md` | §"CSS classes", §"CSS custom properties" |

---

## Dependency direction

- `panelmark-web` depends on `panelmark` and `panelmark-html`.
- Do not make changes to `panelmark` or `panelmark-html` unless a genuine contract gap
  is found. If a gap is found, stop and get explicit user approval before editing either
  upstream package.

---

## Validation

Every change must be tested before completion.

- Run the narrowest relevant test first.
- If the change is broader, run:
  ```
  cd /home/sirrommit/claude_play/panelmark-web
  PYTHONPATH=/home/sirrommit/claude_play/panelmark-web:/home/sirrommit/claude_play/panelmark:/home/sirrommit/claude_play/panelmark-html pytest -q
  ```
- For doc-only changes, state explicitly that no automated check exists.

---

## Git

Each completed update should be committed and pushed unless the user says not to.

- Remote: `origin git@github.com:sirrommit/panelmark-web.git`
- Default branch: `main`

Before pushing:

- Check `git status --short`
- Confirm only intended files changed
- Use a clear scoped commit message

---

## Working style

- Follow the phase order in the implementation plan. Complete one phase before starting
  the next unless the user directs otherwise.
- Make the smallest change that fully solves the task.
- Do not add features, abstractions, or error handling beyond what the plan specifies.
- Keep `panelmark-web` independent of `panelmark-tui` — no imports, no references.
