# .ai/NEXT_TASK.md — The single next actionable task

> Keep this to **one** concrete task. When it's done, replace it with the next
> one. **Updated:** 2026-09-20.

## Now
**Sprint 5 (F3 RBAC, ADR-003) implementation is COMPLETE and audited.**
Milestones M1–M5 are implemented on branch `claude/sprint-5-implementation`
(5 commits, HEAD `ebe58fb`, 5 ahead / 0 behind `main`); each milestone
passed its security audit; M6 documentation closure is done. 130/130 tests
pass; the regression golden changed once intentionally (the M1 RBAC
tables/index, rule 12/13) and not since.

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
Nothing implementation-side. The single next action is the **Product
Owner's release step**: open the Sprint 5 pull request from
`claude/sprint-5-implementation` into `main` and authorize its review/merge.
No further code changes are pending.

## Next
Sprint 6 has **not** been scoped or authorized. Candidate follow-ons remain
per the backlog (e.g. F4 user management — depends on F3; F7 encryption at
rest — sequenced after RBAC per ADR-002 §11). Selecting and scoping the next
phase requires Product Owner planning/authorization; this file does not
decide it.
