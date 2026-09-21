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

## Blocked on
**Product Owner review of the M0 design PR** and **specialist security
review** (approved decision 9) of the §18 items — both required before M1.
Several **[PO-DECISION]** items remain open (exact binding, AEAD family, KDF,
DPAPI scope, journal mode, backup key source — see M0 §21). No implementation
task is in flight; no code changes are pending.

## Next
After M0 approval + specialist sign-off + the open [PO-DECISION] resolutions,
the first implementation action is **M1 — crypto/key-management foundation**
(still separately gated; does not begin automatically). M0 §19 lists the M1
prerequisites.
