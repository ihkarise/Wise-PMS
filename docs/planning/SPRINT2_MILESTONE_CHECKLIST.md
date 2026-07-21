# Sprint 2 — Milestone Checklist (v2): Consultation Domain Model (Hybrid / ADR-001)

Supersedes v1. Per ADR-001. Each milestone independently testable; `main` stays
green. Build in order. One commit at end (or per-milestone), no PR until approval.

---

## Milestone 1 — Database schema (`consultations` table)
- [ ] `app/core/migrations/v0002_consultations.py`: `up` = `CREATE TABLE IF NOT
      EXISTS consultations` (fields per Technical Plan §3) + `idx_consultation_visit`
      (UNIQUE on `visit_id`) + `idx_consultation_patient`.
- [ ] Reversible `down` = `DROP TABLE IF EXISTS consultations` + drop indexes.
- [ ] Append `MIGRATION` to `registry.MIGRATIONS` (sequential; `_validate` passes).
- **Test:** apply, idempotent re-apply, rollback-to-1, fresh-vs-migrated parity,
  legacy-safety. Golden `TABLES:` gains `consultations` — documented.
- **Shippable alone:** schema only; no reader yet.

## Milestone 2 — Models + Repository (`consultation/`)
- [ ] `consultation/models.py`: `Consultation(RowModel)`.
- [ ] `consultation/repository.py`: `create_draft`, `update`, `set_status`, `get`,
      `get_by_visit`, `open_draft_for_visit`, `for_patient`. Only file with
      `consultations` SQL.
- **Test:** CRUD; `open_draft_for_visit` returns open draft; UNIQUE blocks duplicate.

## Milestone 3 — Service + lifecycle (`consultation/service.py`)
- [ ] `open_or_create_draft`, `save_consultation`, `complete_consultation`; extend
      `workspace_context`; `to_ai_context` seam (context dict only, no provider).
- [ ] Audit each mutation (start/save/complete).
- **Test:** `test_consultation_domain.py` — draft→save→complete; 1:1 invariant;
  drafts excluded from completed views; audit rows written; AI-seam grep clean.

## Milestone 4 — Controller + view read-back
- [ ] Controller resolves/creates draft on workspace open; save/complete entry
      points wired to service (buttons remain disabled).
- [ ] View shows draft status in bottom bar; no new editors.
- **Test:** `test_views_build.py` builds with real draft; `test_router.py` green.

## Milestone 5 — Timeline read-model compatibility (optional / low-risk)
- [ ] `timeline/repository.py`: add SELECT over `consultations`
      (kind='consultation'); drafts excluded.
- **Test:** timeline includes completed consultations, excludes drafts. May defer
  to a follow-up without blocking M1–M4.

## Milestone 6 — Tests consolidate + guard
- [ ] Full suite green: migrations, models, consultation-domain, router, views.
- [ ] Regression golden diff = **only** intended `consultations` line, reviewed.
- [ ] Layering + AI-seam greps + `py_compile` clean.

## Milestone 7 — Documentation & memory
- [ ] `DATABASE.md`, `DECISIONS.md` (ref ADR-001), `CHANGELOG.md`,
      `docs/modules/{Consultation,Visits}.md`, `MASTER_BACKLOG.md` (C3).
- [ ] `.ai/CURRENT_PHASE.md`, `NEXT_TASK.md`, `WORK_LOG.md`.
- [ ] Broken-link scan clean.

---

## Definition of done
- [ ] M1–M4 + M6–M7 complete (M5 optional); each independently tested.
- [ ] `python3 -m pytest -q` green; golden change intended + documented.
- [ ] `v0002` reversible; fresh == migrated; legacy DB opens, no data loss.
- [ ] Only `consultation/repository.py` writes `consultations`; no provider SDK
      imported; `visits/*` untouched.
- [ ] No RBAC, no Settings, no live editors, no feeder logic.
- [ ] Committed to Sprint 2 feature branch; **no PR** — await Product Owner.

## Sequencing note
M1–M3 = the domain aggregate (all risk: migration + persistence + invariant).
M4–M7 = integration/read-back/docs (low risk). Minimum shippable slice = M1–M3 + M6.
