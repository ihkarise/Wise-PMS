# Module: Roles (RBAC)

**Status:** ✅ Implemented (backlog **F3**, Sprint 5 / ADR-003) ·
`app/modules/roles/` · tables `roles`, `permissions`, `role_permissions`,
`user_roles` (migration `v0003_rbac`). `users.role` is retained as a
non-authoritative legacy hint only.

## Purpose
Role-based access control so each staff type sees and does only what their role
permits. Delivered as a data-driven model enforced at two seams.

## Roles (exactly five, predefined)
Administrator · Doctor · Reception · Pharmacy · Accounts.
**One active role per user** (enforced by a UNIQUE index on
`user_roles(user_id)`). Custom (runtime-created) roles and multi-role users
are **out of scope** and not implemented.

## Permissions (exactly 16, data-driven)
`dashboard.view` · `patients.view` · `registration.create` · `patients.edit`
· `patients.deactivate` · `attachments.upload` · `attachments.delete` ·
`cases.view` · `cases.manage` · `visits.view` · `visits.manage` ·
`consultation.view` · `consultation.edit` · `settings.edit` · `backup.run` ·
`rbac.manage`.

The canonical code-side catalogue is `app/modules/roles/permissions.py`
(mirrors the seeded `permissions` table; a test asserts they stay identical).

## Default role → permission matrix
- **Administrator:** all 16.
- **Doctor (13):** dashboard.view, patients.view, registration.create,
  patients.edit, patients.deactivate, attachments.upload, attachments.delete,
  cases.view, cases.manage, visits.view, visits.manage, consultation.view,
  consultation.edit.
- **Reception (5):** dashboard.view, patients.view, registration.create,
  patients.edit, attachments.upload.
- **Pharmacy (1):** dashboard.view.
- **Accounts (1):** dashboard.view.

(Pharmacy/Accounts hold only `dashboard.view` today because their functional
modules — dispensing/billing — are not yet built; their keys arrive with
those modules.)

## Authorization model
Authorization resolves through **`user_roles → role_permissions →
permissions`**; `users.role` is never read for an access decision. The
read API is `roles.service.user_has_permission(user, key)` and the guard
primitive `require_permission(user, key)` (fail-closed for missing/unknown/
inactive user, unknown permission, or no role binding).

## Enforcement (two seams — defense in depth)
1. **Router** (`core/router.py`) — guards each route by its declared required
   permission, after the session guard: `authentication → permission → handler`.
2. **Service / controller action level** — sensitive operations independently
   call `require_permission` before mutating (patient create/edit/deactivate,
   case/visit management, consultation editing, attachment upload/delete,
   settings edit, backup run, and RBAC administration). Authorization therefore
   never depends on UI visibility alone.

**Row-level (per-row) authorization is deferred** (see
[`../KNOWN_LIMITATIONS.md`](../KNOWN_LIMITATIONS.md) L16); the repository
remains the designated future seam for it.

## Administration surface
`/admin/roles` (`app/modules/roles/controller.py` + `view.py`),
Administrator-only (gated by `rbac.manage` at the router **and** the service
layer). Capabilities: view the five roles, view the 16 permissions, edit
role→permission grants, and assign an **existing** user to a predefined role
(via `roles.service.assign_role`). This is **not** user management — no user
creation/deletion/credential/profile administration (that is F4).

## Safety invariants
- The last active Administrator cannot be removed/demoted.
- `rbac.manage` cannot be revoked from the Administrator role
  (usable-Administrator invariant, ADR-003 §4.2).
- Role mutations flow only through `roles.service.assign_role`
  (`RoleRepository.set_user_role` is never called from controllers/views).

## Dependencies
Built on the F1 migration runner and the Sprint 4 repository/adapter seams.
RBAC is a prerequisite for — not an enabler of — networked/multi-user
surfaces (Portal, Telemedicine, Sync, API), which still additionally require
encryption at rest (F7) per [`../SECURITY.md`](../SECURITY.md) and ADR-002 §11.

## Out of scope (not implemented)
Custom/runtime roles · multi-role users · full user management (F4) ·
row-level authorization · F7 encryption.

## Notes
Permissions are data-driven, so a future module adds its own permission keys
(seeded in a migration + declared in the registry) without changing the RBAC
core.
