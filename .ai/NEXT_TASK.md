# .ai/NEXT_TASK.md — The single next actionable task

> Keep this to **one** concrete task. When it's done, replace it with the next
> one. **Updated:** 2026-09-20.

## Now
**Sprint 5 (F3 RBAC, ADR-003) is CLOSED and merged to `main`** via **PR #14**
(merge commit `10e0738`). Milestones M1–M6 delivered and security-audited;
each milestone passed its audit; M6 documentation closure is done. 130/130
tests pass, layering PASS, regression golden PASS; the golden changed once
intentionally across the sprint (the M1 RBAC tables/index, rule 12/13) and
not since. There is **no implementation task in flight** — the next action
is a Product Owner planning decision (see "Next").

Delivered:
- [x] M1 — `v0003_rbac` migration + `app/modules/roles/` foundation
  (roles/permissions/role_permissions/user_roles; five roles; 16 permissions;
  one active role per user; lockout-safe admin mapping).
- [x] M2 — permission registry + `user_has_permission`/`require_permission`
  (fail-closed; `user_roles`-authoritative).
- [x] M3 — router-level permission guard (auth → permission → handler).
- [x] M4 — service/controller action-level enforcement for all sensitive
  operations.
- [x] M5 — minimum RBAC administration surface at `/admin/roles`
  (`rbac.manage`-gated; role→permission editing; existing-user role
  assignment).
- [x] M6 — documentation closure (this file, CURRENT_PHASE, NEXT_PHASE,
  SECURITY, KNOWN_LIMITATIONS, Roles, MASTER_BACKLOG, TARGET_ARCHITECTURE).

## Blocked on
Nothing implementation-side, and the Sprint 5 release step is **done**
(PR #14 merged to `main`, commit `10e0738`). The single next action is a
**Product Owner planning decision**: scope and authorize the next phase
(no phase begins automatically per the charter). No code changes are pending.

## Next
Sprint 6 has **not** been scoped or authorized. Candidate follow-ons remain
per the backlog (e.g. F4 user management — depends on F3; F7 encryption at
rest — sequenced after RBAC per ADR-002 §11). Selecting and scoping the next
phase requires Product Owner planning/authorization; this file does not
decide it.
