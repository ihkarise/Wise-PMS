# Changelog

All notable changes to WiseOS Health / Wise PMS. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/). Newest first.

## [Unreleased]

### Added
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
