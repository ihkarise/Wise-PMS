# Sprint 4 — File Map: Settings UI + Database/Storage Abstraction Seams

**Status:** PLAN ONLY — no code. Await Product Owner approval.
**Date:** 2026-08-07 · **Revision 1:** 2026-09-18 — field whitelist noted
under Settings; `absolute_path()` removed from the `StorageProvider`
Protocol file, added as a `LocalDiskStorageProvider`-only method; backup
file entry split into destination-write vs. archive-construction; explicit
out-of-scope list expanded to match `SPRINT4_RECOMMENDATION.md` §3.
Companion to `SPRINT4_TECHNICAL_PLAN.md`.

Legend: 🆕 new file · ✏️ modified (behavior-preserving) · 🚫 not touched
(listed to make the boundary explicit).

## New files

```
app/core/db_adapters/
├── __init__.py                 🆕 get_adapter() -> DatabaseAdapter (single hardcoded
                                    "sqlite" branch — no env var, no Settings UI control)
├── base.py                     🆕 DatabaseAdapter Protocol, Dialect descriptor
└── sqlite_adapter.py           🆕 SQLiteAdapter (wraps existing sqlite3 calls verbatim)

app/core/storage/
├── __init__.py                 🆕 get_storage() -> StorageProvider (single hardcoded
                                    "local" branch — no env var, no Settings UI control)
├── base.py                     🆕 StorageProvider Protocol: save/open/delete/url_for ONLY
                                    (no absolute_path() — Revision 4)
└── local_disk_provider.py      🆕 LocalDiskStorageProvider (wraps existing os/shutil calls
                                    verbatim) + local_path() — a LOCAL-ONLY helper, not on
                                    the StorageProvider Protocol (Revision 4)

app/modules/settings/
├── __init__.py                 🆕
├── models.py                   🆕 Settings(RowModel) — mirrors existing table; service-layer
                                    field whitelist lives in service.py, not here
├── repository.py               🆕 SettingsRepository(BaseRepository)
├── service.py                  🆕 get_clinic_settings, update_clinic_settings — accepts ONLY
                                    clinic_name/doctor_name/clinic_address/phone/email/
                                    logo_path; rejects any other key (Revision 3 field whitelist)
├── controller.py                🆕 SettingsController + ROUTES
└── view.py                     🆕 settings_view(page) — renders ONLY the 6 whitelisted
                                    fields; no database/storage/backup-destination/API-key/
                                    RBAC controls anywhere in this view (Revision 3)

tests/
├── test_db_adapter.py          🆕 SQLiteAdapter behavior parity vs. current get_connection()
├── test_storage_provider.py    🆕 Protocol-conformance tests (save/open/delete/url_for only)
                                    SEPARATE from LocalDiskStorageProvider-specific tests
                                    (path convention, local_path(), path-traversal rejection)
└── test_settings_domain.py     🆕 Settings CRUD + audit + logo upload via StorageProvider +
                                    field-whitelist rejection test (Revision 3 enforcement)
```

## Modified files (behavior-preserving)

```
app/core/repository.py          ✏️ BaseRepository delegates to get_adapter() instead of
                                    importing app.core.database directly; _all/_one/_scalar/
                                    _execute/transaction() signatures and return shapes unchanged
app/core/database.py            ✏️ get_connection() becomes a thin shim delegating to
                                    SQLiteAdapter; init_db()/migration call sites unchanged;
                                    migration runner itself (app/core/migrations/*) NOT touched
app/modules/attachments/service.py ✏️ add_attachment/delete_attachment call storage.save/delete;
                                    absolute_path() calls LocalDiskStorageProvider.local_path()
                                    directly (not the Protocol — Revision 4); public signatures
                                    unchanged
app/modules/backup/service.py   ✏️ backup_now writes its archive's DESTINATION via storage.save;
                                    archive CONSTRUCTION (db + attachments walk → zip bytes)
                                    stays an unchanged local filesystem operation (Revision 5
                                    backup boundary — see SPRINT4_TECHNICAL_PLAN.md §4.4)
app/bootstrap.py                ✏️ mount settings.ROUTES (same pattern as every other module)
app/shared/shell.py              ✏️ add a Settings nav entry to the header workflow bar
tests/test_regression.py        ✏️ (only if the golden needs a new route/view line — no
                                    TABLES:/INDEXES: change expected; any such change is a bug)
tests/test_router.py            ✏️ extend router-contract coverage to ^/settings$
tests/test_views_build.py       ✏️ extend view-build smoke test to settings_view
docs/DATABASE.md                ✏️ document the DatabaseAdapter seam (no schema change)
docs/ARCHITECTURE.md / TARGET_ARCHITECTURE.md ✏️ note the new core/db_adapters, core/storage
                                    packages in the folder map
docs/DECISIONS.md               ✏️ new ADR-0010 entry recording this sprint's adapters
docs/CHANGELOG.md               ✏️ Settings UI + abstraction seams entry
docs/modules/Settings.md        ✏️ (currently absent from docs/modules/ — create alongside
                                    the module, per Article IX §2 "docs in the same commit");
                                    explicitly states the field whitelist and "RBAC-gated
                                    Administrator surface handles everything else, once F3
                                    (Sprint 5) lands"
docs/modules/Backups.md         ✏️ note the backup boundary (destination-write abstracted;
                                    archive construction stays local-disk-native by design)
docs/MASTER_BACKLOG.md          ✏️ close F2 (clinic-profile scope only); note new architecture
                                    items done
docs/KNOWN_LIMITATIONS.md       ✏️ close L7 (no Settings UI) — note the security-sensitive-
                                    configuration gap remains open until F3/F7
.ai/CURRENT_PHASE.md, NEXT_TASK.md, WORK_LOG.md ✏️ phase bookkeeping
```

## Explicitly not touched (🚫)

```
app/core/migrations/*                 🚫 no new migration; DDL stays SQLite-only; no
                                          declarative table/column spec (Revision 6)
app/modules/patients/*, cases/*,      🚫 zero behavior change; no repository SQL text changes
  visits/*, consultation/*,
  attachments/repository.py,
  backup logic beyond the
  destination-write call
app/modules/authentication/*          🚫 no RBAC, no auth change (Sprint 5)
requirements.txt / requirements-dev.txt 🚫 no new dependency (no SQLAlchemy, no Alembic,
                                          no cloud SDK, no ORM — Revision 6)
data/, backups/, attachments/         🚫 no on-disk layout change; existing clinic data
  (runtime folders)                      opens identically after upgrade
```

**Also explicitly out of scope (no file of any kind in this sprint, per
`SPRINT4_RECOMMENDATION.md` §3 / Product Owner Revision 7):** any
PostgreSQL/MySQL/SQL Server/Cloud SQL adapter file; any S3/Azure Blob/GCS/
MinIO/NAS provider file; any `Dockerfile`, Kubernetes manifest, or
cloud-deployment config; any `sync_queue`/sync engine code; any AI/OCR
module or provider adapter; any RBAC/roles/permissions code; any
encryption-at-rest utility; any `provider_credentials`/API-key storage;
any payment-gateway code.

## Diff-size sanity check

Two brand-new leaf packages (`core/db_adapters`, `core/storage`) plus one
new vertical-slice module (`modules/settings`, deliberately narrowed to
clinic-profile fields) plus one explicit, test-enforced Configuration
boundary (no new files beyond the whitelist test) — each independently
testable and each following an existing, established template
(`TARGET_ARCHITECTURE.md` §5's worked module example; `BaseRepository`'s
existing connection-lifecycle pattern). No existing repository's SQL
changes. This keeps the sprint inside the "small, reviewable, runnable
commits" principle (Constitution Art. III §8) despite touching two
cross-cutting concerns.
