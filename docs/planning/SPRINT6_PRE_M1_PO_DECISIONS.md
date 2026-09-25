# Sprint 6 — F7 Pre-M1 Product Owner Decisions (Decision Lock)

**Status:** PRODUCT OWNER DECISIONS RECORDED — **NOT IMPLEMENTATION.**
**Date:** 2026-09-25
**Base:** `main == origin/main == 6722da444d38f51a12d5d6fe5aaeb8967f384d73`
**Companion documents:**
[`SPRINT6_M0_SECURITY_DESIGN.md`](./SPRINT6_M0_SECURITY_DESIGN.md) (M0 design;
Revision 4 applies the N1/N2 corrections recorded here, §28 points here) ·
[`SPRINT6_PRE_M1_EVIDENCE_PLAN.md`](./SPRINT6_PRE_M1_EVIDENCE_PLAN.md) (evidence
IDs E1…E8 referenced below) ·
[`../architecture-decisions/ADR-004-F7-Encryption-at-Rest.md`](../architecture-decisions/ADR-004-F7-Encryption-at-Rest.md)
(unchanged).

> **What this document is.** The authoritative record of the Product Owner's
> pre-M1 decisions D-A…D-H, taken after reviewing the F7 Pre-M1 Product Owner
> Decision Brief (2026-09-25). They are **architecture / product / dependency
> directions and evidence candidates**. They do **not** replace the specialist
> cryptographic review (M0 §24), do **not** replace implementation evidence
> (evidence plan §4), and do **not** authorize M1. No package is installed,
> pinned, or added to `requirements.txt` by this record.
>
> **Three authorities, never mixed (M0 §27):**
> - **PO** — scope, architecture direction, dependency preference, risk appetite.
> - **SPEC** — cryptographic correctness and security construction.
> - **EVID** — whether the chosen packages actually work on the target Windows deployment.

---

## 1. Decision summary

| ID | Decision | Status |
| -- | -------- | ------ |
| D-A | Python **3.14** / Windows **x64** | **APPROVED** |
| D-B | `sqlcipher3` = primary SQLCipher evidence candidate | **APPROVED FOR EVALUATION** |
| D-C | XChaCha20-Poly1305 via PyNaCl/libsodium (candidate) | **APPROVED FOR EVALUATION** |
| D-D | Standard-library RFC 5869 HKDF (`hmac`/`hashlib`) | **APPROVED DIRECTION** |
| D-E | Windows DPAPI via `ctypes` | **APPROVED DIRECTION** |
| D-F | Minimal dependency stack | **APPROVED** |
| D-G | Normal unlock ≈ ≤10 s on the minimum supported clinic PC | **APPROVED TARGET** (product target, not a crypto parameter) |
| D-H / N1 | Strict security gate — SEC-05, SEC-12, SEC-13 before M1 | **APPROVED** (M0 §26 table aligned) |
| D-H / N2 | Correct `cryptography` / XChaCha20-Poly1305 wording | **APPROVED** (M0 §7.1 / §22 corrected) |

**M1 IMPLEMENTATION IS NOT AUTHORIZED.**

---

## 2. Decisions in detail

### D-A — Target runtime: Python 3.14, Windows x64 — APPROVED

- **PO decision:** CPython **3.14**, **Windows x64**. Rationale: longest
  remaining support window among 3.10–3.14 (≈ Oct 2030 per PEP 745); Windows
  x64 is the primary deployment target; the app ships as a packaged Windows
  application, so clinic PCs never install Python.
- **Not assumed:** Python 3.14 + **Flet 0.28.3** compatibility is **not
  proven**. It is an evidence gate.
- **SPEC:** patch status of the bundled interpreter/OpenSSL (`_hashlib`, `_ssl`).
- **EVID:** Flet 0.28.3 on 3.14 (dev + frozen); SQLCipher binding (E1-5/6);
  PyNaCl/cffi (E2-6/7); PyInstaller (E5); native loading (E5-4); clean
  Windows x64 execution (E5-1…E5-13); `hashlib.scrypt` in the frozen build
  (E3-5). Existing `bcrypt` (abi3 wheel) on 3.14 is covered by the same run.

### D-B — SQLCipher binding: `sqlcipher3` primary candidate — APPROVED FOR EVALUATION

- **PO decision:** evaluate and gather evidence for **`sqlcipher3`** (coleifer
  upstream; PyPI metadata lists `cp314-cp314-win_amd64` wheels for 0.6.2) on
  Python 3.14 / Windows x64. **This is not final technical approval.**
  PO Decision 1 (static/prebuilt SQLCipher 4.x + OpenSSL 3.x) is unchanged.
- **No silent substitution:** `sqlcipher3-wheels`, `rotki-pysqlcipher3`,
  other forks, or a source-built SQLCipher are **not** approved. If
  `sqlcipher3` fails a mandatory gate: **STOP and report**; a different
  binding needs a new PO decision, unless SPEC identifies a security-critical
  reason requiring an immediate alternative (which is then still reported to
  the PO).
- **Mandatory verification (EVID → SPEC):** exact SQLCipher version (E1-3);
  exact OpenSSL version (E1-4) and its security/support status (E1-19 —
  desk research indicates the build recipe references OpenSSL 3.6, a non-LTS
  line; to be verified); native linkage and self-containment (E1-7); raw-key
  format (E1-10/11); salt handling (E1-12); PRAGMA configuration (E1-13);
  journal behaviour (E1-14); temp-store behaviour (E1-15); wrong-key and
  corruption detection (E1-16); PyInstaller packaging (E1-21, E5); offline
  installation (E1-22); reproducibility (E1-20); licensing (E1-23, E6 — PyPI
  metadata says MIT; confirm from the wheel's own LICENSE); security
  advisories (E1-19).
- **SPEC:** SEC-05 / SEC-13 (raw-key architecture, codec/journal/temp),
  SQLCipher + OpenSSL version security.

### D-C — AEAD: XChaCha20-Poly1305 via PyNaCl/libsodium — APPROVED FOR EVALUATION

- **PO decision:** retain **XChaCha20-Poly1305** as the preferred F7 AEAD
  direction (PO Decision 2 unchanged). Provider candidate for evidence:
  **PyNaCl / libsodium**. Not implementation authorization.
- **Current understanding (desk research, to be evidenced):** `cryptography`
  (50.0.1) does **not** provide `XChaCha20Poly1305`; PyNaCl provides
  XChaCha20-Poly1305 (`nacl.secret.Aead`,
  `nacl.bindings.crypto_aead_xchacha20poly1305_ietf_*`) and a streaming API
  (`crypto_secretstream_xchacha20poly1305_*`); PyNaCl brings compiled
  dependencies (`cffi`, plus `pycparser`); streaming must be evaluated for
  large attachments/backups (the backup service currently reads the whole
  archive into memory).
- **No silent substitution:** AES-GCM or IETF ChaCha20-Poly1305 must **not**
  replace XChaCha20-Poly1305 merely for packaging convenience. If
  XChaCha20-Poly1305 cannot satisfy the evidence/security gates: **STOP** and
  present the specialist-supported alternative for a **new PO decision**.
- **EVID:** exact PyNaCl version and bundled libsodium version (E2-2);
  Windows x64 / cp314-compatible wheel (E2-6); native dependencies (E2-7);
  PyInstaller packaging (E2-8, E5); offline operation (E2-9); API constants —
  32-byte key, 24-byte nonce, 16-byte tag (E2-3); published test vectors
  (E2-4); tamper/corruption fail-closed (E2-5); large-file memory (E2-12).
- **SPEC:** API correctness; AAD design (E2-11); nonce uniqueness and key
  uniqueness (E2-10, SEC-07); streaming design and truncation detection
  (E2-13); secure failure behaviour.

### D-D — HKDF: standard-library RFC 5869 — APPROVED DIRECTION

- **PO decision:** implement HKDF (when later authorized) as an **RFC 5869**
  construction over the standard library (`hmac`, `hashlib`) — the
  dependency-minimizing direction. **Do not** add `cryptography` merely
  because it provides HKDF, unless a later SPEC/EVID finding shows the
  standard-library approach is unsuitable (then: new PO decision).
- **SPEC (mandatory):** Extract/Expand construction (incl. Expand-only for
  uniform IKM, M0 §4); hash selection; `info` encoding; domain separation
  (`wise-pms/{db,attach,kek-recovery,backup,kek-pass}/v1`, Recovery Key ≠
  KEK_recovery ≠ BACKUP_KEY); output-length handling; test-vector
  correctness; key-material versioning (SEC-04, SEC-12).
- **EVID:** RFC 5869 Appendix A test vectors pass under Python 3.14 (E3-2) and
  inside the frozen exe (E5-6).
- **No implementation is authorized.**

### D-E — Windows DPAPI via `ctypes` — APPROVED DIRECTION

- **PO decision:** Windows **user-scope** DPAPI (PO Decision 4 unchanged)
  through **`ctypes`** calling `crypt32.CryptProtectData` /
  `crypt32.CryptUnprotectData`. **Do not** add `pywin32` for convenience.
- **SPEC (mandatory before implementation):** `DATA_BLOB` structure handling;
  memory ownership and `LocalFree`; `GetLastError` mapping;
  `CRYPTPROTECT_UI_FORBIDDEN`; optional entropy; user-scope semantics;
  wrong-user behaviour; corrupted-profile behaviour; Windows account/profile
  failure behaviour (SEC-06); non-Windows (dev/CI) fallback strategy;
  Recovery-Key fallback.
- **EVID:** evidence plan §4.7 (round-trip; cross-account and cross-machine
  failure; frozen exe).
- **The offline Recovery Key remains mandatory.** DPAPI is a convenience KEK
  path, never the only unwrap path.

### D-F — Dependency policy: minimal stack — APPROVED

- **PO decision:** the smallest practical dependency stack that satisfies the
  approved security architecture. Current intended direction:
  - existing `flet`, existing `bcrypt`;
  - the selected SQLCipher binding (D-B candidate `sqlcipher3`);
  - `PyNaCl` / libsodium for XChaCha20-Poly1305;
  - `cffi` / `pycparser` **only** as required by PyNaCl;
  - standard-library HKDF (D-D);
  - DPAPI through `ctypes` (D-E).
- **Not added** unless evidence or SPEC shows an approved security requirement
  cannot otherwise be met: `cryptography`, `pywin32`, any additional crypto
  library. Any additional runtime dependency requires explicit documentation
  and PO approval.
- **Rationale:** minimal dependency surface, minimal native-library
  duplication (e.g. avoiding a second bundled OpenSSL from `cryptography`),
  easier packaging, easier security review. This is a preference, not a
  permanent prohibition.
- **Not changed now:** `requirements.txt`, `tests/test_layering.py` (the
  `{flet, bcrypt}` dependency gate and import allow-lists), `.gitignore`
  (`*.spec`). These change **intentionally** only at the authorized
  implementation milestone (evidence plan E4-4/E4-5, R12).
- **SPEC:** supply-chain and native-library risk (SEC-09). **EVID:** E4-2
  (transitive tree + hashes), E4-7 (native inventory / duplicate OpenSSL).

### D-G — Unlock time / hardware — APPROVED TARGET

- **PO product target:** **normal unlock should be approximately ≤10 seconds
  on the minimum supported clinic PC.** This is a product target, **not** a
  cryptographic parameter.
- **Not set here:** scrypt `N`, `r`, `p`; memory ceiling; CPU requirement;
  any unlock-time guarantee. The minimum supported clinic PC profile is
  captured through the E8 manifest.
- **SPEC:** translate the target into secure scrypt parameters after
  reviewing the threat model, balancing clinic startup time, resistance to
  offline passphrase guessing, RAM use, CPU use, and avoiding system paging.
- **EVID:** benchmark the final candidate parameters on the actual minimum
  hardware profile, dev and frozen (E3-6, E8).
- **Scope:** scrypt applies only to human-entered passphrases. The Recovery
  Key path remains **HKDF-based** and must not use scrypt merely for symmetry.

### D-H / N1 — Strict gate for SEC-05, SEC-12, SEC-13 — APPROVED

- **PO decision:** adopt the **strict** interpretation. Before M1:
  - SQLCipher binding / raw-key verification (SEC-05) is an M1 prerequisite;
  - HKDF construction / domain-separation verification (SEC-12) is an M1
    prerequisite;
  - SQLCipher codec / temp / journal verification (SEC-13) is an M1
    prerequisite.
- **Documentation effect:** the M0 §26 findings table is aligned to §26.10
  ("Blocks M1?" = **Yes** for all three; SEC-05/SEC-13 milestone column reads
  "Before M1 (verification evidence); enforced in M3 implementation"). **§25
  and §26.10 are not amended and not weakened.**

### D-H / N2 — `cryptography` / XChaCha20-Poly1305 wording — APPROVED

- **PO decision:** `cryptography` must **not** be described as providing
  XChaCha20-Poly1305.
- **Documentation effect (M0 Revision 4):** §7.1 now states that
  `cryptography` provides `ChaCha20Poly1305` but **not** XChaCha20-Poly1305;
  XChaCha20-Poly1305 is currently evaluated through PyNaCl/libsodium; the
  exact provider/API/version remain subject to evidence validation. §7.1's
  PyInstaller row and §22 Decision 2's evidence column are corrected
  accordingly. Documentation only; no provider is implemented.

---

## 3. Still requires specialist review (SPEC) — all OPEN

| Gate | Scope | Source |
| ---- | ----- | ------ |
| S-1 Cryptographic construction (overall) | Full M0 §24 checklist sign-off | M0 §24, E7-15 |
| S-2 SQLCipher raw-key architecture | Raw-key format, salt, HMAC-key derivation, PRAGMA profile | SEC-05, E7-7 |
| S-3 SQLCipher codec / journal / temp | Codec-enabled build, journal + temp encryption, `temp_store` | SEC-13, E7-7 |
| S-4 SQLCipher / OpenSSL security | Bundled versions, support status, advisories | E1-19, E7-14 |
| S-5 AEAD API / model | XChaCha20-Poly1305 via PyNaCl: API correctness, fail-closed | SEC-01, E7-1 |
| S-6 Nonce / key / AAD rules | Nonce and key uniqueness; AAD fields; wrapped-DEK AAD | SEC-07, E7-2, E7-3, E7-6 |
| S-7 Streaming design | Whole-file vs. chunked; truncation/reordering resistance | E2-13 |
| S-8 HKDF implementation | Stdlib RFC 5869 construction, hash, `info` encoding, output length, versioning | SEC-04, SEC-12, E7-4 |
| S-9 Domain separation | Label set; Recovery Key ≠ KEK_recovery ≠ BACKUP_KEY | M0 §5.2/§23/§26.1, E7-5 |
| S-10 Passphrase KDF parameters | scrypt parameters from the D-G target + threat model | D-G, E3-9 |
| S-11 DPAPI memory / API handling | `DATA_BLOB`, `LocalFree`, `GetLastError`, flags, entropy, failure modes, fallback | D-E, SEC-06, E7-8 |
| S-12 Recovery-Key lifecycle | Entropy, encoding, checksum, non-persistence, rotation / re-provisioning | M0 §10, SEC-08, E7-9 |
| S-13 Migration security | Ordering, encrypted pre-migration backup, combined-state marker (before M5) | SEC-02, E7-10 |
| S-14 Plaintext exposure | Decrypt-to-temp, pagefile/hibernation, legacy plaintext backups (before production) | SEC-03, E7-11 |
| S-15 Key lifetime | Python zeroization limits; `cipher_memory_security` | SEC-11, E7-12 |
| S-16 Backup recovery | BACKUP_KEY derivation; restore on a new machine without DPAPI | E7-13 |

## 4. Still requires implementation evidence (EVID) — all PENDING

| Gate | Evidence plan items |
| ---- | ------------------- |
| V-1 Windows x64 wheels for Python 3.14 (`sqlcipher3`, PyNaCl, `cffi`, `bcrypt`) | E1-5/6, E2-6, E4-2 |
| V-2 Python 3.14 compatibility incl. **Flet 0.28.3** | D-A, E5-3 |
| V-3 SQLCipher runtime profile (version, provider, raw key, salt, PRAGMAs, journal, temp, wrong key, corruption) | E1-3…E1-18 |
| V-4 Native library linkage / self-containment / duplicate-OpenSSL check | E1-7, E2-7, E4-7 |
| V-5 Clean-machine packaging (frozen exe on clean Windows x64) | E5-1…E5-13 |
| V-6 PyInstaller loading of all native components | E1-21, E2-8, E5-4 |
| V-7 Offline installation and offline runtime (incl. no Flet client download) | E1-22, E2-9, E5-2, E5-8, E5-13 |
| V-8 Cryptographic test vectors (XChaCha20-Poly1305, RFC 5869 HKDF) | E2-4, E3-2, E5-6 |
| V-9 DPAPI behaviour via `ctypes` | Evidence plan §4.7 |
| V-10 Performance (scrypt vs. ≤10 s target; SQLCipher overhead) | E3-6, E8 |
| V-11 Memory (scrypt peak RSS; AEAD large inputs) | E2-12, E3-6 |
| V-12 Large-file behaviour (one-shot vs. stream API) | E2-12, E2-13 |
| V-13 Backup / restore behaviour (later milestones; not a pre-M1 gate) | M4 test matrix (M0 §16) |
| V-14 Reproducibility (pins + hashes + repeated builds) | E1-20, E5-12 |
| V-15 Licensing inventory (SQLCipher, OpenSSL, `sqlcipher3`, PyNaCl, libsodium, `cffi`, `pycparser`, PyInstaller, CPython) | E6 |
| V-16 Hardware / environment manifests | E8 |

## 5. Stop conditions (carry into evidence gathering)

1. `sqlcipher3` fails any mandatory gate → **STOP, report**; no fork/substitute without a new PO decision.
2. XChaCha20-Poly1305 via PyNaCl fails any gate → **STOP**; specialist-supported alternative presented for a new PO decision.
3. Stdlib HKDF found unsuitable by SPEC/EVID → **STOP**; new PO decision before adding `cryptography`.
4. Any additional runtime dependency needed → documented + PO approval first.
5. Flet 0.28.3 fails on Python 3.14 → **STOP, report**; D-A or the Flet pin needs a new PO decision.

## 6. Sequence (unchanged)

```text
PO Decisions (this record)
      ↓
Pre-M1 Evidence & Validation (separately authorized)
      ↓
Specialist Verification
      ↓
Product Owner Review
      ↓
Explicit M1 Authorization
      ↓
M1 Implementation
```

**M1 IMPLEMENTATION IS NOT AUTHORIZED.** This record authorizes directions
and evidence candidates only.
