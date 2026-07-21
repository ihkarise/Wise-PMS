# Changelog

All notable changes to WiseOS Health / Wise PMS. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/). Newest first.

## [Unreleased]

### Added
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
