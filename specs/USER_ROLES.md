# User Roles & RBAC — Specification

> **Status:** Design only (Phase 2). Not implemented. Backlog **F3** (blocks
> networked surfaces). Planned tables: `roles`, `permissions`,
> `role_permissions`, `user_roles`. **Last updated:** 2026-07-20.
> Extends [`../docs/modules/Roles.md`](../docs/modules/Roles.md).

## 1. Purpose

Role-based access control so each staff type sees and does only what their role
permits. Today `users.role` is a free-text string that **nothing enforces** — any
logged-in user can do anything (L4, a compliance gap). RBAC closes that and is a
hard prerequisite for every patient-facing / multi-user surface (Constitution
Art. VI §3).

## 2. Target roles

Administrator · Doctor · Reception · Pharmacy · Accounts · **Custom Roles**.
Permissions must be **configurable, not hardcoded per role** (Constitution
Art. VIII §4).

## 3. Permission model (data-driven)

Permissions are **data**, keyed strings that modules declare, so a new module adds
its own permission keys without editing the RBAC core.

```
Permission key convention:  <module>.<action>
  patients.create · patients.edit · patients.view ·
  cases.manage · visits.consult · investigation.order ·
  dispensing.fulfil · billing.manage · payments.record ·
  whatsapp.send · settings.edit · users.manage · reports.view · audit.view
```

```
roles              id · name · is_system · description
permissions        id · key (UK) · module · description
role_permissions   role_id FK · permission_id FK
user_roles         user_id FK · role_id FK        # multi-role optional
```

- **System roles** (Administrator, Doctor, Reception, Pharmacy, Accounts) are
  seeded with sensible default permission sets; they are editable but not
  deletable.
- **Custom roles** are fully user-defined combinations of permission keys.

## 4. Default permission matrix (starting point, editable)

| Permission (key) | Admin | Doctor | Reception | Pharmacy | Accounts |
| ---------------- | :---: | :----: | :-------: | :------: | :------: |
| patients.create / edit | ✅ | ✅ | ✅ | | |
| patients.view | ✅ | ✅ | ✅ | ✅ | ✅ |
| appointments.manage | ✅ | ✅ | ✅ | | |
| queue.manage | ✅ | ✅ | ✅ | | |
| cases.manage | ✅ | ✅ | | | |
| visits.consult | ✅ | ✅ | | | |
| investigation.order | ✅ | ✅ | | | |
| dispensing.fulfil | ✅ | | | ✅ | |
| billing.manage / payments.record | ✅ | | | | ✅ |
| whatsapp.send | ✅ | ✅ | ✅ | ✅ | |
| reports.view | ✅ | ✅ | | | ✅ |
| settings.edit | ✅ | | | | |
| users.manage | ✅ | | | | |
| audit.view | ✅ | | | | |

This maps to the clinical workflow: Reception registers/books, Doctor consults,
Pharmacy dispenses, Accounts bills (see
[`../docs/CLINICAL_WORKFLOW.md`](../docs/CLINICAL_WORKFLOW.md)).

## 5. Enforcement seams (two layers)

Per [`../docs/modules/Roles.md`](../docs/modules/Roles.md):

1. **Router** — guard routes by required permission (a route declares the
   permission key it needs; the router checks the session user's effective
   permissions, else redirects with a friendly message).
2. **Repository/service** — row- and action-level checks for sensitive operations.
   The **repository is the natural choke point** and the same seam used for cloud
   sync (Constitution Art. III §5).

Defense in depth: the UI hides what a role can't do, **and** the service/repo
refuses it — the UI is never the authorization (critical for the future Portal,
Art. VI §5).

## 6. User management (backlog F4)

An Administrator-only screen to create/deactivate users, assign roles, reset
passwords, and force a password change. Complements auth (built). Users are
soft-deactivated (`is_active`), never deleted.

- Force change of the default `admin`/`admin123` on first use.
- Optional account lockout / rate limiting (L6) before any networked deployment.

## 7. Audit trail

When RBAC lands, the **audit trail becomes the record of who-did-what under which
permission**. Every mutation already audits via `audit.service.log_action`; RBAC
adds the *authority* dimension (which role/permission allowed it). AI actions are
audited too (Constitution Art. II §6). An `audit.view` permission gates viewing.

## 8. Future multi-clinic support

- A future `clinic_id` scopes users, roles, and data per clinic; roles can be
  clinic-scoped or global (Administrator).
- Designed as an **additive dimension** (migration), not a rewrite (Constitution
  Art. VIII §5). Enforcement stays at the repository seam.

## 9. Dependencies & sequencing

- **Requires:** F1 (tables). **Blocks:** Patient Portal, Telemedicine, Cloud
  Sync, public API (must not ship before RBAC + encryption at rest F7).
- **Sequencing:** roles/permissions/enforcement (F3) → user management (F4) →
  then patient-facing surfaces.

## 10. Manual test checklist (implementing phase)

- [ ] A user limited to a role cannot reach guarded routes (router refuses).
- [ ] A sensitive service call is refused for a role lacking the permission
      (service/repo refuses, not just the UI).
- [ ] Custom roles combine arbitrary permission keys.
- [ ] System roles are editable but not deletable.
- [ ] Every action records the acting user + permission in audit.
- [ ] Default admin creds must be changed on first use.
- [ ] Model/table parity + router contract green.

## 11. Risks

- **Retrofitting enforcement** onto existing routes/services must not break
  current behavior for the Admin (regression golden) — introduce permissions with
  Admin-all defaults, then tighten.
- **Compliance scope** (HIPAA / India DPDP) is an open Product Owner question —
  see the phase-end questions.
</content>
