# .ai/NEXT_TASK.md — The single next actionable task

> Keep this to **one** concrete task. When it's done, replace it with the next
> one. **Updated:** 2026-09-18.

## Now
**Sprint 4 (Cloud-Ready Architecture Seams + Settings UI, ADR-002)
implemented on `claude/sprint-4-implementation` — awaiting Product Owner
review of the implementation PR before merge.**

Delivered:
- [x] `DatabaseAdapter` protocol + `SQLiteAdapter` (sole implementation);
  `BaseRepository`/`core.database` delegate to it, behavior unchanged.
- [x] `StorageProvider` protocol (`save`/`open`/`delete`/`url_for` only,
  no universal `absolute_path()`) + `LocalDiskStorageProvider`.
- [x] Configuration boundary: single hardcoded adapter/provider branch,
  no env var, no Settings UI control.
- [x] Clinic-profile-only Settings UI with a service-layer field
  whitelist rejecting database/storage/backup/API-key/RBAC config.
- [x] `attachments`/backup-destination-write migrated onto
  `StorageProvider`; archive construction stays local (Backup boundary).
- [x] Tests: `test_db_adapter.py`, `test_storage_provider.py`,
  `test_settings_domain.py`, `test_layering.py`, plus router/views/models
  extensions → 56 passing (31 prior + 25 new).
- [x] Docs: DATABASE, DEPLOYMENT (SQLite network rule), CHANGELOG,
  DECISIONS (ADR-0010), module docs, MASTER_BACKLOG, KNOWN_LIMITATIONS,
  TARGET_ARCHITECTURE, `.ai/*`.

## Blocked on
Product Owner review of the Sprint 4 implementation PR (against `main`).

## After approval (next)
- **Sprint 5 (recommended): RBAC (F3)** — roles/permissions schema +
  route/action guards, per `docs/planning/SPRINT4_RECOMMENDATION.md` §2.
  Sequenced before F7 (encryption) and before any future Administrator/
  Security settings surface that would host database/storage/backup/
  API-key configuration (ADR-002 §11).
- Later: F7 encryption at rest → AI Gateway + `provider_credentials` +
  Mode A/B (ADR-002 §6) → a server-grade `DatabaseAdapter` / non-local
  `StorageProvider`, each only when a real deployment needs one.
