# .ai/NEXT_TASK.md — The single next actionable task

> Keep this to **one** concrete task. When it's done, replace it with the next
> one. **Updated:** 2026-09-21.

## Now
**Sprint 6 (F7 Encryption at Rest, ADR-004) — PLANNING/DESIGN ONLY.** The
Product Owner has approved the F7 architecture direction and authorized
converting the F7 planning analysis into formal design documents. This
planning task creates **only**:
- [x] `docs/architecture-decisions/ADR-004-F7-Encryption-at-Rest.md`
- [x] `docs/planning/SPRINT6_TECHNICAL_PLAN.md`
- [x] `.ai/CURRENT_PHASE.md`, `.ai/NEXT_PHASE.md`, `.ai/NEXT_TASK.md`
  (planning-state pointers only)

**Nothing else changes:** no `app/` runtime code, no crypto utility, no key
store, no `EncryptedStorageProvider`, no restore/migration code, no new
dependency, no `requirements.txt` change, no schema/migration, no
bootstrap/auth/RBAC change, no PyInstaller change, no test change, no
regression-golden change. This mirrors the Sprint 5 planning-PR precedent
(`SPRINT5_FILE_MAP.md §5`: ADR + planning docs + the three `.ai` pointers
only).

## Blocked on
**Product Owner review and merge authorization for the F7 planning PR**, and
— separately — explicit authorization to begin F7 **implementation**
(milestones M1–M7). No implementation task is in flight; no code changes are
pending. Prior release (Sprint 5) is done (`main == cf0f1e5`).

## Next
After the planning PR merges, the first implementation action would be **M0
— Architecture/security decision closure** (resolve every [SECURITY DESIGN
DECISION REQUIRED] item in ADR-004 §13/§20; select the crypto
dependency/SQLCipher binding; engage specialist security review; confirm the
milestone order). **M0 requires its own Product Owner authorization** — it
does not begin automatically. Prior candidate follow-ons (F4 user management;
Consultation Workspace feeders; AI Gateway, blocked until F7) remain per the
backlog.
