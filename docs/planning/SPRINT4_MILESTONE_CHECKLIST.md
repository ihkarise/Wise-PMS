# Sprint 4 — Milestone Checklist: Settings UI + Database/Storage Abstraction Seams

**Status:** PLAN ONLY — no code. Await Product Owner approval.
**Date:** 2026-08-07 · **Revision 1:** 2026-09-18 — milestones renumbered
and split to mirror the Product Owner's finalized 10-item scope exactly
(`SPRINT4_RECOMMENDATION.md` §3): Configuration boundary and the backup-
destination migration are now their own milestones (M3, M7) rather than
folded into others; the Settings milestone is narrowed to clinic-profile
fields with a whitelist test; the `StorageProvider` milestone drops
`absolute_path()` from the Protocol. Each milestone independently
testable; `main` stays green throughout. Build in order. No commit, no
push, no PR until the Product Owner approves this plan and each
milestone's implementation.

---

## Milestone 1 — `DatabaseAdapter` protocol + `SQLiteAdapter` (scope items 1–2)
- [ ] `app/core/db_adapters/base.py`: `DatabaseAdapter` Protocol +
      `Dialect` descriptor (design per `SPRINT4_TECHNICAL_PLAN.md` §3.2).
- [ ] `app/core/db_adapters/sqlite_adapter.py`: `SQLiteAdapter`, a
      line-for-line move of today's `get_connection`/transaction bodies.
- [ ] `app/core/db_adapters/__init__.py`: `get_adapter()` — single
      hardcoded `sqlite` branch, no external config surface.
- [ ] `app/core/repository.py`: `_all/_one/_scalar/_execute/transaction()`
      delegate to `get_adapter()`; signatures/return shapes unchanged.
- [ ] `app/core/database.py`: `get_connection()` becomes a shim
      delegating to `SQLiteAdapter` (kept for `init_db()`/migration
      runner/test call sites). **Migration runner itself is untouched —
      no declarative spec, no ORM, no Alembic (Revision 6).**
- **Test:** `test_db_adapter.py` — connection/transaction parity vs.
  pre-refactor behavior; full existing suite green, unmodified assertions
  (patients, cases, visits, consultation, attachments, audit, timeline,
  migrations, router, views all still pass against the new adapter path).
- **Gate:** grep — no file outside `core/db_adapters/` imports `sqlite3`.
- **Rollback:** revert this commit; no data migration involved.

## Milestone 2 — `StorageProvider` protocol + `LocalDiskStorageProvider` (scope items 3–4)
- [ ] `app/core/storage/base.py`: `StorageProvider` Protocol —
      **`save`/`open`/`delete`/`url_for` only. No `absolute_path()`**
      (Revision 4).
- [ ] `app/core/storage/local_disk_provider.py`:
      `LocalDiskStorageProvider` — reproduces `attachments`/`backup`'s
      exact path conventions verbatim, **plus a `local_path()` method
      that exists only on this concrete class, not on the Protocol.**
- [ ] `app/core/storage/__init__.py`: `get_storage()` — single hardcoded
      `local` branch.
- **Test:** `test_storage_provider.py` — Protocol-conformance tests
  (save/open/delete/url_for) kept separate from `LocalDiskStorageProvider`-
  specific tests (path convention, `local_path()`, path-traversal
  rejection per R6).
- **Shippable alone:** net-new package; nothing imports it yet.

## Milestone 3 — Configuration boundary (scope item 5, new milestone per Revision 3/7)
- [ ] Document (in `SPRINT4_TECHNICAL_PLAN.md` Part D, already drafted)
      that `get_adapter()`/`get_storage()` selection is a hardcoded code
      branch — no environment variable, no `settings`-table column, no
      Settings UI control, in this sprint.
- [ ] Confirm the existing `settings.backup_path` column is **not**
      wired to any read/write path in this sprint — it stays present in
      the schema (unchanged, no migration) and unused/read-only.
- [ ] Add the field-whitelist test to `test_settings_domain.py` (written
      here, before Milestone 4's UI exists, so the guard rail is in place
      first).
- **Test:** field-whitelist rejection test (added in this milestone,
  exercised again in Milestone 4).
- **Shippable alone:** a test + documentation milestone; no runtime code
  changes beyond what M1/M2 already introduced.

## Milestone 4 — Safe Settings UI (scope item 6)
- [ ] `app/modules/settings/{models,repository,service,controller,view}.py`
      per the established vertical-slice template.
- [ ] `SettingsRepository` reads/writes the single existing `settings`
      row — **no migration**.
- [ ] `update_clinic_settings` accepts **only** `clinic_name`,
      `doctor_name`, `clinic_address`, `phone`, `email`, `logo_path`;
      rejects any other key (Milestone 3's whitelist test must pass
      against this implementation); writes an audit row
      (`"Settings Updated"`).
- [ ] Logo upload calls `storage.save()` directly (first net-new caller
      of Milestone 2's provider).
- [ ] `settings_view` renders **exactly** the 6 whitelisted fields — no
      database/storage/backup-destination/API-key/RBAC control anywhere
      on the page.
- [ ] Route `^/settings$` registered in `app/bootstrap.py`; nav entry
      added in `app/shared/shell.py`.
- **Test:** `test_settings_domain.py` (CRUD on the 6 fields, validation,
  audit, logo upload, whitelist rejection, `backup_path` read-only);
  `test_router.py` extended for `^/settings$`; `test_views_build.py`
  extended for `settings_view`, asserting no non-whitelisted control is
  rendered.

## Milestone 5 — Migrate `attachments` onto `StorageProvider` (scope item 7)
- [ ] `app/modules/attachments/service.py`: `add_attachment`/
      `delete_attachment` call `storage.save/delete`; `absolute_path()`
      calls `LocalDiskStorageProvider.local_path()` directly (documented
      as the known local-only dependency — Revision 4); public signatures
      unchanged.
- **Test:** existing attachment tests pass unmodified; manual checklist
  item "existing DB + attachments fixture still readable"
  (`SPRINT4_TESTING_PLAN.md` §4) verified.
- **Gate:** grep — no `shutil`/`os.remove`/`os.makedirs` against
  attachment paths outside `core/storage/`.

## Milestone 6 — Migrate backup **destination write** onto `StorageProvider` (scope item 8)
- [ ] `app/modules/backup/service.py`: `backup_now` writes its archive's
      **destination** via `storage.save`. **Archive construction** (the
      local filesystem walk building the zip from `data/wise_pms.db` +
      `attachments/`) stays unchanged — this is the Backup boundary
      (`SPRINT4_TECHNICAL_PLAN.md` §4.4), not a gap to close later in this
      sprint.
- **Test:** existing backup tests pass unmodified; manual checklist item
  "existing backups fixture still readable" verified.
- **Gate:** grep — no `shutil`/`os.remove`/`os.makedirs` against backup
  destination paths outside `core/storage/`; archive-construction code
  is explicitly allowed to keep its local filesystem calls (documented,
  not a gate violation).

## Milestone 7 — Regression + gates consolidate (scope item 9, tests)
- [ ] Full suite green: adapters, storage (Protocol + local-only split),
      configuration-boundary whitelist, settings, plus every pre-existing
      test file, assertions unmodified.
- [ ] Regression golden diff = **only** the new `^/settings$` route/view
      lines; zero `TABLES:`/`INDEXES:` change (reviewed line-by-line).
- [ ] Layering + import grep gates (adapter, storage, local-only-helper
      isolation, no new dependency) clean; `py_compile` clean across the
      tree.
- [ ] Manual test checklist (`SPRINT4_TESTING_PLAN.md` §4) executed
      against both a fresh DB and an existing pre-Sprint-4 fixture DB,
      including the "Settings shows exactly 6 fields" check.

## Milestone 8 — Documentation & memory (scope item 10)
- [ ] `docs/DATABASE.md` — document the `DatabaseAdapter` seam (no schema
      change).
- [ ] `docs/ARCHITECTURE.md` / `TARGET_ARCHITECTURE.md` — note
      `core/db_adapters`, `core/storage`, `modules/settings` in the folder
      map.
- [ ] `docs/architecture-decisions/` — new ADR-0010 (or append to
      ADR-002) recording the adapters as implemented, referencing this
      checklist.
- [ ] `docs/DECISIONS.md`, `docs/CHANGELOG.md` — new entries.
- [ ] `docs/modules/Settings.md` — new module doc, explicitly listing the
      6-field whitelist and stating "database/storage/backup-destination/
      API-key/RBAC configuration is handled by a future, RBAC-gated
      Administrator/Security surface, once F3 (Sprint 5) and F7 land —
      never this module."
- [ ] `docs/modules/Backups.md`, `docs/modules/Attachments.md` — note the
      storage-provider migration; `Backups.md` documents the Backup
      boundary diagram (destination-write abstracted; archive construction
      stays local-disk-native by design).
- [ ] `docs/DEPLOYMENT.md` — add the SQLite network-deployment rule
      (ADR-002 §8.1) explicitly: never run the shipped database as a
      shared file over a network filesystem.
- [ ] `docs/MASTER_BACKLOG.md` — close F2 (clinic-profile scope only);
      record the two new architecture items + configuration boundary as
      done.
- [ ] `docs/KNOWN_LIMITATIONS.md` — close L7 (no Settings UI); note that
      security-sensitive configuration remains unaddressed until F3/F7.
- [ ] `.ai/CURRENT_PHASE.md`, `NEXT_TASK.md`, `WORK_LOG.md`,
      `NEXT_PHASE.md` — phase bookkeeping; propose Sprint 5 = RBAC (F3)
      per `SPRINT4_RECOMMENDATION.md` §2.
- [ ] Broken-link scan clean.

---

## Definition of done
- [ ] M1–M8 complete; each independently tested.
- [ ] `python3 -m pytest -q` green; golden change limited to the
      documented new route/view lines.
- [ ] No new runtime dependency; no database engine change; no storage
      backend change; existing clinic data (DB, attachments, backups)
      verified readable post-upgrade.
- [ ] Settings UI verified to expose **exactly** the 6 clinic-profile
      fields — no security-sensitive configuration.
- [ ] `StorageProvider` Protocol verified to have no `absolute_path()`
      method; `local_path()` verified to exist only on
      `LocalDiskStorageProvider`.
- [ ] SQLite network-deployment rule documented in `docs/DEPLOYMENT.md`.
- [ ] **No commit is pushed and no PR is opened** until the Product Owner
      has reviewed this checklist's execution — per this review's
      explicit governance instructions and Constitution Article IX §3.
