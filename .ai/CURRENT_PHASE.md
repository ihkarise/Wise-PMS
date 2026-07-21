# .ai/CURRENT_PHASE.md

**Phase:** Sprint 2 — Consultation Domain Model (backlog C3, ADR-001 Option C)
**Status:** Implemented → awaiting Product Owner review (not committed)
**Branch:** `claude/sprint-2-implementation` (based on `origin/main`)
**Updated:** 2026-07-20

## Goal
Give the Consultation Workspace a persistence spine as a **dedicated
`consultations` aggregate** (clinical document), 1:1 with a `visits` event, with a
`draft → in_progress → completed` lifecycle. Additive + reversible; `visits`
untouched. Per approved ADR-001 (Hybrid) and Sprint 2 planning.

## Delivered
- Migration `v0002_consultations` (additive, reversible; UNIQUE `visit_id`).
- `consultation` slice: `models.Consultation`, `repository` (sole `consultations`
  writer), `service` lifecycle state machine + audit + composition,
  `controller` create/open-draft on open, `view` status read-back.
- Tests: `test_consultation_domain.py` + `v0002` migration/model/regression
  updates. `python3 -m pytest -q` → 26 passing.

## NOT in scope (deferred)
- Live editors / autosave UI; Timeline `consultations` source row (M5, optional);
  Investigation/OCR/AI logic (seams only — no provider SDK imported); RBAC;
  digital-signature / lock enforcement (reserved states only).

## Verification
```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q     # expect 26 passing
```
