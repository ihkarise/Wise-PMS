# Sprint 6 — M0 Security Design (F7 Encryption at Rest)

**Status:** PROPOSED — Product Owner review. **M0 = Security Design Review;
design/documentation only. No runtime code, no dependency, no migration, no
schema, no crypto implementation, no test change, no packaging change ships
with this document.** Detailed security design for
[`../architecture-decisions/ADR-004-F7-Encryption-at-Rest.md`](../architecture-decisions/ADR-004-F7-Encryption-at-Rest.md)
and [`SPRINT6_TECHNICAL_PLAN.md`](./SPRINT6_TECHNICAL_PLAN.md).
**Date:** 2026-09-21
**Revision 1 (2026-09-21):** M0 review refinements folded in — HIGH-1
(domain-separate `KEK_recovery` vs `BACKUP_KEY`, §4/§5.2/§8), HIGH-2
(authenticated wrapped-DEK context binding + rollback resistance, §5.1),
HIGH-3 (encrypted pre-migration backup, §11) — plus resolved KDF (§4/§5.2),
backup-key architecture (§8), AEAD recommendation (§4/§7), SQLCipher binding
acceptance criteria (§6), and the consolidated decision ledger (§21). The
approved architecture and terminology are unchanged; this revision adds
precision, it does not rewrite the design.
**Revision 2 (2026-09-21) — M0 CLOSURE:** the seven Product Owner decisions
are recorded (§22), the Recovery Key ≠ BACKUP_KEY clarification is made
explicit (§23), the specialist security gate is enumerated as a checklist
(§24), and the M1 prerequisites are finalized (§25). These are **directions
and documentation only** — no cryptographic parameters are fixed, no package
is pinned, no implementation is authorized. ADR-004 is unchanged (the
decisions are detailed design, not architecture-level changes).
**Revision 3 (2026-09-21) — SPECIALIST FINDINGS INCORPORATED:** the completed
specialist cryptographic/security review (verdict **ACCEPTABLE WITH
CONDITIONS**, no BLOCKER) is recorded as SEC-01…SEC-13 (§26), the KDF clarity
is finalized (§26.1: Recovery Key ≠ KEK_recovery ≠ BACKUP_KEY), the M1 gate is
re-tiered by resolution milestone (§26.10), and the three authorities are made
explicit (§27). Documentation only — no cryptographic parameter is invented,
no open implementation detail is selected, no code/dependency/schema/test
change. **M1 remains NOT AUTHORIZED.**

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
| **File/backup AEAD** | **M0 TECHNICAL RECOMMENDATION — REQUIRES SPECIALIST SECURITY REVIEW:** **XChaCha20-Poly1305** for whole-file attachments and backups; **AES-256-GCM** acceptable if the review prefers hardware-AES and per-file keys are used. See §7 "AEAD decision" for the full comparison | XChaCha20's 192-bit random nonce removes nonce-reuse fragility for streamed/large files; GCM is safe here only because per-file keys bound each key to one message. Final choice is a [PO-DECISION] ratified by [SEC-REVIEW] |
| **Nonce size** | GCM: **96-bit random**; XChaCha20: **192-bit random**; unique per encryption | Never reuse (key, nonce) |
| **Auth tag size** | **128-bit** | Full AEAD tag |
| **Key wrapping (HIGH-2)** | AEAD wrap: `wrap = AEAD(KEK, nonce, DEK, AAD)` **or** RFC 5649 AES-KW. **AAD MUST bind** `{keymat_version, kek_path_id, wrap_format_version}` | One wrapped-DEK record per KEK; the authenticated AAD makes substitution/rollback of an old record detectable (see §5.1) |
| **Subkey derivation** | **HKDF-SHA-256** with distinct `info` labels: `"wise-pms/db/v1"`, `"wise-pms/attach/v1"` | The DEK is already a uniform 256-bit key, so **HKDF-Expand-only** is sufficient (Extract/salt is for non-uniform inputs); distinct `info` gives domain separation across CBC/HMAC (SQLCipher) vs. AEAD (files) |
| **KEK-derivation domain separation (HIGH-1)** | Every KEK/backup key derived from a shared secret MUST include a fixed **context label**, not only a salt: `"wise-pms/kek-recovery/v1"` (KEK_recovery) vs `"wise-pms/backup/v1"` (BACKUP_KEY) vs `"wise-pms/kek-pass/v1"` (KEK_pass) | Distinct salts alone do not *guarantee* independence; the context label makes it impossible for two purposes to derive the same/related key even under a salt collision (see §5.2) |
| **Recovery-Key KDF (STEP 5)** | A full-entropy (≥128-bit CSPRNG) **Recovery Key** needs only **HKDF** (with the §5.2 context) — a memory-hard KDF adds startup cost without security benefit for a uniform key. A **low-entropy human passphrase** (operator passphrase / a dedicated backup passphrase) **requires a memory-hard KDF: Argon2id** (needs `argon2-cffi`) **or scrypt** (stdlib `hashlib.scrypt` / the crypto lib — ₹0) | KEK derivation only; the SQLCipher DB raw-key path bypasses SQLCipher's own PBKDF2 (avoids a double KDF). Exact params are [SEC-REVIEW], benchmarked on clinic hardware |
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
     DPAPI unprotect            HKDF(RecoveryKey, salt,          KDF(passphrase, salt,
            │                    "wise-pms/kek-recovery/v1")      "wise-pms/kek-pass/v1")
            │                                │                             │
         KEK_os                        KEK_recovery                    KEK_pass
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
     Recovery Key (or dedicated backup passphrase)
        ──KDF(salt, "wise-pms/backup/v1")──> BACKUP_KEY ──AEAD──> encrypted backup artifact
```

> **Domain separation (HIGH-1):** where `KEK_recovery` and `BACKUP_KEY` derive
> from the *same* Recovery Key, they use **distinct fixed context labels**
> (`"wise-pms/kek-recovery/v1"` vs `"wise-pms/backup/v1"`) in addition to
> distinct salts — see §5.2.

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

### 5.1 Wrapped-DEK record & rollback resistance (HIGH-2)

Each KEK path wraps the DEK into a **wrapped-DEK record** — one per path. To
make substitution/rollback of an old record detectable, every record is an
authenticated structure whose AEAD **AAD binds its own identity**:

```
wrapped-DEK record =
  header{ magic, wrap_format_version, keymat_version, kek_path_id }   <- also the AEAD AAD
  || nonce
  || AEAD(KEK, nonce, DEK, AAD = header)
```

- **`keymat_version`** — a monotonically increasing generation for the DEK's
  key material; bumped on any DEK rotation or KEK-set change.
- **`kek_path_id`** — which path wrapped this record (`os` / `recovery` /
  `pass`), so a `recovery` record can't be presented as an `os` record.
- **`wrap_format_version`** — the wrapping construction version.

Because the AAD is authenticated, altering any of these fields, or swapping a
record between paths, fails AEAD verification. A separate, authenticated
**key-material manifest** (listing the current `keymat_version` and the set of
valid `kek_path_id`s) lets the app reject a record whose `keymat_version` is
older than the manifest — closing the "restore an old/revoked wrapped-DEK"
rollback. `[SEC-REVIEW]` ratifies the exact construction and manifest
integrity mechanism.

Expected behavior by operation:

| Operation | Effect on wrapped-DEK records |
| --------- | ----------------------------- |
| **DEK rotation** (compromise) | new DEK → new `keymat_version` → **all** records re-created; data re-encrypted; old records destroyed and rejected by the manifest |
| **KEK rotation / re-wrap** | DEK unchanged; the affected path's record is re-created under the new KEK; `keymat_version` bumped so the old record is rejected |
| **Recovery Key replacement** | re-derive `KEK_recovery` from the new key → re-create the `recovery` record; invalidate the old (manifest bump) |
| **Adding a new machine** | wrap the existing DEK under the new machine's `KEK_os` → add an `os` record (no data re-encryption) |
| **Removing/revoking a key path** | drop that path's record; bump the manifest so the removed record can't be reinstated |
| **Restoring old key-material metadata** | rejected: the record's `keymat_version` is older than the manifest → fail closed |

### 5.2 Why KEK_recovery and BACKUP_KEY cannot become interchangeable (HIGH-1)

`KEK_recovery` (wraps the DEK) and `BACKUP_KEY` (encrypts backup artifacts)
may share the **same** Recovery Key as input. Relying on different *salts*
alone is insufficient — a salt collision, a salt-handling bug, or reuse of a
stored salt could make the two derivations coincide. The design therefore
**requires a fixed, distinct context label per purpose** bound into the KDF
`info`/context:

- `KEK_recovery = HKDF(RecoveryKey, salt_r, "wise-pms/kek-recovery/v1")`
- `BACKUP_KEY   = KDF(RecoveryKey_or_backup_passphrase, salt_b, "wise-pms/backup/v1")`

With distinct context labels, the two outputs are cryptographically
independent **regardless of salt values**, so a key derived for wrapping can
never be used to decrypt a backup (or vice versa), and a future code path
cannot accidentally cross-use them. The `/vN` suffix versions the derivation
so the scheme can evolve without ambiguity. `[SEC-REVIEW]` confirms the label
set and KDF binding.

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

### 6.1 SQLCipher binding — acceptance criteria (STEP 8)

SQLCipher remains the **[LOCKED]** database-encryption architecture. **No
binding is chosen from memory and none is installed here.** The eventual
binding must be selected during M1 preparation and confirmed by
`[SEC-REVIEW]`, and must satisfy **all** of:

1. SQLCipher **4.x**.
2. A **Windows prebuilt wheel** (no compiler on the clinic machine).
3. **Static/native dependencies bundled** (SQLCipher + OpenSSL inside the wheel).
4. **No system SQLCipher/OpenSSL requirement** on the host.
5. Compatible with the project's supported **Python version**.
6. **PyInstaller** compatibility (loads from a frozen `WisePMS.exe`).
7. Fully **offline** operation (no network at run or build time).
8. A **reproducible version pin** (package + SQLCipher + OpenSSL versions).
9. **Security/maintenance evidence** (active maintenance, OpenSSL 3.x LTS,
   advisory history).
10. A **clean-machine installation + load test** on Windows.

Candidates to *evaluate* against these criteria (not a selection):
`sqlcipher3-binary`, `rotki/pysqlcipher3` (statically linked SQLCipher 4.x +
OpenSSL 3.0.x LTS). Final pin is an M1-preparation `[PO-DECISION]` +
`[SEC-REVIEW]` item.

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

### 7.1 AEAD decision (STEP 7)

**M0 TECHNICAL RECOMMENDATION — REQUIRES SPECIALIST SECURITY REVIEW.**

| Axis | AES-256-GCM | XChaCha20-Poly1305 |
| ---- | ----------- | ------------------- |
| Nonce | 96-bit; **catastrophic on reuse**; safe here only with per-file keys | 192-bit random; reuse risk negligible even across many files |
| Per-file key strategy | required to stay safe | recommended but not required for safety |
| Performance (AES-NI) | fastest with hardware AES | fast in software; no AES-NI dependency |
| Windows HW acceleration | benefits from AES-NI (common but not universal on clinic HW) | consistent without special HW |
| Implementation maturity | ubiquitous, well-audited | widely available, well-regarded (libsodium/`cryptography`) |
| Python library support | `cryptography` (`AESGCM`) | `cryptography` (`XChaCha20Poly1305` / ChaCha20Poly1305) |
| PyInstaller implications | one native wheel (`cryptography`) | same wheel; no extra dependency |
| Backup streaming suitability | fine with chunked construction + per-chunk nonces | large nonce simplifies chunk/stream nonce management |

**Recommendation:** **XChaCha20-Poly1305** for whole-file attachments and
backups (its large random nonce removes nonce-management fragility for
streamed/large data); **AES-256-GCM is acceptable** if the review prefers
hardware-AES *and* the per-file-key strategy (§7) is used. Either way,
128-bit tag, unique random nonce per encryption, AAD binding per §7.
**This is a `[PO-DECISION]` ratified by `[SEC-REVIEW]`; not chosen here.**

### 7.2 Temporary plaintext — residual limitation (STEP 11)

The decrypt-to-temp path for external viewers/printers is an **unavoidable**
plaintext window. The design bounds it; it does **not** eliminate it:

- **Location:** a per-user, non-world-readable directory (e.g. a
  `%LOCALAPPDATA%`-scoped app temp folder), never a shared/world temp path.
- **Permissions:** ACL'd to the current user only.
- **Lifetime:** created immediately before the viewer/print action; the
  shortest lifetime that lets the external app open it.
- **Cleanup:** deleted when the viewer closes and again on application exit;
  a startup sweep removes any strays from a prior crash.
- **Crash behavior:** a hard crash may leave a temp plaintext file; the
  next-launch sweep removes it (best-effort).
- **Application-exit behavior:** the temp directory is purged on clean exit.
- **Secure-deletion limitation:** on SSDs/journaling/COW filesystems,
  deletion does **not** guarantee the bytes are unrecoverable. **No secure-
  erase guarantee is claimed.** Documented residual; `[SEC-REVIEW]` confirms
  the handling is as tight as practical.

## 8. Backup Encryption Design (independently recoverable)

| Item | Design |
| ---- | ------ |
| Encrypted backup format | `magic || format_version || alg_id || kdf_id || kdf_salt || kdf_params || nonce || ciphertext || tag` over the built archive |
| Encryption boundary | encrypt the **whole built archive** (db + attachments zip) at the destination-write step; construction stays a local walk (ADR-002 §5.3) |
| Backup key strategy | `BACKUP_KEY = KDF(Recovery Key or a dedicated backup passphrase, kdf_salt, "wise-pms/backup/v1")`; salt lives in the header. The **context label** (HIGH-1, §5.2) keeps `BACKUP_KEY` cryptographically independent of `KEK_recovery` even when both derive from the same Recovery Key |
| Relationship to clinic/device keys | **independent of `KEK_os`/DPAPI** — that is what makes a backup portable |
| Recovery process | new restore workflow: detect plaintext vs. encrypted (pre-F7 compat) → derive BACKUP_KEY → AEAD-verify → decrypt → atomic swap of `data/` + `attachments/` |
| New-machine portability | restore needs only the backup artifact + the Recovery Key/backup passphrase; **no original-machine keystore** (satisfies decision 5 and the hard rule) |
| Wrong-key behavior | AEAD verify fails → "wrong backup key/passphrase"; nothing written |
| Corruption/tamper detection | AEAD tag over the archive; header AAD; fail closed |
| Format versioning | `format_version` in the header; restore branches on it |
| Restore verification | after decrypt, verify archive integrity + DB opens with its key + row/schema sanity before the atomic swap |
| Backward compatibility | pre-F7 plaintext `backup_*.zip` remain restorable — the restore path detects and handles them |

### 8.1 Backup key architecture — Product Owner decision (STEP 6)

A genuine `[PO-DECISION]`. Both options keep backups **independently
recoverable** (never dependent on the origin machine's DPAPI).

**Option A — Recovery-Key-derived backup key** (`BACKUP_KEY` from the
Recovery Key, §5.2 label).
- *Security:* one high-value secret governs both live recovery and backups →
  **larger blast radius** (a leaked Recovery Key decrypts every backup too).
- *Operational:* **one** offline credential to generate, store, and protect.
- *Recovery:* simplest disaster recovery — the same Recovery Key restores a
  backup on any machine; nothing extra to lose.

**Option B — Dedicated backup credential** (a separate backup passphrase/key).
- *Security:* **separation of blast radius** — compromising the live-system
  Recovery Key does not compromise backups, and vice versa.
- *Operational:* a **second** credential to manage and not lose; low-entropy
  passphrases require a memory-hard KDF (§4/STEP 5).
- *Recovery:* restoring a backup needs the dedicated backup secret, an added
  step/credential during disaster recovery.

**M0 recommendation:** **Option A** for a single-clinician offline desktop —
it minimizes the number of offline secrets the clinic must not lose (the
dominant real-world failure mode, F7-R2), while the §5.2 domain separation
already prevents cross-use of the derived keys. **Option B** is the right
choice if the Product Owner wants backup exposure isolated from live-system
recovery (e.g. backups leave the premises). **Exact decision required from
the Product Owner:** *choose Option A (shared Recovery Key) or Option B
(dedicated backup credential).* Not chosen here.

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

> **What DPAPI does and does not protect (STEP 9).** DPAPI protects the
> `KEK_os` secret **at rest** — it is decryptable only under the same Windows
> user (user-scope) / machine (machine-scope), so a stolen disk or a copied
> app-data folder cannot unwrap it. **DPAPI does NOT protect against a
> compromised process running under the same Windows identity:** any code
> running as that user can call `CryptUnprotectData`, and while the app is
> unlocked the DEK is in memory. This is consistent with the threat model
> (§13): running-process compromise and a compromised, logged-in account are
> **not** protected by F7. The Recovery Key path always bypasses DPAPI for
> at-rest recovery; DPAPI is a convenience KEK, never the only unwrap path.

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

> **Is the Recovery Key ever stored digitally (STEP 10)?** **Not by the
> application in cleartext.** The app generates it (≥128-bit CSPRNG), shows it
> **once** for transcription, and may offer a user-initiated export to a file
> the operator then moves to offline storage — but the app never writes it to
> its own data directory, logs, or config, and never keeps it after
> provisioning. Only KDF **salts** and the authenticated wrapped-DEK records
> (§5.1) persist; the Recovery Key itself lives only offline in the operator's
> custody. Revocation/re-wrapping and rotation follow §5.1 (bump
> `keymat_version`, re-create the `recovery` record, reject the old).
> `[SEC-REVIEW]` confirms entropy, encoding, checksum, and the no-persistence
> guarantee.

## 11. Existing-Data Migration

**[LOCKED]** shape; mechanics **[M0-REC]**. **Required order (HIGH-3) — the
rollback safety net is an *encrypted* backup, never a plaintext one:**

```
1. Provision encryption keys (DEK + KEK paths + Recovery Key)
        ↓
2. Create an ENCRYPTED pre-migration backup (BACKUP_KEY over the current
   still-plaintext data, via the §8 backup path)
        ↓
3. Verify that encrypted backup (AEAD-verify + test-restore integrity)
        ↓
4. Encrypt/stage the database (sqlcipher_export) and attachments to NEW files
        ↓
5. Verify the encrypted result (decrypt-and-compare / AEAD-verify + DB opens
   with its key + row/schema checks)
        ↓
6. Atomic switch (swap encrypted DB + attachments into place)
        ↓
7. Retain the encrypted rollback backup per policy
        ↓
8. Clean up plaintext material as far as technically possible
```

Because keys are provisioned first (step 1), the pre-migration backup at step
2 is **already encrypted** — there is **no full-PHI plaintext backup** acting
as the rollback mechanism. The only plaintext that exists during migration is
the original live data being converted (step 4 reads it), which is removed at
step 8.

| Concern | Design |
| ------- | ------ |
| Administrator authorization | operator-initiated, RBAC-gated (Administrator); never automatic at startup |
| Pre-migration backup (HIGH-3) | mandatory **encrypted** backup first (keys provisioned in step 1); verified; retained as the encrypted rollback net. **The rollback mechanism is never a plaintext backup.** |
| Disk-space requirement | pre-flight check for ~2× peak (old + new coexist); abort with a clear message if insufficient |
| Staging | encrypt DB via `sqlcipher_export` to a new encrypted file; encrypt each attachment to a new object; never mutate originals in place |
| Interruption | a per-item progress ledger records completed items; a crash leaves either the intact plaintext set or a verified encrypted set, never an unusable mix |
| Resume | re-run continues from the ledger |
| Verification | decrypt-and-compare / AEAD-verify + DB opens with key + row/schema checks before switching |
| Idempotency | detect an already-encrypted state and no-op; **never double-encrypt** |
| Rollback | on failure, restore from the **encrypted** pre-migration backup (step 2/7) |
| Cleanup | after verified switch, remove plaintext originals; there is no plaintext backup to dispose of (step 2 is encrypted) |
| Plaintext-remnant limitations | secure deletion of the original plaintext data is **not** guaranteed on SSD/journaling/COW filesystems — documented residual, no secure-erase guarantee claimed; the encrypted rollback backup means recovery never depends on those remnants |

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

## 21. Decision Ledger (five tiers — STEP 12)

### 21.1 LOCKED (Product-Owner-approved architecture — §20)
The nine decisions of §3. Not reopened.

### 21.2 M0 RECOMMENDATIONS (still require specialist confirmation)
Proposals; not approved decisions until the matching [PO-DECISION] /
[SEC-REVIEW] gate clears:
- **AEAD:** XChaCha20-Poly1305 (GCM acceptable with per-file keys) — §7.1.
- **Backup key architecture:** Option A (Recovery-Key-derived) for a single
  clinician — §8.1.
- **KDF split:** HKDF for the high-entropy Recovery Key; Argon2id/scrypt for
  any low-entropy human passphrase — §4/STEP 5.
- **SQLCipher profile:** keep the version-4 defaults; `temp_store=MEMORY`; add
  the §6.1 binding acceptance criteria — §6.
- **Design requirements HIGH-1/2/3** (now folded into §4/§5.1/§5.2/§8/§11):
  KEK/backup domain-separation labels; authenticated wrapped-DEK context +
  rollback resistance; encrypted pre-migration backup. These are **design
  requirements** to be ratified by [SEC-REVIEW], not open questions.

### 21.3 PRODUCT OWNER DECISIONS (explicit choice required before M1)
- Exact crypto **dependency/binding** (accepting the intentional
  `{flet,bcrypt}` layering-gate change) — against §6.1 criteria.
- **AEAD family** (ratify XChaCha20-Poly1305 vs. AES-256-GCM) — §7.1.
- **KDF** for passphrases (Argon2id — adds `argon2-cffi` — vs. scrypt — no
  extra dep) — §4.
- **DPAPI scope** (user vs. machine) and the **non-Windows fallback** — §9.
- **Journal mode** (rollback — recommended — vs. WAL) — §6.
- **Backup key architecture** (Option A vs. Option B) — §8.1.
- Whether a **committed PyInstaller spec** lands within F7 — §15.

### 21.4 SPECIALIST SECURITY DECISIONS (cryptographic/security review)
Every §18 item: AEAD/mode + nonce strategy · KDF + parameters · key-wrap
construction and its authenticated AAD (HIGH-2) · KEK/backup domain-separation
labels (HIGH-1) · HKDF labels · SQLCipher profile/PRAGMAs/WAL · DPAPI
usage/permissions + fallback · Recovery-Key entropy/encoding/checksum + the
no-digital-persistence guarantee · in-memory key lifetime/zeroization ·
migration security incl. the encrypted-pre-migration-backup ordering (HIGH-3)
· temporary-plaintext handling · the exact binding pin + bundled
SQLCipher/OpenSSL versions. **Repository review alone does NOT prove
cryptographic correctness.**

### 21.5 M1 PREREQUISITES (§19)
The five gates in §19 must all be satisfied — PO approval of this design,
specialist sign-off of §18/§21.4, PO resolution of §21.3, a pinned/verified
Windows static wheel, and pre-approval of the intentional dependency/layering
gate changes — before M1 begins.

---

## 22. Product Owner Decisions — F7 M0

Recorded verbatim from the Product Owner's M0 closure. Each is a **direction**;
none authorizes implementation, fixes a cryptographic parameter, or pins a
package. Columns: **PO direction** · **Specialist review required** ·
**Implementation evidence required** · **Blocks M1?**

| # | Decision | PO architecture direction | Specialist security review required | Implementation evidence required | Blocks M1? |
| - | -------- | ------------------------- | ----------------------------------- | -------------------------------- | :--------: |
| 1 | **SQLCipher binding** | APPROVED: statically linked / prebuilt **SQLCipher 4.x + OpenSSL 3.x** wheel approach. **Do NOT select/pin the final package** until the M1 evidence gate is met | SQLCipher cipher profile, raw-key handling, PRAGMAs; bundled SQLCipher/OpenSSL versions | Clean-Windows install, offline run, PyInstaller load, reproducible pin, DB-API compatibility, licensing/redistribution (§6.1) | **Yes** |
| 2 | **Attachment & backup AEAD** | APPROVED DIRECTION: **XChaCha20-Poly1305** (architecture direction only) | Exact API/version, nonce construction & uniqueness, AAD, tag verification, whole-file vs chunked/streamed design | `cryptography` version/API availability for the chosen AEAD | **Yes** |
| 3 | **KDF** | APPROVED: high-entropy **Recovery Key → HKDF**; human passphrases → **memory-hard KDF, scrypt preferred** over adding `argon2-cffi` (dependency minimization) | KDF choice confirmation; **exact scrypt parameters** | Parameters selected after specialist review **and benchmarked on representative clinic hardware** | **Yes** |
| 4 | **Windows DPAPI** | APPROVED: **user-scope** DPAPI for `KEK_os` only; Recovery Key remains the mandatory offline recovery; DPAPI is **not** protection against a compromised same-Windows-identity process | DPAPI usage/permissions; the non-Windows dev/CI fallback | Non-Windows fallback explicitly designed & reviewed before implementation | **Yes** |
| 5 | **SQLite journal mode** | APPROVED: **retain rollback journal**; do NOT migrate to WAL (selected F7 direction for the single-clinician offline architecture) | Confirm side-file (journal) encryption under SQLCipher | — | **No** (selected default) |
| 6 | **Backup key architecture** | APPROVED: **Recovery-Key-derived `BACKUP_KEY`** — but the Recovery Key **MUST NOT** be reused directly as `BACKUP_KEY`; use explicit domain separation / independent derivation context (preserve the §5.2 requirement) | The exact derivation construction | — | **Yes** |
| 7 | **PyInstaller** | APPROVED: commit a **reproducible `.spec`** as part of F7, introduced at the implementation milestone when native SQLCipher/crypto deps are known (M3/M7). **Do NOT create it during M0 closure** | Native-library loading behavior | Clean-Windows native-crypto load evidence (at M3/M7) | **No** (M3/M7; not now) |

**Cross-references:** Decision 1 → §6/§6.1; 2 → §4/§7.1; 3 → §4/§5.2/STEP 5;
4 → §9; 5 → §6; 6 → §5.2/§8/§8.1/§23; 7 → §15.

## 23. Backup-key clarification — Recovery Key ≠ BACKUP_KEY

**Explicit, non-negotiable per the PO decision (§22 #6):**

- The **Recovery Key** is the high-entropy root recovery secret (§10); it is
  never persisted digitally in cleartext and is held offline by the operator.
- **`BACKUP_KEY` is NOT the Recovery Key** and is **never** the Recovery Key
  used directly. It is **independently derived** from the Recovery Key through
  the KDF with a **distinct domain-separation context**
  (`"wise-pms/backup/v1"`, §5.2) and its own salt.
- This preserves the previously approved domain separation between
  recovery-KEK material (`"wise-pms/kek-recovery/v1"`) and backup-key material
  (`"wise-pms/backup/v1"`) so the two derived keys are cryptographically
  independent even though they share one root secret (§5.2 rationale, §5.1
  wrapped-DEK binding).
- **The exact derivation construction (KDF choice, ordering, encoding) remains
  subject to specialist cryptographic review (§24).** This document does not
  invent the final construction beyond the approved domain-separation
  requirement.

## 24. Specialist Security Gate — mandatory review checklist

Every item below must be reviewed and signed off by a cryptography/security
specialist **before implementation approval**. A Product Owner architecture
decision does **not** substitute for this review. Repository/design review
alone does **not** prove cryptographic correctness.

- [ ] XChaCha20-Poly1305 API/version (availability in the chosen crypto library)
- [ ] Nonce generation and uniqueness (per-encryption, CSPRNG)
- [ ] AAD design (fields bound; tamper/relocation resistance)
- [ ] Authentication tag verification (fail-closed on mismatch)
- [ ] Whole-file vs chunked/streamed encryption (large attachments/backups)
- [ ] scrypt parameters (N, r, p) — benchmarked on clinic hardware
- [ ] HKDF labels (domain-separation `info` values)
- [ ] Key wrapping construction (AEAD-wrap / AES-KW)
- [ ] Wrapped-key AAD ({keymat_version, kek_path_id, wrap_format_version}, §5.1)
- [ ] Domain separation (`KEK_recovery` vs `BACKUP_KEY`, §5.2/§23)
- [ ] SQLCipher profile and PRAGMAs (`key`, `foreign_keys`, `temp_store`, memory security)
- [ ] SQLCipher raw-key handling (`DB_KEY` hex raw key; no passphrase-PBKDF2 double KDF)
- [ ] DPAPI user-scope behavior (protection boundary; permissions)
- [ ] Recovery Key entropy and encoding (≥128-bit; checksum)
- [ ] Recovery Key non-persistence (never stored digitally in cleartext)
- [ ] In-memory key lifetime (minimization; best-effort wipe limits in Python)
- [ ] Temporary plaintext handling (viewer decrypt-to-temp; location/lifetime/cleanup)
- [ ] Migration ordering (keys → encrypted backup → stage → verify → switch, §11)
- [ ] Encrypted pre-migration backup (rollback net is never plaintext, HIGH-3)
- [ ] Secure deletion limitations (no guarantee on SSD/journaling/COW FS)
- [ ] Bundled SQLCipher/OpenSSL versions (pin + advisory review)
- [ ] PyInstaller native-library loading (frozen `.exe`, offline)

## 25. M1 Prerequisites (closure — supersedes/confirms §19)

**M1 remains NOT AUTHORIZED until ALL of the following are satisfied:**

1. Final M0 documentation is approved by the Product Owner.
2. Specialist security review is completed and signs off on the cryptographic
   design (the §24 checklist).
3. The SQLCipher binding candidate is verified against the required criteria
   (§6.1).
4. Windows clean-machine / offline / PyInstaller-loading evidence exists.
5. AEAD implementation/API availability (XChaCha20-Poly1305) is verified.
6. KDF parameters are selected after specialist review and hardware
   benchmarking (§22 #3).
7. Dependency/layering-gate impact is explicitly reviewed and approved
   (the intentional `{flet,bcrypt}` gate + `test_layering.py` allow-list change).
8. Any required licensing/redistribution review is completed (bundled native
   libraries).

Only when all eight clear does M1 (crypto/key-management foundation) become
eligible for its own separate Product Owner authorization — it still does not
begin automatically.

## 26. Specialist Security Review — Conditional Findings

The specialist cryptographic/security review is **complete**. **Verdict:
SECURITY DESIGN ACCEPTABLE WITH CONDITIONS — no BLOCKER.** The architecture
(SQLCipher raw-key at the adapter seam; envelope DEK/KEK with HKDF domain
separation; mandatory offline Recovery Key; authenticated wrapped-DEK records;
per-file AEAD; independently recoverable encrypted backups; keys-first /
encrypted-pre-migration-backup ordering) is sound and the threat model does
not overclaim. The conditions below must be resolved or routed to the correct
gate before the milestone that implements them. **This section records the
findings; it does not fix them in code, invent parameters, or select any
implementation detail the review left open.**

| ID | Severity | Security issue | Design consequence | Required resolution | Milestone/gate | Blocks M1? | External verify? |
| -- | -------- | -------------- | ------------------ | ------------------- | -------------- | :--------: | :--------------: |
| SEC-01 | HIGH | XChaCha20-Poly1305 may be unavailable in the pinned crypto library (recent addition) or need PyNaCl (extra native dep) | The approved AEAD direction may not be implementable as-is | Verify exact package/version/API or select a formally reviewed alternative (§26.2) | Before M1 (AEAD gate) | **Yes** | **Yes** |
| SEC-02 | HIGH | DB file + attachment tree cannot switch in one atomic filesystem op | A crash between the two switches leaves a mixed encrypted/plaintext state | Durable combined migration-phase marker + exclusive/resumable/idempotent recovery (§26.3) | Before M5 | No | Specialist/design |
| SEC-03 | HIGH | Pre-F7 plaintext `backups/*.zip` survive migration; OS pagefile/hibernation may hold plaintext/keys | Full-PHI plaintext can persist off the encrypted set | Define legacy-backup handling; document pagefile/hibernation residual + recommend OS FDE (§26.4) | Before production | No | Specialist judgment |
| SEC-04 | MEDIUM | KDF ambiguity between the high-entropy Recovery Key and low-entropy passphrases | Risk of an unnecessary/incorrect KDF on `BACKUP_KEY`/`KEK_recovery` | Fix: HKDF for the Recovery Key paths; memory-hard KDF only for passphrases (§26.1) | Before M1 | **Yes** | Specialist confirm |
| SEC-05 | MEDIUM | SQLCipher raw-key format/salt/HMAC-key/PRAGMA specifics unpinned | Wrong raw-key handling could weaken/keying-break the DB | Pin format/salt/PRAGMA against the exact binding (§26.5) | Before M3 | **Yes** | **Yes** (SQLCipher) |
| SEC-06 | MEDIUM | User-scope DPAPI can fail on account change, forced password reset, profile corruption/replacement | KEK_os becomes unusable | Document + operational runbook; Recovery Key is the recovery path (§26.6) | Before production | No | **Yes** (Windows) |
| SEC-07 | MEDIUM | Nonce/key uniqueness must be enforced per encryption | Nonce reuse (esp. AES-GCM) would break confidentiality | Fresh per-file key / fresh nonce; no reuse; no unsafe in-place re-encrypt (§26.8) | Before M2/M4 | No | Specialist |
| SEC-08 | MEDIUM | Recovery Key is never stored → a lost printout on a still-unlocked machine cannot be re-shown | Clinics may be stranded without a re-issue path | Authenticated rotate/re-provision flow while the current key is available (§26.7) | Before production/recovery workflow | No | Specialist/operational |
| SEC-09 | MEDIUM | Native crypto/DB deps change requirements, the dependency gate, and packaging | Layering gate + PyInstaller impact | Approve dependency architecture; pin versions; verify Windows/PyInstaller load; known OpenSSL/SQLCipher versions (§26.9) | Before M1 | **Yes** | **Yes** |
| SEC-10 | LOW | Bundled native libs carry licensing/NOTICE obligations (Apache-2.0 attribution) | Redistribution compliance | Licensing/NOTICE review; include required notices in the `.exe` | Before production | No | **Yes** (legal) |
| SEC-11 | INFORMATIONAL | Python cannot guarantee key zeroization; DEK/plaintext in memory while unlocked | Residual consistent with the threat model (running-process not protected) | Document residual; minimize key lifetime | — | No | No |
| SEC-12 | INFORMATIONAL | HKDF domain separation adequacy | Depends on a uniform Recovery Key + one consistent HKDF construction | Confirm HKDF construction and uniform IKM (§26.1) | Before M1 | No | Specialist confirm |
| SEC-13 | INFORMATIONAL | SQLCipher codec/temp/journal behavior varies by build | `temp_store`/journal/temp encryption may not hold as assumed | Verify codec-enabled build; journal + temp files encrypted; `temp_store=MEMORY` supported (§26.5) | Before M3 | No | **Yes** (SQLCipher) |

### 26.1 KDF clarification (SEC-04, SEC-12)

- **Recovery Key** — high entropy (≥128-bit CSPRNG). It is **NOT** passed
  through a memory-hard password KDF. Derivation is **HKDF-based** with
  explicit domain separation.
- **`KEK_recovery`** — derived from the Recovery Key using the approved
  recovery-domain context (`"wise-pms/kek-recovery/v1"`).
- **`BACKUP_KEY`** — derived **independently** from the *same* Recovery Key
  using the approved backup-domain context (`"wise-pms/backup/v1"`).
- Therefore **Recovery Key ≠ KEK_recovery ≠ BACKUP_KEY.** The exact HKDF
  construction remains subject to specialist verification (SEC-12).
- **Human passphrase** (operator passphrase, or a dedicated backup passphrase
  under the not-selected Option B) is a *different* security input: it
  **requires a memory-hard KDF**. Preferred direction remains **scrypt**;
  **exact parameters are deferred to specialist review and hardware
  benchmarking and are not invented here.**

### 26.2 AEAD availability gate (SEC-01)

XChaCha20-Poly1305 remains the Product Owner's **preferred direction**. It is
**NOT implementation-approved** until the actual pinned library/API is
verified. The implementation gate must establish: exact package; exact
version; API availability; Windows support; offline packaging; PyInstaller
compatibility; native-dependency implications. **If** XChaCha20-Poly1305
cannot be reliably supported within the approved dependency/packaging
constraints, a **formally reviewed alternative** must be selected before AEAD
implementation. **No alternative is selected now.**

### 26.3 Migration atomicity requirement (SEC-02)

The database file and the attachment tree **cannot** be assumed to have a
single filesystem atomic switch. Migration **MUST** therefore keep a durable
migration-phase/state marker representing the combined state of: database ·
attachments · encrypted staging · plaintext source · rollback backup. It must
recover safely after power loss, process crash, disk-full, partial
encryption, and interrupted cleanup, and be **exclusive/offline · resumable ·
idempotent · verifiable.** This is a **design requirement for M5**; the state
machine and its final schema are **not** implemented or invented here.

### 26.4 Residual plaintext surfaces (SEC-03)

- **Pre-F7 plaintext backups:** existing `backups/*.zip` may remain plaintext
  after F7 migration unless specifically handled. The migration plan must
  define how legacy backups are handled. **They are not auto-deleted or
  converted in this task.**
- **OS pagefile / hibernation:** decrypted DB pages, plaintext attachment
  content, and key material may temporarily exist in memory and potentially in
  OS-managed pagefile/hibernation storage. **F7 does not claim protection
  against this.** OS-level full-disk encryption is documented as complementary
  protection. Application-level encryption does **not** eliminate this residual.

### 26.5 SQLCipher raw-key & codec verification gate (SEC-05, SEC-13)

Unresolved until the exact binding/version is verified: raw-key format · key
encoding · salt handling · SQLCipher key-derivation behavior · HMAC-key
derivation · PRAGMA compatibility · journal encryption · temporary-file
encryption · `temp_store=MEMORY` · codec-enabled build. **These are not
invented here.** **M3 must not begin DB-encryption implementation until the
exact SQLCipher binding/profile is externally verified.**

### 26.6 DPAPI operational gate (SEC-06)

Windows user-scope DPAPI may fail or become unusable following: a Windows
account change · forced password-reset scenarios · profile corruption ·
profile replacement · machine replacement. The **Recovery Key remains the
recovery mechanism** in every such case. Add this to the operational/recovery
**runbook** requirements. DPAPI is not implemented here.

### 26.7 Recovery Key operational requirement (SEC-08)

The Recovery Key is **not stored** by the application; if lost, it **cannot be
redisplayed**. The eventual product must provide an **authenticated
recovery-key rotation/re-provision flow while the existing key is available**.
This flow is **not implemented** here, and no cryptographic detail beyond the
already-approved design is introduced.

### 26.8 Nonce/key requirements (SEC-07)

Every independent encryption operation must have safe nonce/key uniqueness.
For the preferred per-file-key model: a fresh key per file/object where
required; a fresh nonce per encryption; **never reuse a `(key, nonce)` pair**;
never perform unsafe in-place re-encryption; backup encryption must
independently satisfy nonce uniqueness. **Final wire-format details are not
selected here.**

### 26.9 Packaging / dependency gate (SEC-09, SEC-10)

F7 will necessarily affect the current dependency/layering gate because native
crypto/database dependencies are expected. **Before M1 implementation:** the
dependency architecture must be approved; exact package versions pinned;
Windows native loading verified; PyInstaller behavior verified; OpenSSL/
SQLCipher versions known; licensing/NOTICE obligations reviewed.
**`requirements.txt` is not modified now.**

### 26.10 M1 gate — re-tiered by resolution milestone (SEC → gate)

**Must be resolved BEFORE M1:** SEC-01 (AEAD direction + library availability)
· SEC-04 (KDF clarification) · SEC-05 (SQLCipher raw-key format/salt/profile)
· SEC-09 (dependency/layering direction) · SEC-12 (HKDF construction
confirmation) · SEC-13 (codec/temp/journal verification) · specialist
confirmation of the complete cryptographic design (§24).

**Can be resolved DURING later implementation milestones:** SEC-02 (migration
state machine → before M5) · SEC-07 (implementation-level nonce enforcement →
before M2/M4) · SEC-08 (Recovery Key rotation/re-provision → before the
production/recovery workflow).

**Must be resolved BEFORE production:** SEC-03 (legacy plaintext-backup
handling + residual-plaintext documentation) · SEC-06 (DPAPI operational
runbook) · SEC-10 (licensing/NOTICE).

This re-tiering **augments** the eight §25 prerequisites; it does not relax
any of them.

## 27. Authority Boundaries

Three distinct authorities govern F7, and **none of them, alone, authorizes
M1:**

- **Product Owner decisions** define: scope · architecture direction · risk
  appetite · operational direction.
- **Specialist security review** defines: cryptographic correctness
  requirements · security conditions · required verification. (Repository/
  design review alone does **not** prove cryptographic correctness.)
- **Implementation evidence** defines: whether the chosen libraries/bindings
  actually work in the target Windows deployment (clean-machine, offline,
  PyInstaller, native loading).

M1 becomes eligible only when all three are satisfied for the "before M1"
items (§25 + §26.10) — and then still requires its own separate Product Owner
authorization; it does not begin automatically.

---

**M0 status:** design/documentation complete and internally consistent, with
the M0-review refinements (HIGH-1/2/3), the seven recorded Product Owner
decisions (§22), and the **completed specialist security review (SEC-01…13,
§26)** folded in. No runtime code, dependency, migration, schema, test, or
packaging change. **Product Owner decisions: 7/7 recorded. Specialist security
review: COMPLETE — ACCEPTABLE WITH CONDITIONS (no BLOCKER). M1: NOT
AUTHORIZED** until the §25 + §26.10 "before M1" conditions clear and M1
receives its own authorization.
