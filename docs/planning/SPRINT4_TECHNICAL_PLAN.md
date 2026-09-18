# Sprint 4 — Technical Plan: Settings UI + Database/Storage Abstraction Seams

**Architecture:** ADR-002 §3 (Option C — `DatabaseAdapter` protocol), §5
(`StorageProvider` protocol). **Depends on:** F1 migration runner
(Sprint 0), the domain-driven module layout (ADR-0003–ADR-0005).
**Status:** PLAN ONLY — no code. Await Product Owner approval.
**Date:** 2026-08-07 · **Revision 1:** 2026-09-18 — see §0 for the change
summary; content below reflects the revised plan throughout.

---

## 0. Revision 1 summary

Per Product Owner review, this plan now: (1) restricts the Settings UI to
clinic-profile fields only (§2.3); (2) adds a Configuration boundary as
its own part (§0.1/Part D) so adapter/provider selection is never a
Settings UI control; (3) removes `absolute_path()` from the universal
`StorageProvider` Protocol and isolates it as a local-only helper (§4.2);
(4) documents the backup boundary explicitly (§4.3, §5.4); (5) states
plainly that the migration runner and declarative-spec mechanism are
untouched/undeferred (§3.4, §6); (6) uses ADR-002's readiness-tier
language throughout. No implementation, migration, or dependency change
is introduced by this revision.

## 1. Objectives

1. Ship a working **Settings** module over the existing, unused `settings`
   table — **clinic-profile fields only**: clinic name, doctor name,
   address, phone, email, logo. Editable by an authenticated user.
2. Introduce a `DatabaseAdapter` protocol so `BaseRepository` (and
   therefore every repository in the codebase) no longer imports
   `sqlite3` directly — with **zero behavior change** and **zero engine
   change**.
3. Introduce a `StorageProvider` protocol so `attachments.service` and
   `backup.service` no longer call `os`/`shutil` directly — with **zero
   behavior change** and **zero storage-backend change**.
4. Establish the Configuration boundary (Part D) so that adapter/provider
   selection, and any future database/storage/backup-destination/
   credential configuration, is never exposed through the Settings UI in
   this phase.
5. Leave every other module, table, and test untouched; regression golden
   stays byte-identical.

Non-goals: RBAC, encryption at rest, any AI/OCR/messaging code, any new
database engine or storage backend, any schema migration beyond what
already exists, any ORM/Alembic/declarative migration spec, any exposure
of security-sensitive configuration in this module's UI.

## 2. Part A — Settings UI

### 2.1 Module shape (matches the established template, `TARGET_ARCHITECTURE.md` §5)
```
app/modules/settings/
├── __init__.py
├── models.py       # Settings(RowModel) mirroring the existing `settings` table
├── repository.py   # SettingsRepository(BaseRepository): get_settings(), update_settings()
├── service.py      # get_clinic_settings(), update_clinic_settings(data, user_id) — validation + audit
├── controller.py   # SettingsController + ROUTES
└── view.py         # settings_view(page) — Flet form over shared/theme.py + shared/widgets.py
```

### 2.2 Data
No migration. `settings` already has exactly one row
(`clinic_name, doctor_name, clinic_address, phone, email, logo_path,
backup_path, created_at`), seeded by `core/database.init_db()`. The
repository always targets that single row (`UPDATE settings WHERE id = 1`
pattern, mirroring the existing seed guard).

### 2.3 Service rules — field whitelist (revised, Product Owner Revision 3)
`update_clinic_settings(data, user_id)` accepts **only** this whitelist:
`clinic_name`, `doctor_name`, `clinic_address`, `phone`, `email`,
`logo_path`. Any other key present in `data` is rejected (service raises
rather than silently persisting an unexpected field) — this is the
enforcement point for the Configuration boundary (Part D) at the service
layer, not just a UI omission.

**Explicitly not editable through this module, this sprint, or this
UI** (ADR-002 §6.6): `backup_path` (the existing column is left alone —
read-only, sourced from `app/config/paths.py`, not user-editable, even
though the column already exists in the table from Sprint 1), database
configuration, storage-provider configuration, API keys/credentials,
RBAC/permissions, or any other security setting. These require a future
Administrator/Security surface gated behind RBAC (F3) and, for secrets,
encryption at rest (F7) — neither exists today.

- `update_clinic_settings` validates required fields (`clinic_name`
  non-empty) the same way `patients.service`/`cases.service` validate
  today — no new validation framework.
- Every update writes an audit row (`audit.service.log_action`,
  `"Settings Updated"`) per Article VI §2.
- Logo upload (`logo_path`) goes through the new `StorageProvider` (§4)
  from day one — this module is the **first caller** of the new
  abstraction, proving it end-to-end on a low-risk, non-security-
  sensitive surface (a logo image, not a credential or config value)
  before `attachments`/`backup` are migrated onto it.

### 2.4 Route & nav
`^/settings$`; a new nav entry in `app/shared/shell.py`. Session guard
applies like every other route. **Known accepted gap (see
`SPRINT4_RISK_ASSESSMENT.md` R7):** without RBAC (F3, not yet built), any
authenticated user can reach this route — acceptable because the field
whitelist above limits what can be changed to clinic-profile text/logo,
never security-sensitive configuration.

## 3. Part B — `DatabaseAdapter` protocol

### 3.1 Module shape
```
app/core/db_adapters/
├── __init__.py       # get_adapter() -> DatabaseAdapter, selected by config (SQLite only today)
├── base.py           # DatabaseAdapter Protocol + Dialect descriptor
└── sqlite_adapter.py # SQLiteAdapter — wraps today's sqlite3 calls verbatim
```

### 3.2 Interface (design; final signatures fixed at implementation time)
```python
class DatabaseAdapter(Protocol):
    def connect(self) -> "Connection": ...
    def execute(self, conn, sql: str, params: tuple = ()) -> "Cursor": ...
    @contextmanager
    def transaction(self) -> Iterator["Connection"]: ...
    dialect: Dialect   # placeholder style, autoincrement keyword, upsert syntax
```
`SQLiteAdapter.connect()` returns exactly what `core.database.get_connection()`
returns today (`row_factory = sqlite3.Row`, `PRAGMA foreign_keys = ON`).
`SQLiteAdapter.transaction()` is `BaseRepository.transaction()`'s current
body, moved verbatim.

### 3.3 Integration
- `app/core/repository.BaseRepository` calls `get_adapter()` once (module-
  level, mirroring today's `get_connection` import) instead of importing
  `app.core.database` directly. `_all`, `_one`, `_scalar`, `_execute`,
  `transaction()` keep their exact current signatures and return shapes
  (`list[dict]`, `dict | None`, scalar, `lastrowid`) — **no repository
  subclass changes**.
- `app/core/database.get_connection()` **stays** as a public function
  (used by `init_db()`, tests, and the migration runner) and internally
  delegates to `SQLiteAdapter` — a compatibility shim, same pattern used
  when `db.py` became `core/database.py` in the original refactor
  (`TARGET_ARCHITECTURE.md` §2 Stage 3).

### 3.4 What does NOT change (strengthened per Revision 6)
- The migration runner (`app/core/migrations/runner.py`) is **unchanged**
  — it keeps writing SQLite DDL directly, exactly as today.
- **No declarative table/column spec is built.** ADR-002 §3 Option C
  mentions this as a *future, not-Sprint-4* mechanism only; Sprint 4 does
  not implement it.
- **No ORM. No Alembic. No PostgreSQL, MySQL, or SQL Server adapter.**
  `get_adapter()` has exactly one branch (`sqlite`) today; any
  `if engine == "postgres"` branch is a documented comment, not code
  (Article IV §3 — no dead scaffolding).
- No repository's SQL text changes. No migration file changes. No new
  runtime dependency.

## 4. Part C — `StorageProvider` protocol (revised, Product Owner Revision 4)

### 4.1 Module shape
```
app/core/storage/
├── __init__.py            # get_storage() -> StorageProvider, selected by config (local only today)
├── base.py                # StorageProvider Protocol (universal — cloud-compatible)
└── local_disk_provider.py # LocalDiskStorageProvider — wraps today's os/shutil calls verbatim,
                            #   plus a local-only helper not on the Protocol
```

### 4.2 Interface

**Universal `StorageProvider` Protocol** (every current and future
provider implements exactly this — no more):
```python
class StorageProvider(Protocol):
    def save(self, key: str, data: bytes) -> str: ...      # returns a storage URI
    def open(self, uri: str) -> bytes: ...
    def delete(self, uri: str) -> None: ...
    def url_for(self, uri: str, expires_in: int | None = None) -> str | None: ...
```
`absolute_path()` is **not** part of this Protocol (corrected from the
original plan) — a cloud object (S3 key, Azure Blob, GCS object) has no
local absolute filesystem path, so requiring it on the universal
interface would make every future non-local provider a partial, leaky
implementation.

**Local-only helper (not part of the Protocol):**
```python
class LocalDiskStorageProvider:
    ...
    def local_path(self, uri: str) -> str: ...   # local-disk-specific; not on StorageProvider
```
Call sites that currently need a raw filesystem path — e.g. handing a
path to an OS "open file" action or a print-preview call — call
`local_path()` directly against the concrete `LocalDiskStorageProvider`
instance (not through the `StorageProvider` Protocol type), and are
documented inline as a **known local-only dependency**. When a non-local
provider is ever introduced, those specific call sites (not the Protocol)
are what will need redesigning (e.g. to `url_for()` + a temporary local
download) — that redesign is explicitly out of scope for Sprint 4.

`LocalDiskStorageProvider.save()` reproduces
`attachments.service.add_attachment`'s exact folder convention
(`attachments/patient_<reg_no>/<stem>_<timestamp><ext>`) and
`backup.service.backup_now`'s exact `backups/backup_YYYY_MM_DD[_HHMMSS].zip`
convention. The returned URI is the same relative path string stored in
`attachments.file_path` today — **on-disk layout and DB values are
unchanged**, so existing clinic data opens identically after upgrade.

### 4.3 Integration
- `app/modules/attachments/service.py`: `add_attachment`/`delete_attachment`
  call `storage.save/delete` instead of `os.makedirs`/`shutil.copy2`/
  `os.remove` directly. Public function signatures and return values are
  unchanged. `attachments.service.absolute_path()` — the one existing
  public function that needs a raw filesystem path — calls
  `LocalDiskStorageProvider.local_path()` directly (§4.2), documented
  inline as the known local-only dependency; it is **not** promoted to
  the `StorageProvider` Protocol.
- `app/modules/backup/service.py`: `backup_now` calls `storage.save` for
  the **destination write only** (§4.4/Backup boundary). Archive
  *construction* (reading `data/wise_pms.db` and walking `attachments/`
  into a zip) remains a local filesystem operation — unchanged from
  today, because that step depends on the database engine and local
  attachment tree, not on the storage destination.
- New Settings module (§2.3) is the first net-new caller, exercising the
  provider on a fresh, non-security-sensitive code path (a logo image)
  before the two existing services are migrated onto it in the same
  sprint.

### 4.4 Backup boundary (new, Product Owner Revision 5)

```
Backup Builder (local filesystem walk: db file + attachments/ tree
                → zip bytes — UNCHANGED from today)
  ↓
Backup Artifact (the zip bytes)
  ↓
StorageProvider.save()          ← Sprint 4 abstracts exactly this step
  ↓
Local Disk (today, Production-supported)
S3 / GCS / Azure Blob (later — Architecture-ready only, NOT built)
```

Sprint 4's `StorageProvider` does **not** constitute a complete cloud
backup system. It abstracts only the destination write of an
already-built archive. Cloud backup (writing to S3/GCS/Azure, or
backing up a non-SQLite database) is **not implemented now** and is a
future, separately approved phase.

### 4.5 What does NOT change
No file moves, no path convention changes, no new dependency. `NAS`/`S3`/
`AzureBlob`/`GCS`/`MinIO` providers are documented extension points in
ADR-002 §5.1, not code.

## 5. Part D — Configuration boundary (new, Product Owner Revision 3 & 7)

This is its own scope item (distinct from Part A's Settings UI) precisely
so it is reviewed and tested as an explicit boundary, not an incidental
side effect of Parts B/C:

- **`get_adapter()` and `get_storage()` selection is a hardcoded code
  branch in Sprint 4** (`sqlite`, `local` respectively) — there is no
  environment variable, no `settings`-table column, and no Settings UI
  control for either. A second option in either function is not added
  until a real deployment needs it (ADR-002 §3/§5.1), and even then, the
  selection mechanism (env var vs. a future Administrator UI) is a
  decision for that later phase, not assumed here.
- **The Settings UI (Part A) cannot, by construction, change which
  adapter or provider is active** — `SettingsRepository`/`service` never
  reads or writes any adapter/provider selection value; the field
  whitelist (§2.3) has no such field.
- **The `backup_path` column already in the `settings` table stays
  read-only** in Sprint 4 (§2.3) — its existence predates this plan and
  is not repurposed as a user-facing destination picker.
- This boundary is enforced by a test (`SPRINT4_TESTING_PLAN.md` §2 —
  field-whitelist test) so a future edit cannot silently reintroduce a
  security-sensitive Settings field without failing CI.

## 6. Sequencing within Sprint 4

1. `DatabaseAdapter` + `SQLiteAdapter` (Part B) — foundation, touches
   `core/repository.py`, so land and green the full suite before Part A/C
   build on top of it.
2. `StorageProvider` + `LocalDiskStorageProvider` (Part C) — independent
   of Part B; can proceed in parallel once Part B's pattern is agreed.
3. Configuration boundary (Part D) — documented and test-enforced
   alongside Parts B/C, before Part A's UI exists, so the whitelist test
   exists before there is a form to whitelist.
4. Settings module (Part A) — consumes both: `SettingsRepository` uses the
   new adapter path (automatically, via `BaseRepository`); logo upload
   uses the new storage provider directly; field whitelist enforced from
   the first commit.
5. Migrate `attachments.service` onto `StorageProvider`.
6. Migrate the backup **destination write** onto `StorageProvider` (§4.4)
   — kept as its own step, distinct from attachments, matching the
   finalized 10-item scope (`SPRINT4_RECOMMENDATION.md` §3).

## 7. Compatibility & rollback

Every change in this plan is a **pure refactor**: same SQL, same file
layout, same public function signatures, same regression-golden output.
If any milestone produces a golden diff beyond the intentional new
`settings` route/view entries the router-contract test expects, that is a
bug to fix before merge, not an intentional change to document. Rollback
for any milestone is `git revert` of that milestone's commit — no data
migration is ever involved (no new tables, no altered columns).
