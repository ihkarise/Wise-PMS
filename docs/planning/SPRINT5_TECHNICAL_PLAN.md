# Sprint 5 — Technical Plan (F3 RBAC)

**Status:** PROPOSED — Product Owner review. **Planning only; no code in
this document is implemented.** Implements ADR-003.
**Date:** 2026-09-18

> This plan defines *how* RBAC would be implemented without implementing
> it. Where the repository does not provide enough evidence to fix a
> detail, the item is marked **[UNRESOLVED — decide at implementation]** or
> **[PRODUCT OWNER DECISION]** rather than invented.

---

## 1. Design summary

Data-driven RBAC (ADR-003): `roles`/`permissions`/`role_permissions`/
`user_roles` tables; enforcement at the **router** (route-level) and
**service/controller** (action-level) seams; fail-closed audited denial; a
separate Administrator-only management surface. All behavior-preserving for
the Administrator (who receives every permission), so existing
Administrator flows are unchanged; new behavior is the *restriction* of
lower-privilege roles.

## 2. Schema & domain model

### 2.1 Tables (new migration `v0003_rbac`, additive/idempotent/reversible)

```sql
CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT UNIQUE NOT NULL,
    description TEXT,
    is_system   INTEGER DEFAULT 0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key         TEXT UNIQUE NOT NULL,        -- module.action
    description TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id       INTEGER NOT NULL REFERENCES roles(id),
    permission_id INTEGER NOT NULL REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id),
    role_id INTEGER NOT NULL REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);
```

Indexes: `idx_role_permissions_role`, `idx_user_roles_user` (exact index
set finalized with the migration; whatever is added is reflected in the
golden `INDEXES:` line — §9).

Written against the **portable SQL subset** (ADR-002 §3) through
`BaseRepository`/`DatabaseAdapter`; the migration DDL stays hand-written
SQLite in the runner (ADR-0008 unchanged; no ORM/Alembic).

### 2.2 Migration `down`

Drops `user_roles`, `role_permissions`, `permissions`, `roles` (reverse
order). No change to `users` (the legacy `role` column is never touched),
so `down` is a clean reversal.

### 2.3 Models (`RowModel`, per ADR-0004)

`Role`, `Permission`, `RolePermission`, `UserRole` dataclasses mirroring the
tables, with `from_row`/`to_dict`. Home: `app/modules/roles/models.py`.

### 2.4 Seed data (run in the migration or in `init_db()` seed step)

> **[UNRESOLVED — decide at implementation]** whether the role/permission
> *seed* lives in the migration `up` or in the `init_db()` Python seed
> (which already seeds the default admin + clinic settings). ADR-0008 keeps
> the admin seed in Python because of bcrypt; RBAC seed has no such need,
> so the migration is the natural home. Decide for consistency at
> implementation; either way the seed is idempotent (`INSERT … WHERE NOT
> EXISTS` / `INSERT OR IGNORE`).

- Roles: Administrator (`is_system=1`), Doctor, Reception, Pharmacy,
  Accounts.
- Permissions: the catalogue in §5.
- `role_permissions`: Administrator ← all permissions; the other four ←
  their scoped sets (§5).
- `user_roles`: map every existing `users` row from its legacy `role`
  string (§6).

## 3. `users.role` handling (ADR-003 §5)

- **Keep** `users.role TEXT` (never drop/rename — Constitution Art. IV §2).
- `user_roles` becomes **authoritative** for enforcement; `users.role` is a
  non-authoritative display hint.
- **[UNRESOLVED — decide at implementation]** whether services keep writing
  `users.role` for display when a role is (re)assigned, or stop writing it.
  Recommended: keep it in sync for display, but never read it for an
  authorization decision. This choice has no schema impact.

## 4. Repositories & services

### 4.1 `app/modules/roles/repository.py` (SQL only, ADR-0005)
- `list_roles()`, `get_role(id|name)`, `list_permissions()`,
  `permissions_for_role(role_id)`, `permissions_for_user(user_id)`
  (join `user_roles → role_permissions → permissions`),
  `set_role_permissions(role_id, permission_ids)`,
  `assign_user_role(user_id, role_id)`, `roles_for_user(user_id)`,
  `count_active_admins()`.

### 4.2 `app/modules/roles/service.py` (rules + audit)
- `get_user_permissions(user) -> set[str]` — the single source consulted by
  the guard and by action checks. **[UNRESOLVED — perf]** whether to cache
  the current user's permission set in `page.session` at login vs. query
  per dispatch; recommended: resolve at login and store the permission set
  in session, re-resolved when the user's role changes. Grounded in the
  existing pattern (`page.session.get("user")` already holds the user).
- `assign_role(actor, user_id, role_id)` — enforces the
  **at-least-one-active-Administrator** invariant (deny demoting the last
  admin); audits via `audit.service.log_action`.
- `set_role_permissions(actor, role_id, permission_ids)` — Administrator
  role's full-permission grant is protected from being stripped below a
  usable Administrator (invariant); audited.
- Raises a typed `AuthorizationError` for denied checks (§7).

### 4.3 Permission-check API (the seam both guards use)
```
roles.service.user_has_permission(user, "patients.edit") -> bool
roles.service.require_permission(user, "patients.edit")   # raises AuthorizationError
```
One implementation, consulted by the router guard (§7.1) and by
action-level checks (§7.2), so there is a single, testable definition of
"is this allowed."

## 5. Permission catalogue & default role→permission matrix — FINAL

**FINAL (Product Owner, 2026-09-19).** This is the concrete Sprint 5
catalogue, derived **only** from functionality that exists today (verified
`main` HEAD `eb9fb92`), using the repository's actual module/action
terminology. No permission is defined for functionality that does not exist
(no appointments, no medicine/dispensing, no inventory, no audit-viewing
surface — those modules are not built, so they get no keys until they are).
Assignments are data-driven, so a later refinement is a seed change, not a
code change; the mapping below is the seeded default the Product Owner has
approved.

### 5.1 Legend
- **Route** permissions gate opening a screen (router guard, §7.1).
- **Action** permissions gate a mutating operation (service/controller
  check, §7.2). A route and an action can share a key (e.g. `settings.edit`
  gates both the `/settings` screen and the write).
- Administrator holds the **complete Sprint 5 permission set** (every key
  below).

### 5.2 The matrix

| Permission | Kind | Controls / protects (existing route → service op) | Administrator | Doctor | Reception | Pharmacy | Accounts |
| ---------- | ---- | ------------------------------------------------- | :-----------: | :----: | :-------: | :------: | :------: |
| `dashboard.view` | Route | `^/dashboard$` (also the router fallback) → dashboard read | ✓ | ✓ | ✓ | ✓ | ✓ |
| `patients.view` | Route | `^/search$`, `^/patient/{id}$` → `search_patients`, `get_patient`, profile read (cases/timeline/attachments tabs) | ✓ | ✓ | ✓ | — | — |
| `registration.create` | Route+Action | `^/register$` → `patients.create_patient` (new patient) | ✓ | ✓ | ✓ | — | — |
| `patients.edit` | Route+Action | `^/patient/{id}/edit$` → `patients.update_patient` | ✓ | ✓ | ✓ | — | — |
| `patients.deactivate` | Action | `patients.deactivate_patient` (soft-delete; no UI route today, guards the existing service op) | ✓ | ✓ | — | — | — |
| `attachments.upload` | Action | profile "Upload File" → `attachments.add_attachment` | ✓ | ✓ | ✓ | — | — |
| `attachments.delete` | Action | profile file delete → `attachments.delete_attachment` | ✓ | ✓ | — | — | — |
| `cases.view` | Route | `^/patient/{id}/case…$` (open case record) → `cases.get_case`, `cases_for_patient` | ✓ | ✓ | — | — | — |
| `cases.manage` | Action | `cases.create_case`, `cases.update_case` | ✓ | ✓ | — | — | — |
| `visits.view` | Route | `^/patient/{id}/visit…$` (open visit entry) → `visits.get_visit`, `visits_for_patient` | ✓ | ✓ | — | — | — |
| `visits.manage` | Action | `visits.create_visit`, `visits.update_visit` | ✓ | ✓ | — | — | — |
| `consultation.view` | Route | `^/patient/{id}/case/{cid}/workspace…$` → `consultation.workspace_context`, `open_or_create_draft` (read) | ✓ | ✓ | — | — | — |
| `consultation.edit` | Action | `consultation.save_consultation`, `complete_consultation`, `amend_consultation`, `lock_consultation` | ✓ | ✓ | — | — | — |
| `settings.edit` | Route+Action | `^/settings$` → `settings.update_clinic_settings`, `settings.upload_logo` | ✓ | — | — | — | — |
| `backup.run` | Action | shell "Backup" button (`app/shared/shell.py`) → `backup.backup_now` | ✓ | — | — | — | — |
| `rbac.manage` | Route+Action | `^/admin/roles$` (new) → all RBAC administration writes | ✓ | — | — | — | — |

### 5.3 Rationale (why each role gets or is denied each permission)

- **Administrator** — full access: the only role that administers the
  system and RBAC, edits clinic settings, and runs backups. Holds every
  key (including all clinical keys) so it is never locked out and can act
  in any capacity.
- **Doctor** — runs the consultation (`docs/CLINICAL_WORKFLOW.md`): full
  clinical access (patients view/edit, registration, cases, visits,
  consultation, attachments up/delete, patient deactivate). **Denied**
  `settings.edit`, `backup.run`, `rbac.manage` — these are
  administrative/config operations, not clinical, so least privilege
  excludes them.
- **Reception** — front desk: registers and finds patients and maintains
  demographics and documents (`dashboard.view`, `patients.view`,
  `registration.create`, `patients.edit`, `attachments.upload`).
  **Denied** the clinical *authoring* surfaces (`cases.*`, `visits.*`,
  `consultation.*`), `attachments.delete` (destructive), `patients.deactivate`,
  and all admin keys — Reception books/registers, it does not author or
  delete clinical records.
- **Pharmacy** — dispenses (`docs/CLINICAL_WORKFLOW.md`), but the
  **dispensing module does not exist yet** (B2/B4 backlog). It therefore
  has only `dashboard.view` today; its functional keys (e.g.
  `dispensing.*`) arrive **with** that module (`docs/modules/Roles.md`:
  "future modules add their own permission keys"). Granting it patient or
  clinical access now would exceed least privilege with no current
  function to justify it.
- **Accounts** — invoices (`docs/CLINICAL_WORKFLOW.md`), but the
  **billing module does not exist yet** (B1 backlog). Same treatment as
  Pharmacy: `dashboard.view` only today; `billing.*` keys arrive with the
  billing module.

> Pharmacy/Accounts intentionally have only `dashboard.view` in Sprint 5.
> This is the honest least-privilege state: their modules are unbuilt, so
> there is nothing yet for them to be permitted. This is **not** a gap to
> fill by inventing permissions — it is corrected when B1/B2/B4 land, each
> adding its own keys and its own row-appropriate grants.

### 5.4 Notes
- `registration.create` (new patient) and `patients.edit` (update existing)
  are kept distinct because they map to distinct routes/operations; both
  are granted to the same three roles today but may diverge later.
- `patients.deactivate` guards an **existing** service function
  (`deactivate_patient`, a soft-delete) that is not currently wired to a
  route/UI; the key protects the operation wherever it is invoked, so a
  future UI cannot expose it un-guarded.
- The profile screen's read-only Cases/Timeline/Attachments tabs are served
  under `patients.view`; the dedicated `cases.view`/`visits.view`/
  `consultation.view` keys gate the standalone case/visit/workspace
  **editor** routes, which are clinical-authoring surfaces.

## 6. Migration of the existing admin (ADR-003 §6) — safe, no lockout

`init_db()` seeds `("admin", <bcrypt>, "Administrator", role="Admin")`. The
`v0003_rbac` seed:
1. Ensures the Administrator role exists with all permissions.
2. For each `users` row, creates a `user_roles` binding by mapping its
   legacy `role` string:
   - `"Admin"` / `"Administrator"` → Administrator role.
   - Other recognized strings → the matching seeded role.
   - **Unrecognized / null legacy role → the FINAL non-locking,
     zero-permission state (§8 case 4):** no `user_roles` binding; the user
     can authenticate but lands on the denial view until an Administrator
     assigns a role. **Never** silently Administrator, never silently any
     populated role. The clinic is never locked out (invariant, step 3).
3. The at-least-one-active-Administrator invariant guarantees the `admin`
   account remains a full Administrator after migration.

**No credential or account-data change.** The default `admin`/`admin123`
posture and "change on first use" guidance are unchanged (`SECURITY.md`).

## 7. Enforcement (ADR-003 §7) — two seams

### 7.1 Router guard (route-level) — `app/core/router.py`
- Today: `dispatch()` runs a **session guard** (`route != "/login" and not
  authenticated → login`). Extend to a **permission guard**: after the
  session guard passes, resolve the route's **required permission** and, if
  the current user lacks it, render the fail-closed denial outcome (§8)
  instead of the handler.
- **Route→permission association.** Routes register today as
  `(regex, handler)` tuples (each module's `ROUTES`, assembled in
  `app/bootstrap.py`). Extend the registration so a route can declare its
  required permission. **[UNRESOLVED — decide at implementation]** exact
  mechanism — recommended options, lowest-churn first:
  1. A third tuple element: `(regex, handler, "patients.edit")`, with the
     `Router` treating a missing/`None` third element as "session-only"
     **only where explicitly whitelisted** (so a forgotten permission fails
     the route-coverage test, not open).
  2. A per-route registry/decorator mapping handler→permission.
  Either keeps the guard generic infrastructure (no per-route conditionals
  in the router body), consistent with ADR-0006.
- The guard consults `roles.service.user_has_permission` (§4.3) — one
  definition of "allowed."

### 7.2 Action-level (service/controller)
- Sensitive operations call `roles.service.require_permission(user, key)`
  before mutating: `settings.edit` (settings service write), `backup.run`
  (backup trigger), `rbac.manage` (all RBAC admin writes), and any
  privileged/destructive mutation a route guard cannot fully capture.
- On denial the service raises `AuthorizationError`; the controller renders
  the friendly denial (§8). The attempt is audited.

### 7.3 Repository/row-level — **DEFERRED**
No row-scoping requirement in Sprint 5 (ADR-003 §7). The repository seam
(`SECURITY.md` rule 4) is preserved and documented as the future home; no
row-filtering code is added. Adding it now would be an unnecessary layer.

## 8. Denial / failure behavior (ADR-003 §8) — FINAL, fail-closed

**FINAL (Product Owner, 2026-09-19).** All four cases are fail-closed:

| Case | Behavior |
| ---- | -------- |
| **Authenticated user lacking the required permission** | Route: render a dedicated **"You don't have permission"** denial view (never the guarded handler, never a traceback). Action: the service raises `AuthorizationError`; the controller shows the friendly denial via the existing `snack(page, …, error=True)`; **no mutation** occurs. The attempt is **audited** (`audit_logs`, `SECURITY.md` rule 2). |
| **Unauthenticated user** | The existing **session guard** (`app/core/router.py`: `route != "/login" and not authenticated → login`) runs **first**, unchanged, and diverts to `/login`. The permission guard only runs after authentication succeeds. |
| **Nonexistent / unknown permission key** (a route/action requires a key not in the catalogue) | **Denied for everyone, including Administrator** — the key is not in any resolved permission set, so the fail-closed guard denies it. This surfaces the misconfiguration loudly rather than silently allowing access, and the route-coverage / catalogue test (`SPRINT5_TESTING_PLAN.md`) prevents such a route from shipping. |
| **Unknown / unrecognized legacy `users.role`** (at migration) | Mapped to a documented **non-locking, zero-permission** state (no `user_roles` binding), **never** silently Administrator and never silently any populated role. The user can still authenticate but lands on the denial view ("no access — contact your administrator") until an Administrator assigns a role. The clinic is never locked out because the at-least-one-active-Administrator invariant (§6) guarantees Administrator access. |

**UX (resolved):** a **standalone denial view** for a guarded deep-linked
route; a **snackbar** for an in-screen denied action. Both are fail-closed
and audited.

## 9. Regression golden strategy (rule 12/13)
- The four new tables (and their indexes) change the golden's `TABLES:` and
  `INDEXES:` lines **once, intentionally** — exactly as ADR-0009 did for
  `consultations`. The updated `EXPECTED` snapshot ships in the **same
  commit** as the migration, with ADR-003 + CHANGELOG + DECISIONS.
- Administrator flows are behavior-identical (admin holds all permissions),
  so the rest of the snapshot stays byte-identical.
- **No golden edit during planning.** `tests/test_regression.py` is not
  touched by this planning PR.

## 10. UI implications
- New `app/modules/roles/` vertical slice with an Administrator-only
  management view (roles list, role→permission matrix editor, assign an
  existing user to a role), gated by `rbac.manage`. Registered as a new
  route (e.g. `^/admin/roles$`) in `bootstrap.py`.
- Existing views **may** hide/disable controls the current role can't use
  (convenience only — the server-side check is authoritative; hiding is
  never the enforcement, per RB4).
- A new route adds one documented line to the golden's route surface if the
  snapshot enumerates routes; that line is an intentional, documented
  change.

## 11. Admin management surface — boundary (F4)
The surface implements **only** minimum RBAC administration (view roles,
edit role permissions, assign an existing user to a role). It does **not**
create/deactivate users or change credentials — that is F4 and stays out of
scope (`SPRINT5_RECOMMENDATION.md` §7).

## 12. Backward compatibility
- Additive schema; `users.role` kept; migration `down` reverses cleanly.
- Existing tests continue to pass except the intended golden update (§9)
  and the router test, which gains permission-guard cases (admin path
  unchanged).
- No new runtime dependency (`requirements.txt` stays `{flet, bcrypt}` —
  layering gate extended to assert it).

## 13. Test architecture (see `SPRINT5_TESTING_PLAN.md`)
New `tests/test_rbac_domain.py` (roles/permissions/assignment/invariants),
`tests/test_rbac_enforcement.py` (allow/deny per role, route-coverage,
action-level, direct-service-call denial), migration + existing-admin
migration cases, `test_layering.py` extension, and the intentional golden
update. The **route-coverage** test is the anti-bypass keystone: it asserts
every route in the assembled registry has an explicit authorization intent.

## 14. Decision status

**Product Owner decisions — FINAL (2026-09-19), no longer open:**
- **Role set:** exactly five predefined roles (Administrator, Doctor,
  Reception, Pharmacy, Accounts); no additional roles this phase.
- **Runtime custom-role creation:** **OUT OF SCOPE** — no custom-role
  creation UI or workflow; the data model stays compatible with future
  configurable roles, but none is built.
- **User↔role cardinality:** **one user → one active role**; multi-role
  users out of scope (no role aggregation / permission union).
- **Permission→role matrix:** **FINAL** per §5.2 (data-driven seed).
- **Denial model:** **FINAL** per §8 (four fail-closed cases).
- **F4 user management:** out of scope beyond the minimum RBAC admin (§11).
- **F7 encryption / row-level authorization:** out of scope (ADR-003
  §7/§11).

**Implementation-level details (not Product Owner decisions; resolved at
implementation, no scope/schema impact):** seed location (migration vs.
`init_db()` Python — §2.4), the exact route→permission registration
mechanism (§7.1), permission-set caching (§4.2), and `AuthorizationError`
placement (§4.2 / `SPRINT5_FILE_MAP.md`). Each is marked inline; none
changes the schema shape or the matrix.
