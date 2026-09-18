# ADR-002 — Cloud-Ready Architecture (Multi-Environment, Multi-Database, Multi-Provider)

**Status:** Proposed (Product Owner review) · **Date:** 2026-08-07
**Revision 1:** 2026-09-18 — Product Owner requested edits applied (readiness-
tier language, SQLite network rule, Settings security boundary, StorageProvider
interface correction, backup boundary, migration-scope tightening). See
`SPRINT4_RECOMMENDATION.md` and the revision's Final Report for the full
change list.
**Revision 2:** 2026-09-18 — Sprint 4 Implementation Authorization's Final
Planning Correction applied: readiness tiers finalized to the exact three
terms (Production-supported / Conditionally permitted-temporary /
Architecture-ready — §0), the canonical deployment-tier table and the
verbatim single-machine-clinic-server rule inserted at §8.0, and a prior
inconsistency corrected (this ADR previously and incorrectly implied
single-machine Clinic Server was Production-supported in §0 and
Architecture-ready in §8's old matrix; it is **Conditionally permitted /
temporary**, and only that). **Approved by Product Owner — implementation
authorized (Sprint 4 Implementation Authorization). Planning documents are
being committed and a planning PR opened per that authorization's required
Git sequence; implementation does not begin until that PR is merged into
`main`.**
**Extends:** ADR-001 (Consultation Domain), ADR-0005 (Repository seam), ADR-0008
(Migration runner), Product Constitution Articles III/IV/VII.
**Context:** Sprint 3 (Consultation narrative editors + autosave) is merged.
Before Sprint 4 clinical modules are approved, this ADR defines the
target architecture that lets WiseOS Health's business logic be written
**once**, against stable interfaces, so that it does not need rewriting to
reach Local Desktop, Clinic Server, VPS, Docker, Kubernetes, AWS, Azure,
Google Cloud, Railway, Render, and to run against SQLite, PostgreSQL, MySQL,
SQL Server, or a managed Cloud SQL, with pluggable file storage and a single
AI egress gateway supporting both clinic-owned and WiseOS-managed API keys.

**This ADR designs. It does not implement.** No code, migration, or
dependency changes ship with it. SQLite remains the only database engine
in use; local disk remains the only storage backend in use; no AI/OCR
provider is implemented. Await Product Owner approval before any Sprint 4
implementation begins.

---

## 0. Readiness tiers (vocabulary used throughout this ADR)

Per Product Owner Revision 1 (and reaffirmed, precisely, in the Sprint 4
Implementation Authorization), this ADR must never imply that an untested
deployment target or database engine is already usable. Every claim about
a target/engine/provider in this document uses one of three tiers,
**used precisely and exactly as defined here — "cloud-ready" is never
used to mean "cloud-supported":**

| Tier | Meaning |
| ---- | ------- |
| **Production-supported** | Currently implemented and supported for the stated deployment. |
| **Conditionally permitted / temporary** | Allowed under explicit limitations but not the target architecture. |
| **Architecture-ready** | The architecture provides a boundary that could support the future implementation, but the implementation itself is NOT currently supported. |

No target may be described as more than the tier that is actually true
today. Nothing in §4–§10 elevates any target above **Architecture-ready**
until a concrete adapter/provider for it is actually built and deployed/
verified as **Production-supported** in a later, separately approved
phase. A target may sit at **Conditionally permitted / temporary** only
where §8.1's explicit rule allows it — this is not a stepping stone tier
between the other two; it is its own bounded exception.

**Today, the only Production-supported configuration is:** SQLite +
Local Disk + Local Desktop. **Single-machine Clinic Server is
Conditionally permitted / temporary, not Production-supported** — see
§8.1/§8.2, and do not weaken or reinterpret that distinction anywhere in
this document set.

---

## 1. Problem statement

The Sprint 2/3 refactor (ADR-0003–ADR-0005, ADR-0009) gave WiseOS Health a
clean vertical-slice layering (`views → controllers → services →
repositories → core`) and a working migration runner (ADR-0008). That
work was scoped to **behavior-preserving structure**, not **deployment
independence**. Verified against the current code:

- `app/core/database.py:get_connection()` returns a raw `sqlite3.Connection`
  and is imported directly by `app/core/repository.BaseRepository`. There is
  no interface between a repository and SQLite — swapping engines today
  means editing `core/database.py` and every migration's DDL.
- Migrations (`app/core/migrations/v0001_initial.py`,
  `v0002_consultations.py`) are hand-written SQLite DDL strings
  (`INTEGER PRIMARY KEY AUTOINCREMENT`, `PRAGMA foreign_keys`). This syntax
  is not portable to PostgreSQL/MySQL/SQL Server without a translation
  layer.
- `app/modules/attachments/service.py` and `app/modules/backup/service.py`
  call `os.makedirs`, `shutil.copy2`, `os.remove`, `zipfile` directly
  against local paths from `app/config/paths.py`. There is no storage
  interface at all — not even a stub.
- No AI, OCR, WhatsApp, Email, SMS, or Payment code exists. `docs/modules/AI.md`
  describes a target **AI Gateway** design (see also ADR-001 §7) but no
  `app/modules/ai/` package exists yet.
- There is no API key storage, no encryption-at-rest utility, and no RBAC
  enforcement (`users.role` is decorative — `KNOWN_LIMITATIONS.md` L4).
- Packaging targets Windows desktop only (PyInstaller). There is no
  containerfile, no server entrypoint, no headless/web run mode documented,
  and Flet's session model (`page.session`) has not been evaluated for
  multi-user concurrent access.

None of this is a defect in what Sprint 1–3 built — it was correctly scoped
to the desktop-first, ₹0, single-clinician posture that was the approved
target (ADR-0001). But Article VIII of the Constitution ("no assumption may
block... Cloud Sync") and the new product direction require the *next*
layer of seams to exist **before** Sprint 4 adds more clinical modules that
would otherwise need to be touched twice.

**Decision needed:** what abstraction layers must exist, in what order, so
that (a) SQLite stays the only engine in use today, (b) business logic
(services, controllers, views) never imports a vendor SDK or engine
driver, and (c) every future clinical module (Appointments, Billing,
Inventory, OCR, AI, Telemedicine, Portal, Sync) is written once against
stable interfaces — while never overstating what is actually running or
supported today (§0).

## 2. Requirements

### Functional (design goals — Architecture-ready target, not a current-state claim)
- `app/modules/*` business logic is written so that it would not require a
  rewrite to run on: Local Desktop (Production-supported), single-machine
  Clinic Server (Conditionally permitted / temporary — §8.0/§8.1, never
  stronger than that), VPS, Docker, Kubernetes, AWS, Azure, GCP, Railway,
  Render (all Architecture-ready only). None of the targets beyond Local
  Desktop and single-machine Clinic Server is Production-supported today —
  each requires its own adapter/provider and deployment verification (§0)
  before it is used.
- `app/modules/*` business logic is written so that it would not require a
  rewrite to run against: SQLite (Production-supported today), PostgreSQL,
  MySQL, SQL Server, Cloud SQL, and future engines (all Architecture-ready
  only — §0).
- File attachments/backups/exports are written against one interface so
  that Local Disk (Production-supported today), NAS, S3, Azure Blob, GCS,
  and MinIO are Architecture-ready without an application-code change —
  none beyond Local Disk exists yet.
- Every AI request — regardless of module — passes through one gateway;
  no module imports `openai`, `anthropic`, `google.generativeai`,
  `ollama`, or any provider SDK. (No AI code exists yet — see §6.5.)
- A clinic can configure its own provider API keys (Mode A) **or** consume
  a WiseOS-managed subscription plan (Mode B), switchable without a code
  change, once that phase is built (§6.5 — not Sprint 4).

### Non-functional (evaluation axes, per ADR-001 convention)
Portability · Testability · Security (secrets, PHI) · Operability
(observability, migrations-on-deploy) · Offline-first preservation ·
Implementation risk · Reversibility.

### Constraints (from Product Constitution / `.ai/ARCHITECTURE_RULES.md`)
- Dependency direction stays `views → controllers → services →
  repositories → core`; nothing lower imports anything higher.
- SQL lives only in repositories; narrative stays authoritative; nothing
  clinical is physically deleted; every mutation is audited.
- External providers sit behind an interface; secrets never committed;
  offline/₹0 remains the default; cloud is additive, never assumed.
- No behavior change without an updated regression golden + CHANGELOG +
  DECISIONS entry in the same commit (rule 12/13).
- **Security-sensitive configuration** (database engine/connection,
  storage-provider selection, backup destination, API keys, RBAC,
  permissions) is never exposed through an unauthenticated-by-role UI
  surface (§5.2, §6.6) — new in this revision, per Product Owner
  Revision 3.

---

## 3. Architecture options — the database seam

### Option A — Keep `BaseRepository` → raw `sqlite3` (status quo)
Repositories call `get_connection()` which returns `sqlite3.Connection`
directly; SQL text is SQLite dialect.

- **+** Zero work now; simplest for a single-engine product.
- **−** Every future engine requires touching every repository and every
  migration file. The "repository is the sync/portability seam" claim in
  ADR-0005 is only half true today — it centralizes *call sites*, not
  *dialect*. This is the option the new product direction explicitly
  rejects.

### Option B — Adopt a full ORM (SQLAlchemy Core/ORM or similar)
Replace hand-written SQL with an ORM; let the ORM's dialect layer handle
portability.

- **+** Mature, well-trodden path to multi-engine support; connection
  pooling, migrations (Alembic) come largely for free.
- **−** Heavy dependency addition for a project whose Constitution
  (Article VII) prizes a minimal, offline, ₹0-cost footprint and whose
  domain logic is already comfortable with plain SQL + `RowModel`
  dataclasses. Would force a rewrite of every repository and every
  migration file **now**, which the STOP conditions on this review
  explicitly forbid ("do not change the database engine yet"). Highest
  implementation risk and largest single diff of any option.
  **Rejected outright per Product Owner Revision 6: no ORM, no Alembic,
  in this or any Sprint 4 revision.**

### Option C — Thin `DatabaseAdapter` protocol + SQL-portability discipline (recommended)
Introduce a small `DatabaseAdapter` interface (`connect()`, `execute()`,
`executemany()`, `transaction()`, plus a `Dialect` describing
placeholder style, autoincrement syntax, and upsert syntax) between
`BaseRepository` and the engine driver. `SQLiteAdapter` is the **only**
concrete implementation shipped now — it wraps the existing `sqlite3`
calls verbatim, so behavior is byte-identical. Repository SQL is written
against a documented **portable SQL subset** (ANSI types, no
SQLite-only pragmas in query code — pragmas stay isolated to the adapter).

A future, **not-Sprint-4** mechanism could move migrations from raw DDL
strings to a small declarative table/column spec (`Column`, `Table`,
`Index` descriptors already shaped like `RowModel`) that each adapter
would render into its own dialect at apply time. **This declarative spec
is design commentary only — it is explicitly out of scope for Sprint 4
(Product Owner Revision 6).** `PostgresAdapter`, `MySQLAdapter`,
`SqlServerAdapter` are documented extension points (per Article IV §3 "no
dead scaffolding" — they are not stubbed until a real engine is added and
a real deployment requires it).

- **+** Repositories stop importing `sqlite3` directly; the interface is
  the actual seam ADR-0005 intended. No new runtime dependency. The
  existing regression golden, migration runner, and `BaseRepository`
  call patterns are preserved almost verbatim — lowest-risk path
  compliant with "do not change the engine yet." A future engine is
  additive (new adapter file + its own test suite), never a rewrite.
- **−** More design discipline required up front (portable-SQL subset
  must be documented and enforced by review/lint, since SQLite is
  permissive about things Postgres/MySQL are not — e.g. implicit type
  coercion, `AUTOINCREMENT` vs `SERIAL`/`IDENTITY`). This is accepted:
  it is design cost paid once, not per-repository migration cost paid
  per engine later.

### Trade-off summary

| Axis | A: status quo | B: full ORM | C: adapter protocol (rec.) |
| ---- | -------------- | ----------- | --------------------------- |
| Portability | ✗ single engine | ✓✓ | ✓ (declared subset + adapters, Architecture-ready) |
| Implementation risk *today* | ✓ none | ✗ large rewrite now | ✓ near-zero (wraps existing code) |
| New dependency | ✓ none | ✗ heavy (SQLAlchemy) | ✓ none |
| Matches "don't change engine yet" | ✓ | ✗ forces engine-facing rewrite | ✓ SQLite-only, unchanged behavior |
| Long-term engine addition cost | ✗ rewrite every repo | ✓ mostly free | ✓ one new adapter + tests, only when needed |
| Fit with existing `RowModel`/`BaseRepository` idioms | ✓ | ✗ replaces them | ✓ extends them |

**Decision: Option C.** `SQLiteAdapter` ships as the sole implementation
this phase (Production-supported today; every other engine stays
Architecture-ready only). `Postgres`/`MySQL`/`SqlServer` adapters are
documented extension points built only when a real deployment needs them
— **not in Sprint 4, and no ORM/Alembic ever, per Revision 6, unless a
future ADR explicitly revisits that decision.**

---

## 4. Target layer model

```
UI (Flet views)
  ↓
Controller            orchestrates a screen: calls services, navigates
  ↓
Service               business rules, validation, workflow, audit
  ↓
Repository            SQL against the portable subset, per aggregate
  ↓
DatabaseAdapter        connection lifecycle, dialect, transactions
  ↓
SQLite (Production-supported) · PostgreSQL · MySQL · SQL Server · Cloud SQL · future
                        (all Architecture-ready only — §0)
```

Business logic (services, controllers, views) never imports `sqlite3`,
`psycopg`, `pymysql`, `pyodbc`, or any driver. Only
`app/core/db_adapters/*.py` may.

## 5. Storage architecture

Same shape as the database seam. `app/modules/attachments/service.py` and
`app/modules/backup/service.py` currently call `os`/`shutil` directly —
this is the second concrete gap the new product direction flags.

### 5.1 `StorageProvider` protocol (revised — Product Owner Revision 4)

The universal interface must be cloud-compatible: a cloud object (S3 key,
Azure Blob, GCS object) does not necessarily have a local absolute
filesystem path, so **`absolute_path()` is removed from the universal
protocol**:

```
save(key: str, data: bytes) -> str        # returns a storage URI
open(uri: str) -> bytes
delete(uri: str) -> None
url_for(uri: str, expires_in: int = None) -> str | None   # signed URL where applicable
```

Any local-filesystem-specific need (e.g. handing a raw path to an OS
"open file" dialog or a print-preview call) is **not** a universal
storage capability. It is isolated to a local-storage-specific helper —
e.g. `LocalDiskStorageProvider.local_path(uri) -> str` — that exists only
on that concrete class, is never called through the `StorageProvider`
Protocol type, and is documented as a capability that a non-local
provider (S3/Blob/GCS/MinIO) does not have to implement. Call sites that
currently need a raw path (print preview, direct file open) are flagged
as a known local-only dependency to be redesigned (e.g. via `url_for()` +
a temporary local download) whenever a non-local provider is actually
introduced — that redesign is out of scope for Sprint 4.

`LocalDiskStorageProvider` (wraps today's `attachments/patient_<reg_no>/`
and `backups/` conventions verbatim) is the only implementation shipped
now — **Production-supported**. `NasStorageProvider`, `S3StorageProvider`,
`AzureBlobStorageProvider`, `GcsStorageProvider`, `MinioStorageProvider`
are documented extension points (**Architecture-ready only**), selected by
a single configuration point (§5.2), never inferred by module code.
`attachments.service` and `backup.service` are rewritten (Sprint 4, per
the finalized scope in §11) to call `storage.save/open/delete` instead of
`os`/`shutil`; the on-disk layout does not change, so
`LocalDiskStorageProvider` is byte-for-byte compatible with existing
clinic data on first upgrade.

### 5.2 Configuration boundary (new — Product Owner Revision 3 & 7)

Which adapter/provider is active is **system configuration**, not a
clinic-editable setting. In Sprint 4 there is exactly one valid value for
each (`sqlite`, `local`), selected by a hardcoded branch in
`get_adapter()`/`get_storage()` — there is no environment variable, no
`settings`-table column, and **no Settings UI control** for this. Any
future exposure of database engine, storage-provider, backup-destination,
or credential configuration to an operator is a distinct, RBAC-gated
Administrator/Security surface (Constitution Art. VI §3), built only once
RBAC (F3) and encryption at rest (F7) exist — never the F2 clinic-profile
Settings UI. See §6.6 for the equivalent rule on API keys, and
`SPRINT4_TECHNICAL_PLAN.md` Part D for the Sprint 4 implementation of this
boundary.

### 5.3 Backup boundary (new — Product Owner Revision 5)

```
Backup Builder (assembles db + attachments into an archive — local
                filesystem walk, unchanged from today)
  ↓
Backup Artifact (the zip bytes)
  ↓
StorageProvider.save()
  ↓
Local Disk (today, Production-supported)
S3 / GCS / Azure Blob (later, Architecture-ready only — not built)
```

Sprint 4's `StorageProvider` abstracts **only the destination write** of
the already-built backup artifact. It does **not** constitute a complete
cloud backup system: archive *construction* (reading `data/wise_pms.db`
and walking `attachments/` into a zip) remains a local-filesystem
operation, because Sprint 4 does not change the database engine or
introduce network-attached storage sources. Cloud backup (writing that
archive to S3/GCS/Azure, or backing up a non-SQLite database) is
**explicitly not implemented now** and requires its own future,
separately approved phase.

## 6. AI Gateway & API key management

Restates and extends ADR-001 §7, now with the mandatory dual-mode key
management from the new product direction. **Nothing in this section is
implemented by this ADR or by Sprint 4.**

### 6.1 Single egress rule (unchanged)
Every module calls `ai_gateway.request(capability, context)`. No module
imports a provider SDK. This is enforced today by convention
(ADR-001 AR4) and must gain a CI/lint gate (grep for provider imports
outside `app/modules/ai/`) before any AI code lands.

### 6.2 Provider interface
```
AiProvider.complete(capability, context, **params) -> AiResult
```
Adapters (future, not built now): OpenAI, Claude, Gemini, OpenRouter,
Azure OpenAI, Ollama, NVIDIA NIM, and future providers — each a thin file
in `app/modules/ai/providers/`, none imported outside the gateway.

### 6.3 Mode A — Bring Your Own Key
- New table `provider_credentials` (clinic-scoped once multi-clinic
  lands; single-row scope today): `id`, `provider`, `encrypted_key`,
  `enabled`, `created_at`, `updated_at`.
- Keys are encrypted at rest using the same encryption-at-rest mechanism
  RBAC/PHI work requires (F7) — **never** stored plaintext, **never**
  committed, **never** logged. A key is decrypted only inside the
  provider adapter call, in memory, for the duration of the request.
- **Corrected per Revision 3/6.6:** BYO key configuration is **not** a
  feature of the F2 clinic-profile Settings UI. It belongs to a future,
  RBAC-gated Administrator/Security settings surface, built only after
  F3 (RBAC) and F7 (encryption) exist. The two "Settings" surfaces are
  distinct: F2 (clinic profile — Sprint 4) and the future Security
  Settings (credentials/providers — a later, separately approved phase).

### 6.4 Mode B — WiseOS Managed AI
- `subscription_plans` (Basic/Professional/Enterprise: limits, price) and
  `ai_usage_events` (append-only, mirrors `audit_logs` conventions: who,
  what capability, tokens/cost, timestamp) back plan enforcement and
  billing. Table shapes are designed here; billing integration is a
  future phase (Payment Gateway abstraction, §7).
- The Gateway resolves Mode A vs Mode B per clinic setting
  (`ai_mode = byo | managed`) and per provider — **callers never branch
  on mode**; `ai_gateway.request(...)` is mode-agnostic by construction,
  satisfying "switch between BYO and Managed without changing business
  logic."

### 6.5 What this ADR does NOT authorize
No AI/OCR code, no provider adapter, no `provider_credentials` migration,
no encryption utility ships as part of this ADR. These are a future
phase (§11), sequenced behind RBAC (F3) and encryption at rest (F7), per
`.ai/ARCHITECTURE_RULES.md` rule 17 and Security Rule 1.

### 6.6 Security-sensitive configuration rule (new — Revision 3)
Database configuration, storage-provider configuration, backup-destination
configuration, API keys/credentials, RBAC/permissions, and other security
settings are **never** exposed through the Sprint 4 (F2) clinic-profile
Settings UI. They require an Administrator role (RBAC, F3) and, for
secrets, encryption at rest (F7) — both absent today. This rule applies
retroactively to every mention of "Settings UI" elsewhere in this ADR and
in the Sprint 4 planning documents: any prior wording suggesting F2
Settings hosts provider/storage/backup/credential configuration is
superseded by this section.

## 7. External-dependency abstraction rule (Article III §9, generalized)

Every vendor integration gets the same shape: a protocol in
`app/core/<concern>/`, adapters that implement it, and a single
configuration point (§5.2-style boundary, never a general-access UI)
selecting the active adapter. No controller or service imports a vendor
SDK.

| Concern | Interface (future name) | Adapters (future) | Status today |
| ------- | ------------------------ | ------------------ | ------------- |
| Database | `DatabaseAdapter` | SQLite (Production-supported), Postgres, MySQL, SQL Server, Cloud SQL (Architecture-ready only) | SQLite hardwired — gap this ADR closes |
| Storage | `StorageProvider` | Local Disk (Production-supported), NAS, S3, Azure Blob, GCS, MinIO (Architecture-ready only) | Local disk hardwired — gap this ADR closes |
| AI | `AiProvider` via `ai_gateway` | none built | Design only (ADR-001) — no code |
| OCR | `OcrEngine` | none built | Design only (`docs/modules/OCR.md`) — no code |
| WhatsApp | `MessagingProvider` | none built | Design only (`docs/modules/WhatsApp.md`) — no code |
| Email | `EmailProvider` | none built | Not designed yet |
| SMS | `SmsProvider` | none built | Not designed yet |
| Payment Gateway | `PaymentProvider` | none built | Not designed yet |
| Cloud Sync | `SyncTransport` | none built | Design only (§9) — no code |
| Authentication | `AuthProvider` (local bcrypt today; future SSO/OAuth) | local (Production-supported) | Local bcrypt hardwired in `authentication/service.py` — acceptable gap (single-tenant desktop), revisit only if SSO is required |

Database and Storage are the two gaps this ADR closes with concrete
designs (§3, §5) because they are the two every existing module already
depends on. AI/OCR/WhatsApp/Email/SMS/Payment/Sync are **not implemented
in any form** — this table exists so Sprint 4+ modules are written
against the right shape from day one, per the "no assumption may block"
rule, without building the abstraction before there is a second
implementation to justify it (YAGNI at the adapter-count level, not at
the interface-shape level).

## 8. Deployment target matrix

**Revised per Product Owner Revision 1 & 2, and finalized per the Sprint 4
Implementation Authorization's Final Planning Correction.** Every row
uses exactly the three tiers defined in §0 — **Production-supported**,
**Conditionally permitted / temporary**, or **Architecture-ready** — and
none is weakened or reinterpreted below.

### 8.0 Canonical deployment-tier table (required, verbatim)

| Deployment | Database | Readiness |
| ---------- | -------- | --------- |
| Local Desktop | SQLite | Production-supported |
| Single-machine clinic server | SQLite | Conditionally permitted / temporary |
| Multi-user/networked clinic | Server-grade DB | Not yet supported |
| Cloud / VPS / Docker / Kubernetes | Server-grade DB | Architecture-ready only |
| PostgreSQL / MySQL / SQL Server etc. | Future adapter | Architecture-ready only |

> **Single-machine clinic-server deployment with SQLite is permitted only
> where the database remains local to that machine and is not
> concurrently accessed through a network filesystem. It is a
> transitional deployment option, not the target multi-user
> architecture.**

This table and this quoted rule are the governing statement for every
other deployment claim in this ADR and in the rest of the Sprint 4
document set. No other section may state or imply a stronger readiness
than this table for any row.

### 8.1 SQLite deployment rule (mandatory, non-negotiable)

> **SQLite is not a multi-user network database and must not be deployed
> as a shared database file over a network filesystem.** SQLite's
> file-level locking is not reliable over SMB/NFS/network-attached shared
> drives; doing so risks silent data corruption. This rule is
> non-negotiable and applies regardless of deployment target.

### 8.2 Elaboration (detail beneath the canonical table — §8.0 governs; this only elaborates it)

| Target tier | Database | What changes | Readiness (must match §8.0) |
| ----------- | -------- | ------------- | :-------: |
| Local Desktop | SQLite, on local disk of that one machine | none (today's mode) | **Production-supported** |
| Single-machine clinic server (one process, one machine, no network DB access) | SQLite | `STORAGE_PROVIDER=local`; still single-process; DB file stays local to that machine — never opened over SMB/NFS from a second machine; transitional, not the target architecture (§8.0 quoted rule) | **Conditionally permitted / temporary** |
| Multi-user / networked clinic (more than one machine/process needs concurrent write access) | Server-grade DB (Postgres/MySQL/SQL Server/Cloud SQL) — SQLite is disallowed per §8.1 | No `DatabaseAdapter` implementation exists for any server-grade engine yet; container/service topology not built | **Not yet supported** |
| VPS / Docker | Server-grade DB | No containerfile exists; `DatabaseAdapter` would need to select a server-grade engine that does not exist yet | **Architecture-ready only** |
| Kubernetes | Server-grade DB | No container image or manifests exist | **Architecture-ready only** |
| AWS / Azure / GCP | Server-grade DB (managed RDS/Cloud SQL/Azure Database) | No managed-DB adapter or managed object-storage provider exists | **Architecture-ready only** |
| Railway / Render | Server-grade DB (platform-provided Postgres) | No adapter exists | **Architecture-ready only** |
| Cloud / multi-instance (any target running more than one app instance concurrently) | Server-grade DB | No adapter exists | **Architecture-ready only** |
| PostgreSQL / MySQL / SQL Server (as engines, independent of hosting target) | Future adapter | `PostgresAdapter`/`MySQLAdapter`/`SqlServerAdapter` are documented extension points only (§3) — none is written | **Architecture-ready only** |

**Concurrency note:** SQLite is single-writer and, per §8.1, is never a
shared network database. The `DatabaseAdapter` seam (§3) exists precisely
so that when a real multi-user or networked deployment is scheduled, a
server-grade engine adapter is added — additively, without touching
business logic — rather than retrofitted under pressure. **Flet's session
model** (`page.session`) has not been load-tested for concurrent
multi-user web mode; this remains an open question for whichever future
sprint first targets a networked deployment, not resolved here.

**Restated for emphasis:** the existence of the `DatabaseAdapter` and
`StorageProvider` abstractions (§3, §5) does not, by itself, constitute
cloud support. An abstraction/interface existing is what makes a target
**Architecture-ready** — it is never, on its own, grounds to claim
**Production-supported** or even **Conditionally permitted / temporary**
for that target. Only §8.0's table decides that, row by row.

## 9. Future synchronization (design only)

```
Offline write → Sync Queue → Synchronization Engine → Cloud
                                    ↓
                          Conflict Resolution → Audit → Version History
```

- **Sync Queue:** an additive `sync_queue` table (future migration, not
  now) recording `entity_type, entity_id, operation, payload, status,
  created_at` for every local mutation once a clinic opts into sync.
  Populated by the repository layer (the seam ADR-0005 already
  designated) via a write-through hook — services and views are
  unaffected.
- **Synchronization Engine:** a future service that drains the queue
  against `SyncTransport` (§7), idempotent per queue row (safe to retry).
- **Conflict Resolution:** every synced table already carries
  `created_at`/`updated_at` (ADR-0009 convention) as the basis for
  last-write-wins or field-level merge, decided per-aggregate when sync
  is actually built — not decided here.
- **Audit / Version History:** `audit_logs` already records every
  mutation; sync reuses it rather than inventing a parallel log.
  Version history (row-level diffs) is a future additive table, not
  required for Sprint 4.
- **Offline remains the default.** Per Constitution Article VII, sync is
  an opt-in module layered on the repository seam — never a dependency
  of core CRUD flows.
- Sync inherently requires a server-grade, network-reachable database
  (§8.1 rules out syncing against a shared SQLite file) — so Sync is
  necessarily sequenced after a real server-grade `DatabaseAdapter` is
  Production-supported somewhere, consistent with §11.

Nothing here is implemented. This section exists so §3 (DatabaseAdapter)
and §5 (StorageProvider) are not designed in a way that later blocks a
sync engine from reading their write path.

## 10. Future clinical module compatibility check

Every module named in the new product direction is checked against the
target architecture (§4–§9); each is **Architecture-ready** (none requires
a redesign of the layering) — this is not a claim that any of them are
built:

| Module | Compatibility (Architecture-ready) |
| ------ | -------------- |
| Patient Portal, Telemedicine | New modules behind Auth (§7) + existing repository/service layers; UI-agnostic domain layer (Constitution Art. IV §6) already supports a non-Flet or Flet-web front end |
| Inventory (WHIMS), PillFill | New vertical slices; PillFill's hardware integration gets its own adapter interface when scoped |
| Protocol Engine, OCR, AI Assistant | Feed through `ai_gateway`/`OcrEngine` (§6/§7); advisory-only per Constitution Art. II §6 |
| Appointments, Waiting Queue, Billing | New vertical slices; Billing's Payment Gateway is an adapter (§7) |
| WhatsApp | `MessagingProvider` adapter (§7) |
| Analytics, Reports | Read models over repositories (Constitution Art. IV §5) — engine-agnostic by construction once §3 lands |
| Cloud Sync | §9 — additionally requires a server-grade `DatabaseAdapter` to be Production-supported first (§8.1) |
| Public API | A new presentation layer calling the same services/controllers — no service rewrite (Constitution Art. IV §6) |
| Mobile Apps | Same domain layer via API or a Flet mobile target |
| Multi-clinic | Additive nullable `clinic_id` per table (ADR-001 §11, Constitution Art. VIII §5) — every table already carries the right shape for this |

## 11. Sequencing this ADR implies

Extends the Roadmap build order (`.ai/PRODUCT_DIRECTION.md`) with the
architecture work this ADR adds. This is a sequencing **input** to
`SPRINT4_RECOMMENDATION.md`, not a schedule commitment. **Revised to match
the Product Owner's finalized Sprint 4 scope (Revision 7):**

1. **Sprint 4 (this phase):** `DatabaseAdapter` + `SQLiteAdapter` (§3) →
   `StorageProvider` + `LocalDiskStorageProvider` (§5.1) → the
   Configuration boundary (§5.2) → the Safe Settings UI (F2, clinic
   profile only — §6.6) → migrate `attachments.service` onto
   `StorageProvider` → migrate the backup *destination write* onto
   `StorageProvider` (§5.3) → tests → documentation. All behavior-
   preserving; zero engine change; zero storage-backend change; zero new
   dependency unless explicitly justified.
2. **Sprint 5 (proposed):** F3 RBAC — required before any networked
   surface (Constitution Art. VI §3), before F7, and before any
   Administrator/Security settings surface (§5.2, §6.6) can exist.
3. **Sprint 6+ (proposed, not scheduled):** F7 Encryption at rest —
   required before `provider_credentials` (BYO keys) or any PHI leaves a
   single trusted machine.
4. **Later (not scheduled):** AI Gateway + `provider_credentials` + Mode
   A/B (§6) — only after 2–3 are in place.
5. **Later (not scheduled), and only once a server-grade `DatabaseAdapter`
   is Production-supported (§8.1):** Sync Queue / Synchronization Engine
   (§9).

## 12. Risks

| ID | Risk | Mitigation |
| -- | ---- | ---------- |
| CR1 | "Portable SQL subset" is under-specified and repositories quietly reintroduce SQLite-only syntax | Document the subset explicitly when `DatabaseAdapter` ships; lint/grep gate for banned constructs (`AUTOINCREMENT`, SQLite-only pragmas) outside the adapter |
| CR2 | Adapter/provider seams get scaffolded as empty folders before any second implementation exists, violating Article IV §3 ("no dead scaffolding") | Ship only `SQLiteAdapter`/`LocalDiskStorageProvider`; document other adapters as extension points in this ADR, not as code |
| CR3 | AI Gateway design is built but a module bypasses it once AI work starts | Same layering-grep gate used for the Consultation AI seam (ADR-001 AR4), extended to CI |
| CR4 | Encryption-at-rest (F7) is deferred past when BYO keys are wanted | Hard sequencing rule in §11 and Security.md rule 1: `provider_credentials` migration is blocked until F7 ships |
| CR5 | SQLite single-writer / network-filesystem misuse breaks silently under a future or even present networked deployment | §8.1 makes the rule explicit and non-negotiable now, not deferred; revisit engine choice only when a real multi-user target is scheduled |
| CR6 | Scope creep — a future phase tries to build DatabaseAdapter *and* StorageProvider *and* RBAC *and* Settings in one phase | `SPRINT4_RECOMMENDATION.md` scopes a single phase per the finalized 10-item list (§11); remaining items become Sprint 5+ |
| CR7 (new) | ADR/planning language is read as claiming production support for untested cloud/engine targets, misleading a future reader or reviewer | §0 readiness-tier vocabulary applied throughout; every target/engine claim in §2, §8, §10 is explicitly tiered |
| CR8 (new) | Security-sensitive configuration (DB, storage, backup destination, API keys) is accidentally exposed through the F2 Settings UI in this or a future phase | §5.2/§6.6 rule stated explicitly; Sprint 4 testing plan adds a field-whitelist test enforcing it (`SPRINT4_TESTING_PLAN.md`) |

## 13. Migration guidelines (once implementation is approved)

- `DatabaseAdapter`/`StorageProvider` land as **pure refactors**: same
  SQL, same file layout, same regression-golden output, wrapped behind
  the new interface. Any accidental behavior change is a bug, not a
  feature, and must be caught by the existing regression/model/router
  test suite before merge.
- **Sprint 4 does not implement the declarative table/column spec
  mentioned in §3 Option C.** The migration runner
  (`app/core/migrations/runner.py`) is unchanged — hand-written SQLite
  DDL, exactly as today. No ORM, no Alembic, no second dialect renderer,
  in this or any Sprint 4 revision (Product Owner Revision 6).
- No migration may target a non-SQLite dialect until a second adapter is
  actually implemented in some future, separately approved phase.
- `provider_credentials`, `ai_usage_events`, `subscription_plans`,
  `sync_queue` are **not created** until their owning phase is approved;
  this ADR fixes their shape, not their arrival date.

---

## Decision

**Adopt the target architecture in §4–§10, with every deployment
target/engine/provider explicitly tiered per §0/§8.0: Local Desktop
(SQLite + Local Disk) is Production-supported today; single-machine
Clinic Server (SQLite) is Conditionally permitted / temporary only,
never elevated further; every multi-user, networked, cloud, VPS,
Docker, and Kubernetes target, and every non-SQLite engine, is
Architecture-ready only (Not yet supported where §8.0 says so).**
Introduce a `DatabaseAdapter` protocol
(Option C, §3) with `SQLiteAdapter` as the sole implementation, and a
`StorageProvider` protocol (§5.1, revised to drop `absolute_path()` from
the universal interface) with `LocalDiskStorageProvider` as the sole
implementation, both as behavior-preserving wrappers around existing
code. Establish the Configuration boundary (§5.2) and the Security-
sensitive configuration rule (§6.6) so the F2 Settings UI never exposes
database/storage/backup/credential/RBAC configuration. Establish the
SQLite network-deployment rule (§8.1) as non-negotiable. Design (do not
build) the AI Gateway's dual-mode API key management (§6) and the future
Sync architecture (§9). No database engine change, no storage backend
change, no AI/OCR implementation, no RBAC, no encryption, and no new
runtime dependency ships with this ADR. Sequencing (§11) is a proposed
input to Sprint 4 planning, per the finalized 10-item scope in
`SPRINT4_RECOMMENDATION.md`. **Await Product Owner approval of this
revision before any implementation.**
