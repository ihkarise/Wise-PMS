# Sprint 2 — File Map (v2): Consultation Domain Model (Hybrid / ADR-001)

Legend: 🆕 new · ✏️ modify · 🔒 must NOT change
Supersedes v1 (Option A). Architecture per ADR-001.

## Application code

| File | Action | Change |
| ---- | ------ | ------ |
| `app/core/migrations/v0002_consultations.py` | 🆕 | `MIGRATION` v2: `up` = `CREATE TABLE IF NOT EXISTS consultations` + `idx_consultation_visit` (UNIQUE) + `idx_consultation_patient`; `down` = `DROP TABLE`/drop indexes (reversible) |
| `app/core/migrations/registry.py` | ✏️ | import + append `v0002` `MIGRATION` (sequential; `_validate` passes) |
| `app/modules/consultation/models.py` | 🆕 | `Consultation(RowModel)` — mirrors table |
| `app/modules/consultation/repository.py` | 🆕 | ALL `consultations` SQL: `create_draft`, `update`, `set_status`, `get`, `get_by_visit`, `open_draft_for_visit`, `for_patient` |
| `app/modules/consultation/service.py` | ✏️ | lifecycle API: `open_or_create_draft`, `save_consultation`, `complete_consultation`; extend `workspace_context`; `to_ai_context` seam; audit each mutation; no SQL |
| `app/modules/consultation/controller.py` | ✏️ | resolve/create draft on open; save/complete entry points (buttons stay disabled) |
| `app/modules/consultation/view.py` | ✏️ | read draft status into bottom bar; no new editable widgets |
| `app/modules/timeline/repository.py` | ✏️(optional) | add SELECT over `consultations` (kind='consultation') — read model; may defer |
| `app/core/database.py` | 🔒 | no change — `init_db()` already runs `migrate()` |
| `app/bootstrap.py` | 🔒 | no change — no new route |
| `app/modules/visits/*` | 🔒 | unchanged — visit = event only |
| `app/modules/{cases,patients,attachments,audit}/*`, `app/shared/*` | 🔒 | no change |

## Tests

| File | Action | Change |
| ---- | ------ | ------ |
| `tests/test_migrations.py` | ✏️ | `v0002` apply, idempotent re-apply, rollback-to-1, fresh-vs-migrated parity |
| `tests/test_models.py` | ✏️ | `Consultation` round-trips fields |
| `tests/test_consultation_domain.py` | 🆕 | repository + service: draft → save → complete; `visit_id UNIQUE` invariant; audit rows; drafts excluded from completed views |
| `tests/test_views_build.py` | ✏️ | workspace builds with a real consultation draft |
| `tests/test_router.py` | 🔒/✏️ | stay green; touch only if `_setup` needs a draft |
| `tests/test_regression.py` | ✏️(intended) | golden `TABLES:` line gains `consultations` — **one documented change**, not silent |

## Documentation & memory

| File | Action | Change |
| ---- | ------ | ------ |
| `docs/DATABASE.md` | ✏️ | `consultations` table + lifecycle + 1:1 invariant |
| `docs/DECISIONS.md` | ✏️ | new ADR entry referencing ADR-001; note intended golden change |
| `docs/CHANGELOG.md` | ✏️ | Sprint 2 entry + golden-line change note |
| `docs/modules/Consultation.md` | ✏️ | status → domain model (aggregate + lifecycle); seams |
| `docs/modules/Visits.md` | ✏️ | clarify visit = event; consultation = document (link ADR-001) |
| `docs/MASTER_BACKLOG.md` | ✏️ | advance C3 |
| `.ai/CURRENT_PHASE.md`, `NEXT_TASK.md`, `WORK_LOG.md` | ✏️ | Sprint 2 state |
| `docs/architecture-decisions/ADR-001-Consultation-Domain.md` | 🔒 | frozen — reference only |
| `docs/planning/SPRINT2_*.md` | 🔒 | these v2 plans — reference once approved |

## Expected diff
1 migration + full `consultation` slice (2 new, 3 modified) + 2 new/2 modified
tests + intended golden line + ~8 docs. Single commit, no PR until approved.
