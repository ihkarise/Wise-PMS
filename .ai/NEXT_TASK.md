# .ai/NEXT_TASK.md — The single next actionable task

> Keep this to **one** concrete task. When it's done, replace it with the next
> one. **Updated:** 2026-09-18.

## Now
**Sprint 4 (Cloud-Ready Architecture Seams + Settings UI, ADR-002) is
CLOSED.** Planning (PR #10) and implementation (PR #11) are both merged
into `main`. Post-merge final verification is complete: `main` is
synchronized with `origin/main`, contains implementation commit
`0523d3c`, 56/56 tests pass, the regression golden is byte-identical, and
no scope creep was detected. **The repository is ready for Sprint 5
planning.**

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
Nothing. Sprint 4 is closed; no further action is required on it.

## Next
**Sprint 5 planning (F3 RBAC) is drafted and awaiting Product Owner
review.** The Product Owner authorized *planning only*; the planning
package lives on branch `claude/sprint-5-planning`: `ADR-003` (Role-Based
Access Control) plus the six `docs/planning/SPRINT5_*.md` documents. The
single next task is the **Product Owner's review/approval** of ADR-003 and
that package, and resolution of the open decisions it flags (runtime custom
roles; user↔role cardinality; the permission→role default mapping).
**Implementation is NOT authorized** and must not begin until the Product
Owner approves and the planning PR merges. This file does not decide
Sprint 5's scope.
