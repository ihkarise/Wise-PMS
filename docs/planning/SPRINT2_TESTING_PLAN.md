# Sprint 2 — Testing Plan (v2): Consultation Domain Model (Hybrid / ADR-001)

Supersedes v1. Per ADR-001. Every milestone independently testable.

## Test matrix

| Area | File | Assertions |
| ---- | ---- | ---------- |
| Migration apply | `tests/test_migrations.py` | `v0002` brings DB v1→v2; `consultations` table exists (`PRAGMA table_info`); `idx_consultation_visit` UNIQUE + `idx_consultation_patient` present |
| Migration idempotency | `tests/test_migrations.py` | apply twice = no-op (`CREATE TABLE IF NOT EXISTS`) |
| Migration rollback | `tests/test_migrations.py` | `rollback_to(1)` drops table + indexes; re-apply works |
| Fresh vs migrated parity | `tests/test_migrations.py` | fresh-v2 schema == v1-migrated-to-v2 |
| Legacy safety | `tests/test_migrations.py` | seeded Sprint-1 DB → migrate → existing visits/cases/patients untouched, no data loss |
| Model | `tests/test_models.py` | `Consultation.from_row`/`to_dict` round-trips all fields |
| Repository/service lifecycle | `tests/test_consultation_domain.py` (new) | `create_draft` → `status='draft'`; `save_consultation` persists fields + bumps `updated_at`; `complete_consultation` → `'completed'`; `open_draft_for_visit` returns open draft |
| 1:1 invariant (R2) | `tests/test_consultation_domain.py` | second `create_draft` for same `visit_id` returns existing row; direct duplicate INSERT raises (UNIQUE) |
| Draft isolation (R3) | `tests/test_consultation_domain.py` | `status='draft'` excluded from completed/timeline views |
| Audit (R10) | `tests/test_consultation_domain.py` | start/save/complete each write an `audit_logs` row |
| No SQL in module | grep gate | `consultations` SQL only in `consultation/repository.py` |
| AI seam (R5) | grep gate | no `openai`/`google.generativeai`/`anthropic`/`ollama`/`mistralai`/`cohere` import anywhere |
| Router | `tests/test_router.py` | workspace route resolves (unchanged) |
| View build | `tests/test_views_build.py` | workspace builds with real consultation draft; case-not-found safe |
| Regression golden | `tests/test_regression.py` | diff = **only** new `consultations` in `TABLES:` + its indexes in `INDEXES:` — reviewed + documented |

## Hygiene checks (repeat from Sprint 1 audit)
- grep: no `view`/`controller` import inside any `service.py`/`repository.py`.
- grep: no provider SDK import outside future `ai_gateway`.
- import-sweep: all `app.modules.*` submodules import, no circular error.
- `python3 -m py_compile` on all changed files.

## Manual checklist (post-impl, on display)
- [ ] Open case → workspace opens on a **draft** consultation; bottom bar shows draft.
- [ ] Kill app mid-consult, reopen case → **same draft** (no duplicate).
- [ ] Draft does not appear as completed visit/consultation in Dashboard/timeline.
- [ ] Complete → status flips, one audit row.
- [ ] Legacy visits still open normally.
- [ ] `rollback_to(1)` → relaunch → app runs on Sprint-1 schema, no error.

## Exit criteria
`python3 -m pytest -q` green; golden change = only the intended `consultations`
line, documented; all migration + lifecycle + invariant + audit tests pass;
grep gates clean.
