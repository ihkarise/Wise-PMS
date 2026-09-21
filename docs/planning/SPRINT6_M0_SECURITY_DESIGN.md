# Sprint 6 — M0 Security Design (F7 Encryption at Rest)

**Status:** PROPOSED — Product Owner review. **M0 = Security Design Review;
design/documentation only. No runtime code, no dependency, no migration, no
schema, no crypto implementation, no test change, no packaging change ships
with this document.** Detailed security design for
[`../architecture-decisions/ADR-004-F7-Encryption-at-Rest.md`](../architecture-decisions/ADR-004-F7-Encryption-at-Rest.md)
and [`SPRINT6_TECHNICAL_PLAN.md`](./SPRINT6_TECHNICAL_PLAN.md).
**Date:** 2026-09-21

> **Reading contract — four tiers, kept strictly distinct (do not collapse):**
> - **[LOCKED]** — Product-Owner-approved architecture (the nine decisions in
>   §3). Not reopened here.
> - **[M0-REC]** — an M0 *technical recommendation*. A proposal, not an
>   approved decision. Must not be treated as final until ratified.
> - **[PO-DECISION]** — needs explicit Product Owner approval before it binds.
> - **[SEC-REVIEW]** — needs specialist cryptographic/security validation
>   before implementation and before production readiness. **Repository review
>   alone does NOT prove cryptographic correctness.**
>
> An item may carry both **[M0-REC]** and **[SEC-REVIEW]**: M0 proposes it,
> the specialist review ratifies it. This document never silently converts a
> recommendation into an approved decision.

---

## 1. Executive Summary

F7 encrypts Wise PMS PHI at rest — the SQLite database, patient attachments,
and backups — at the existing `SQLiteAdapter` and `StorageProvider` seams,
under an **envelope key model** with a **mandatory offline Recovery Key**.
The nine high-level decisions are approved and locked (§3). This M0 document
turns them into an implementation-ready security design precise enough that
M1 invents **no** cryptographic decisions:

- **Database:** SQLCipher 4 (AES-256-CBC + per-page HMAC-SHA512), opened with
  a **raw** DB subkey inside `SQLiteAdapter.connect()` — nothing above the
  adapter changes (§6).
- **Attachments:** an `EncryptedStorageProvider` decorator applying per-file
  AEAD (§7); the viewer/`local_path` path decrypts to a scoped temp file
  (documented plaintext window).
- **Backups:** an **independently recoverable** encrypted artifact keyed off
  the Recovery Key path — never the machine's Windows keystore alone (§8).
- **Keys:** one random **DEK** wrapped by multiple **KEKs** (Windows-DPAPI
  convenience path + mandatory Recovery-Key disaster path), with
  HKDF-derived DB/attachment subkeys and an independent backup key path (§5).
- **Migration:** administrator-initiated, atomic, resumable, verified,
  idempotent, backed by a mandatory pre-migration backup (§11).

Every concrete primitive/parameter is proposed as **[M0-REC]** and flagged
**[SEC-REVIEW]**; the mandatory specialist security review (approved
decision 9) is the ratification gate. Nothing here is implemented.

## 2. Ground-Truth Verification

Verified live against the repository (not the planning report):

| Check | Result |
| ----- | ------ |
| Branch / HEAD / origin/main | working branch built from `main`; `main == origin/main == d534487006c0cd97967dbf50eb1fe45308789f22`; clean tree |
| PR #16 | merged (F7 planning docs) |
| `requirements.txt` | `flet==0.28.3`, `bcrypt>=4.0` (unchanged); `test_no_new_runtime_dependency_added` pins `{flet, bcrypt}` |
| `SQLiteAdapter.connect()` | `sqlite3.connect(paths.DB_PATH)` + `row_factory` + `PRAGMA foreign_keys=ON`; the sole DB-open site |
| `BaseRepository` | delegates to `get_adapter()`; no repository opens a connection |
| `StorageProvider` | `save(key,bytes)->uri / open(uri)->bytes / delete / url_for`; `LocalDiskStorageProvider` + local-only `local_path()` |
| `attachments.service` | `add_attachment` reads bytes → `get_storage().save`; `absolute_path()` → `local_path()` (raw path for viewer) |
| `backup.service` | `_build_archive` reads `DB_PATH` + walks `attachments/` → zip → `get_storage().save`; no restore code |
| `bootstrap.run()` | `init_db()` (→ `migrate` → seed) then `ft.app`; **no unlock stage today** |
| Migration runner | forward-only, idempotent, additive; receives an injected connection |
| `test_layering.py` | `sqlite3` import allowed only in `sqlite_adapter.py` + migration runner; storage-write gates; dependency-set gate |
| PyInstaller config | **no `.spec` file exists**; packaging is the ad-hoc `DEPLOYMENT.md` command |

External grounding (SQLCipher facts) captured in §6/§18.

## 3. Approved Architecture — **[LOCKED]** (not reopened)

1. Database encryption: **SQLCipher**.
2. Key architecture: **envelope model**.
3. Recovery: **mandatory offline Recovery Key**.
4. Scope: **DB + attachments + backups together**.
5. Backups: **independently recoverable**.
6. Migration: **administrator-controlled, atomic, resumable, verified,
   idempotent**.
7. Windows packaging work: **accepted**.
8. Cryptographic dependency: **allowed when technically required**.
9. Security review: **mandatory before production readiness**.

These bound every recommendation below and are not reopened absent a concrete
technical conflict (none found).

## 4. Cryptographic Primitive Design

Precise enough that M1 invents nothing. All **[M0-REC] + [SEC-REVIEW]**.

| Concern | Recommendation | Rationale / notes |
| ------- | -------------- | ----------------- |
| **CSPRNG** | `secrets` / `os.urandom` (OS CSPRNG) for all keys, salts, nonces, Recovery Key | Stdlib; no custom RNG |
| **Symmetric key size** | **256-bit** for DEK, all KEKs, all subkeys | Matches SQLCipher AES-256 |
| **DB cipher** | SQLCipher 4 default: **AES-256-CBC + per-page HMAC-SHA512** | See §6; keep defaults unless review dictates otherwise |
| **File/backup AEAD** | **[PO/SEC choice]** AES-256-GCM **or** ChaCha20-Poly1305/XChaCha20-Poly1305 | GCM if hardware-AES present; XChaCha20 removes nonce-reuse fragility (192-bit nonce). Recommend **XChaCha20-Poly1305** for whole-file/backup unless AES-NI + GCM is preferred by review |
| **Nonce size** | GCM: **96-bit random**; XChaCha20: **192-bit random**; unique per encryption | Never reuse (key, nonce) |
| **Auth tag size** | **128-bit** | Full AEAD tag |
| **Key wrapping** | AEAD wrap: `wrap = AEAD(KEK, nonce, DEK, AAD=context)` **or** RFC 5649 AES-KW | One wrapped-DEK blob per KEK |
| **Subkey derivation** | **HKDF-SHA-256(DEK, salt, info)** with distinct `info` labels: `"wise-pms/db/v1"`, `"wise-pms/attach/v1"` | Domain separation across CBC/HMAC (SQLCipher) vs. AEAD (files) |
| **Passphrase/Recovery-Key KDF** | **[PO/SEC choice]** **Argon2id** (memory-hard, preferred; needs `argon2-cffi`) **or** **scrypt** (available via stdlib `hashlib.scrypt` and the crypto lib — ₹0, no extra dep) | KEK derivation only; DB raw-key path bypasses SQLCipher's own PBKDF2 (avoids double KDF) |
| **KDF salt size** | **128-bit random**, stored beside the wrapped blob | Per key-material record |
| **Argon2id params (start point)** | e.g. memory 256–512 MiB, time 3, parallelism 1–4 | Tune to clinic hardware; startup-latency vs. brute-force trade-off — **measure at M1** |
| **scrypt params (start point)** | e.g. N=2^17, r=8, p=1 | Same tuning caveat |
| **Associated data (AAD)** | Bind a format version + context label + logical identity (attachment: its stable id; backup: format id + timestamp) into AEAD AAD | Prevents ciphertext relocation/swap; detects header tampering |
| **Encoding of stored crypto records** | Versioned binary header (magic + version + algorithm ids + salt + nonce) | Enables format evolution/rotation |

## 5. Key Hierarchy

```
   Windows DPAPI-protected secret          Offline Recovery Key            (optional) operator passphrase
   [persistent, machine+user bound]        [NOT persisted in clear;        [not persisted; entered]
            │                                shown ONCE, stored offline]              │
     DPAPI unprotect                          KDF(Argon2id/scrypt, salt)      KDF(Argon2id/scrypt, salt)
            │                                            │                             │
         KEK_os                                    KEK_recovery                    KEK_pass
            │                                            │                             │
            └─────── each AEAD-wraps the SAME DEK ───────┴─────────────────────────────┘
                                       │  (N wrapped-DEK blobs on disk, one per KEK)
                                     DEK  [random 256-bit; NEVER persisted in clear; in RAM only while unlocked]
                                       │
            ┌──────────────────────────┼──────────────────────────┐
     DB_KEY = HKDF(DEK,"db/v1")   ATTACH_KEY = HKDF(DEK,"attach/v1")
            │                          │
   SQLCipher raw key          per-file AEAD (a fresh random per-file key,
                              wrapped by ATTACH_KEY, is [M0-REC] to bound
                              message count per key)

   BACKUP (independent branch — NOT DPAPI-bound):
     Recovery Key (or dedicated backup passphrase) ──KDF(salt)──> BACKUP_KEY ──AEAD──> encrypted backup artifact
```

Per-key properties:

| Key | Generated | Derived | Persistent | Wrapped | Stored where | Encrypts |
| --- | --------- | ------- | ---------- | ------- | ------------ | -------- |
| **DEK** | random (once) | — | only as wrapped blobs | yes (per KEK) | key-material store under the data root (never cleartext) | (via subkeys) DB + attachments |
| **DB_KEY** | — | HKDF(DEK) | no (in RAM) | — | — | SQLCipher database (raw key) |
| **ATTACH_KEY** | — | HKDF(DEK) | no (in RAM) | — | — | wraps per-file keys |
| **KEK_os** | — | from DPAPI-protected secret | secret persisted via DPAPI | — | DPAPI blob | wraps DEK (convenience) |
| **KEK_recovery** | — | KDF(Recovery Key, salt) | **no** (salt persists) | — | salt on disk; key never stored | wraps DEK (recovery) |
| **BACKUP_KEY** | — | KDF(Recovery Key / backup passphrase, salt) | no | — | salt embedded in backup header | backup artifact |
| **Recovery Key** | random (once, at provisioning) | — | **NOT persisted in clear** | — | offline, operator-held | (root of recovery + backup paths) |

- **What is randomly generated:** DEK, Recovery Key, per-file keys, all salts,
  all nonces.
- **What is derived:** DB_KEY, ATTACH_KEY (HKDF); KEK_recovery, KEK_pass,
  BACKUP_KEY (KDF); KEK_os (DPAPI).
- **What is wrapped:** the DEK (once per KEK); each per-file key (by
  ATTACH_KEY).
- **What is persistent:** the wrapped-DEK blobs, the DPAPI blob, salts, and
  format headers — **never a cleartext key**.
- **If Windows credential protection becomes unavailable** (profile lost,
  account changed, DPAPI fails): `KEK_os` cannot unwrap the DEK →
  application enters **locked state** and requires the **Recovery Key**
  (`KEK_recovery`) to unlock and then re-provision a new `KEK_os`. **No
  plaintext fallback.**
- **When the application moves to another machine:** `KEK_os` (DPAPI) is
  machine-bound and will not unwrap → the operator unlocks with the
  **Recovery Key**, and the app re-wraps the DEK under a new `KEK_os` on the
  new machine. **Backups** move independently because `BACKUP_KEY` derives
  from the Recovery Key/backup passphrase, not DPAPI.

## 6. SQLCipher Database Design

Grounded in SQLCipher 4 documented behavior (§18 sources). All parameter
choices **[M0-REC] + [SEC-REVIEW]**.

| Item | Design |
| ---- | ------ |
| Version target | SQLCipher **4.x** |
| Binding selection **[M0-REC/PO-DECISION]** | A statically-linked, prebuilt-wheel, DB-API-2.0 binding bundling SQLCipher 4.x + OpenSSL 3.x LTS (candidates to evaluate: `sqlcipher3-binary`, `rotki/pysqlcipher3`). Decisive criterion: a **Windows** wheel that needs no host libsqlcipher/OpenSSL, so PyInstaller can bundle it. Final pin + Windows-wheel + PyInstaller-load evidence is gating |
| Cipher / page | AES-256-CBC + per-page HMAC-SHA512; page size **4096** (defaults) |
| Key path | **Raw key**: `PRAGMA key = "x'<64-hex = DB_KEY>'"` — bypasses SQLCipher's PBKDF2 on the DB key (KDF cost is spent once on the KEK/Recovery path) |
| PRAGMAs | keyed `PRAGMA key` first; keep `PRAGMA foreign_keys=ON`; **`PRAGMA temp_store=MEMORY`** to prevent plaintext temp spill; evaluate `PRAGMA cipher_memory_security=ON`; verify open via `SELECT count(*) FROM sqlite_master` |
| WAL/SHM | **[PO-DECISION]** journal mode. Default today is rollback journal (`.db-journal`, encrypted by SQLCipher). If WAL is chosen, `-wal`/`-shm` frames are encrypted too. `.gitignore` already excludes all side files |
| Temp files | Closed via `temp_store=MEMORY` + verifying the binding's `SQLITE_TEMP_STORE` |
| Where the change lives | Only `app/core/db_adapters/sqlite_adapter.py` (`connect()` swaps the import + adds keyed open); layering allow-list adds the binding there. Migration runner unchanged (receives a keyed, DB-API-compatible connection) |
| Migration primitive | `sqlcipher_export()` / `ATTACH … KEY ''` to copy plaintext↔encrypted for §11 |
| Corruption | Per-page HMAC failure raises on read → "database corrupt → restore from backup"; never silent |
| Wrong key | First statement after `PRAGMA key` raises ("file is not a database") → "unlock failed"; no partial init |
| Startup ordering | The unlock stage (DEK → DB_KEY) runs **before** `init_db()`/`migrate()` so migrations execute on a keyed connection |

## 7. Attachment Encryption Design (`EncryptedStorageProvider`)

Decorator over `LocalDiskStorageProvider`, selected at
`app/core/storage/__init__.py:get_storage()`. Byte contract unchanged;
`attachments.service`/repository byte path untouched.

| Item | Design |
| ---- | ------ |
| File format/version header | `magic || format_version || alg_id || nonce || wrapped_file_key || ciphertext || tag` |
| Nonce handling | fresh random nonce per file (96-bit GCM / 192-bit XChaCha20); stored in header; never reused |
| Authentication | AEAD tag over ciphertext; **AAD** = header (version + alg + logical attachment id) so a file can't be swapped/relocated |
| Associated data | version + algorithm id + stable attachment identity |
| Filename/metadata leakage | **[M0-REC]** opaque on-disk names (random id) with real name/type held only in the (encrypted) `attachments` row — closes today's `patient_<reg_no>/<stem><ext>` leak. Residuals (file size ±block, per-patient count, directory existence) documented, not hidden |
| Atomic writes | write ciphertext to `*.tmp` then `os.replace()` (atomic on same volume); interrupted save leaves no half-file |
| Corruption/tamper detection | AEAD verify fails → "attachment unreadable/corrupt"; never wrong-plaintext |
| Wrong-key behavior | AEAD verify fails → clear error; no partial output |
| Partial-write behavior | temp-then-rename ensures a reader never sees a partially written object |
| Deletion | best-effort delete of the ciphertext object (preserves current `StorageProvider.delete` semantics); crypto-shredding a file's key is a stronger future option (not F7 scope) |
| `local_path()` handling | redesigned: **decrypt to a scoped temp file** for the viewer/print action; the raw path returned points at that temp file, not the ciphertext |
| Decrypt-to-temp strategy | temp file under a per-user, non-world-readable location (e.g. `%LOCALAPPDATA%`-scoped), created for the viewer's lifetime, removed on close/app-exit |
| **Unavoidable plaintext exposure (documented)** | the decrypt-to-temp window is real, unavoidable for external OS viewers/printers, and best-effort cleanup only; on SSD/journaling FS the temp bytes may persist after deletion — a documented residual limitation, not eliminated |

## 8. Backup Encryption Design (independently recoverable)

| Item | Design |
| ---- | ------ |
| Encrypted backup format | `magic || format_version || alg_id || kdf_id || kdf_salt || kdf_params || nonce || ciphertext || tag` over the built archive |
| Encryption boundary | encrypt the **whole built archive** (db + attachments zip) at the destination-write step; construction stays a local walk (ADR-002 §5.3) |
| Backup key strategy | `BACKUP_KEY = KDF(Recovery Key or a dedicated backup passphrase, kdf_salt)`; salt lives in the header |
| Relationship to clinic/device keys | **independent of `KEK_os`/DPAPI** — that is what makes a backup portable |
| Recovery process | new restore workflow: detect plaintext vs. encrypted (pre-F7 compat) → derive BACKUP_KEY → AEAD-verify → decrypt → atomic swap of `data/` + `attachments/` |
| New-machine portability | restore needs only the backup artifact + the Recovery Key/backup passphrase; **no original-machine keystore** (satisfies decision 5 and the hard rule) |
| Wrong-key behavior | AEAD verify fails → "wrong backup key/passphrase"; nothing written |
| Corruption/tamper detection | AEAD tag over the archive; header AAD; fail closed |
| Format versioning | `format_version` in the header; restore branches on it |
| Restore verification | after decrypt, verify archive integrity + DB opens with its key + row/schema sanity before the atomic swap |
| Backward compatibility | pre-F7 plaintext `backup_*.zip` remain restorable — the restore path detects and handles them |

## 9. Windows Key Protection

| Item | Design **[M0-REC/SEC-REVIEW]** |
| ---- | ------ |
| Mechanism | **Windows DPAPI** (`CryptProtectData`/`CryptUnprotectData`) to protect the `KEK_os` secret. Rationale: OS-native, offline, no key server, per-user; simplest fit for a single-clinician desktop |
| Protected material | the `KEK_os` secret (which unwraps the DEK) — **not** the DEK directly and never PHI |
| Scope | **[PO-DECISION]** user-scope (`CRYPTPROTECT_*`) vs. machine-scope. Recommend **user-scope** (tighter: bound to the Windows user), accepting that a Windows account change forces Recovery-Key re-provisioning |
| Reinstall behavior | app reinstall preserves the DPAPI blob if the same Windows profile persists → seamless unlock; otherwise Recovery Key |
| Same-machine recovery | if the DPAPI blob is intact and profile unchanged → automatic |
| New-machine recovery | DPAPI blob does not transfer → **Recovery Key** unlocks, then re-provision `KEK_os` |
| Windows account change | user-scope DPAPI cannot unprotect under a new account → locked → Recovery Key → re-provision |
| Permissions | key-material files ACL'd to the user; least privilege **[SEC-REVIEW]** |
| Failure behavior | any DPAPI failure → **locked state + Recovery-Key prompt**; **no plaintext fallback** |
| Non-Windows fallback | **[PO-DECISION]** dev/CI/Linux path (e.g. Recovery-Key/passphrase-only, or an OS-keyring abstraction). F7 targets Windows desktop; the fallback must at least keep tests runnable without DPAPI |

## 10. Offline Recovery Key

| Item | Design **[M0-REC/SEC-REVIEW]** |
| ---- | ------ |
| Entropy | ≥128-bit from the OS CSPRNG |
| Encoding | human-transcribable — grouped Base32 or a word-list (BIP-39-style) representation |
| Human/file representation | shown on screen for transcription and offered as a printable/exportable file; **never persisted in cleartext by the app** |
| Checksum/error detection | built-in checksum (e.g. CRC/last-word checksum) to catch transcription errors on entry |
| Administrator provisioning UX | generated at first launch / migration under the RBAC-gated Administrator/Security surface (ADR-002 §5.2/§6.6); operator must confirm they stored it before proceeding |
| Storage recommendation | offline, physically secured (safe/sealed envelope); never on the same disk as the data |
| Import/recovery process | operator enters/loads the key → KDF → `KEK_recovery` → unwrap DEK → resume |
| New-machine recovery | Recovery Key + data (or backup) → unlock → re-provision `KEK_os` |
| Re-provisioning | after use or on suspicion, generate a **new** Recovery Key, re-wrap the DEK under the new `KEK_recovery`, invalidate the old blob |
| Rotation | rotate by re-deriving `KEK_recovery` and re-wrapping the DEK (no data re-encryption) |
| Lost-key scenario | if **all** unwrap paths are lost (Recovery Key lost **and** DPAPI unavailable) the data is unrecoverable — the fundamental reason the Recovery Key must be stored offline and backups kept; documented starkly |
| Compromised-key scenario | treat as key compromise: rotate DEK (full re-encrypt) + issue a new Recovery Key; a leaked Recovery Key can decrypt any backup encrypted under it |

## 11. Existing-Data Migration

`plaintext → encrypted staging → verification → atomic switch → cleanup`.
**[LOCKED]** shape; mechanics **[M0-REC]**.

| Concern | Design |
| ------- | ------ |
| Administrator authorization | operator-initiated, RBAC-gated (Administrator); never automatic at startup |
| Pre-migration backup | mandatory full backup first; retained until the migration verifies |
| Disk-space requirement | pre-flight check for ~2× peak (old + new coexist); abort with a clear message if insufficient |
| Staging | encrypt DB via `sqlcipher_export` to a new encrypted file; encrypt each attachment to a new object; never mutate originals in place |
| Interruption | a per-item progress ledger records completed items; a crash leaves either the intact plaintext set or a verified encrypted set, never an unusable mix |
| Resume | re-run continues from the ledger |
| Verification | decrypt-and-compare / AEAD-verify + DB opens with key + row/schema checks before switching |
| Idempotency | detect an already-encrypted state and no-op; **never double-encrypt** |
| Rollback | on failure, restore from the mandatory pre-migration backup |
| Cleanup | after verified switch, remove plaintext originals; the transient plaintext backup is itself sensitive — encrypt it or securely remove it |
| Plaintext-remnant limitations | secure deletion is not guaranteed on SSD/journaling/COW filesystems — documented residual; recommend the operator also encrypt/retain the pre-migration backup securely |

## 12. Startup / Locked-State Machine

Format per state: **Detection → User-visible state → Allowed → Forbidden →
Recovery path.** The unlock stage runs before any DB access.

| State | Detection | User-visible | Allowed | Forbidden | Recovery |
| ----- | --------- | ------------ | ------- | --------- | -------- |
| First launch | no key material, no DB | provisioning wizard | generate DEK + Recovery Key, create encrypted DB, seed | any PHI access pre-provision | — |
| Provisioning | wizard in progress | "set up encryption" | store Recovery Key, confirm | skip Recovery Key | restart wizard |
| Normal unlocked | KEK_os unwraps DEK | app runs | all per RBAC | — | — |
| Locked startup | key material present, no unlock yet | unlock prompt | enter key/Recovery Key | PHI access | Recovery Key |
| Missing key | wrapped-DEK/DPAPI blob absent | "cannot unlock" | Recovery Key entry | plaintext fallback | Recovery Key → re-provision KEK_os |
| Wrong key | unwrap/`PRAGMA key` fails | "unlock failed" | retry / Recovery Key | partial init | Recovery Key |
| Corrupt database | per-page HMAC / open fails | "database corrupt" | restore-from-backup | migrate/run on corrupt DB | restore workflow |
| Corrupt attachment | per-file AEAD fails | that item "unreadable" | continue; restore item | trust the bytes | restore/backup |
| Missing attachment | object absent | that item "missing" | continue | crash | restore/backup |
| Interrupted migration | ledger shows partial | "resume/rollback migration" | resume or rollback | normal run mid-migration | ledger resume / pre-migration backup |
| Restored backup | restore flow ran | "restored" | unlock normally | run before verify | Recovery Key/backup passphrase |
| New machine | DPAPI cannot unwrap | "new machine — recover" | Recovery Key entry | plaintext fallback | Recovery Key → re-provision KEK_os |
| Recovery-Key startup | operator chose recovery | "recover with key" | enter Recovery Key | bypass | KEK_recovery → unwrap |
| Windows keystore unavailable | DPAPI error | "secure store unavailable" | Recovery Key entry | plaintext fallback | Recovery Key → re-provision |

**Invariant:** no state permits a silent plaintext fallback.

## 13. Threat Model

| Threat | Classification |
| ------ | -------------- |
| Stolen database file (+ side files) | **F7 PROTECTS** (key not co-located in clear) |
| Stolen attachment directory | **F7 PROTECTS** (content; filename opaqued; size/count residual) |
| Stolen backup artifact | **F7 PROTECTS** (independent backup key) |
| Filesystem access at rest / disk imaged | **F7 PROTECTS** |
| Copied application-data folder | **F7 PROTECTS** (wrapped keys only; DEK needs a KEK path) |
| Lost computer (powered off) | **F7 PROTECTS** |
| Compromised Windows account | **PARTIAL** — user-scope DPAPI ties `KEK_os` to the account; a compromised *logged-in* account with the app unlocked is not protected (see running-process) |
| Malicious administrator (clinic) | **F7 DOES NOT PROTECT** — needs audit/separation of duties |
| Running-process compromise (unlocked) | **F7 DOES NOT PROTECT** — DEK/plaintext in memory |
| Memory extraction of a live process | **F7 DOES NOT PROTECT** — mitigate with `cipher_memory_security`, minimal key lifetime; not eliminated |
| Ransomware / corruption | **F7 DOES NOT PREVENT** — AEAD/HMAC *detect* corruption; recovery is backups, not F7 |
| Key theft (wrapped blobs) | **F7 PROTECTS** unless the KEK is also obtained (DPAPI secret or Recovery Key) |
| Recovery-Key theft | **F7 DOES NOT PROTECT** — a stolen Recovery Key unwraps the DEK and decrypts backups; hence offline storage + rotation on suspicion |

No overclaiming: F7 is at-rest confidentiality/integrity. It does not address
authorization (RBAC/row-level), transport (F8), live-process compromise,
insider misuse, or guaranteed erasure.

## 14. Performance Requirements

Requirements + what M1 must **measure** (no invented benchmarks):

- Database open/unlock time (KDF + `PRAGMA key`) — target: not perceptibly
  slower to launch; measure.
- Per-query overhead of page-level AES — watch the search-per-keystroke hot
  path (L11); measure on representative data.
- Attachment encrypt/decrypt latency, especially large imaging files; decide
  streaming vs. whole-file by measured memory/latency.
- Backup encryption duration + temp space over a full data set.
- Migration duration (∝ PHI size) with progress + interruptibility.
- KDF cost (Argon2id/scrypt) — the startup-latency vs. brute-force knob;
  choose parameters from measurement on target-class hardware.
- Memory (KDF memory-hardness; `cipher_memory_security`) and disk overhead
  (per-page HMAC; per-file headers).

## 15. Packaging Requirements

- Introduce a **committed PyInstaller `.spec`** (none exists today) that
  bundles the native SQLCipher/OpenSSL wheel and any crypto lib, verified to
  load on a clean Windows machine, fully offline. **[PO-DECISION]** on the
  spec's inclusion at M3/M7.
- Acceptance gate: clean-install + offline-run + native-crypto-load smoke
  test on Windows.
- No ADR-002 §8.0 deployment-tier change; §8.1 SQLite-over-network rule
  preserved.

## 16. Security Test Matrix (M1–M7; specified, not written in M0)

> **No test is created or modified in M0.** The existing 130-test baseline,
> layering gates, and regression golden are preserved; the dependency-set and
> allow-list gates change **intentionally** at implementation (rule 12/13).

- **Database:** correct-key open · missing-key locked · wrong-key fail ·
  corruption detection · migration correctness · migration
  interruption/resume/idempotency.
- **Attachments:** round-trip · wrong key · tamper (AEAD reject) · corruption
  · atomic writes · temp-file cleanup.
- **Backups:** creation · restore round-trip · wrong key · corruption ·
  cross-machine portability · Recovery-Key restore · interrupted restore ·
  pre-F7 plaintext compatibility.
- **Key management:** provisioning · Windows (DPAPI) retrieval · Recovery-Key
  unwrap · key loss (all paths) · new machine · re-provisioning · KEK
  re-wrap/rotation.
- **Startup:** every §12 locked/error/recovery state.
- **Regression:** all 130 existing tests green; golden evaluated for
  intentional change with the key available in the fixture; layering gates
  updated intentionally.

## 17. Open Risks

| ID | Risk | Mitigation |
| -- | ---- | ---------- |
| F7-R1 | Native SQLCipher wheel fails to load under PyInstaller on a clinic Windows box | Early M1 packaging spike; static-wheel criterion; fallback binding evaluated |
| F7-R2 | Recovery Key lost **and** DPAPI unavailable → unrecoverable data | Provisioning forces Recovery-Key confirmation; backups kept; documented starkly |
| F7-R3 | Decrypt-to-temp leaks plaintext (viewer/print) | Scoped temp dir, minimal lifetime, best-effort cleanup; documented residual |
| F7-R4 | Nonce reuse under a long-lived key | Per-file keys / XChaCha20 large nonce; specialist review |
| F7-R5 | KDF params too weak (brute force) or too slow (UX) | Measured tuning at M1; specialist ratification |
| F7-R6 | Metadata leakage (sizes, counts) despite content encryption | Opaque filenames; document residuals |
| F7-R7 | Migration interrupted into a mixed state | Ledger + atomic swap + mandatory pre-migration backup |
| F7-R8 | Dependency supply-chain / maintenance burden | Pin versions; prefer maintained static-wheel bindings; document |
| F7-R9 | Windows account change silently locks the clinic out | Recovery-Key path + clear locked-state UX |
| F7-R10 | Secure-deletion expectation not met on SSD | Documented limitation; no guarantee claimed |

## 18. Specialist Security Review Requirements

Repository review alone does **not** prove cryptographic correctness. The
mandatory specialist review (approved decision 9) must ratify, before
implementation and before production readiness:

- AEAD algorithm + mode (GCM vs. XChaCha20-Poly1305) and nonce sizing/strategy
- KDF choice (Argon2id vs. scrypt) and parameters (memory/time/parallelism)
- key-wrap construction (AEAD-wrap vs. AES-KW)
- HKDF domain-separation labels
- SQLCipher cipher profile (keep defaults vs. custom) + PRAGMAs
  (`temp_store`, memory security) + WAL decision
- DPAPI usage (scope, permissions) + non-Windows fallback
- Recovery-Key entropy/encoding/checksum and provisioning/rotation flows
- key lifetime in memory / secure-wipe expectations
- migration security (staging, verification, plaintext-remnant handling)
- temporary-plaintext handling
- the exact binding pin + its bundled SQLCipher/OpenSSL versions

Grounding sources for the SQLCipher defaults cited in §4/§6:
- Zetetic, "SQLCipher 4.0.0 Release" — https://www.zetetic.net/blog/2018/11/30/sqlcipher-400-release/
- SQLCipher CHANGELOG — https://github.com/sqlcipher/sqlcipher/blob/master/CHANGELOG.md
- rotki/pysqlcipher3 (static wheels, SQLCipher 4.x + OpenSSL 3.0.x LTS) — https://github.com/rotki/pysqlcipher3

## 19. M1 Implementation Prerequisites

Before M1 begins (each is a gate, not an M0 action):
1. Product Owner approval of this M0 design.
2. Specialist security review sign-off of the §18 items.
3. Product Owner decisions on the **[PO-DECISION]** items in §21.
4. A pinned binding + verified Windows static wheel (evidence, not install).
5. Confirmation that the dependency-gate + layering-gate changes are
   pre-approved as intentional (rule 12/13).

M1 then implements the crypto/key foundation only (still separately gated).

## 20. LOCKED Decisions (Product-Owner-approved architecture)

The nine of §3: SQLCipher · envelope keys · mandatory offline Recovery Key ·
DB+attachments+backups scope · independently recoverable backups ·
admin-controlled/atomic/resumable/verified/idempotent migration · Windows
packaging accepted · crypto dependency allowed when required · mandatory
security review. Not reopened here.

## 21. OPEN Decisions

**[PO-DECISION] — need Product Owner approval:**
- exact crypto **dependency/binding** to adopt (and accepting the
  intentional `{flet,bcrypt}` gate change)
- **AEAD** family (AES-256-GCM vs. XChaCha20-Poly1305)
- **KDF** (Argon2id — adds `argon2-cffi` — vs. scrypt — no extra dep)
- **DPAPI scope** (user vs. machine) and the **non-Windows fallback**
- **journal mode** (WAL vs. rollback) under encryption
- whether a **committed PyInstaller spec** lands in F7
- backup key source (Recovery Key vs. a **dedicated backup passphrase**)

**[SEC-REVIEW] — need specialist validation:** every §18 item (parameters,
constructions, nonce strategy, key lifecycle, migration security, temp
handling).

**[M0-REC] — technical recommendations herein** are proposals only and do
**not** become approved decisions until the corresponding [PO-DECISION] /
[SEC-REVIEW] gate clears.

---

**M0 status:** design/documentation complete and internally consistent; no
runtime code, dependency, migration, schema, test, or packaging change.
Awaiting Product Owner approval and specialist security review before M1.
