# .ai/CURRENT_PHASE.md

**Phase:** Sprint 5 — F3 RBAC (Role-Based Access Control, ADR-003)
**Status:** ✅ CLOSED — merged to `main` via **PR #14** (merge commit
`10e0738`, on top of the Sprint 4 base). Milestones M1–M5 implemented and
security-audited; M6 documentation closure done. `main == origin/main ==
10e0738`, working tree clean.
`python3 -m pytest -q` → **130 passing** (0 failed/skipped/errors/warnings);
layering checks PASS (5); regression golden PASS (1).
Regression golden changed exactly once across the sprint, intentionally (the
M1 RBAC tables/index — rule 12/13); no golden change in M2–M5.
**No implementation work is pending. No next phase is authorized.**
**Updated:** 2026-09-20 (post-merge synchronization: PR #14 confirmed merged)

## Goal
Make `users.role` **enforced** instead of decorative (close L4 / the
SECURITY.md RBAC gap): a data-driven role/permission model with a
consistent, testable authorization boundary, so each staff type does only
what its role permits — without changing the database engine, storage
backend, deployment tier, or adding a runtime dependency.

## Delivered (M1–M5)
- **M1 — Foundation (ADR-0011).** Migration `v0003_rbac` (additive,
  reversible) adds `roles`, `permissions`, `role_permissions`, `user_roles`
  and seeds the five predefined roles (Administrator/Doctor/Reception/
  Pharmacy/Accounts), the 16-permission catalogue, and the default
  role→permission grants. `idx_user_roles_user` UNIQUE index enforces one
  active role per user. Legacy `admin` mapped to Administrator (no lockout);
  `users.role` kept as a non-authoritative legacy hint. New
  `app/modules/roles/` (models, repository, service) with the
  at-least-one-active-Administrator invariant.
- **M2 — Permission infrastructure.** `app/modules/roles/permissions.py`
  registry (16 keys, mirrors the DB) + `user_has_permission` /
  `require_permission` read API resolving via
  `user_roles → role_permissions → permissions`; fail-closed for missing/
  unknown/inactive user, unknown permission, no binding; no `users.role`
  read; no Administrator bypass.
- **M3 — Router enforcement.** `core/router.py` gains a permission guard
  after the session guard (auth → permission → handler). Each route
  declares its required permission via registry constants; fail-closed
  denial. `/login` public; `/settings` = `settings.edit`; clinical routes
  gated per the matrix.
- **M4 — Action-level enforcement.** `require_permission` at the service/
  controller action boundary for `create_patient`(registration.create),
  `update_patient`(patients.edit), `deactivate_patient`(patients.deactivate),
  case/visit mutations(cases.manage/visits.manage), consultation edits
  (consultation.edit), attachment upload/delete, `settings.edit`, and the
  shell backup action(backup.run). Guards precede every mutation/side effect.
- **M5 — Administration surface.** Administrator-only `^/admin/roles$`
  (`app/modules/roles/controller.py` + `view.py`), gated by `rbac.manage`
  at the router and again at every service op: view roles, view the 16
  permissions, edit role→permission grants, and assign an existing user to
  a predefined role (via `assign_role`). `rbac.manage` cannot be revoked
  from Administrator; the last Administrator cannot be demoted.

## Enforcement architecture
`authentication → router permission guard → service/controller action
guard → business operation`. Authorization resolves through `user_roles →
role_permissions → permissions`; `users.role` is never the source of truth.

## NOT in scope (deferred — unchanged from the approved plan)
Custom (runtime-created) roles; multi-role users; full F4 user management
(user creation/deletion/credential/profile administration); repository/
row-level authorization; F7 encryption at rest; any new permission or role.
These are not implemented and are not described as implemented anywhere.

## Prior phase
Sprint 4 (Cloud-Ready Architecture Seams + Settings UI, ADR-002) is CLOSED —
merged to `main` via PR #10 (planning) and PR #11 (implementation).

## Verification
```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q     # expect 130 passing
```
