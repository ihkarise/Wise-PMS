# Sprint 1 — Code-Quality Report

**Feature:** Consultation Workspace Skeleton (C1)
**Branch:** `claude/consultation-workspace-skeleton-qi1nfx`
**Date:** 2026-07-20 · Read-only audit (nothing modified)

---

## Automated scans

| Scan | Result |
| ---- | ------ |
| `TODO` / `FIXME` / `XXX` / `HACK` in `app/` | **none** |
| Unused imports in new files (`consultation/*`, `widgets.py`) | **none** — every import is used |
| Hex colour literals in `consultation/view.py`, `widgets.py` | **none** (rule 11 clean) |
| Raw `ft.ElevatedButton` / `OutlinedButton` / `TextField` in the view | **none** — all via `theme`/`widgets` |
| Secrets / passwords / tokens in the diff | **none** |
| New runtime dependencies | **none** (`requirements*.txt` unchanged) |
| `python3 -m py_compile` on all changed `.py` | **OK** |
| `python3 -m pytest -q` | **16 passed** |

---

## Findings (all Low severity)

### CQ-1 — Layout dimensions are magic numbers in the view 🟢
`view.py` hardcodes rail widths (`220`, `300`) and font/icon sizes (`11`, `13`,
`18`, `20`). Not drawn from `theme` constants.
*Assessment:* consistent with the existing `shell.py` (which also inlines sizes);
no theme token exists for these yet. Acceptable; consider a `theme.SPACING`/rail
tokens if the pattern spreads.

### CQ-2 — `visit_id` parsed but only decorates a status label 🟢
`controller.py` resolves the `new|\d+` visit sentinel and passes it to the view,
which uses it only for the bottom-bar text ("Draft consultation" vs "Visit #N").
*Assessment:* deliberate forward wiring toward spec §5 (draft/reopen). Harmless,
but currently near-dead. Keep only because the route shape is spec-mandated.

### CQ-3 — Third hand-rolled `_not_found` view 🟢
`consultation/view.py._not_found` duplicates the shape already in
`cases/view.py` and `patients/views/profile.py`.
*Assessment:* pre-existing pattern; a shared `widgets.not_found_view(...)` helper
would DRY all three. Non-blocking tech debt.

### CQ-4 — `workspace_context` fetches case without patient-ownership check 🟢
Returns `{patient, case}` independently; no assertion that `case.patient_id ==
patient_id`. See Risk R3. Harmless while read-only; must be closed before writes.

### CQ-5 — Test depth: no structural assertions 🟢
`test_views_build.py` asserts the view *builds* but not that all 7 sections / 5
right panels are present or that the 5 action buttons are `disabled=True`.
*Assessment:* matches the suite's existing "build-only" contract (event handlers
need a live Flet runtime). A lightweight structural assertion would raise
confidence; schedule with the editors sprint.

### CQ-6 — Full-view rebuild on section navigation 🟢
Each `?section=` click re-runs the controller → `workspace_context` (a DB read) →
rebuilds the whole view. See Risk R6 / L11. Fine at skeleton scale.

---

## Positives worth recording

- **True composition:** the module adds **no `models.py`, no `repository.py`, and
  no SQL** — exactly the "coordinating view" the spec asks for.
- **DRY helpers:** `disabled_button` and `placeholder_card` were extracted to
  `shared/widgets.py` rather than inlined (≈10 call sites), and `theme.card`
  gained an **optional, backward-compatible** `border` param.
- **Honest placeholders:** unbuilt panels/actions are visibly unfinished; nothing
  simulates working functionality.
- **Backward-compatible signature change:** `cases.view.save()` gained
  `then_workspace=False`; all existing call sites (`then_visit`, default) behave
  identically → regression golden unchanged.
- **Clean imports / no cycles:** `consultation.service` depends only downward on
  `patients`/`cases` services.

---

## Technical-debt ledger (carried forward, non-blocking)

| Item | Owner sprint |
| ---- | ------------ |
| Shared `not_found_view` helper (CQ-3) | Cleanup / next UI sprint |
| Patient↔case ownership guard (CQ-4 / R3) | Editors sprint (before writes) |
| Structural build assertions for the workspace (CQ-5) | Editors sprint |
| Section-level updates instead of full rebuild (CQ-6 / R6) | Performance pass |
| Theme tokens for rail widths/spacing (CQ-1) | Design-system pass |
