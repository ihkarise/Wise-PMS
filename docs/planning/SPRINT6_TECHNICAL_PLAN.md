# Sprint 6 — Technical Plan (F7 Encryption at Rest)

**Status:** PROPOSED — Product Owner review. **Planning/design only; no code
in this document is implemented.** Implements
[`../architecture-decisions/ADR-004-F7-Encryption-at-Rest.md`](../architecture-decisions/ADR-004-F7-Encryption-at-Rest.md).
**Date:** 2026-09-21

> This plan defines *how* F7 would be implemented without implementing it.
> Where the repository does not provide enough evidence to fix a
> cryptographic or key-handling detail, the item is marked **[SECURITY
> DESIGN DECISION REQUIRED]**, **[SECURITY REVIEW REQUIRED]**, or
> **[IMPLEMENTATION DETAIL]** rather than invented. The Product Owner has
> approved the architecture **direction** (SQLCipher, envelope keys, offline
> recovery key, independently recoverable backups, explicit/resumable
> migration, DB+attachments+backups scope, a dependency in principle,
> mandatory security review); this plan does **not** authorize installing a
> dependency, choosing a specific crypto library/binding, or writing any
> runtime/crypto/migration/test code.

---

## 1. Objective

Encrypt Wise PMS Protected Health Information **at rest** — the SQLite
database, patient attachments, and backups — at the existing `SQLiteAdapter`
and `StorageProvider` seams, with an envelope key model and a mandatory
offline recovery path, migrating existing plaintext data safely, without
changing the domain/repository architecture, the offline/₹0 posture, or any
ADR-002 §8.0 deployment tier. Closes `KNOWN_LIMITATIONS.md` L5 /
`SECURITY.md` "No encryption at rest" **when implemented** (not by this
plan).

## 2. Scope

**In scope (ADR-004 §10):** database encryption · attachment encryption ·
backup encryption · key management (envelope) · recovery (offline recovery
key) · existing-data migration · startup/unlock architecture · failure-state
handling · restore architecture · Windows packaging implications · security
testing · performance validation · security review.

## 3. Non-goals (FUTURE SCOPE / out of scope)

Cloud Sync · network transport security · F8 · `provider_credentials`
implementation · AI Gateway / BYO AI keys · multi-user key-sharing
implementation · row-level authorization · cloud/off-device backup ·
remote key server · secure-erase guarantees · automatic/scheduled off-device
backup · any second DB engine or storage backend · unrelated RBAC changes ·
ORM/Alembic.

## 4. Architecture

```
UI (Flet views) → Controller → Service → Repository → DatabaseAdapter
                                                          ↓ (F7: keyed open)
                                                       SQLite (SQLCipher)

attachments.service / backup destination → get_storage()
                                              ↓ (F7: decorator)
                                     EncryptedStorageProvider
                                              ↓
                                     LocalDiskStorageProvider → disk (ciphertext)

Key layer (envelope): DEK ← wrapped by KEKs (OS keystore + offline recovery key)
                        ↑ unlock stage runs BEFORE init_db()/migrate()
```

- **Database (ADR-004 §6):** keyed open inside `SQLiteAdapter.connect()`;
  nothing above the adapter changes; the unlock stage precedes
  `init_db()`/`migrate(conn)`.
- **Attachments (ADR-004 §7):** `EncryptedStorageProvider` decorator wrapping
  `LocalDiskStorageProvider`, selected at `app/core/storage/__init__.py:
  get_storage()`. Byte contract (`save/open/delete/url_for`) unchanged;
  `attachments.service`/repository byte path untouched. The
  `absolute_path()`/`local_path()` viewer path is redesigned to
  decrypt-to-temp.
- **Backups (ADR-004 §8):** independent, transportable key path; encrypt the
  built archive before the destination write; a new restore workflow.
- **Keys (ADR-004 §9):** envelope DEK/KEK; RBAC-gated Administrator/Security
  surface for any operator key action (ADR-002 §5.2/§6.6), never F2 Settings.

## 5. Dependencies

- **[APPROVED IN PRINCIPLE — not installed here]** a cryptographic runtime
  dependency may be added. Stdlib is insufficient (no AEAD cipher; only
  KDFs/`hmac`/`secrets`).
- **[SECURITY DESIGN DECISION REQUIRED]** exact SQLCipher binding/distribution
  (database); exact Python crypto library (attachment/backup AEAD + key
  wrapping); exact OS-keystore integration (Windows DPAPI or equivalent + a
  cross-platform fallback).
- **Test-gate impact:** `tests/test_layering.py::test_no_new_runtime_
  dependency_added` asserts `{flet, bcrypt}`; an approved dependency changes
  this gate **intentionally** (rule 12/13) at implementation.
- No ORM/Alembic; no second DB/storage adapter (ADR-002 Revision 6 / §11).

## 6. Protected data (ADR-004 §3)

`data/wise_pms.db` (+ journal/WAL/shm/temp) → SQLCipher; `attachments/
patient_<reg_no>/…` → per-file AEAD; `backups/*.zip` → independently
recoverable encrypted artifact; new key/recovery material → protected,
never committed/logged. Not targets: bcrypt hashes; `exports/`/`logs/`;
`provider_credentials` (future).

## 7. Threat model (ADR-004 §2)

Protects stolen DB/attachments/backups and at-rest filesystem access; does
**not** protect a running unlocked process, insider/admin misuse,
authorization (RBAC/row-level), or transport (F8); key loss is mitigated
only by the mandatory recovery key (§11). No claim that F7 solves what it
cannot.

## 8. Key management (ADR-004 §9) — envelope

- **DEK** encrypts DB/attachments/backups; **KEKs** wrap the DEK via more
  than one independent unwrap path (OS-convenience + offline recovery key).
- Multi-user future is additive (re-wrap DEK per user; no data re-encrypt).
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]:**
  key-wrapping construction; OS keystore usage + fallback; key-material
  format and storage paths; key rotation / DEK re-wrap lifecycle.
- **[IMPLEMENTATION DETAIL]:** in-memory DEK handoff from the key layer to
  `SQLiteAdapter`/`EncryptedStorageProvider`; DEK lifetime in memory.

## 9. Recovery (ADR-004 §10) — mandatory offline recovery key

- Not dependent on a Windows profile or machine-bound key alone; usable
  offline. Covers lost profile, replaced computer, reinstall, admin
  replacement, corrupted local key material, backup restore.
- The plan states verbatim: **"Encryption without a viable recovery path is
  not acceptable for Wise PMS."**
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]:**
  recovery-key encoding, generation, one-time presentation, storage, and
  unwrap flow. **[IMPLEMENTATION DETAIL]:** provisioning/entry UX.

## 10. Database encryption (ADR-004 §5/§6) — SQLCipher

- Keyed open in `SQLiteAdapter.connect()`; unlock precedes migrations; SQL,
  repositories, migrations, and the golden's schema queries unchanged once
  keyed. An encrypted `.db` archives into a backup as-is.
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]:**
  SQLCipher binding, cipher/KDF/page settings exposed by it.
- **[IMPLEMENTATION DETAIL]:** journal/WAL interaction under encryption.

## 11. Attachment encryption (ADR-004 §7)

- `EncryptedStorageProvider` decorator; AEAD; atomic write (temp + rename);
  corruption/wrong-key → clear error, never wrong-plaintext; streaming vs
  whole-file for large files.
- **Viewer/`local_path` redesign:** decrypt-to-temp for the viewer/print
  lifetime — an explicit temporary plaintext exposure.
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]:**
  filename-encryption strategy (today the on-disk name leaks
  `reg_no`/stem/ext); temp-file location/lifetime/cleanup. **Metadata/size/
  directory leakage** documented as residual.

## 12. Backup encryption (ADR-004 §8)

- Independent, transportable key path (recovery-key/passphrase-derived) so a
  backup is restorable on a replacement machine; encrypt the built archive
  before the destination write.
- **[SECURITY DESIGN DECISION REQUIRED] / [SECURITY REVIEW REQUIRED]:** backup
  key derivation; whether backup key == recovery key or a distinct
  passphrase; artifact format.

## 13. Migration (ADR-004 §11) — explicit, atomic, resumable, verified, idempotent

`plaintext → safety backup → encrypted copy → verify → atomic switch →
confirm → cleanup`. Operator-initiated + RBAC-gated (Administrator); never
silent at startup; pre-flight ~2× disk check; never destroy the only
plaintext copy before verification; resumable; detect partial state;
idempotent (no double-encrypt); rollback via the pre-migration backup.

## 14. Restore (ADR-004 §8)

New restore workflow (none exists today): detect plaintext vs. encrypted
artifact (pre-F7 compatibility); AEAD-verify; decrypt; atomically replace
`data/` + `attachments/`; wrong-key/corrupt-archive handled cleanly.

## 15. Startup states (ADR-004 §12)

Unlock stage before any DB access. First launch (provision key + recovery,
create encrypted DB), key available (unlock → migrate → run), key
unavailable (locked, prompt), wrong key (clean fail), corrupt DB (restore
route), missing attachments (graceful), migration pending (route to §13),
migration interrupted (resume/rollback), upgraded (migration pending),
restored (restore → unlock). **No silent plaintext fallback.**

## 16. Failure states

Wrong key, corrupt DB, corrupt attachment (per-file), corrupt backup,
interrupted migration, missing key material, lost OS profile — each has a
defined, fail-closed behavior (ADR-004 §12); recovery key is the escape
hatch; backups are the corruption escape hatch.

## 17. Performance requirements (ADR-004 §16) — measure, do not assume

DB read/write overhead (esp. search-per-keystroke, L11); unlock/KDF cost;
attachment encrypt/decrypt (large files, streaming); backup encryption +
temp space; migration duration + progress. **[IMPLEMENTATION DETAIL]:** the
measured KDF cost/parameter tuning.

## 18. UX requirements

Net-new surfaces: unlock prompt; recovery-key provisioning + one-time
presentation; recovery-key entry; migration progress (interruptible);
restore workflow. Any operator **key** surface is RBAC-gated
Administrator/Security (ADR-002 §5.2/§6.6), never F2 Settings.

## 19. Packaging requirements (ADR-004 §14/§15)

PyInstaller `WisePMS.exe` bundles + reliably loads any native crypto
library; clean-install + offline-run verification is an acceptance gate.
No deployment-tier change (ADR-002 §8.0); §8.1 SQLite-over-network rule
untouched.

## 20. Test strategy (ADR-004 §17)

Preserve the 130-test suite, layering gates, and the regression golden.
Future tests (specified, not written now):

- **Database:** correct-key open · wrong-key failure · locked state ·
  corruption · migration · restore.
- **Attachments:** round-trip · integrity failure · wrong key · corruption ·
  atomic writes · temp-file cleanup.
- **Backups:** encrypted backup · restore round-trip · wrong key · corruption
  · pre-F7 backup compatibility.
- **Key management:** provisioning · unlock · recovery · key replacement ·
  machine replacement · OS-profile replacement · re-wrapping.
- **Migration:** row integrity · attachment integrity · interruption · resume
  · rollback · idempotency · disk-space-failure pre-flight.
- **Packaging:** clean Windows install · PyInstaller runtime · native-
  dependency loading (if applicable) · offline operation.
- **Regression:** all 130 existing tests stay green; the dependency-set /
  allow-list layering gates change **intentionally**; the golden is
  evaluated for intentional change with the key available in the fixture
  (rule 12/13). **No golden/test edit in the planning PR.**

## 21. Security gates (ADR-004 §13/§20)

Every cryptographic detail is **[SECURITY DESIGN DECISION REQUIRED]** and/or
**[SECURITY REVIEW REQUIRED]**: cipher · AEAD mode · KDF · KDF parameters ·
nonce/IV · key wrapping · OS keystore · recovery-key design · backup
encryption · temporary plaintext files · migration security · corruption
handling · key rotation · key loss · secure-deletion limitations. **Security
review is mandatory before F7 is production-ready.** No security approval is
claimed by this plan.

## 22. Milestones (proposal — verify dependencies at M0)

Milestone **order and count are a planning proposal**, to be confirmed at
M0. None is implemented by this plan.

| Milestone | Objective | Key dependencies | Acceptance (high level) | Out of scope |
| --------- | --------- | ---------------- | ----------------------- | ------------ |
| **M0 — Architecture/security decision closure** | Resolve every §21 [SECURITY DESIGN DECISION REQUIRED]; select dependency/binding; confirm milestone order | ADR-004 approved; specialist review engaged | Signed decisions; dependency choice justified | Any code |
| **M1 — Crypto/key-management foundation** | AEAD primitive + KDF + envelope DEK/KEK + offline recovery key + unlock stage | M0 | Provisioning/unlock/recovery tests green, offline | Touching PHI |
| **M2 — Attachment encryption** | `EncryptedStorageProvider` + decrypt-to-temp viewer path | M1 | Round-trip/integrity/atomic/temp-cleanup tests; golden attachment behavior preserved | Database |
| **M3 — Database encryption** | Keyed `SQLiteAdapter` (SQLCipher) + startup unlock before migrate | M1 (M0 binding) | Encrypted DB opens with key, wrong-key fails, migrations run; layering gate updated | Existing-data migration |
| **M4 — Backup encryption + restore** | Independent encrypted backup + restore workflow + pre-F7 compatibility | M2, M3 | Restore round-trip; wrong-key/corrupt handling | Cloud/off-device (F8) |
| **M5 — Existing-data migration** | Operator-initiated, atomic, resumable, verified, idempotent plaintext→encrypted | M2, M3 | Correctness, rollback, interrupted-resume, idempotent re-run, disk pre-flight | Scheduling/automation |
| **M6 — Startup/failure-state handling** | All §15/§16 states | M3, M5 | Each state behaves as specified; no silent plaintext | — |
| **M7 — Final security/regression gate** | Independent security review + full 130-test green + intentional gate/golden changes documented | M1–M6 | Review sign-off; CHANGELOG/DECISIONS entries; L5 closable | Shipping any networked surface |

Each milestone is separately gated; **none begins without explicit Product
Owner authorization** (charter: no phase starts automatically).

## 23. File map (proposed — nothing created now)

**Existing files to MODIFY (implementation phase — not now)**

| Path | Change |
| ---- | ------ |
| `app/core/db_adapters/sqlite_adapter.py` | Keyed SQLCipher open (M3) |
| `app/core/db_adapters/__init__.py` | Adapter selection (still one active) |
| `app/core/storage/__init__.py` | `get_storage()` returns the encrypting decorator (config boundary, ADR-002 §5.2) |
| `app/modules/attachments/service.py` | `absolute_path()` decrypt-to-temp redesign (M2) |
| `app/modules/backup/service.py` | Backup encryption + restore hook (M4) |
| `app/core/database.py` and/or `app/bootstrap.py` | Unlock stage before `init_db()`/`migrate()` (M3/M6) |
| `requirements.txt` | The approved crypto dependency (intentional gate change) |
| `tests/test_layering.py` | New allow-list entry (crypto module) + updated dependency-set assertion |
| `app/config/paths.py` | Possibly key/recovery-material path **[IMPLEMENTATION DETAIL]** |

**New files to CREATE (implementation phase — not now)**

| Path | Purpose |
| ---- | ------- |
| `app/core/crypto/…` | AEAD primitive + KDF wrapper (layering allow-listed) |
| `app/core/keys/…` (or `app/modules/security/…`) | Envelope wrap/unwrap, OS-keystore adapter, recovery-key logic |
| `app/core/storage/encrypted_provider.py` | `EncryptedStorageProvider` decorator |
| migration/encryption service | Operator-initiated plaintext→encrypted (M5) |
| restore service | Encrypted/plaintext restore workflow (M4) |

**Test files to CREATE/MODIFY (implementation phase — not now):**
`tests/test_crypto.py`, `tests/test_encrypted_storage.py`,
`tests/test_db_encryption.py`, `tests/test_key_management.py`,
`tests/test_encrypted_backup.py`, `tests/test_data_migration.py`; updates to
`tests/test_layering.py`; evaluation of `tests/test_regression.py`.

**Documentation files (implementation phase — not now):** `docs/SECURITY.md`
(close L5), `docs/KNOWN_LIMITATIONS.md` (L5), `docs/DATABASE.md`,
`docs/DEPLOYMENT.md` (packaging), `docs/ARCHITECTURE.md`,
`docs/TARGET_ARCHITECTURE.md`, `docs/MASTER_BACKLOG.md` (close F7),
`docs/ROADMAP.md`, `docs/DECISIONS.md` (ADR-00NN ledger entry at
implementation), `docs/CHANGELOG.md`, `docs/modules/Attachments.md`,
`docs/modules/Backups.md`, and the `.ai/*` state files.

**Migration files:** encryption sits **below** the schema, so a new
`vNNNN_*` migration is required **only** if metadata columns are added (e.g.
an encrypted-filename mapping) — additive/idempotent per ADR-0008. **No F7
migration is created in this planning PR.**

**Packaging/configuration files:** PyInstaller spec / build configuration
(M3/M7) — **not** modified now.

## 24. Acceptance criteria (for the eventual implementation, not this plan)

L5 closable; DB/attachments/backups encrypted at rest; correct-key
round-trips for all three; wrong-key fails cleanly with no plaintext
fallback; recovery key proven to restore access after simulated
key/machine/profile loss; migration atomic/resumable/idempotent/verified;
restore round-trip proven; all 130 existing tests green; intentional
layering/golden/dependency-gate changes documented (ADR + CHANGELOG +
DECISIONS same commit, rule 12/13); Windows clean-install + offline run
verified; **specialist security review signed off**.

## 25. Rollback / recovery

Planning-PR rollback: revert the docs commit (no runtime effect).
Implementation-phase rollback: each milestone is additive and behind the
unlock stage; the existing-data migration is guarded by a mandatory
pre-migration backup (§13) and is resumable/rollback-able; the offline
recovery key is the key-loss escape hatch; backups are the corruption escape
hatch.

## 26. Deployment requirements (ADR-004 §15)

Native-crypto bundling + offline-run verification on Windows; new operator
surfaces (unlock/recovery/migration/restore); no ADR-002 §8.0 tier change;
§8.1 SQLite-over-network rule preserved.

## 27. Documentation requirements

At **implementation** (not now): close L5 in `SECURITY.md`/
`KNOWN_LIMITATIONS.md`; add the `DECISIONS.md` ledger entry; update
`DATABASE.md`/`DEPLOYMENT.md`/`ARCHITECTURE.md`/module docs/`CHANGELOG.md`/
`.ai/*` in the same commit(s) as the behavior change (rule 12/13). This
**planning PR** updates only ADR-004, this plan, and the `.ai/*`
planning-state pointers.

## 28. Explicit implementation boundaries

This plan implements nothing. It does not install any dependency, choose a
specific crypto library/binding/KDF/cipher/nonce strategy/key-storage/
recovery implementation, modify `requirements.txt` for runtime, create
crypto/key/encrypted-storage/restore/migration code, modify SQLite
connection/bootstrap/auth/RBAC/controller/service/view behavior, modify
PyInstaller packaging, change the regression golden, or modify tests to
support implementation. Each milestone (M1–M7) is separately gated and
requires explicit Product Owner authorization.

## 29. Decision status

**Product Owner decisions — APPROVED (2026-09-21):**
- **Database encryption:** SQLCipher / transparent full-database encryption
  (direction; not installed/implemented).
- **Key management:** envelope model (DEK wrapped by ≥1 KEK).
- **Recovery:** mandatory offline recovery key.
- **Backups:** independently recoverable.
- **Migration:** explicit, administrator-controlled, atomic, resumable,
  verified, idempotent.
- **Scope:** DB + attachments + backups together.
- **Dependency:** a crypto runtime dependency approved **in principle**
  (not installed; not chosen).
- **Security review:** mandatory before production-ready.

**Still requiring specialist review / decision (not resolved here):** exact
cipher · AEAD mode · KDF · KDF parameters · nonce/IV design · key wrapping ·
Windows keystore implementation · recovery-key encoding/storage · secure-
deletion limitations · temporary plaintext exposure · exact SQLCipher
binding · exact crypto library. These are the M0 gate.

**Implementation-level details (resolved at implementation; no scope/schema/
architecture impact):** in-memory DEK handoff, key/recovery-material storage
paths, journal/WAL interaction, unlock/migration/restore UX. Each is marked
inline.
