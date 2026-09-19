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
**Sprint 5 planning (F3 RBAC) is finalized and awaiting Product Owner
approval.** The theme is approved and the Product Owner's scope decisions
are **FINAL (2026-09-19)**: five-role set fixed; custom roles out; one
active role per user (no multi-role); F4 (beyond minimum RBAC admin), F7,
and row-level authorization out. The permission catalogue + default
role→permission matrix are finalized (`SPRINT5_TECHNICAL_PLAN.md` §5.2) and
the four-case denial model is finalized (§8). The package lives on branch
`claude/sprint-5-planning` (PR #12): `ADR-003` plus the six
`docs/planning/SPRINT5_*.md` documents. The single next task is the
**Product Owner's approval** of the revised package. **Implementation is
NOT authorized** and must not begin until the Product Owner approves and the
planning PR merges.
