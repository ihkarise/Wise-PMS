# Sprint 3 — Milestone Checklist: Narrative Editors + Autosave

**Status:** PLAN ONLY — execute only after Product Owner approval.
**Date:** 2026-07-21. **Single commit, no PR until asked.**

## M0 — Gate

- [ ] Product Owner approves **Narrative Editors + Autosave** as Sprint 3.
- [ ] Confirm scope: editors + autosave + Complete Visit only; right rail stays placeholders.

## M1 — Constants & controller (no UI yet)

- [ ] Add `AUTOSAVE_QUIET_MS = 900` to `app/config/constants.py`.
- [ ] `consultation/controller.py`: `open_workspace(pid, cid, user)` → `open_or_create_draft`.
- [ ] `controller.autosave(id, dirty_fields, user)` → `save_consultation` (with no-op guard).
- [ ] `controller.complete(id, user)` → flush pending, then `complete_consultation`.
- [ ] Controller holds **no SQL, no status logic** — delegates to service.

## M2 — Editable view

- [ ] `consultation/view.py`: add Examination to `_SECTIONS`.
- [ ] Replace placeholder section bodies with multiline `text_field` bound to
      consultation values (Complaint, History, Examination, Diagnosis, Remarks).
- [ ] Wire `on_change` → debounce → `controller.autosave`.
- [ ] Flush on: Complete Visit, section nav, route-away.
- [ ] Save-state pill: "Saving…" / "Saved HH:MM:SS".
- [ ] Enable **Complete Visit** → `controller.complete`.
- [ ] Read-only render when status ∈ {completed, amended, locked}.
- [ ] All controls via `shared/theme.py`/`widgets.py`; no hex literals (rule 11).

## M3 — Tests (green before docs)

- [ ] `test_consultation_domain.py`: autosave round-trip, draft→in_progress,
      no-op guard, coalesced fields, complete-then-edit-rejected, flush-before-complete.
- [ ] `test_views_build.py`: editable draft builds; completed builds read-only.
- [ ] `test_regression.py`: assert golden `TABLES:` line **UNCHANGED**.
- [ ] `python3 -m pytest -q` green (≥ 26 + new).

## M4 — Docs & memory (same commit)

- [ ] `docs/modules/Consultation.md` — live editors + autosave + flush contract.
- [ ] `docs/CLINICAL_WORKFLOW.md` — narrative-authoring loop.
- [ ] `docs/CHANGELOG.md` — Sprint 3 entry; note **no schema change** (golden unchanged).
- [ ] `docs/DECISIONS.md` — debounce/flush/no-op-guard decision (refs ADR-001 §4e).
- [ ] `docs/MASTER_BACKLOG.md` — advance C1; flag C6 fast-follow.
- [ ] `docs/KNOWN_LIMITATIONS.md` — no optimistic-locking UI yet.
- [ ] `.ai/CURRENT_PHASE.md`, `NEXT_TASK.md`, `WORK_LOG.md` — Sprint 3 state.

## M5 — Ship

- [ ] Manual checklist (Testing Plan) passes on fresh + legacy DB.
- [ ] Single commit on `claude/sprint-3-*` branch.
- [ ] Do **not** open a PR until explicitly asked.

## Definition of Done

A doctor writes a consultation by typing — autosaved, audited, status-tracked —
and seals it with Complete Visit, with **zero schema change** and every Sprint 2
test still green.
