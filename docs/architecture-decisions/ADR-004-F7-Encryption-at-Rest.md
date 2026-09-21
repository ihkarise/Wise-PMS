# ADR-004 — F7 Encryption at Rest (Database, Attachments, Backups)

**Status:** Proposed (Product Owner review) · **Date:** 2026-09-21
**Phase:** Sprint 6 (F7 Encryption at Rest) — **planning/design only; nothing
in this ADR is implemented.**
**Extends:** ADR-001 (Consultation Domain), ADR-002 (Cloud-Ready
Architecture), ADR-003 (RBAC), ADR-0005 (Repository seam), ADR-0008
(Migration runner), ADR-0010 (DatabaseAdapter/StorageProvider seams),
Product Constitution Articles III/IV/VI/VII.
**Depends on:** the Sprint 4 `DatabaseAdapter` and `StorageProvider` seams
(ADR-002 §3/§5, ADR-0010) and F3 RBAC (ADR-003) — ADR-002 §11 sequences F7
**after** the seams and RBAC so encryption is written against the final
adapter/storage shape and so any key-management surface can be RBAC-gated
(ADR-002 §5.2/§6.6).

> **This ADR designs. It does not implement.** No code, migration, table,
> crypto utility, key store, encrypted storage provider, restore workflow,
> dependency, `requirements.txt` change, packaging change, or test change
> ships with it. `data/wise_pms.db`, `attachments/`, and `backups/` remain
> **plaintext** until a separately approved Sprint 6 implementation phase
> begins. Await Product Owner approval of this ADR and the accompanying
> `docs/planning/SPRINT6_TECHNICAL_PLAN.md` before any implementation.

> **Decision-tier legend used throughout this ADR:**
> **[APPROVED ARCHITECTURE]** — a direction the Product Owner has approved
> in this session. **[SECURITY DESIGN DECISION REQUIRED]** — a cryptographic
> or key-handling detail that must be fixed by design + specialist review at
> implementation, never guessed here. **[SECURITY REVIEW REQUIRED]** — an
> item that additionally requires specialist security review before it is
> considered production-ready. **[IMPLEMENTATION DETAIL]** — resolved at
> implementation with no scope/schema/architecture impact. **[FUTURE
> SCOPE]** — explicitly out of scope for F7.

---

## 0. Context

`docs/KNOWN_LIMITATIONS.md` L5 and `docs/SECURITY.md` both record the same
gap: **"No encryption at rest. DB, attachments, backups are plaintext …
PHI exposed to anyone with file access."** Verified against the current
tree (HEAD `cf0f1e5`):

- **Database:** `SQLiteAdapter.connect()` opens
  `sqlite3.connect(paths.DB_PATH)` with `row_factory` + `PRAGMA
  foreign_keys` and nothing else (`app/core/db_adapters/sqlite_adapter.py`).
  The single data file `data/wise_pms.db` — plus its rollback journal /
  WAL / shm side files (`.gitignore` already excludes `*.db-journal`,
  `*.db-wal`, `*.db-shm`) — stores all PHI in cleartext SQLite pages.
- **Attachments:** `attachments.service.add_attachment` reads the source
  bytes and calls `get_storage().save(rel_path, data)`;
  `LocalDiskStorageProvider` writes them verbatim under
  `attachments/patient_<reg_no>/` (`app/core/storage/local_disk_provider.py`).
  Files are plaintext; the on-disk filename leaks `reg_no`, original stem,
  and extension.
- **Backups:** `backup.service._build_archive` reads `paths.DB_PATH` and
  walks `attachments/` directly into a plaintext ZIP, then
  `get_storage().save()` writes it to `backups/`. The zip is full PHI in
  the clear, and — being a single portable file — is today the single
  largest at-rest exposure.
- **Keys/secrets:** none exist. `bcrypt` protects the `users.password_hash`
  (a one-way hash, not an F7 target). There is no key store, no encryption
  key, no recovery mechanism.
- **Dependencies:** `requirements.txt` is exactly `{flet, bcrypt}`, and
  `tests/test_layering.py::test_no_new_runtime_dependency_added` **asserts**
  that set. Python's standard library provides KDFs (`hashlib.scrypt`,
  `hashlib.pbkdf2_hmac`), `hmac`, and `secrets`, but **no AEAD symmetric
  cipher** — a fact central to §14.

Every authoritative planning document names F7 as the sequenced next
foundation item after RBAC:

- `docs/architecture-decisions/ADR-002-Cloud-Ready-Architecture.md` §11:
  Sprint 4 seams → F3 RBAC → **F7 encryption at rest** → AI Gateway /
  `provider_credentials` → Cloud Sync.
- `docs/SECURITY.md` rule 1: RBAC (F3, done) **and** encryption at rest
  (F7) must land before any networked or multi-user surface.
- ADR-002 §6.3 / CR4: `provider_credentials.encrypted_key` (BYO AI keys)
  is **blocked until F7 ships** and must reuse F7's encryption mechanism.

**Decision needed:** where database encryption sits relative to the
`SQLiteAdapter` seam; how attachment/backup encryption sits relative to the
`StorageProvider` seam; the key-management architecture and its recovery
path; how existing plaintext data migrates safely; how startup and failure
states behave; the dependency/packaging consequences; and which
cryptographic details require specialist review — all without overstating
what ships this phase or silently choosing any cryptographic primitive.

## 1. Problem statement

Wise PMS stores Protected Health Information (names, contacts, clinical
narrative, prescriptions, documents) as plaintext on the clinic machine.
The trust boundary today is **physical access to that machine**
(`SECURITY.md`). F7 must raise the cost of **offline, at-rest** compromise
— a stolen disk, a stolen database file, a stolen attachment directory, a
stolen backup — without:

- changing the `views → controllers → services → repositories → core`
  layering or forcing repositories/services to carry PHI-encryption logic;
- degrading the offline, ₹0 posture (Architecture rule 17) — all crypto
  must be fully local, no network/license service;
- introducing an unrecoverable-data failure mode (encryption without a
  viable recovery path is unacceptable — §10);
- elevating any ADR-002 §8.0 deployment tier (F7 is a **prerequisite for**,
  never an **enabler of**, networked/multi-user deployment).

## 2. Threat model

F7 protects **data at rest when the application is not running / the machine
is not in a trusted, unlocked state**. It does not defend a live, unlocked
process. Classification (from the F7 planning analysis, verified against
`SECURITY.md`):

| Threat | Classification |
| ------ | -------------- |
| Stolen database file (`.db` + journal/WAL/shm) | **Protected by F7** (given the key is not co-located in cleartext) |
| Stolen attachment directory | **Protected by F7** (content; filename/size metadata is a separate decision — §7) |
| Stolen backup archive | **Protected by F7** (independent backup key — §8) |
| Unauthorized filesystem access / disk imaged at rest | **Protected by F7** (core scenario) |
| Compromised **running** application (in-process malware while unlocked) | **Not protected by F7** — key/plaintext is in memory; needs OS hardening/EDR |
| Authenticated user exceeding their role | **Requires another control** — RBAC (F3, done) + future row-level authz (L16), not F7 |
| Malicious administrator | **Requires another control** — audit / separation of duties, not F7 |
| Lost encryption key | **F7 failure mode** — mitigated only by the mandatory recovery model (§10); not a threat F7 "solves" |
| Corrupted encrypted data | **Requires another control** — AEAD *detects* corruption; repair needs backups (§9/§11) |
| Data in transit (network) | **Not F7** — that is transport security (F8) |
| Weak passphrase brute force of an encrypted artifact | **Partially protected** — depends entirely on the KDF and passphrase strength (§13/§20) |

**F7 must not be described as solving** live-process compromise, insider/
admin misuse, authorization, transport security, or key loss.

## 3. Protected-data inventory (what F7 encrypts)

**[APPROVED ARCHITECTURE]** F7 scope is database + attachments + backups
**together** (Product Owner decision, §10 scope). Concretely:

| Data | Location today | F7 treatment |
| ---- | -------------- | ------------ |
| SQLite database | `data/wise_pms.db` (+ journal/WAL/shm, temp spill files) | Full-database encryption at the adapter boundary (§6) |
| Patient attachments | `attachments/patient_<reg_no>/…` | Per-file authenticated encryption via a storage decorator (§7) |
| Backups | `backups/backup_*.zip` (DB + attachments tree) | Independently recoverable encrypted backup artifact (§8) |
| Encryption keys / recovery material | *none today* | New protected key material (§9), never committed, never logged |

Not F7 targets: `bcrypt` password hashes (one-way); `exports/`, `logs/`
(reserved/unused, L9); `provider_credentials` (**[FUTURE SCOPE]**, ADR-002
§6.3 — reuses F7's mechanism when built).

## 4. Requirements

### Functional (design goals)
- Database, attachments, and backups are unreadable at rest without the
  clinic's key material.
- Encryption sits at the existing seams: `SQLiteAdapter` (DB) and
  `StorageProvider` (attachments/backups) — no PHI-crypto logic in
  repositories/services/controllers/views.
- A Data-Encryption-Key (DEK) is wrapped by one or more Key-Encryption
  mechanisms (envelope model, §9), including a **mandatory offline recovery
  key** (§10).
- Existing plaintext data migrates via an explicit, administrator-
  controlled, atomic, resumable, verified, idempotent process (§11).
- Backups are **independently recoverable** on a replacement machine
  (§8).
- All operation is fully offline (no network, no key server).

### Non-functional (evaluation axes, per ADR-001/002/003 convention)
Security (confidentiality, integrity/authentication, fail-closed) ·
Recoverability (no unrecoverable-loss mode) · Testability · Additivity
(schema largely unchanged) · Offline-first preservation · Windows-desktop
packaging feasibility · Implementation risk · Reversibility of the
planning decision.

### Constraints (Constitution / `.ai/ARCHITECTURE_RULES.md`)
- Dependency direction unchanged; SQL only in repositories; every mutation
  audited; narrative authoritative; nothing clinical physically deleted.
- Migrations additive/forward-only/idempotent/reversible (ADR-0008); never
  drop/rename a column an older build reads.
- No behavior change without an updated regression golden + CHANGELOG +
  DECISIONS in the **same commit** (rule 12/13) — applies at *implementation*,
  not to this planning PR.
- Security-sensitive configuration (which includes key management) is never
  on the F2 clinic-profile Settings UI; it belongs to a future RBAC-gated
  Administrator/Security surface (ADR-002 §5.2/§6.6; ADR-003 §9).
- F7 does **not** change any ADR-002 §8.0 deployment tier or relax the §8.1
  SQLite-over-network prohibition.

---

## 5. Options considered — where database encryption sits

### D1 — SQLCipher / transparent full-database encryption (CHOSEN)
Replace the stdlib `sqlite3` connection inside `SQLiteAdapter` with a
SQLCipher-backed driver; supply the key on connect (a keyed-`PRAGMA`-style
open). Encryption is page-level and transparent to all SQL above the
adapter.
- **+** Fits the existing seam exactly — `SQLiteAdapter.connect()` is the
  only place that opens the engine, and only it (plus the migration runner)
  may import the driver (`tests/test_layering.py`). Repositories, services,
  controllers, views, migrations (raw DDL via `executescript`), and the
  golden's schema queries all keep working once the connection is keyed. An
  encrypted DB file archives into a backup as-is.
- **−** Requires a **native library** (libsqlcipher / an OpenSSL-class
  crypto provider) plus a Python binding → the heaviest dependency and the
  Windows-packaging cost (§14/§15). Page-level AES adds measurable (must be
  measured, not assumed — §16) overhead.

### D2 — Application-layer encryption around stdlib `sqlite3` (REJECTED for the DB)
Keep `sqlite3`; encrypt the DB "around" SQLite (decrypt-to-temp on open /
re-encrypt on close, or per-column field encryption).
- **−** Whole-file decrypt-to-temp means a **full-session plaintext temp
  file**, defeating much of F7 and risking corruption/locking. Field-level
  encryption breaks search/sort/indexing on encrypted columns and forces
  changes across every repository — contradicting "SQL only in
  repositories, behavior-preserving" and the golden. **Rejected for
  whole-database PHI.** Field-level encryption remains a niche option for a
  *specific future secret* (e.g. `provider_credentials.encrypted_key`,
  **[FUTURE SCOPE]**), not for PHI-at-rest.

### D3 — OS/volume encryption only (BitLocker/dm-crypt) (REJECTED as sole control)
- **−** Zero application protection for a **stolen backup copied off the
  machine**, and depends on clinic IT enabling it (not guaranteed on a
  clinic laptop). May be a **complementary** control, never a substitute for
  backup encryption. **Rejected as F7's mechanism.**

**Decision — [APPROVED ARCHITECTURE]: D1 (SQLCipher / transparent
full-database encryption).** Rationale: smallest code blast radius given the
adapter seam; preserves the repository/domain architecture; keeps the
migration runner and golden model intact. This approves the **direction**;
it does **not** authorize installing SQLCipher, selecting a specific
binding, or implementing it (§14/§21).

## 6. Decision — database encryption

**[APPROVED ARCHITECTURE]** Database encryption is applied at the
`SQLiteAdapter` boundary (D1). The keyed open happens inside
`SQLiteAdapter.connect()`; nothing above the adapter changes. The key is
supplied by the key-management layer (§9) during an unlock stage that
**precedes** `init_db()`/`migrate(conn)` at startup (§12), so migrations run
against an already-keyed connection.

- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]:** the
  exact SQLCipher binding/distribution, cipher/KDF configuration exposed by
  that binding, page size, and KDF iteration settings.
- **[IMPLEMENTATION DETAIL]:** how the key is passed to the adapter
  (in-memory handoff from the key layer), and whether/how the journal/WAL
  mode interacts with encryption (the side files inherit page encryption
  under SQLCipher; confirm at implementation).
- **[FUTURE SCOPE]:** any second (server-grade) `DatabaseAdapter` — F7 does
  not build one; SQLite + Local Disk + Local Desktop stays the only
  Production-supported configuration (ADR-002 §8.0).

## 7. Decision — attachment encryption

**[APPROVED ARCHITECTURE]** Attachment encryption is applied at the
`StorageProvider` seam via an **`EncryptedStorageProvider` decorator** that
wraps `LocalDiskStorageProvider`, selected at the single configuration point
`app/core/storage/__init__.py:get_storage()` (the ADR-002 §5.2 boundary).
The byte contract is unchanged, so `attachments.service` and its repository
are untouched on the byte path:

```
save:  plaintext bytes → EncryptedStorageProvider.encrypt (AEAD)
                       → LocalDiskStorageProvider.save → ciphertext at rest
open:  LocalDiskStorageProvider.open → ciphertext
                       → EncryptedStorageProvider.decrypt/verify → plaintext bytes
```

Design requirements the plan must satisfy:
- **AEAD / integrity** — authenticated encryption so tampering/corruption is
  detected on `open()`.
- **Atomic writes** — write ciphertext to a temp name then atomic rename; an
  interrupted save never leaves a half-encrypted file.
- **Corruption / wrong key** — AEAD verification failure surfaces a clear
  "attachment unreadable" error, never silent wrong-plaintext.
- **Metadata / filename / size / directory leakage** — content encryption
  does not hide file size (±block), per-patient file counts, or the
  `patient_<reg_no>` directory structure; whether to also opaque the on-disk
  **filename** (which today leaks `reg_no`, stem, extension) is a design
  choice.
- **Streaming vs whole-file** — the current code reads whole files into
  memory; large attachments (imaging) may need chunked/streaming AEAD.

**The `local_path()` / `absolute_path()` problem (critical).** The
attachment viewer/print path needs a **real filesystem path**
(`attachments.service.absolute_path` → `LocalDiskStorageProvider.local_path`,
allow-listed in `tests/test_layering.py`), but the on-disk file is now
ciphertext — the OS viewer cannot open ciphertext directly. **[APPROVED
ARCHITECTURE]** this call site is redesigned to **decrypt to a temporary
plaintext file** for the viewer's lifetime. **[SECURITY DESIGN DECISION
REQUIRED] / [SECURITY REVIEW REQUIRED]:** the temp-file location (secure
per-user temp dir), lifetime, and cleanup/best-effort-shred strategy — the
decrypt-to-temp window is an explicit, documented **temporary plaintext
exposure** (§13/§19/§20). Filename-encryption strategy is likewise
**[SECURITY DESIGN DECISION REQUIRED]**.

## 8. Decision — backup encryption

**[APPROVED ARCHITECTURE]** Backups are **independently recoverable**: a
backup moved to a replacement machine must not depend exclusively on the
original machine's OS-bound key. The preferred direction:

```
Clinic data → Backup Builder (db + attachments → archive bytes)
            → Encrypt(archive, backup key derived from a recovery secret / passphrase)
            → encrypted backup artifact → StorageProvider.save() → storage / transfer
```

- **[APPROVED ARCHITECTURE]** backup encryption uses an **independent,
  transportable key path** (recovery-key / passphrase-derived), not the
  live machine-bound DEK-unwrap path alone, so §11.10 (backup moved to
  another machine) and §11.7 (new computer) are recoverable. Archiving an
  already-encrypted DB/attachment set (option "inherit the live key") is
  documented as the rejected alternative because it ties restore to the
  original machine's key material.
- **[APPROVED ARCHITECTURE]** a **restore workflow must be designed** — none
  exists today (Backups.md: restore is manual "unzip into place"). It must:
  verify integrity (AEAD), decrypt, atomically replace `data/` +
  `attachments/`, and handle wrong-key / corrupt-archive cleanly.
- **[APPROVED ARCHITECTURE]** **pre-F7 plaintext backups remain restorable**
  — the restore path detects plaintext vs. encrypted artifacts (backup
  compatibility).
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]:** the
  backup key derivation, whether the backup key is the recovery key or a
  distinct passphrase, and the archive/artifact format.
- **[FUTURE SCOPE]:** cloud / off-device backup transfer, scheduled/automatic
  backup (F8-adjacent) — F7 encrypts the artifact and defines local restore
  only.

## 9. Decision — key-management architecture (envelope model)

**[APPROVED ARCHITECTURE]** An **envelope key-management model**:

```
Data Encryption Key (DEK)   ← the key that actually encrypts DB / attachments / backups
        ↓ wrapped by
Key Encryption mechanisms (KEKs)   ← one or more independent unwrap paths
        ↓ yields
protected key material at rest
```

The architecture must support: normal operation on the trusted clinic
machine; recovery after loss of the normal OS/user key path; machine
replacement; application reinstallation; and future multi-user evolution
(re-wrapping the DEK per user without re-encrypting data). The DEK may be
protected through **more than one** recovery/unwrapping mechanism —
minimally an OS-convenience path **and** the mandatory offline recovery key
(§10).

Explicitly **not decided here** (must be documented as decisions, never
silently chosen):
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]** — the
  exact key-wrapping algorithm/construction.
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]** — the
  exact Windows keystore integration (DPAPI or equivalent) and its
  cross-platform fallback for dev/CI/Linux.
- **[SECURITY DESIGN DECISION REQUIRED]** — the key-material file format and
  on-disk storage paths.
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]** — key
  rotation behavior and DEK re-wrap lifecycle.

Key management is security-sensitive configuration: any operator-facing key
surface is an RBAC-gated Administrator/Security surface (ADR-002 §5.2/§6.6;
ADR-003 §9), **never** the F2 clinic-profile Settings UI.

## 10. Decision — recovery (mandatory offline recovery key)

**[APPROVED ARCHITECTURE]** A **mandatory offline recovery key** is required.
The system must **not** depend exclusively on a Windows user profile or a
machine-bound key. The ADR states plainly:

> **Encryption without a viable recovery path is not acceptable for Wise
> PMS.**

The recovery mechanism must be usable **without any network service** and
must account for: a lost Windows profile; a failed/replaced computer;
application reinstallation; administrator replacement; corrupted local key
material; and backup restoration (§11).

- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]** — the
  recovery-key encoding, generation, presentation to the operator (e.g.
  displayed/printed once), storage, and the unwrap-with-recovery-key flow.
- **[IMPLEMENTATION DETAIL]** — the operator UX for provisioning/entering the
  recovery key (a net-new surface, §12).

## 11. Migration strategy (existing plaintext → encrypted)

**[APPROVED ARCHITECTURE]** Migration of existing plaintext data is
**explicit, administrator-controlled, atomic, resumable, verified, and
idempotent** — **never** a silent conversion at startup.

```
plaintext data → safety backup → encrypted copy → verification
              → atomic switch → confirm encrypted state → cleanup
```

Requirements:
- **Trigger:** operator-initiated, RBAC-gated (Administrator); never
  automatic on launch/upgrade.
- **Backup before migration:** take a full backup first; do not delete it
  until migration verifies.
- **Pre-flight disk check:** require the temporary storage headroom
  (approximately 2× peak while old + new coexist) before starting.
- **Atomicity:** encrypt to new files/DB, verify, then atomically swap;
  never mutate the only copy in place; never destroy the only plaintext copy
  before verification.
- **Resumable / partial:** track per-item progress; a crash leaves either
  the old plaintext set or a verified encrypted set, never an unusable mixed
  state; detect partial migration and resume.
- **Idempotent:** detect an already-encrypted state and no-op; **never
  double-encrypt** on re-run.
- **Verification:** decrypt-and-compare (or AEAD-verify + schema/row checks)
  before cleanup.
- **Rollback:** on failure, the pre-migration backup restores the plaintext
  state.

**[FUTURE SCOPE]** — no automatic/background migration; no scheduling.
Migration is a discrete, verifiable, operator-driven operation.

## 12. Startup / failure-state architecture

**[APPROVED ARCHITECTURE]** Startup gains a **key-acquisition / unlock stage
before any DB access** (before `init_db()`/`migrate(conn)`). Expected
behavior per state:

| State | Expected behavior |
| ----- | ----------------- |
| First launch (fresh install) | Provision key material (generate DEK, wrap per §9, generate + present recovery key per §10), create encrypted DB, seed admin. No migration. |
| Existing install, key available | Unlock → migrations run against the keyed connection → normal. |
| Key unavailable | Start to a **locked state**; prompt for key/recovery; never open plaintext. |
| Wrong key | Clean "unlock failed"; retry / recovery; no partial init. |
| Corrupt encrypted DB | Detect on open; route to restore-from-backup; do not migrate a corrupt file. |
| Missing encrypted attachments | App still starts; individual reads fail gracefully. |
| Migration pending (plaintext data present) | Detect; route to the operator-initiated migration (§11); never silent. |
| Migration interrupted | Detect mixed state; resume or roll back from the pre-migration backup. |
| Upgraded install (F7 build over old plaintext) | Behaves as "migration pending". |
| Restored install | Restore workflow (§8) decrypts + swaps, then normal unlock. |

**No silent plaintext fallback** in any state.
**[IMPLEMENTATION DETAIL]** — the exact unlock/migration/restore UX surfaces
(all net-new).

## 13. Security requirements

The ADR and technical plan **require**, and mark for review:
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]** —
  authenticated encryption (AEAD) for DB, attachments, and backups.
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]** —
  a strong KDF wherever a passphrase/recovery secret derives a key, with
  tuned parameters (a measured startup-latency vs. brute-force-resistance
  trade-off, §16).
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]** —
  unique nonce/IV handling; never reused under one key.
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]** —
  secure key wrapping; explicit key lifecycle and recovery lifecycle.
- **Required behaviors:** integrity/authentication on every artifact;
  corruption detection; clean wrong-key failure; **no silent plaintext
  fallback**.
- **[SECURITY REVIEW REQUIRED]** — temporary plaintext exposure windows
  (viewer decrypt-to-temp §7; migration/backup temp files §8/§11); secure-
  deletion limitations (overwriting plaintext does not guarantee erasure on
  SSDs/journaling filesystems — documented as a known limitation, §19,
  never over-promised).

This ADR does **not** select a specific cipher, AEAD mode, KDF, or KDF
parameters, and makes **no claim of security approval** for any
construction.

## 14. Dependency / packaging consequences

**[APPROVED ARCHITECTURE — in principle only]** A new cryptographic runtime
dependency **may** be introduced **if** required by the approved
architecture. It is **not** installed here, `requirements.txt` is **not**
modified here, and no specific package is chosen here.

- **Why stdlib is insufficient:** the standard library has no AEAD symmetric
  cipher (only KDFs/`hmac`/`secrets`). Authenticated encryption of
  attachments/backups, and a keyed SQLCipher database, cannot be built from
  stdlib alone.
- **SQLCipher binding:** the D1 database decision (§6) requires a SQLCipher
  driver/binding backed by a **native library** — **[SECURITY DESIGN
  DECISION REQUIRED]** which binding/distribution.
- **Python crypto library:** attachment/backup AEAD + key wrapping likely
  require a vetted crypto library — **[SECURITY DESIGN DECISION REQUIRED]**
  which one.
- **OS integration:** the envelope KEK convenience path (§9) likely uses a
  Windows keystore (DPAPI or equivalent) with a cross-platform fallback —
  **[SECURITY DESIGN DECISION REQUIRED]**.
- **Windows packaging:** PyInstaller `WisePMS.exe` must bundle any native
  crypto library and load it reliably on target machines — a real packaging
  risk to verify (§16/§17).
- **Test-gate change:** `tests/test_layering.py::test_no_new_runtime_
  dependency_added` asserts `{flet, bcrypt}`. Any approved dependency makes
  this an **intentional, documented gate change** (rule 12/13) at
  implementation — treated as an architecture gate, not an accident.
- **Dependency-maintenance implications:** a native crypto dependency adds
  supply-chain and update responsibilities — documented for the Product
  Owner.

## 15. Deployment consequences

- Windows desktop (`WisePMS.exe`) packaging must bundle and load native
  crypto reliably; a clean-install + offline-run verification is an
  acceptance gate (§17 tests).
- No ADR-002 §8.0 deployment tier changes: SQLite + Local Disk + Local
  Desktop stays the only Production-supported configuration; the §8.1
  SQLite-over-network prohibition is untouched.
- New operator surfaces (unlock, recovery-key provisioning/entry, migration
  progress, restore) are net-new deployment/UX considerations.
- **[FUTURE SCOPE]:** off-device/cloud backup, transport security (F8),
  server-grade adapters.

## 16. Performance considerations

No benchmarks are invented. Items that **must be measured** during
implementation:
- database read/write overhead of page-level encryption on representative
  clinic data (search-per-keystroke over large `patients` is already a hot
  path — L11); unlock/`PRAGMA key` cost at startup;
- attachment encrypt/decrypt latency, especially large files; whole-file vs.
  streaming;
- backup encryption cost over a full DB + attachments tree, and temp-space;
- KDF cost (startup-latency vs. brute-force-resistance trade-off);
- migration duration (proportional to total PHI size; must show progress and
  be interruptible).

## 17. Testing strategy

Preserve the existing regression discipline (130 tests, layering gates,
regression golden). Future F7 tests (specified, not written now):
- **Database:** correct-key open; wrong-key failure; locked state;
  corruption detection; migration correctness; restore.
- **Attachments:** encrypt/decrypt round-trip; AEAD integrity failure;
  wrong key; corruption; atomic writes; temp-file cleanup.
- **Backups:** encrypted backup; restore round-trip; wrong key; corruption;
  pre-F7 plaintext-backup compatibility.
- **Key management:** provisioning; unlock; recovery; key replacement;
  machine replacement; OS-profile replacement; re-wrapping.
- **Migration:** row integrity; attachment integrity; interruption; resume;
  rollback; idempotency; disk-space-failure pre-flight.
- **Packaging:** clean Windows install; PyInstaller runtime; native-
  dependency loading (if applicable); offline operation.
- **Regression:** all existing 130 tests stay green (most are transparent to
  the byte path — RBAC/router/permission tests do not touch it); the
  `test_no_new_runtime_dependency_added` and any allow-list gates change
  **intentionally**; the regression golden is evaluated for intentional
  change with the key available in the fixture (rule 12/13). **No golden or
  test edit in this planning PR.**

## 18. Rejected alternatives

- **D2 — whole-file application-layer DB encryption** (decrypt-to-temp for
  the whole session / field-level PHI encryption): full-session plaintext
  temp file or broken search/indexing + repository-wide churn. Rejected for
  the database (§5).
- **D3 — OS/volume encryption as F7's sole mechanism:** no protection for a
  backup copied off the machine; depends on clinic IT. Complementary only.
- **Backup inheriting the live machine-bound key:** ties restore to the
  original machine; rejected in favor of independently recoverable backups
  (§8).
- **App-managed key stored next to the data as the sole model:** stolen-disk
  defeats it; only acceptable inside the envelope as one wrapped path, never
  alone.
- **No recovery path:** converts routine key loss into total irreversible
  PHI loss; rejected (§10).
- **An ORM/Alembic or a second DB engine for F7:** out of scope; ADR-002
  Revision 6 bars ORM/Alembic; F7 builds no second adapter.

## 19. Known limitations

- **Secure deletion** of plaintext is not guaranteed on SSDs/journaling
  filesystems — documented, not over-promised.
- **Temporary plaintext exposure** windows exist (viewer decrypt-to-temp;
  migration/backup temp files) — minimized and documented, not eliminated.
- **Metadata leakage** persists under content encryption (file sizes,
  per-patient counts, directory structure; filename unless separately
  opaqued).
- F7 does **not** protect a running, unlocked process, and does not address
  authorization (RBAC/row-level) or transport (F8).

## 20. Security-review requirements

**[SECURITY REVIEW REQUIRED]** before F7 is considered production-ready, at
minimum: cipher selection · AEAD mode · KDF · KDF parameters · nonce/IV
handling · key wrapping · OS keystore integration · recovery-key design ·
backup encryption · temporary plaintext files · migration security ·
corruption handling · key rotation · key loss · secure-deletion limitations.
This ADR **documents** what requires review and **claims no security
approval**.

## 21. Consequences

- A cryptographic dependency (and likely a native library + OS keystore
  integration) will be added at implementation, changing the `{flet,
  bcrypt}` dependency gate intentionally.
- Windows packaging gains native-crypto bundling + verification work.
- Startup gains an unlock stage; new operator surfaces (unlock, recovery,
  migration, restore) appear.
- The irreversible-key-loss risk is mitigated (not eliminated) by the
  mandatory offline recovery key.
- The database/repository/domain architecture is preserved; encryption lives
  at the adapter and storage seams.
- `provider_credentials` / BYO AI keys (ADR-002 §6.3) become unblockable in a
  **later** phase once F7 ships.

## 22. Explicit implementation boundary

This ADR is design only. It does **not** implement encryption; modify SQLite
connection behavior; replace `sqlite3`; install SQLCipher, `cryptography`,
or any dependency; modify `requirements.txt` for runtime; create crypto/key-
management/encrypted-storage/restore/migration code; create keys or recovery
keys or key stores; modify bootstrap/auth/RBAC/controllers/services/views for
F7; modify PyInstaller packaging; change the regression golden; or modify
tests to support implementation. Implementation is separately gated and
requires explicit Product Owner authorization.

## 23. Future dependencies / F8 relationship

- **`provider_credentials` / AI Gateway (BYO keys):** **[FUTURE SCOPE]** —
  blocked until F7 ships (ADR-002 §6.3/§11); reuses F7's mechanism.
- **F8 (Cloud Sync / transport security):** **[FUTURE SCOPE]** — F7 is a
  prerequisite (`SECURITY.md` rule 1); F7 encrypts data at rest and defines
  local restore, not network transport or off-device sync. Off-device/cloud
  backup transfer is F8-adjacent, not F7.
- **Multi-user key sharing:** **[FUTURE SCOPE]** — the envelope model leaves
  per-user DEK re-wrapping additive; F7 does not build multi-user key
  sharing.

---

## Decision

**Adopt F7 Encryption at Rest for database, attachments, and backups
together, at the existing seams.** The database is encrypted transparently
via **SQLCipher** at the `SQLiteAdapter` boundary (D1); attachments are
encrypted via an **`EncryptedStorageProvider` decorator** at the
`StorageProvider` seam, with the viewer/`local_path` path redesigned to
decrypt-to-temp; backups are **independently recoverable** encrypted
artifacts with a designed restore workflow and pre-F7 plaintext
compatibility. Key management uses an **envelope model** (a DEK wrapped by
one or more KEKs), with a **mandatory offline recovery key** — *encryption
without a viable recovery path is not acceptable for Wise PMS.* Existing
plaintext data migrates via an **explicit, administrator-controlled, atomic,
resumable, verified, idempotent** process, never silently at startup;
startup gains an unlock stage before any DB access, with fail-closed,
no-silent-plaintext behavior across all failure states. A cryptographic
runtime dependency (and likely a native SQLCipher library and OS keystore
integration) is **approved in principle** but **not installed, not chosen,
and not implemented here**; adding it is an intentional dependency-gate
change at implementation. Every cryptographic detail — cipher, AEAD mode,
KDF and parameters, nonce/IV, key wrapping, Windows keystore usage,
recovery-key encoding/storage, key rotation, secure-deletion limitations,
and the exact SQLCipher binding/crypto library — is marked **[SECURITY
DESIGN DECISION REQUIRED]** and/or **[SECURITY REVIEW REQUIRED]**, and
**security review is mandatory before F7 is production-ready**. F7 changes no
ADR-002 §8.0 deployment tier and is a **prerequisite for**, never an
**enabler of**, networked/multi-user deployment. The concrete milestone
sequence and file map are in `docs/planning/SPRINT6_TECHNICAL_PLAN.md`.
**Await Product Owner approval before any implementation.**
