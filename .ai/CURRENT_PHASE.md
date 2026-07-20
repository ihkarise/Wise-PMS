# .ai/CURRENT_PHASE.md

**Phase:** Sprint 1 — Consultation Workspace Skeleton (backlog C1)
**Status:** Complete → committed; awaiting Product Owner approval before Sprint 2
**Branch:** `claude/consultation-workspace-skeleton-qi1nfx`
**Updated:** 2026-07-20

## Goal
Build the **structural foundation** of the Consultation Workspace — the central
screen of WiseOS Health. Framework only: layout, navigation, and honest
placeholders. **No** business logic, OCR, AI, Protocol Engine, WhatsApp,
Billing, Dispensing, or Investigation processing.

## Scope (this sprint)
- New `app/modules/consultation/` vertical slice — **composition-only** (no
  table, no `models.py`, no `repository.py`, no SQL):
  - `service.py` — `workspace_context(pid, cid)`, read-only composition over
    `patients`/`cases` services.
  - `controller.py` — `workspace_controller` + `ROUTES`; parses the optional
    draft-visit sentinel and `?section=` deep-link.
  - `view.py` — the workspace layout: shell header · left section-nav rail ·
    center section cards · right placeholder panels · bottom status/action bar.
- Layout regions: Top header (shared shell) · Left sidebar (section nav) · Main
  workspace (Patient Summary, Chief Complaint, History, Diagnosis, Prescription,
  Remarks, Follow-up) · Right panel (Timeline, Investigations, OCR, Protocol
  Suggestions, AI Assistant — placeholders) · Bottom bar (Print, Invoice,
  Dispense, WhatsApp, Complete Visit — disabled placeholders).
- Shared additions: `widgets.disabled_button`, `widgets.placeholder_card`,
  optional `theme.card(border=…)`.
- Navigation: `bootstrap.py` registers the routes; `cases/view.py` gains a
  **Start Consultation** entry point.
- Tests: router-contract + view-build extended to cover the new route/view.

## Explicitly NOT in scope
- No persistence/autosave, no visit finalization, no feeder-module calls.
- No OCR, AI, Protocol Engine, WhatsApp, Billing, Dispensing, Investigation.
- No new tables and **no migration** — Sprint 0 DB infrastructure untouched.

## Definition of done
- `python3 -m pytest -q` green (**16 passing**; regression golden byte-identical).
- Workspace opens, navigation works, panels render, disabled buttons render.
- Every affected doc updated in the same commit. Committed + pushed; **no PR**.

## Verification
```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q     # expect 16 passing
```

See [`NEXT_TASK.md`](./NEXT_TASK.md) for the proposed next sprint.
