# .ai/NEXT_TASK.md — The single next actionable task

> Keep this to **one** concrete task. When it's done, replace it with the next
> one. **Updated:** 2026-09-21.

## Now
**Sprint 6 (F7 Encryption at Rest) — M0 Security Design Review, DESIGN ONLY.**
F7 planning (ADR-004 + Sprint 6 technical plan) is merged to `main` via
**PR #16** (`d534487`). The Product Owner has authorized **M0** (turn the
approved F7 architecture into an implementation-ready security design). This
task creates **only**:
- [x] `docs/planning/SPRINT6_M0_SECURITY_DESIGN.md` (detailed security design:
  crypto primitives, key hierarchy, SQLCipher, attachment/backup encryption,
  Windows DPAPI, offline Recovery Key, migration, locked-state machine,
  threat model, test matrix, LOCKED vs OPEN decisions)
- [x] `.ai/CURRENT_PHASE.md`, `.ai/NEXT_TASK.md` (M0-status pointers)

**Nothing else changes:** no `app/` runtime code, no crypto utility, no key
store, no `EncryptedStorageProvider`, no restore/migration code, no new
dependency, no `requirements.txt` change, no schema/migration, no
bootstrap/auth/RBAC change, no PyInstaller change, no test change, no
regression-golden change.

## M0 closure
The **seven Product Owner decisions are recorded** in M0 §22 (SQLCipher
static-wheel approach; AEAD = XChaCha20-Poly1305 direction; HKDF for Recovery
Key / scrypt for passphrases; user-scope DPAPI; rollback journal; Recovery-Key-
derived `BACKUP_KEY` with mandatory domain separation, Recovery Key ≠
`BACKUP_KEY`; commit a PyInstaller `.spec` at M3/M7). None fixes a crypto
parameter, pins a package, or authorizes implementation.

## Blocked on
**Specialist cryptographic security review — COMPLETE** (verdict: ACCEPTABLE
WITH CONDITIONS, no BLOCKER; findings SEC-01…13 recorded in M0 §26). What now
blocks M1 is clearing the §26.10 "before M1" conditions (SEC-01 AEAD/library,
SEC-04 KDF clarification, SEC-05 SQLCipher raw-key/profile, SEC-09 dependency/
packaging, SEC-12/13 HKDF + codec verification) plus final Product Owner
approval. No implementation task is in flight; no code changes are pending.

## Next
**M1 remains NOT AUTHORIZED.** It becomes eligible only after the eight M0 §25
prerequisites all clear (final M0 approval, specialist sign-off, verified
SQLCipher binding + Windows/offline/PyInstaller evidence, AEAD API
availability, benchmarked KDF params, dependency/layering-gate approval,
licensing review) — and then still requires its own separate Product Owner
authorization; it does not begin automatically.

## Pre-M1 status (2026-09-25)
- Evidence plan: `docs/planning/SPRINT6_PRE_M1_EVIDENCE_PLAN.md` (all gates PENDING).
- PO decisions D-A…D-H recorded: `docs/planning/SPRINT6_PRE_M1_PO_DECISIONS.md`
  (Python 3.14 / Windows x64; `sqlcipher3` candidate; XChaCha20-Poly1305 via
  PyNaCl/libsodium candidate; stdlib RFC 5869 HKDF; `ctypes` DPAPI; minimal
  dependency stack; ≈ ≤10 s unlock target; strict N1; N2 corrected in M0 Rev. 4).
- **Next (requires separate authorization):** Pre-M1 Evidence & Validation
  using the approved PO decisions. **M1 IMPLEMENTATION IS NOT AUTHORIZED.**
