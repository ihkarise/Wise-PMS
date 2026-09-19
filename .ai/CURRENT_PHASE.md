# .ai/CURRENT_PHASE.md

**Phase:** Sprint 5 — F3 RBAC (Role-Based Access Control) — **PLANNING**
**Status:** 🟡 PLANNING (planning only — implementation NOT authorized).
Sprint 4 is CLOSED (see below); the Product Owner authorized Sprint 5
*planning*. The planning package is drafted on branch
`claude/sprint-5-planning`: `docs/architecture-decisions/ADR-003-Role-Based-
Access-Control.md` plus `docs/planning/SPRINT5_{RECOMMENDATION,TECHNICAL_PLAN,
FILE_MAP,RISK_ASSESSMENT,TESTING_PLAN,MILESTONE_CHECKLIST}.md`. **Awaiting
Product Owner review; no `app/` code, tests, or migrations are changed by
the planning PR.**
**Branch:** `claude/sprint-5-planning` (planning docs only; base `main` `eb9fb92`)
**Updated:** 2026-09-18 (Sprint 5 planning drafted)

---

## Sprint 4 — CLOSED (prior phase)
**Status:** ✅ CLOSED — planning (PR #10) and implementation (PR #11) both
reviewed and merged into `main`. Post-merge final verification completed:
`main` HEAD `18ff96d` contains implementation commit `0523d3c`; 56/56 tests
passing; regression golden byte-identical; deployment-tier documentation
verified consistent; no scope creep detected.

## Goal
Close the two concrete architecture gaps ADR-002 found (no database
abstraction, no storage abstraction) with behavior-preserving seams, and
ship a clinic-profile-only Settings UI over the existing `settings`
table — all without changing the database engine, storage backend, or
adding any new dependency, per the approved Sprint 4 scope
(`docs/planning/SPRINT4_RECOMMENDATION.md` §3).

## Delivered
- `app/core/db_adapters/` — `DatabaseAdapter` protocol + `SQLiteAdapter`
  (sole implementation). `BaseRepository`/`core.database.get_connection()`
  delegate to it; behavior verified identical to the pre-Sprint-4
  direct-`sqlite3` implementation.
- `app/core/storage/` — `StorageProvider` protocol
  (`save`/`open`/`delete`/`url_for` only, **no** universal
  `absolute_path()`) + `LocalDiskStorageProvider` (sole implementation,
  with a local-only `local_path()` helper kept off the Protocol).
- Configuration boundary: adapter/provider selection is a single
  hardcoded branch each — no env var, no Settings UI control.
- `app/modules/settings/` — clinic-profile-only Settings UI
  (`clinic_name`, `doctor_name`, `clinic_address`, `phone`, `email`,
  `logo_path`); service-layer whitelist rejects any other key;
  `backup_path` stays read-only.
- `attachments.service` and the backup archive's *destination write*
  migrated onto `StorageProvider`; archive construction stays local
  (Backup boundary, ADR-002 §5.3).
- Tests: `test_db_adapter.py`, `test_storage_provider.py`,
  `test_settings_domain.py`, `test_layering.py` (import/dependency
  boundary gates), plus extensions to `test_router.py`,
  `test_views_build.py`, `test_models.py`. `python3 -m pytest -q` → 56
  passing (31 prior + 25 new). Regression golden byte-identical except
  the intentional new `^/settings$` route/view lines.
- Docs: `DATABASE.md`, `DEPLOYMENT.md` (SQLite network-deployment rule),
  `CHANGELOG.md`, `DECISIONS.md` (ADR-0010), `modules/Settings.md` (new),
  `modules/Attachments.md`, `modules/Backups.md` (Backup boundary),
  `MASTER_BACKLOG.md` (F2 closed; AR1/AR2 closed), `KNOWN_LIMITATIONS.md`
  (L7 closed; L12 formalized), `TARGET_ARCHITECTURE.md` (folder map).

## NOT in scope (deferred, per ADR-002 §11 / SPRINT4_RECOMMENDATION.md)
RBAC (F3, recommended Sprint 5), encryption at rest (F7), any AI/OCR/
messaging code, any second database adapter or non-local storage
provider, any ORM/Alembic, any cloud deployment artifact, any sync code,
any API-key storage.

## Verification
```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q     # expect 56 passing
```
