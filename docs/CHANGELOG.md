# Changelog

All notable changes to WiseOS Health / Wise PMS. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/). Newest first.

## [Unreleased]

### Added
- **Sprint 5 — RBAC foundation (F3 / ADR-003), Milestone 1.** New migration
  `v0003_rbac` (additive + reversible) adds the `roles`, `permissions`,
  `role_permissions`, and `user_roles` tables and seeds the approved five
  roles (Administrator/Doctor/Reception/Pharmacy/Accounts), the 16-permission
  catalogue, and the default role→permission grants
  (`docs/planning/SPRINT5_TECHNICAL_PLAN.md` §5.2). A UNIQUE index
  `idx_user_roles_user` enforces one active role per user at the database
  level; the legacy `users.role` column is left untouched (non-authoritative).
  New `app/modules/roles/` vertical slice (models, repository, service) whose
  service enforces the at-least-one-active-Administrator invariant on role
  assignment; the existing `admin` account (legacy role `Admin`) is bound to
  the Administrator role by the migration (existing DBs) and by `init_db`
  (fresh DB) — credentials are never altered. This is the
  **database/domain foundation only**: no route guard, no service
  authorization check, and no RBAC UI ship in this milestone. New
  `tests/test_rbac_foundation.py`. **Intentional, documented golden change
  (rule 12/13):** the regression golden's `TABLES:` line gains
  `permissions`, `role_permissions`, `roles`, `user_roles` and its `INDEXES:`
  line gains `idx_user_roles_user`; no other golden output changed.
  `python3 -m pytest -q` → 72 passing (56 prior + 16 new).
- **Sprint 4 — Cloud-Ready Architecture Seams (ADR-002).** New
  `app/core/db_adapters/` (`DatabaseAdapter` protocol + `SQLiteAdapter`,
  the sole implementation) and `app/core/storage/` (`StorageProvider`
  protocol -- `save`/`open`/`delete`/`url_for` only, deliberately no
  universal `absolute_path()` -- + `LocalDiskStorageProvider`, the sole
  implementation). Both are behavior-preserving wrappers around the
  pre-existing `sqlite3`/`os`/`shutil` code; zero engine change, zero
  storage-backend change, zero new dependency. New `app/modules/settings/`
  vertical slice: a clinic-profile-only Settings UI (`clinic_name`,
  `doctor_name`, `clinic_address`, `phone`, `email`, `logo_path`), with a
  service-layer field whitelist that rejects any other key (database,
  storage, backup-destination, API-key, or RBAC configuration are
  explicitly out of scope for this module -- ADR-002 §6.6). `attachments`
  and the backup archive's *destination write* (not its construction) now
  go through the StorageProvider seam. New tests:
  `test_db_adapter.py`, `test_storage_provider.py`,
  `test_settings_domain.py`, `test_layering.py` (import/dependency
  boundary gates), plus Settings coverage in `test_router.py`/
  `test_views_build.py`/`test_models.py`. No schema change, no migration,
  no new runtime dependency. `python3 -m pytest -q` -> 56 passing (31
  prior + 25 new); regression golden byte-identical.

### Added (prior)
- **Consultation Domain Model (Sprint 2 / C3, ADR-001 Option C).** New
  `consultations` table (migration `v0002_consultations`, additive + reversible)
  — the clinical *document*, 1:1 with a `visits` *event* (`visit_id` UNIQUE).
  New `consultation` vertical slice: `models.Consultation`, `repository`
  (sole writer of `consultations`), `service` lifecycle state machine
  (`draft → in_progress → completed`, `amended`/`locked` reserved; every
  transition audited), controller create/open-draft on workspace open, and view
  status read-back. `visits` untouched. New `tests/test_consultation_domain.py`
  + `v0002` migration/model coverage.

### Changed
- **Regression golden** `TABLES:`/`INDEXES:` lines gain `consultations`,
  `idx_consultation_visit`, `idx_consultation_patient` — intentional, documented
  (ADR-0009). No behaviour change to existing features.

### Added (prior)
- **Consultation Workspace skeleton (Sprint 1 / backlog C1).** New
  `app/modules/consultation/` vertical slice — the structural foundation of the
  central consultation screen. Composition-only (no table, no SQL, no business
  logic): a read-only `workspace_context` service over `patients`/`cases`, a
  controller registering the route
  `/patient/<pid>/case/<cid>/workspace(/visit/<new|vid>)?` (with `?section=`
  deep-link), and a `workspace_view` laying out a left section-nav rail, a
  center column of section cards (Patient Summary shows real read-only data;
  Chief Complaint / History / Diagnosis / Prescription / Remarks / Follow-up are
  placeholders), a right rail of placeholder context panels (Timeline /
  Investigations / OCR / Protocol Suggestions / AI Assistant), and a bottom
  status/action bar with **disabled** terminal actions (Print / Invoice /
  Dispense / WhatsApp / Complete Visit). Reachable from the Case Record via a new
  **Start Consultation** button. New shared widgets `disabled_button` and
  `placeholder_card`, and an optional `border` argument on `theme.card`. Router
  contract and view-build smoke tests extended to cover the new route and view.
- **DB Migration Framework (Sprint 0 / backlog F1).** New
  `app/core/migrations/` package: an ordered, forward-only, idempotent migration
  runner with a `schema_version` ledger table and rollback support. `init_db()`
  now brings the database up to the latest schema version before seeding.
  Migration `0001_initial` is the behaviour-preserving conversion of the former
  inline `SCHEMA`. Legacy databases are stamped at their current version with no
  data loss (baseline is create-if-not-exists). New `tests/test_migrations.py`
  covers idempotency, legacy stamping, rollback, and a fresh-vs-migrated parity
  check. Closes the L1 / F1 schema-versioning gap.

### Changed
- **Regression golden** (`tests/test_regression.py`) `TABLES` line now includes
  the new internal `schema_version` ledger table. Intentional, documented schema
  addition (no service-layer behaviour change) — see ADR-0008.

- **Project Memory System (Phase 1).** Full `docs/` product & system
  documentation set, `docs/modules/` per-module docs (built + planned), and
  `.ai/` machine-facing memory files (context, phases, rules, logs). No runtime
  code changed; the app is unaffected.

## Architecture Refactor (PR #1, merged)

### Changed
- Reorganized the codebase from screen-oriented (`app/ui`, `app/services`,
  `app/database`) to **domain-driven vertical-slice modules**
  (`app/modules/<domain>/` with `models → repository → service → controller →
  view`).
- Introduced `app/core/` (database, router, base repository, base model),
  `app/config/` (paths, constants), `app/shared/` (theme, shell, widgets),
  `app/utils/` (prescription extraction).
- Replaced the hand-rolled `if/elif` router in `main.py` with a centralized
  regex `Router`; `main.py` is now a thin entrypoint to `app.bootstrap.run()`.
- Added `models` and `repository` layers; services delegate SQL to repositories.

### Added
- `.gitignore`, `.gitkeep` for runtime dirs, `requirements-dev.txt`.
- Test suite: regression golden, model/table parity, view-build, router-contract.
- `docs/ARCHITECTURE.md`, `docs/TARGET_ARCHITECTURE.md`, `docs/DEPENDENCY_MAP.md`.

### Removed
- Malformed literal-brace directories; compatibility shims (final cleanup).

## Sprint 2

### Added
- Case Records (multiple cases per patient), Visit Entry (narrative editors),
  Prescription intelligence (regex extraction), Patient Timeline, Attachments,
  Profile tabs, Dashboard visits/follow-ups, backup includes attachments.

## Sprint 1

### Added
- Login (`admin`/`admin123`), Registration (auto reg-no `P000001…`), real-time
  Patient Search, Patient Profile, Dashboard, one-click Backup, Audit log,
  soft-delete for patients.
