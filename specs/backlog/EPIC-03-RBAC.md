# EPIC-03 — User Roles, RBAC & User Management

> **Spec:** [`../USER_ROLES.md`](../USER_ROLES.md) · **Backlog:** F3, F4 ·
> **Stage:** A — Foundation · **Depends on:** EPIC-01 (F1) ·
> **Complexity:** M · **Risk:** Medium · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. VI.

## 1. Objective

Enforce role-based access so each staff type does only what its role permits.
Today `users.role` is decorative — any logged-in user can do anything (L4). RBAC
closes the compliance gap and is a hard prerequisite for every networked/
patient-facing surface (Portal, Telemedicine, Sync, API).

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E03-F1 | Roles & permissions model | `roles`, `permissions`, `role_permissions`, `user_roles` |
| E03-F2 | Data-driven permission keys | `<module>.<action>` keys modules declare |
| E03-F3 | System roles + defaults | Admin/Doctor/Reception/Pharmacy/Accounts seeded editable-not-deletable |
| E03-F4 | Custom roles | Arbitrary permission-key combinations |
| E03-F5 | Router enforcement | Routes declare required permission; guard redirects |
| E03-F6 | Service/repository enforcement | Action/row-level checks at the choke point |
| E03-F7 | User management (F4) | Admin screen: create/deactivate users, assign roles, reset password |
| E03-F8 | First-use hardening | Force change of default `admin/admin123`; optional lockout |

## 3. User stories

- **E03-F3-S1** — As an Administrator, I want default roles preconfigured, so that
  staff get sensible access on day one.
- **E03-F4-S1** — As an Administrator, I want to build a custom role, so that I can
  fit an unusual staffing setup.
- **E03-F5-S1** — As the clinic, I want reception blocked from the consultation
  screen, so that clinical notes are doctor-only.
- **E03-F6-S1** — As a security reviewer, I want the service to refuse an
  unauthorized action even if the UI is bypassed, so that the UI is never the
  authorization.
- **E03-F7-S1** — As an Administrator, I want to create and deactivate user
  accounts and assign roles, so that staff changes are manageable.
- **E03-F8-S1** — As the clinic, I want to be forced to change the default admin
  password on first use, so that we aren't shipping known credentials.

## 4. Engineering tasks

- **E03-T1** — Migration: `roles`, `permissions`, `role_permissions`, `user_roles`;
  seed system roles + default permission matrix (from spec §4).
- **E03-T2** — `modules/roles/` slice: models, repository, service
  (`has_permission(user, key)`, role CRUD, assignment), controller, view.
- **E03-T3** — Permission-key registry: each module declares its keys; a central
  catalog aggregates them (no core edit when a module adds keys).
- **E03-T4** — Router: routes optionally declare `required_permission`; guard
  checks effective permissions; friendly redirect on denial.
- **E03-T5** — Service/repository guards for sensitive ops (dispense, bill, settings
  edit, user manage) — the repository is the choke point.
- **E03-T6** — User management screen (`^/users$`, F4): create/deactivate, assign
  roles, reset/force-change password; soft-deactivate only.
- **E03-T7** — First-use password change flow; optional lockout/rate-limit (L6).
- **E03-T8** — Introduce with **Admin-all defaults** to preserve current behavior,
  then tighten; keep regression golden green.
- **E03-T9** — Tests + docs (Roles/Users module docs, SECURITY, KNOWN_LIMITATIONS
  L4/L6, CHANGELOG, DECISIONS ADR).

## 5. Dependencies

- **Upstream:** EPIC-01 (tables). Pairs well after EPIC-02 (gate settings edit).
- **Downstream:** gates EPIC-16 (Portal), EPIC-17 (Telemedicine), EPIC-20 (Sync),
  EPIC-21 (API); every epic's routes/actions declare permission keys.

## 6. Acceptance criteria

- **AC1** — *Given* a user with a role lacking `visits.consult`, *when* they open
  the Workspace route, *then* the router refuses with a friendly message.
- **AC2** — *Given* the same user, *when* the consult service is called directly,
  *then* it refuses (defense in depth, not just UI).
- **AC3** — *Given* a custom role with chosen keys, *when* assigned, *then* the
  user's effective permissions equal that set.
- **AC4** — *Given* a system role, *when* an Admin tries to delete it, *then* it is
  editable but not deletable.
- **AC5** — *Given* first launch, *when* the default admin logs in, *then* a
  password change is required before proceeding.
- **AC6** — *Given* any action, *when* performed, *then* the audit row records the
  acting user (and, where relevant, the permission that allowed it).

## 7. Regression tests

- **Must stay green:** golden (with Admin-all defaults preserving behavior),
  models, router, views.
- **New:** permission-check unit tests, route-guard tests (allowed/denied),
  service-guard tests, role CRUD/assignment tests, user-management view-build,
  model/table parity for 4 new tables, router contract for `/users`.

## 8. Rollout phases

- **E03-R1** — Tables + model + `has_permission` + system roles seeded (no
  enforcement yet; Admin-all).
- **E03-R2** — Router enforcement on new/high-risk routes; friendly denial.
- **E03-R3** — Service/repository guards on sensitive ops.
- **E03-R4** — User management screen (F4) + first-use password hardening.
- **E03-R5** — Tighten defaults per the matrix; docs closeout (L4/L6).

## 9. Rollback

Revert enforcement layer → falls back to session-guard-only (current behavior);
tables inert. Never lock out the Administrator (seed guarantees an admin role).

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: no route/action is enforceable only in
the UI; default credentials cannot persist unchanged past first use.
</content>
