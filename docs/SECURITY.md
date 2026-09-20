# WiseOS Health — Security

> Current posture and the roadmap to a PHI-grade posture. Be honest about what
> is and isn't protected today. **Last updated:** 2026-09-20 (RBAC / F3
> delivered — Sprint 5, ADR-003).

## Threat context

Wise PMS stores **Protected Health Information** (names, contacts, clinical
notes, prescriptions, documents). Today it runs as a **single-user, offline
desktop app on the clinic's own machine** — the trust boundary is physical
access to that machine.

## What exists today

| Control | Status | Detail |
| ------- | ------ | ------ |
| Password hashing | ✅ | bcrypt (`gensalt` + `checkpw`) for the `users` table |
| Session guard | ✅ | Router forces `/login` for any route without a session user |
| **RBAC (F3)** | ✅ | Role-based access control (ADR-003, Sprint 5): five roles, 16 permissions, enforced at the router **and** the service/controller action layer — see "Access control" below |
| Audit trail | ✅ | `audit_logs` records login/logout, every mutation, and RBAC changes (role assignment, permission grant/revoke); writes never raise |
| Soft delete | ✅ | Patients never physically removed (`is_active`) |
| Error containment | ✅ | Router hides tracebacks behind a friendly snackbar |
| Local-only data | ✅ | No network calls; DB is a local file |

## Access control (RBAC — F3, delivered Sprint 5 / ADR-003)

`users.role` is no longer decorative. Authorization is data-driven and
resolves through **`user_roles → role_permissions → permissions`**; the
legacy `users.role` column is retained only as a non-authoritative display
hint and is never read for an access decision.

- **Roles (exactly five, predefined):** Administrator, Doctor, Reception,
  Pharmacy, Accounts. **One active role per user** (enforced by a UNIQUE
  index on `user_roles(user_id)`).
- **Permissions (exactly 16):** `dashboard.view`, `patients.view`,
  `registration.create`, `patients.edit`, `patients.deactivate`,
  `attachments.upload`, `attachments.delete`, `cases.view`, `cases.manage`,
  `visits.view`, `visits.manage`, `consultation.view`, `consultation.edit`,
  `settings.edit`, `backup.run`, `rbac.manage`.
- **Two enforcement layers (defense in depth):** the router guards each
  route by required permission (after the session guard), and sensitive
  operations independently call `require_permission` at the service/
  controller action boundary — so authorization never depends on UI
  visibility alone. All checks fail closed.
- **Administration:** an Administrator-only surface at `/admin/roles`
  (gated by `rbac.manage`) can view roles/permissions, edit role→permission
  grants, and assign an existing user to a predefined role.
- **Safety invariants:** the last active Administrator cannot be demoted,
  and `rbac.manage` cannot be revoked from the Administrator role.
- **Out of scope (not implemented):** custom/runtime-created roles,
  multi-role users, full user management (F4), and repository/row-level
  (per-row) access control.

## What is NOT protected today — ⚠️

| Gap | Impact | Backlog |
| --- | ------ | ------- |
| **No encryption at rest** | `data/wise_pms.db` and `attachments/` are plaintext on disk | F7 |
| **Default credentials** | Ships `admin`/`admin123`; must be changed on first use | — |
| **No account lockout / rate limiting** | Brute force possible if machine is accessed | — |
| **Backups unencrypted** | `backups/backup_*.zip` contains the full DB + attachments in the clear | — |
| **No transport security** | N/A today (offline); becomes critical for Portal/API/Sync | F8 |

## Rules for future work

1. **RBAC (F3) is delivered.** Encryption at rest (F7) must still land before
   any networked or multi-user surface (Patient Portal, Online Consultation,
   Cloud Sync, API) — RBAC alone is necessary but not sufficient for those.
2. Every new mutation must write an audit row via `audit.service.log_action`.
3. New routes and sensitive actions must declare/enforce the appropriate
   RBAC permission (router route guard + service-level `require_permission`);
   authorization is resolved via `user_roles`, never `users.role`.
4. Secrets (future API keys for WhatsApp/Meet/AI) must never be committed —
   route them through Settings/env, and add them to `.gitignore` paths.
5. The **repository layer remains the designated seam** for future
   *row-level* (per-row) access control; that layer is **deferred** (not
   implemented in Sprint 5, which enforces at the router and action level).
6. Backups and exports must be encryptable before any off-device transfer.

## Compliance note

No formal HIPAA/GDPR/Indian DPDP compliance work has been done. RBAC (F3)
is now in place, but treat the current build as **suitable for a single
trusted clinician on a controlled machine**, not for multi-user or cloud
deployment, until encryption at rest (F7) and transport security (F8) are
also complete.
