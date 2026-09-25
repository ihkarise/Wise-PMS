# Sprint 6 — F7 Pre-M1 Evidence & Validation Plan

**Status:** PRE-M1 EVIDENCE / PLANNING — NOT IMPLEMENTATION.
**Date:** 2026-09-25
**Base:** `main == origin/main == 6722da444d38f51a12d5d6fe5aaeb8967f384d73`
(PR #18 merged; M0 + specialist review complete).
**Authority:** subordinate to
[`SPRINT6_M0_SECURITY_DESIGN.md`](./SPRINT6_M0_SECURITY_DESIGN.md) (§22 PO
decisions, §24 specialist gate, §25 M1 prerequisites, §26 SEC-01…13, §27
authority boundaries) and
[`../architecture-decisions/ADR-004-F7-Encryption-at-Rest.md`](../architecture-decisions/ADR-004-F7-Encryption-at-Rest.md).
This document changes none of them.

> **Scope contract.** This plan defines *what evidence must exist* before M1
> can even be considered for authorization, *how* it is gathered, and *which
> gate* judges it. It installs nothing, pins nothing, selects no package, fixes
> no cryptographic parameter, and changes no runtime code, dependency, schema,
> test, or packaging file. **Every gate below starts PENDING. M1 REMAINS NOT
> AUTHORIZED.**

> **Desk observations vs. evidence.** §2.2 records read-only public-metadata
> observations (PyPI JSON / upstream source read on 2026-09-25, nothing
> installed). They are **leads that shape the evidence plan**, not evidence:
> none of them moves any gate to PASS. Only the controlled procedures in §4
> produce evidence.

---

## 1. Sequence (not skippable)

```text
Evidence Plan (this document)
      ↓
Evidence Gathering (isolated, recorded — §4)
      ↓
Specialist Verification (§3 E7 / M0 §24)
      ↓
Product Owner Review (§7)
      ↓
Explicit M1 Authorization (separate PO act)
      ↓
M1 Implementation
```

---

## 2. Repository facts relevant to evidence

### 2.1 Verified in the repository (2026-09-25, at `6722da4`)

| # | Fact | Location | Evidence consequence |
| - | ---- | -------- | -------------------- |
| R1 | `requirements.txt` = `flet==0.28.3`, `bcrypt>=4.0`; `requirements-dev.txt` adds `pytest>=7.0` only | root | No crypto dependency present — consistent with "not started" |
| R2 | `test_no_new_runtime_dependency_added` asserts the package set is exactly `{flet, bcrypt}` | `tests/test_layering.py` | Any F7 dependency is an **intentional gate change** needing prior approval (E4) |
| R3 | `sqlite3` import allow-list = `sqlite_adapter.py`, `migrations/runner.py`, `migrations/__init__.py` | `tests/test_layering.py` | A SQLCipher binding import needs an allow-list decision (E4) |
| R4 | `SQLiteAdapter.connect()` = `sqlite3.connect(DB_PATH)` + `row_factory = sqlite3.Row` + `PRAGMA foreign_keys = ON`; sole DB-open site | `app/core/db_adapters/sqlite_adapter.py` | Binding must provide a `Row`-equivalent row factory and identical PRAGMA behavior (E1) |
| R5 | Migration runner/entry take `sqlite3.Connection` (type hints) and run `executescript` | `app/core/migrations/runner.py`, `__init__.py` | Binding must support `executescript` + transaction semantics identical to stdlib (E1) |
| R6 | Tests catch **`sqlite3.IntegrityError`** raised through adapter connections and assert `isinstance(conn, sqlite3.Connection)` / `row_factory is sqlite3.Row` | `tests/test_consultation_domain.py:91-101`, `tests/test_db_adapter.py:24-37` | A binding's exception/Connection/Row classes are generally **not** stdlib subclasses → exception-hierarchy compatibility is an explicit evidence item (E1-17); these tests would change intentionally at M3, not before |
| R7 | `bootstrap.run()` = `init_db()` → `ft.app(...)`; `init_db()` = `ensure_folders()` → `migrate()` → seed; **no unlock stage** | `app/bootstrap.py`, `app/core/database.py` | Unlock-before-migrate ordering remains M3/M6 work; no evidence needed pre-M1 beyond the binding opening a keyed DB before DDL |
| R8 | `StorageProvider` byte contract `save/open/delete/url_for`; `local_path()` only on `LocalDiskStorageProvider` | `app/core/storage/*` | Attachment AEAD sits behind the seam (M2); pre-M1 evidence is library/API only |
| R9 | Backup builds a zip on disk, then **reads the whole archive into memory** (`fh.read()`) before `get_storage().save()` | `app/modules/backup/service.py` | Whole-file vs. streamed AEAD and memory ceiling must be measured (E2-10/11, E3/E8) |
| R10 | Python requirement stated only as "3.10+"; no `python_requires`, no pinned interpreter | `README.md`, `docs/DEPLOYMENT.md` | Native wheels are per-CPython-ABI → the **target Python version + architecture must be fixed by the PO** before binding evidence is meaningful (§7 D-A) |
| R11 | Packaging = ad-hoc `pip install pyinstaller` (unpinned) + `pyinstaller --noconfirm --windowed --name WisePMS main.py`; **no `.spec`** | `docs/DEPLOYMENT.md` | PyInstaller version must be pinned for evidence reproducibility (E5) |
| R12 | **`.gitignore` contains `*.spec`** | `.gitignore` | The PO-approved committed `.spec` (decision 7, M3/M7) will be **silently ignored by git** unless a negation (e.g. `!WisePMS.spec`) is added at that milestone — recorded now so it is not missed; **not changed here** |
| R13 | `.gitignore` already excludes `*.db`, `*.db-journal`, `*.db-wal`, `*.db-shm`, `/data/*`, `/backups/*`, `/attachments/*` | `.gitignore` | Evidence harness artifacts (test DBs) must live outside the repo tree anyway (§4.0) |
| R14 | No CI workflow directory (`.github/` absent) | root | Gates run locally; evidence must be captured manually and attached (§4.0) |
| R15 | `flet==0.28.3` is installed **without** the `desktop` extra; in flet 0.28.3 the Windows desktop client ships in the separate `flet-desktop==0.28.3` package (`requires_dist`: `flet-desktop; platform_system=="Windows" and extra=="desktop"`) | `requirements.txt`, PyPI metadata | The offline clean-machine test must prove the frozen app **does not fetch the Flet client at runtime** (E5-8). Pre-existing, not F7-specific, but it can invalidate an "offline" F7 evidence run |
| R16 | Backups are currently plaintext `backup_YYYY_MM_DD.zip`; restore code does not exist | `docs/DEPLOYMENT.md`, backup service | SEC-03 legacy-backup handling remains a before-production item; not a pre-M1 evidence item |

### 2.2 Desk observations (public metadata, read-only, 2026-09-25) — NOT evidence

| # | Observation | Source | Consequence for the plan |
| - | ----------- | ------ | ------------------------ |
| O1 | `sqlcipher3-binary` 0.6.0 publishes **manylinux x86_64 wheels only — no Windows wheel**; its PyPI summary still reads "SQLCipher 3.x" | PyPI JSON | Named as an M0 §6.1 candidate, it appears to **fail criterion 2 (Windows prebuilt wheel)**. Must be confirmed or eliminated formally in E1 |
| O2 | `sqlcipher3` 0.6.2 (coleifer, MIT per metadata) publishes `win32` / `win_amd64` / `win_arm64` wheels for cp310–cp312+; its `setup.py` links `libcrypto` (OpenSSL via Conan) on Windows | PyPI JSON, upstream `setup.py` | A plausible **additional candidate**; whether OpenSSL is statically linked into the `.pyd` or shipped as a DLL, and which SQLCipher/OpenSSL versions are embedded, is **unknown → E1-3/4/7** |
| O3 | `rotki-pysqlcipher3` latest (2026.8.3) ships Windows wheels **only for cp314/cp314t** (`requires_python >=3.14,<3.15`); last cp311/cp312 Windows wheels are from 2024.10.1 | PyPI JSON | Candidate viability depends on the **target Python version** (D-A). An older build implies older bundled SQLCipher/OpenSSL → advisory review (E1-19) |
| O4 | `pyca/cryptography` (latest 50.0.1) AEAD module on `main` exports `AESCCM, AESGCM, AESGCMSIV, AESOCB3, AESSIV, ChaCha20Poly1305` — **no `XChaCha20Poly1305`** | upstream `src/cryptography/hazmat/primitives/ciphers/aead.py` | **Materially confirms SEC-01.** M0 §7.1's table cell "`cryptography` (`XChaCha20Poly1305`)" appears inaccurate; flagged for specialist/PO attention (§7 D-C), **not edited here** |
| O5 | `PyNaCl` 1.6.2 (Apache-2.0, bundles libsodium) exposes `crypto_aead_xchacha20poly1305_ietf_{encrypt,decrypt}` and `crypto_secretstream_xchacha20poly1305_*` in `nacl.bindings`; Windows `win32/win_amd64/win_arm64` abi3 wheels | PyPI JSON, upstream `nacl/bindings` | The most direct XChaCha20-Poly1305 path; would be a **new native dependency** (SEC-09). Does **not** provide HKDF (§3 E3/E4) |
| O6 | PyInstaller latest 6.22.3 (GPLv2+ with bootloader exception) | PyPI JSON | Pin a version for evidence; licensing exception must be confirmed (E6) |

---

## 3. Evidence matrix

Column legend — **Source:** where the evidence comes from. **Method:** how it
is produced (procedures in §4). **Gate:** who judges it (PO = Product Owner,
SPEC = specialist security reviewer, IMPL-EV = implementation evidence per M0
§27, LEGAL = licensing reviewer). **Status:** all **PENDING**. **Blocks M1:**
per M0 §25/§26.10 (conservative reading, see §5 note N1).

### E1 — SQLCipher binding

| ID | Evidence item | Source | Verification method | Gate | Status | Blocks M1? |
| -- | ------------- | ------ | ------------------- | ---- | ------ | :--------: |
| E1-1 | Candidate package shortlist (≥2, incl. elimination rationale for `sqlcipher3-binary` per O1) | PyPI/upstream metadata | Desk review recorded in evidence log | PO + SPEC | PENDING | YES |
| E1-2 | Exact package version + wheel filename + SHA-256 | PyPI `pip download --no-deps` into quarantine dir | `pip download` + `certutil -hashfile`/`sha256sum` (§4.1) | IMPL-EV | PENDING | YES |
| E1-3 | Embedded SQLCipher version | runtime | `PRAGMA cipher_version;` (§4.2) | IMPL-EV → SPEC | PENDING | YES |
| E1-4 | Embedded crypto provider + OpenSSL version (PO decision 1 requires OpenSSL 3.x) | runtime | `PRAGMA cipher_provider;` `PRAGMA cipher_provider_version;` (§4.2) | IMPL-EV → SPEC | PENDING | YES |
| E1-5 | Python compatibility — wheel ABI tag matches the PO-fixed target CPython (D-A) | wheel filename / `WHEEL` metadata | Inspect tag; import under the target interpreter | IMPL-EV | PENDING | YES |
| E1-6 | Windows architecture — wheel platform tag matches target (`win_amd64` expected; confirm per E8) | wheel filename | Tag inspection + import on target arch | IMPL-EV | PENDING | YES |
| E1-7 | Static/prebuilt: no host SQLCipher/OpenSSL required; enumerate every DLL the `.pyd` imports | wheel contents + PE imports | `dumpbin /dependents` (or `pefile`-based listing on an analysis box) of each `.pyd`/`.dll` in the wheel; confirm only OS DLLs + bundled files (§4.3) | IMPL-EV | PENDING | YES |
| E1-8 | Codec-enabled build (not plain SQLite): keyed file is unreadable without key | runtime | Create keyed DB; open with stdlib `sqlite3` → must fail "file is not a database"; hex-dump header shows no `SQLite format 3` magic (§4.2) | IMPL-EV → SPEC | PENDING | YES (SEC-13) |
| E1-9 | DB-API 2.0 parity used by Wise PMS: `connect`, `execute`, `executescript`, `commit`, `rollback`, `close`, `Row` factory with name access, `lastrowid`, parameter style `?` | runtime | Scripted parity checks mirroring R4/R5 usage (§4.2) | IMPL-EV | PENDING | YES |
| E1-10 | Raw-key support: `PRAGMA key = "x'<64 hex>'"` accepted, bypasses PBKDF2 | runtime + SQLCipher docs | Open with raw key; time open (≈ no KDF delay) vs. passphrase key; confirm documented semantics (§4.2) | SPEC | PENDING | YES (SEC-05) |
| E1-11 | Raw-key **format** — 64-hex (key only) vs. 96-hex (key + explicit salt) behavior for the exact version | SQLCipher docs for that version + runtime | Document both forms' behavior; SPEC decides which is used | SPEC | PENDING | YES (SEC-05) |
| E1-12 | Salt behavior — per-file random 16-byte salt in page 1 when raw key without salt; HMAC-key derivation from raw key | SQLCipher docs + runtime | Create two DBs with same raw key → first 16 bytes differ; record `cipher_kdf_iter`/`cipher_hmac_*` settings | SPEC | PENDING | YES (SEC-05) |
| E1-13 | PRAGMA profile: `cipher_compatibility`/defaults = SQLCipher 4 (AES-256-CBC, HMAC-SHA512, page 4096, KDF iter 256000 for passphrase path); `foreign_keys=ON` honored after keying; `cipher_memory_security` availability | runtime | Query each `PRAGMA cipher_*` and `PRAGMA foreign_keys` after key; record values (§4.2) | SPEC | PENDING | YES (SEC-05) |
| E1-14 | Rollback-journal encryption (PO decision 5) | runtime | `journal_mode=DELETE`; open a write transaction, copy `*-journal` mid-transaction, scan for known plaintext marker (§4.2) | IMPL-EV → SPEC | PENDING | YES (SEC-13) |
| E1-15 | Temp-file behavior: compile-time `SQLITE_TEMP_STORE` and runtime `PRAGMA temp_store=MEMORY` honored | runtime | `PRAGMA compile_options;` (look for `TEMP_STORE=`); set `temp_store=2`, run large `ORDER BY`/temp index; Process Monitor/`handle` confirms no `etilqs_*` temp file (§4.2) | IMPL-EV → SPEC | PENDING | YES (SEC-13) |
| E1-16 | Wrong-key / corrupt-page behavior: raises on first statement; per-page HMAC failure raises | runtime | Wrong raw key → error; flip one byte in page 2 → HMAC error on read | IMPL-EV | PENDING | YES |
| E1-17 | Exception-hierarchy + `Row`/`Connection` class identity vs. stdlib (R6) | runtime | Check `issubclass(binding.IntegrityError, sqlite3.IntegrityError)` etc.; record result for the M3 intentional test change | IMPL-EV | PENDING | YES (informs E4) |
| E1-18 | Migration primitive `sqlcipher_export()` and `ATTACH … KEY` available (M0 §6 / §11) | runtime | Plain→encrypted export of a copy of a fixture DB; row-count parity | IMPL-EV | PENDING | YES |
| E1-19 | Security/maintenance: release cadence, open advisories for bundled SQLCipher + OpenSSL versions | upstream repos, CVE/OSV, OpenSSL advisories | Desk review; list CVEs affecting embedded versions | SPEC | PENDING | YES |
| E1-20 | Reproducibility: same version + hash re-downloaded yields identical wheel; build provenance known | PyPI hashes, upstream CI | Compare hashes across two downloads; record upstream build workflow | IMPL-EV | PENDING | YES |
| E1-21 | PyInstaller compatibility (frozen load) | E5 procedure | See E5 | IMPL-EV | PENDING | YES |
| E1-22 | Offline installation from local wheelhouse | E5 procedure | `pip install --no-index --find-links` on offline box | IMPL-EV | PENDING | YES |
| E1-23 | Licensing (binding + SQLCipher Community BSD-style + OpenSSL Apache-2.0) | E6 | See E6 | LEGAL | PENDING | YES |

### E2 — AEAD (XChaCha20-Poly1305 — PO preferred direction, not yet implementation-approved)

No alternative is selected. If E2-1…E2-5 cannot be satisfied within the
approved dependency/packaging constraints, a **formally reviewed alternative**
must be proposed to SPEC and decided by the PO (M0 §26.2). Silent substitution
of AES-GCM or IETF ChaCha20-Poly1305 is prohibited.

| ID | Evidence item | Source | Verification method | Gate | Status | Blocks M1? |
| -- | ------------- | ------ | ------------------- | ---- | ------ | :--------: |
| E2-1 | Package providing XChaCha20-Poly1305 (desk leads: PyNaCl `nacl.bindings` per O5; `cryptography` **lacks** it per O4 — confirm against the exact version considered) | upstream source + docs for the pinned version | Record module/function names from the pinned wheel's source (§4.4) | SPEC + PO | PENDING | YES (SEC-01) |
| E2-2 | Exact version + wheel hash + bundled libsodium (or other) version | wheel + runtime | `pip download`; runtime `nacl.bindings.sodium_version_*` or equivalent (§4.4) | IMPL-EV | PENDING | YES |
| E2-3 | API availability: encrypt/decrypt signatures, key 32 B, nonce 24 B, tag 16 B, AAD parameter present | runtime | Constant checks (`KEYBYTES`, `NPUBBYTES`, `ABYTES`) + round-trip (§4.4) | IMPL-EV → SPEC | PENDING | YES |
| E2-4 | Known-answer test against a published XChaCha20-Poly1305 test vector (draft-irtf-cfrg-xchacha / libsodium vectors) | public vectors | Run KAT; byte-exact ciphertext+tag | SPEC | PENDING | YES |
| E2-5 | Tag verification fails closed (tampered ciphertext, tampered AAD, truncated tag, wrong key) | runtime | Negative tests (§4.4) | IMPL-EV → SPEC | PENDING | YES |
| E2-6 | Windows support: wheel for target ABI/arch | wheel tag | As E1-5/E1-6 | IMPL-EV | PENDING | YES |
| E2-7 | Native dependencies enumerated (e.g. bundled `libsodium`, `_cffi_backend`) | wheel contents + PE imports | As E1-7 | IMPL-EV | PENDING | YES |
| E2-8 | PyInstaller support (hooks exist / frozen import works) | E5 | See E5 | IMPL-EV | PENDING | YES |
| E2-9 | Offline availability (wheelhouse install, no build step, no network at import) | E5 | See E5 | IMPL-EV | PENDING | YES |
| E2-10 | Nonce model: 192-bit random per encryption from OS CSPRNG; never reuse `(key, nonce)`; per-file key model (SEC-07) | design + SPEC | SPEC ratifies model; M2/M4 enforce | SPEC | PENDING | YES (model) / enforcement before M2/M4 |
| E2-11 | AAD model: fields bound (format version, alg id, logical id; wrapped-DEK header per M0 §5.1) | design + SPEC | SPEC ratifies field list; wire format not selected here | SPEC | PENDING | YES |
| E2-12 | Large-file handling: `MESSAGEBYTES_MAX`, peak memory for one-shot encrypt of largest expected attachment and full backup (R9) | runtime + E8 data profile | Measure peak RSS for 10 MB / 100 MB / 1 GB synthetic inputs (§4.4) | IMPL-EV → SPEC | PENDING | YES (informs streaming decision) |
| E2-13 | Streaming/chunking implications: one-shot AEAD vs. a chunked construction (e.g. libsodium `secretstream` if available) — truncation/reordering resistance, nonce per chunk, final-chunk marker | design + SPEC | SPEC decides whole-file vs. chunked and the construction; not selected here | SPEC + PO | PENDING | YES |

### E3 — KDF (plan only; no parameters selected)

**Separation is mandatory (SEC-04 / M0 §26.1):**

```text
Recovery Key (≥128-bit CSPRNG)
   ├─ HKDF, info "wise-pms/kek-recovery/v1" ─→ KEK_recovery
   └─ HKDF, info "wise-pms/backup/v1"       ─→ BACKUP_KEY
Recovery Key ≠ KEK_recovery ≠ BACKUP_KEY          (no memory-hard KDF here)

Human passphrase (low entropy) ─ memory-hard KDF (scrypt preferred) ─→ KEK_pass
```

| ID | Evidence item | Source | Method | Gate | Status | Blocks M1? |
| -- | ------------- | ------ | ------ | ---- | ------ | :--------: |
| E3-1 | HKDF implementation source: a vetted library class (e.g. `cryptography` HKDF) **or** an RFC 5869 construction over stdlib `hmac` — the choice changes the dependency set (O5: PyNaCl has no HKDF) | design | SPEC chooses; PO approves dependency impact (E4) | SPEC + PO | PENDING | YES (SEC-12) |
| E3-2 | HKDF KATs: RFC 5869 Appendix A test cases 1–3 pass on the chosen implementation | RFC 5869 | Run vectors under target interpreter (§4.5) | IMPL-EV → SPEC | PENDING | YES |
| E3-3 | HKDF construction confirmed: Extract vs. Expand-only for uniform IKM, salt handling, `info` label set and encoding (UTF-8, no ambiguity), output length | SPEC | Written specialist confirmation | SPEC | PENDING | YES (SEC-04/12) |
| E3-4 | Recovery Key HKDF cost is negligible (sanity only, no tuning) | runtime | Time 1 000 derivations on target HW | IMPL-EV | PENDING | NO (informational) |
| E3-5 | scrypt availability in the **frozen** app: `hashlib.scrypt` exists in the target CPython build (OpenSSL-backed) and in the PyInstaller bundle; max memory argument (`maxmem`) behavior | runtime | `hasattr(hashlib, "scrypt")`, run once in dev and frozen builds (§4.5) | IMPL-EV | PENDING | YES |
| E3-6 | scrypt benchmark on representative clinic hardware (§4.5 protocol) | E8 hardware | Parameter grid, repeated runs, latency + peak memory + CPU | IMPL-EV → SPEC | PENDING | YES |
| E3-7 | UX threshold: acceptable unlock latency (proposed to PO as a measurable budget, e.g. "≤ N s on the slowest supported machine") | PO | PO sets budget; benchmark must meet it | PO | PENDING | YES |
| E3-8 | Parameter versioning: params stored in the record header (`kdf_id`, N/r/p, salt) so future re-tuning is possible | design | SPEC ratifies header fields | SPEC | PENDING | YES |
| E3-9 | Final parameter selection | SPEC after E3-6/E3-7 | Written selection with benchmark reference | SPEC + PO | PENDING | YES |

**Benchmark protocol requirements (E3-6):**
- Run on **every** machine class in E8 (at minimum: the actual clinic PC or
  an identical model, plus the slowest machine the PO wants supported).
- Mains power, "Balanced"/default power plan recorded, app and AV state
  recorded, no other heavy workload; one warm-up run discarded.
- Grid: candidate `(N, r, p)` values chosen by SPEC (not here); for each, ≥10
  runs; report min/median/p95 wall-clock latency, peak process RSS (working
  set), and CPU time.
- Measure both dev interpreter and **frozen `WisePMS.exe`** (latency can
  differ).
- Record memory headroom: available physical RAM before run; confirm no
  paging during run (Performance Monitor "Pages/sec").
- Output: CSV + environment manifest (E8), hash of the script used, stored
  under the evidence log (§4.0). Repeatability: rerun on a different day;
  medians within ±10 % or explained.

### E4 — Dependency / layering

| ID | Evidence item | Source | Method | Gate | Status | Blocks M1? |
| -- | ------------- | ------ | ------ | ---- | ------ | :--------: |
| E4-1 | Proposed runtime dependency set — likely: **(a)** one SQLCipher binding; **(b)** an XChaCha20-Poly1305 provider (PyNaCl is the desk lead); **(c)** possibly `cryptography` for HKDF (or none, if SPEC accepts stdlib-`hmac` HKDF); **(d)** DPAPI access via `ctypes`→`crypt32.dll` (no dependency) **or** `pywin32` (dependency) | E1/E2/E3/E6 | Dependency proposal with per-package justification + transitive deps (`pip download` tree, e.g. PyNaCl → `cffi` → `pycparser`) | PO + SPEC | PENDING | YES (SEC-09) |
| E4-2 | Transitive dependency tree + hashes (for `--require-hashes`) | wheelhouse | `pip download -r candidates.txt`; record every wheel + SHA-256 | IMPL-EV | PENDING | YES |
| E4-3 | Placement of crypto code: `app/core/crypto/` (primitives) and `app/core/keys/` (envelope, DPAPI, Recovery Key) per SPRINT6_TECHNICAL_PLAN §23; only those modules may import the crypto packages | design | PO/SPEC approve module boundary | PO | PENDING | YES |
| E4-4 | Layering-gate impact (intentional, pre-approved): `test_no_new_runtime_dependency_added` set changes; new import allow-list for the binding (in `sqlite_adapter.py`) and crypto packages (in `app/core/crypto`/`keys` only); decision whether `migrations/*` keep stdlib `sqlite3` type hints | `tests/test_layering.py` | Written gate-change proposal (text only — **no test edit now**) | PO | PENDING | YES |
| E4-5 | Existing-test impact list (R6: `sqlite3.IntegrityError` catch, `isinstance(..., sqlite3.Connection)`, `row_factory is sqlite3.Row`; in-memory `sqlite3.connect(":memory:")` migration tests) | tests | Enumerate; classify as intentional M3 change | PO | PENDING | YES |
| E4-6 | Out-of-scope-technology gate unaffected (no ORM/cloud SDK introduced) | `tests/test_layering.py` | Confirm candidate list has none | IMPL-EV | PENDING | NO |
| E4-7 | Native-binary inventory across all candidates, and **duplicate-OpenSSL risk**: CPython's own `libcrypto-3*.dll` (for `_hashlib`/`_ssl`) vs. a SQLCipher binding that links OpenSSL dynamically vs. `cryptography`'s statically linked OpenSSL | E1-7/E2-7 | PE-import listing; check DLL name collisions in one flat bundle | IMPL-EV → SPEC | PENDING | YES |
| E4-8 | Maintenance/supply-chain evidence per package (maintainers, release cadence, signed releases/attestations if published) | upstream | Desk review | SPEC | PENDING | YES |

### E5 — Windows / PyInstaller clean-machine evidence

Target configuration: **Clean Windows + offline + frozen `WisePMS.exe` +
SQLCipher native libs + OpenSSL + AEAD library.** The `.spec` is **not**
created by this plan (PO decision 7: M3/M7). The evidence build is a
throwaway **spike build outside the repository** (§4.6); its spec, if any,
is never committed.

| ID | Evidence item | Method | Gate | Status | Blocks M1? |
| -- | ------------- | ------ | ---- | ------ | :--------: |
| E5-1 | Clean target: fresh Windows VM/PC with **no Python, no VC build tools, no dev tooling**; snapshot hash/ID recorded | Environment manifest (E8) | IMPL-EV | PENDING | YES |
| E5-2 | Offline: network adapter disabled (not merely unplugged proxy); verified by failing `Test-NetConnection` | Screenshot/log | IMPL-EV | PENDING | YES |
| E5-3 | Executable starts and reaches login screen | Launch log + screenshot | IMPL-EV | PENDING | YES |
| E5-4 | Native libraries load **from the bundle** (not from System32 or PATH) | Process Monitor `Load Image` capture or `ListDLLs`; paths must be inside `dist\WisePMS\` | IMPL-EV | PENDING | YES |
| E5-5 | Encrypted DB created + reopened with raw key; wrong key fails; `PRAGMA cipher_version/provider_version` logged from frozen app | Spike-harness self-test mode run inside the frozen exe | IMPL-EV | PENDING | YES |
| E5-6 | Crypto APIs load: AEAD round-trip + KAT, HKDF KAT, `hashlib.scrypt` single run — all inside the frozen exe | Spike self-test | IMPL-EV | PENDING | YES |
| E5-7 | No development Python required: `where python` fails on target; exe runs from a non-dev user account | Log | IMPL-EV | PENDING | YES |
| E5-8 | No internet required — including **Flet desktop client** (R15): no runtime download attempt; confirm with firewall log / Process Monitor network events | Log | IMPL-EV | PENDING | YES |
| E5-9 | Architecture match: `python -c "import platform,struct;print(platform.machine(),struct.calcsize('P')*8)"` on build box equals target; exe PE header machine type = target | `dumpbin /headers` or `sigcheck` | IMPL-EV | PENDING | YES |
| E5-10 | VC++ runtime dependency: whether bundled `vcruntime140*.dll` suffice on a clean box, or a VC++ Redistributable is required | PE imports + clean run | IMPL-EV | PENDING | YES |
| E5-11 | AV/SmartScreen behavior on unsigned exe with native crypto DLLs (Defender quarantine/false positive) | Clean run with Defender on; record events | IMPL-EV | PENDING | NO (record; affects deployment) |
| E5-12 | Reproducibility: pinned PyInstaller version, pinned wheelhouse with hashes, two builds from the same inputs produce the same file list and same DLL hashes | Diff of file manifests | IMPL-EV | PENDING | YES |
| E5-13 | Build is itself offline-capable from the wheelhouse (`--no-index --find-links`) | Build log | IMPL-EV | PENDING | YES |

### E6 — Licensing

| ID | Component | Checks | Gate | Status | Blocks M1? |
| -- | --------- | ------ | ---- | ------ | :--------: |
| E6-1 | SQLCipher (Community Edition) | License text (BSD-style, Zetetic) as shipped in the wheel; attribution requirement; confirm Community (not Commercial) edition terms apply to the embedded build | LEGAL | PENDING | YES |
| E6-2 | OpenSSL 3.x | Apache-2.0 — include LICENSE; NOTICE handling; confirm exact version's license file | LEGAL | PENDING | YES |
| E6-3 | Python binding (e.g. `sqlcipher3` MIT per metadata / `rotki-pysqlcipher3` zlib per upstream — confirm from wheel `LICENSE`, not metadata) | License file in wheel; attribution | LEGAL | PENDING | YES |
| E6-4 | SQLite (public domain) + any bundled extensions in the binding | Confirm no additional licensed extensions (e.g. ICU) | LEGAL | PENDING | YES |
| E6-5 | AEAD provider (e.g. PyNaCl Apache-2.0 + libsodium ISC) and transitive `cffi` (MIT) / `pycparser` (BSD) | License files; NOTICE if present | LEGAL | PENDING | YES |
| E6-6 | `cryptography` (Apache-2.0 OR BSD) + its statically linked OpenSSL, if used | License files; Rust crate licenses listed by upstream | LEGAL | PENDING | YES (if selected) |
| E6-7 | `pywin32` (PSF-style) if chosen for DPAPI | License file | LEGAL | PENDING | YES (if selected) |
| E6-8 | PyInstaller bootloader exception (GPLv2+ with exception permitting distribution of frozen apps under any license) | Confirm exception text for the pinned version | LEGAL | PENDING | YES |
| E6-9 | CPython (PSF) + bundled OpenSSL/libffi/Tcl etc. in the frozen app | Standard third-party notices | LEGAL | PENDING | YES |
| E6-10 | Bundled-executable obligations: where the THIRD-PARTY NOTICES file lives in `dist\WisePMS\` and in any installer; "About" screen or docs reference | Proposal (text only) | PO + LEGAL | PENDING | NO (before production, SEC-10) — inventory YES |

### E7 — Specialist security evidence checklist

Each item needs a **written specialist statement** (accept / accept-with-
conditions / reject) referencing the evidence IDs it relied on. Maps to M0 §24.

| ID | Topic | Specialist must confirm | Evidence relied on | Status | Blocks M1? |
| -- | ----- | ----------------------- | ------------------ | ------ | :--------: |
| E7-1 | AEAD | Library/API correctness; KAT; fail-closed tag verification | E2-1…E2-5 | PENDING | YES |
| E7-2 | Nonce uniqueness | 192-bit CSPRNG nonce per encryption; per-file key model; no `(key, nonce)` reuse; rules for re-encryption | E2-10 | PENDING | YES (model) |
| E7-3 | AAD | Field set for files, backups, wrapped-DEK records | E2-11, M0 §5.1 | PENDING | YES |
| E7-4 | HKDF | Construction, Extract/Expand choice, KATs | E3-1…E3-3 | PENDING | YES |
| E7-5 | Domain separation | Label set `wise-pms/{db,attach,kek-recovery,backup,kek-pass}/v1`; encoding; Recovery Key ≠ KEK_recovery ≠ BACKUP_KEY | E3-3, M0 §5.2/§23/§26.1 | PENDING | YES |
| E7-6 | Key wrapping | AEAD-wrap vs. RFC 5649 AES-KW; wrapped-DEK header as AAD; `keymat_version` manifest integrity | M0 §5.1, E2 | PENDING | YES |
| E7-7 | SQLCipher raw-key path | Raw-key format, salt, HMAC key derivation, profile PRAGMAs, codec/journal/temp behavior | E1-8, E1-10…E1-15 | PENDING | YES |
| E7-8 | DPAPI | User-scope `CryptProtectData` flags (e.g. `CRYPTPROTECT_UI_FORBIDDEN`), optional entropy, file ACLs, access via `ctypes` vs. `pywin32`, non-Windows dev/CI fallback design | §4.7 | PENDING | YES (design); SEC-06 runbook before production |
| E7-9 | Recovery Key | ≥128-bit, encoding + checksum, never persisted by the app, entry UX error detection | M0 §10 | PENDING | YES |
| E7-10 | Migration | Ordering (keys → encrypted backup → stage → verify → switch); SEC-02 combined-state marker requirement acknowledged for M5 | M0 §11/§26.3 | PENDING | NO (before M5) — acknowledgement YES |
| E7-11 | Temporary plaintext | Decrypt-to-temp location/ACL/lifetime/sweep; pagefile/hibernation residual; legacy plaintext backups (SEC-03) | M0 §7.2/§26.4 | PENDING | NO (before production) |
| E7-12 | Key lifetime | Python zeroization limits documented (SEC-11); `cipher_memory_security` decision | E1-13 | PENDING | NO (documented residual) |
| E7-13 | Backup recovery | BACKUP_KEY derivation, backup header fields, restore-on-new-machine without DPAPI | M0 §8/§23, E3 | PENDING | YES (derivation) |
| E7-14 | Bundled versions | SQLCipher/OpenSSL/libsodium versions free of known exploitable advisories | E1-3/4/19, E2-2 | PENDING | YES |
| E7-15 | Overall sign-off | Complete M0 §24 checklist signed | all of the above | PENDING | YES |

### E8 — Hardware / environment manifest (capture before any benchmark or clean-machine run)

No personal or patient data. Use machine class labels (e.g. "CLINIC-PC-1"),
never names, serial numbers, usernames, IPs, or clinic identifiers.

| ID | Field | How to capture (PowerShell, read-only) |
| -- | ----- | -------------------------------------- |
| E8-1 | Windows edition, version, build (e.g. 10/11, 22H2/23H2/24H2) | `Get-ComputerInfo -Property OsName,OsVersion,OsBuildNumber,OsArchitecture` |
| E8-2 | CPU model, cores/threads, base clock; AES-NI / AVX2 presence (informs AEAD/scrypt performance) | `Get-CimInstance Win32_Processor \| Select Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed`; Sysinternals `coreinfo` for instruction flags |
| E8-3 | Installed RAM + typical free RAM with the clinic's normal apps open | `Get-CimInstance Win32_ComputerSystem \| Select TotalPhysicalMemory`; Task Manager snapshot |
| E8-4 | Storage type (HDD/SATA SSD/NVMe), free space on the data volume, filesystem | `Get-PhysicalDisk \| Select MediaType,BusType,Size`; `Get-Volume` |
| E8-5 | BitLocker/device-encryption status (complementary control, SEC-03) | `manage-bde -status` (status only) |
| E8-6 | Pagefile + hibernation configuration (SEC-03 residual) | `Get-CimInstance Win32_PageFileUsage`; `powercfg /a` |
| E8-7 | Python version + architecture used for the build (target CPython fixed by PO, D-A) | `python -VV`; `python -c "import struct;print(struct.calcsize('P')*8)"` |
| E8-8 | PyInstaller version; pip version; wheelhouse manifest hash | `pyinstaller --version`; `pip --version`; `sha256sum` of manifest |
| E8-9 | Windows account type (local vs. Microsoft account; standard vs. admin) — relevant to DPAPI (SEC-06) | `whoami /groups` summarized to "standard/admin"; account *type* only |
| E8-10 | Antivirus product + real-time protection on/off | `Get-MpComputerStatus \| Select AMRunningMode,RealTimeProtectionEnabled` |
| E8-11 | Power plan + on-battery/mains | `powercfg /getactivescheme` |
| E8-12 | Data profile (sizes only): current DB size, attachment count, total attachment bytes, largest attachment, latest backup size | `Get-ChildItem` sums over `data\`, `attachments\`, `backups\` — sizes/counts only, no filenames exported |
| E8-13 | Deployment facts: exe location, `WISE_PMS_HOME` usage, whether data dir is on a local disk (ADR-002 §8.1: never network share) | Record answers; no paths containing personal names |

---

## 4. Evidence-gathering procedures (to be executed later — NOT in this task)

### 4.0 Controls common to all procedures
- Execute on **disposable machines/VMs** or a quarantine directory **outside
  this repository**; never on the clinic's live data; never `pip install`
  into the project environment; never modify `requirements*.txt`.
- Use only **synthetic data** (fixture DBs, random bytes, a known plaintext
  marker such as `WISEPMS-PLAINTEXT-CANARY-0001`). No PHI.
- Every run produces: environment manifest (E8), command transcript, tool
  versions, input hashes, output (logs/CSV/screenshots). Store in an evidence
  log owned by the PO (location to be decided; not committed with binaries).
- Evidence IDs (E1-x…E8-x) are quoted in each artifact so SPEC/PO can trace.

### 4.1 Package acquisition (quarantine)
```text
python -m venv C:\f7-evidence\venv-<candidate>          # throwaway venv, target CPython
C:\f7-evidence\venv-<candidate>\Scripts\python -m pip download --no-deps --only-binary=:all: ^
    --python-version <D-A> --platform win_amd64 -d C:\f7-evidence\wheelhouse <package>==<version>
certutil -hashfile <wheel> SHA256                        # record
```
Then install **only into the throwaway venv** from the wheelhouse with
`--no-index --find-links`. Delete the venv after capture.

### 4.2 SQLCipher probe (throwaway script, not committed)
Queries to run and record for each candidate: `PRAGMA cipher_version`,
`cipher_provider`, `cipher_provider_version`, `compile_options`,
`cipher_page_size`, `cipher_hmac_algorithm`, `cipher_kdf_algorithm`,
`kdf_iter`, `cipher_memory_security`; raw-key open (`PRAGMA key = "x'…'"`),
`foreign_keys` after key, `journal_mode=DELETE`, `temp_store=2`; the stdlib
`sqlite3` negative open; header hex dump; wrong-key and byte-flip tests;
`executescript`, `Row` name access, `lastrowid`, exception subclass checks
(E1-17); `sqlcipher_export` plain→encrypted copy of a synthetic fixture with
row-count parity; mid-transaction journal copy scanned for the canary;
Process Monitor capture filtered on the process for temp-file creation.

### 4.3 Native dependency inventory
For every `.pyd`/`.dll` in each candidate wheel and later in `dist\WisePMS\`:
`dumpbin /dependents` (VS Build Tools on an **analysis** box, never the clean
target) or Sysinternals `sigcheck -m`; flag any non-OS, non-bundled import and
any DLL name present twice (e.g. two `libcrypto-3*.dll`).

### 4.4 AEAD probe
Constants (`KEYBYTES`, `NPUBBYTES`, `ABYTES`, `MESSAGEBYTES_MAX`), library
version, published KAT, round-trip with AAD, negative tests (flip ciphertext
byte / flip AAD byte / truncate tag / wrong key → exception, no output), peak
RSS for 10 MB/100 MB/1 GB one-shot inputs, and — if SPEC wants chunking
evaluated — the same for the chunked/stream API.

### 4.5 KDF probe
RFC 5869 Appendix A vectors on the chosen HKDF implementation;
`hashlib.scrypt` presence in dev and frozen builds; scrypt grid per the E3
benchmark protocol, output CSV (params, run, latency_ms, peak_rss_mb,
cpu_ms).

### 4.6 Frozen spike build (outside the repository)
Copy of the repo at a recorded commit into `C:\f7-evidence\spike\`, plus a
**spike-only** self-test entry point that runs §4.2/§4.4/§4.5 checks and
writes a log, then exits. Build with a pinned PyInstaller from the offline
wheelhouse. Any spec/hook files generated stay in the spike directory and are
**never committed** (PO decision 7: the real `.spec` lands at M3/M7; note R12
`.gitignore` issue for that milestone). Copy `dist\WisePMS\` to the clean
offline target (E5-1) and run E5-2…E5-13.

### 4.7 DPAPI probe (Windows only)
In the spike self-test: user-scope `CryptProtectData`/`CryptUnprotectData`
round-trip of a random 32-byte test value via the candidate access method
(`ctypes`/`crypt32` or `pywin32`); confirm a blob created under account A
fails under account B on the same machine, and fails on a second machine.
Password-reset / profile-replacement scenarios (SEC-06) are recorded as a
runbook test list for before production — not required pre-M1.

---

## 5. Pre-M1 gate table

| Gate | Required evidence | Status | Blocks M1? |
| ---- | ----------------- | ------ | :--------: |
| Target runtime fixed | PO decision D-A: target CPython minor version + Windows architecture (R10, O2, O3) | PENDING | YES |
| SQLCipher binding | E1-1…E1-9, E1-16…E1-23 on ≥1 candidate meeting M0 §6.1 criteria 1–10 | PENDING | YES |
| Raw-key profile | E1-10…E1-15 + SPEC statement E7-7 (SEC-05, SEC-13) | PENDING | YES |
| AEAD API | E2-1…E2-9 + SPEC E7-1 (SEC-01); if unmet → formally reviewed alternative, PO decision | PENDING | YES |
| AEAD model | E2-10…E2-13 + SPEC E7-2/E7-3 (nonce, AAD, whole-file vs. chunked) | PENDING | YES |
| KDF | E3-1…E3-9 incl. hardware benchmark + SPEC E7-4/E7-5 (SEC-04, SEC-12) | PENDING | YES |
| DPAPI | §4.7 probe + access-method decision + non-Windows fallback design + SPEC E7-8 | PENDING | YES |
| Packaging | E5-1…E5-13 on a clean offline Windows target (frozen spike, no committed `.spec`) | PENDING | YES |
| Dependencies | E4-1…E4-8, PO-approved dependency set + layering/test-gate change proposal (SEC-09) | PENDING | YES |
| Licensing | E6-1…E6-9 inventory reviewed; E6-10 notice plan (SEC-10 completion before production) | PENDING | YES |
| Hardware/environment | E8 manifest for every machine used for benchmark and clean-machine runs | PENDING | YES |
| Specialist sign-off | E7-15: full M0 §24 checklist signed with evidence references | PENDING | YES |
| Product Owner approval | Final M0 approval (§25 item 1) + decisions D-A…D-G (§7) + explicit, separate M1 authorization | PENDING | YES |

**Note N1 — M0 §26 internal inconsistency (not edited here).** In the §26
findings table, SEC-05 is tagged "Before M3" yet "Blocks M1 = Yes", and SEC-12
/ SEC-13 are tagged "Blocks M1 = No", while §26.10 lists SEC-05, SEC-12 and
SEC-13 all as "Must be resolved BEFORE M1". This plan follows the **stricter**
§26.10 reading (all three block M1). The PO/SPEC should reconcile the table in
a future documentation revision.

**Note N2 — possible M0 factual error (not edited here).** M0 §7.1 lists
`cryptography` as providing `XChaCha20Poly1305`. Desk observation O4 indicates
the current `cryptography` AEAD module does not export it. This is exactly the
risk SEC-01 anticipated; E2-1 must settle it with evidence.

---

## 6. External verification required

| Party | What |
| ----- | ---- |
| Specialist cryptographer/security reviewer | E7-1…E7-15; SQLCipher raw-key semantics for the exact version; HKDF construction; AEAD model; DPAPI usage; bundled-version advisories |
| Windows test operator (non-developer machine) | E5 clean-machine offline frozen run; §4.7 DPAPI cross-account/cross-machine checks |
| Clinic hardware owner | E8 manifest + E3 benchmark on the actual (or identical) clinic machine |
| Licensing reviewer | E6-1…E6-10 |
| Upstream sources | SQLCipher documentation/CHANGELOG for the exact embedded version; OpenSSL and libsodium security advisories; package maintainers' release/provenance info |

---

## 7. Product Owner decisions still required (none made here)

| ID | Decision | Why it is needed before evidence is conclusive |
| -- | -------- | ---------------------------------------------- |
| D-A | **Target CPython minor version and Windows architecture** for the shipped exe | Binding/AEAD wheel availability is per ABI/arch (O2, O3); "3.10+" is not specific enough |
| D-B | **SQLCipher binding** selection from evidenced candidates (PO decision 1 stays: static/prebuilt SQLCipher 4.x + OpenSSL 3.x) — including what to do if a candidate uses a non-OpenSSL provider or a dynamically linked OpenSSL DLL | Decision 1 requires OpenSSL 3.x; E1-4/E1-7 may show otherwise |
| D-C | **AEAD provider** for XChaCha20-Poly1305 (e.g. accept PyNaCl as a new native dependency), or — only if E2 fails — a formally reviewed alternative | SEC-01; O4/O5 |
| D-D | **HKDF source**: add `cryptography` vs. SPEC-approved stdlib-`hmac` RFC 5869 construction | Changes dependency set and packaging (E3-1, E4-1) |
| D-E | **DPAPI access method** (`ctypes` vs. `pywin32`) and the **non-Windows dev/CI fallback** design | Decision 4 records this as required before implementation |
| D-F | **Dependency/layering gate change** approval (new `{…}` set, allow-lists, intentional test changes per E4-4/E4-5) | M0 §25 item 7 |
| D-G | **Unlock-latency UX budget** for scrypt benchmarking (E3-7) and the minimum supported hardware class | KDF parameters cannot be selected without it |
| D-H | Final approval of the M0 documentation (M0 §25 item 1) and reconciliation of Notes N1/N2 | Pre-condition for M1 eligibility |

---

## 8. Recommended evidence sequence

1. **PO fixes D-A** (target CPython + arch) and **D-G** (latency budget, minimum hardware). Everything downstream depends on them.
2. **E8 manifests** for the clinic machine class(es) and the clean test VM.
3. **Desk shortlist** (E1-1, E2-1, E4-1, E6 inventory draft) — eliminate candidates with no target-ABI Windows wheel (e.g. confirm O1).
4. **Quarantine acquisition** (§4.1) + native inventory (§4.3, E1-7, E2-7, E4-7).
5. **Dev-interpreter probes** on Windows: SQLCipher (§4.2), AEAD (§4.4), HKDF/scrypt availability (§4.5).
6. **Frozen spike build + clean offline target run** (§4.6, E5) including DPAPI probe (§4.7). Fail fast here: this is the highest-risk item (F7-R1).
7. **scrypt benchmark** on representative hardware (E3-6), dev + frozen.
8. **Licensing review** (E6) against the exact wheels.
9. **Specialist verification** (E7) with the evidence pack; resolve N1/N2.
10. **PO review**: decisions D-B…D-F, D-H; dependency/layering change approval.
11. **Separate, explicit M1 authorization** — or not.

---

## 9. Boundary statement

This document is planning only. It adds no runtime code, dependency,
`requirements*.txt` change, schema/migration, test, SQLiteAdapter change,
crypto/DPAPI/Recovery-Key/attachment/backup code, or PyInstaller `.spec`. It
changes no Product Owner decision and does not authorize M1.

**M1 REMAINS NOT AUTHORIZED.**
