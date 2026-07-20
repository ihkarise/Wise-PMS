# Module: Roles (RBAC)

**Status:** 🔜 Planned (backlog **F3**) — **not implemented** · related table:
`users.role` (free text, unenforced)

## Purpose (target)
Role-based access control so each staff type sees and does only what their role
permits.

## Today
`users.role` stores a string (`Admin` for the seeded user) but **nothing
enforces it** — any logged-in user can perform any action. This is a compliance
gap for a PMS (L4 / [`../SECURITY.md`](../SECURITY.md)).

## Target roles
Administrator · Doctor · Reception · Pharmacy · Accounts · **Custom Roles**.
Permissions must be **configurable**, not hardcoded per role.

## Target design (planned — needs approval)
- New tables (via migration F1): `roles`, `permissions`, `role_permissions`
  (and optionally `user_roles` for multi-role users).
- `app/modules/roles/` vertical slice; an Administrator-only management screen.
- Enforcement at two seams:
  1. **Router** — guard routes by required permission.
  2. **Repository/service** — row- and action-level checks for sensitive
     operations (the repository is the natural choke point).
- Map roles to workflow (see [`../CLINICAL_WORKFLOW.md`](../CLINICAL_WORKFLOW.md)):
  Reception registers/books; Doctor consults; Pharmacy dispenses; Accounts bills.

## Dependencies
Depends on migrations (F1). Blocks any networked/multi-user surface (Portal,
Telemedicine, Sync, API) — those must not ship before RBAC.

## Notes
Keep permissions data-driven so future modules add their own permission keys
without code changes to the RBAC core.
