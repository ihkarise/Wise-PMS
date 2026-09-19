# ADR-003 — Role-Based Access Control (RBAC)

**Status:** Proposed (Product Owner review) · **Date:** 2026-09-18
**Phase:** Sprint 5 (F3 RBAC) — **planning only; nothing in this ADR is
implemented.**
**Extends:** ADR-001 (Consultation Domain), ADR-002 (Cloud-Ready
Architecture), ADR-0005 (Repository seam), ADR-0006 (Centralized router),
ADR-0008 (Migration runner), Product Constitution Articles III/IV/VI.
**Depends on:** the F1 migration runner (Sprint 0) and the Sprint 4
`DatabaseAdapter`/`StorageProvider` seams (ADR-002 §11 sequences RBAC
*after* those seams so its enforcement is written against the final
repository shape).

**This ADR designs. It does not implement.** No code, migration, table,
route guard, UI, or dependency ships with it. `users.role` remains
decorative until a separately approved Sprint 5 implementation phase
begins. Await Product Owner approval of this ADR and the accompanying
Sprint 5 planning documents before any implementation.

---

## 0. Context

`docs/KNOWN_LIMITATIONS.md` L4 and `docs/SECURITY.md` both record the same
gap: **"No RBAC — `users.role` is decorative; any logged-in user can do
anything."** The `users` table (migration `v0001_initial`) carries a
`role TEXT` column; `init_db()` seeds a single `admin`/`admin123` user with
`role = "Admin"`; nothing reads that column for authorization. The router
(`app/core/router.py`) enforces exactly one access rule today — a **session
guard**: every route except `/login` requires a logged-in user. There is no
notion of *which* logged-in user may reach *which* route or perform *which*
action.

Every authoritative planning document identifies closing this gap as the
next phase:

- `docs/planning/SPRINT4_RECOMMENDATION.md` §2: "**F3 RBAC is Sprint 5.**"
- `docs/architecture-decisions/ADR-002-Cloud-Ready-Architecture.md` §11:
  RBAC is required *before* any networked surface, *before* F7 encryption,
  and *before* the future Administrator/Security settings surface.
- `docs/SECURITY.md` rule 1: "RBAC (F3) and encryption at rest (F7) must
  land before any networked or multi-user surface."
- `docs/modules/Roles.md`: the target RBAC design (planned, needs
  approval).

**Decision needed:** the role model, the permission model, how roles bind
to permissions and users, where authorization is enforced, how the schema
migrates additively, how the existing admin account is protected against
lockout, how denial is represented, and how RBAC relates to the Sprint 4
Settings boundary and to future networked deployment — all without
overstating what ships this phase.

## 1. Requirements

### Functional (design goals)
- `users.role` becomes **enforced**, not decorative (closes L4).
- Each staff type does only what its role permits
  (`docs/modules/Roles.md`): Administrator · Doctor · Reception ·
  Pharmacy · Accounts.
- **Permissions are configurable, not hardcoded per role**
  (`docs/modules/Roles.md`) — a data-driven permission model, so future
  modules add their own permission keys without editing the RBAC core.
- Authorization is enforced at a **consistent, testable boundary** with no
  obvious bypass.
- The existing single Administrator account is never locked out by the
  migration.

### Non-functional (evaluation axes, per ADR-001/ADR-002 convention)
Security (least privilege, fail-closed) · Testability (every guarded
route provably guarded) · Additivity (no destructive schema change) ·
Reversibility (migration `down`) · Offline-first preservation · Backward
compatibility · Implementation risk.

### Constraints (from the Constitution / `.ai/ARCHITECTURE_RULES.md`)
- Dependency direction stays `views → controllers → services →
  repositories → core`; SQL lives only in repositories.
- Migrations are additive, forward-only, idempotent, reversible (ADR-0008);
  never drop or rename a column an older build reads (Constitution
  Art. IV §2).
- No behavior change without an updated regression golden + CHANGELOG +
  DECISIONS entry in the same commit (rule 12/13).
- **Security-sensitive configuration** stays off the F2 clinic-profile
  Settings UI (ADR-002 §5.2/§6.6). RBAC administration is a **distinct,
  Administrator-only surface**, which this phase introduces — it is *not*
  a widening of the F2 Settings UI.
- RBAC does **not** elevate any deployment tier (ADR-002 §8.0): SQLite +
  Local Disk + Local Desktop stays the only Production-supported
  configuration; the single-machine-clinic-server rule and the SQLite
  network rule (§8.1) are untouched.

---

## 2. Decision — the role model

**DECIDED NOW.** A data-driven role model, seeded with five predefined
roles matching `docs/modules/Roles.md`:

| Role | Intended scope (`docs/CLINICAL_WORKFLOW.md`) |
| ---- | -------------------------------------------- |
| **Administrator** | Full access; the only role that may administer RBAC and hold all permissions. |
| **Doctor** | Consults: cases, visits, consultation workspace, patient clinical data. |
| **Reception** | Registers/books: patient registration, search, profiles, appointments (when built). |
| **Pharmacy** | Dispensing (when built); read of prescriptions. |
| **Accounts** | Billing (when built); read of the data billing needs. |

Roles live in a `roles` table (not hardcoded enum), so permission→role
assignments are editable by an Administrator without a code change. **These
five are the complete role set for Sprint 5; no additional roles are added
this phase (Product Owner, FINAL 2026-09-19).**

**OUT OF SCOPE — administrator-created custom roles (Product Owner, FINAL
2026-09-19).** `docs/modules/Roles.md` lists "Custom Roles" as a *target*
capability, and the data-driven model stays structurally compatible with a
future Administrator creating a brand-new role at runtime. **Sprint 5 does
not ship that capability** — no custom-role creation UI or workflow. Sprint
5 ships the five predefined roles with **configurable permission
assignments only**. The schema below remains compatible with future
configurable roles without change.

## 3. Decision — the permission model

**DECIDED NOW.** Permissions are **data-driven capability keys**, not
per-role code branches (`docs/modules/Roles.md`: "Keep permissions
data-driven so future modules add their own permission keys without code
changes to the RBAC core"). A permission key names a capability in a
stable `module.action` form, e.g.:

```
patients.view      patients.edit        registration.create
cases.view         cases.manage         visits.manage
consultation.view  consultation.edit    settings.edit
backup.run         audit.view           rbac.manage
```

- Each module **declares** the permission keys it owns (a registry the
  RBAC core reads), so a future module adds keys without editing RBAC.
- The **concrete Sprint 5 catalogue and the default role→permission
  matrix are FINAL** (Product Owner, 2026-09-19) and specified in
  `SPRINT5_TECHNICAL_PLAN.md` §5.2, derived only from functionality that
  exists today (no keys invented for unbuilt appointments/dispensing/
  billing/inventory/audit-viewing). This ADR fixes the *shape* (key format
  + data-driven registry); §5.2 fixes the *content*.
- `rbac.manage` is the permission that gates the RBAC administration
  surface itself. Administrator holds the complete Sprint 5 permission set.

## 4. Decision — role↔permission and user↔role relationships

**DECIDED NOW — schema shape** (additive tables via the F1 runner; a new
`v0003_rbac` migration):

```
roles            (id, name UNIQUE, description, is_system, created_at)
permissions      (id, key UNIQUE, description, created_at)
role_permissions (role_id FK, permission_id FK, PRIMARY KEY(role_id, permission_id))
user_roles       (user_id FK, role_id FK, PRIMARY KEY(user_id, role_id))
```

- `role_permissions` is the configurable many-to-many that makes
  permissions editable per role.
- `user_roles` binds users to roles. **Sprint 5 enforces exactly one
  active role per user (Product Owner, FINAL 2026-09-19)** — a single-role
  invariant. **No role aggregation or permission union across multiple
  active roles is implemented.** The join-table shape leaves multi-role
  support as a future additive capability with no schema change, but
  multi-role is **out of scope** this phase.
- `is_system` marks the seeded predefined roles (notably Administrator) so
  the management surface can protect them from deletion.

## 5. Decision — the existing `users.role` column

**DECIDED NOW — non-destructive.** The legacy `users.role TEXT` column is
**kept** (never dropped or renamed — Constitution Art. IV §2). It becomes
a **denormalized, non-authoritative** hint; `user_roles` is authoritative
for enforcement. The migration reads each existing `users.role` string and
creates the corresponding `user_roles` binding (see §6). Whether to
continue writing `users.role` for display convenience is an implementation
detail resolved in `SPRINT5_TECHNICAL_PLAN.md`; it never becomes an
enforcement input.

## 6. Decision — migration & safe admin handling

**DECIDED NOW.** The `v0003_rbac` migration is additive, idempotent, and
reversible (ADR-0008), and its data seed is **lockout-safe**:

1. Create the four tables (§4) with `CREATE TABLE IF NOT EXISTS`.
2. Seed the five predefined roles (§2) with `is_system = 1` for
   Administrator.
3. Seed the permission catalogue (§3).
4. Grant the Administrator role **every** permission (full access).
5. Grant the other four roles their scoped permission sets (§2).
6. **Map existing users:** for every row in `users`, create a `user_roles`
   binding from its legacy `role` string. The legacy seed value `"Admin"`
   (and any `"Administrator"` variant) maps to the **Administrator** role,
   so the existing `admin` account retains full access. Any user whose
   legacy role is null/unrecognized is handled per a documented, **non-
   locking** default resolved in the technical plan (never silently
   granted Administrator, never left able to lock the clinic out).

**Administrator-protection invariants (DECIDED NOW):**
- The Administrator role is `is_system` and **cannot be deleted**.
- The system guarantees **at least one active Administrator** exists: an
  operation that would remove/deactivate/demote the last active
  Administrator is denied (enforced in the RBAC service, audited).
- The default `admin`/`admin123` credential posture is **unchanged** by
  this phase (still "must be changed on first use" per `SECURITY.md`);
  RBAC does not touch credentials or account data.

## 7. Decision — enforcement boundary (depth)

**DECIDED NOW.** Authorization is enforced at **two seams**, matching
`docs/modules/Roles.md` and deliberately **not** adding a third layer for
theoretical completeness (per the Product Owner's enforcement-depth
directive):

1. **Router (route-level) — the primary seam.** The router already runs a
   session guard (`app/core/router.py`). It gains a **permission guard**:
   a guarded route declares a required permission key; the router resolves
   the current user's permissions and, if the required key is absent,
   renders a fail-closed "not authorized" outcome instead of the handler
   (§8). Route→permission association extends the existing per-module route
   registration (`ROUTES` tuples assembled in `bootstrap.py`) so a route
   cannot be added without an explicit authorization intent.
2. **Service / controller (action-level).** Sensitive operations that a
   route guard cannot fully capture — e.g. `backup.run`, `settings.edit`,
   destructive or privileged mutations, and RBAC administration itself —
   perform an explicit permission check in the service/controller layer,
   audited via `audit.service.log_action`.

**DEFERRED — repository / row-level access control.** `SECURITY.md` rule 4
names the **repository** as the enforcement seam for *row-level* access
control "when RBAC arrives." Sprint 5's roles do not require row scoping
(Doctor/Reception/etc. all operate over the single clinic's full data
set), so row-level filtering (which *rows* a user may see) is **not built
this phase**. The repository seam is preserved and documented as the home
for that future capability, needed only when multi-clinic, Patient Portal,
or per-doctor data partitioning is scheduled. Building it now would be an
unnecessary layer with no current requirement.

## 8. Decision — denial behavior

**DECIDED NOW — fail-closed, four cases FINAL (Product Owner, 2026-09-19);
full specification in `SPRINT5_TECHNICAL_PLAN.md` §8:**

1. **Authenticated user lacking the permission** — route: a friendly
   **"You don't have permission"** denial view (never the handler, never a
   traceback); action: a typed `AuthorizationError` → friendly snackbar,
   **no mutation**. Audited.
2. **Unauthenticated user** — the existing session guard runs first and
   diverts to `/login` (unchanged); the permission guard runs only after
   authentication.
3. **Nonexistent / unknown permission key** — denied for everyone
   (including Administrator): the key is in no resolved permission set, so
   the fail-closed guard denies it and the route-coverage test blocks such
   a route from shipping.
4. **Unknown / unrecognized legacy `users.role` at migration** — mapped to
   a documented **non-locking, zero-permission** state (no binding), never
   silently Administrator; the user lands on the denial view until an
   Administrator assigns a role. The clinic is never locked out (the
   at-least-one-active-Administrator invariant, §6, holds).

Every denial is **audited** (`audit_logs`, `SECURITY.md` rule 2). Sensitive
routes **must** carry an explicit permission before merge (route-coverage
assertion — `SPRINT5_TESTING_PLAN.md`); the only routes that need no
permission are `/login` (unauthenticated) and the logged-in landing
(`dashboard.view`, held by all five roles) — documented explicitly, not
left implicit.

## 9. Relationship with existing Settings (ADR-002 §6.6)

**DECIDED NOW.** The Sprint 4 **F2 clinic-profile Settings UI is not
widened.** RBAC administration (viewing roles, editing role→permission
assignments, assigning a role to an existing user) is a **separate,
Administrator-only surface** gated by `rbac.manage`. This honors ADR-002
§5.2/§6.6 (security-sensitive configuration never lives on the
clinic-profile Settings UI) and is the first concrete instance of the
"future RBAC-gated Administrator surface" those sections anticipated.
Database/storage/backup-destination/API-key configuration remains **out of
scope** even for this new surface (that still awaits F7 and a later phase).

## 10. Relationship with future networked/multi-user architecture

**DECIDED NOW — documentation invariant.** RBAC is a **prerequisite** for
networked surfaces (`SECURITY.md` rule 1, ADR-002 §11), **not** an enabler
of them. Shipping RBAC does **not** make networked/multi-user SQLite
Production-supported, does not change the ADR-002 §8.0 deployment-tier
table, and does not relax the §8.1 SQLite-over-network prohibition. Sprint
5 preserves that language verbatim.

## 11. What this ADR does NOT authorize (DEFERRED / OUT OF SCOPE)

- **F4 user management** as a feature (creating/deactivating users,
  resetting credentials). Sprint 5 includes only the *minimum RBAC
  administration* needed to assign existing users to roles and to
  configure role permissions — see the F4 boundary in
  `SPRINT5_RECOMMENDATION.md`.
- **F7 encryption at rest**, `provider_credentials`, API-key storage
  (ADR-002 §11 sequences these after RBAC).
- Runtime **custom-role creation** (Product Owner, FINAL — out of scope §2).
- **Multi-role per user** / role aggregation / permission union (Product
  Owner, FINAL — out of scope §4).
- **Row-level** access control (§7).
- AI, OCR, WhatsApp/messaging, payment, Cloud Sync, cloud/Docker/K8s
  deployment, any second database/storage adapter, any ORM/Alembic, any
  new runtime dependency.

## 12. Options considered

### Enforcement location
- **A — Router-only guards.** Simple, but cannot cover privileged actions
  that share a route with allowed ones (e.g. a mutation inside an
  otherwise-viewable screen). Rejected as insufficient alone.
- **B — Router + service/controller (recommended).** Route-level for
  navigation, action-level for sensitive operations. Matches
  `Roles.md`'s two named seams; testable; no obvious bypass. **Chosen.**
- **C — B plus repository row-level enforcement now.** Adds a third layer
  with no current row-scoping requirement. Rejected for Sprint 5 as an
  unnecessary layer; the seam is preserved for when it is needed (§7).

### Permission representation
- **A — Roles hardcoded to fixed permission sets in code.** Contradicts
  `Roles.md` ("permissions must be configurable, not hardcoded"). Rejected.
- **B — Data-driven `permissions` + `role_permissions` (recommended).**
  Configurable, module-extensible. **Chosen.**

### User↔role binding
- **A — `users.role_id` FK column.** Smallest change, but hardcodes
  single-role and needs a schema change to ever support multi-role.
- **B — `user_roles` join table (recommended).** Single-role enforced now,
  multi-role later without schema change; matches `Roles.md`'s "optionally
  `user_roles`". **Chosen.**

## 13. Risks

See `SPRINT5_RISK_ASSESSMENT.md` for the full table (likelihood/impact/
mitigation/verification). Headline risks:

| ID | Risk | Mitigation |
| -- | ---- | ---------- |
| RB1 | A sensitive route ships unguarded (authorization bypass) | Route-coverage test asserts every route in the registry has an explicit authorization intent (`SPRINT5_TESTING_PLAN.md`) |
| RB2 | Migration locks the clinic out (no usable Administrator) | Lockout-safe seed (§6) + at-least-one-active-Administrator invariant; migration test on a live-shaped DB |
| RB3 | Privilege escalation via unchecked service action | Action-level checks on sensitive/privileged operations (§7); denial audited |
| RB4 | UI hides a control but the server still allows it (UI/server mismatch) | Server-side checks are authoritative; UI hiding is convenience only; tests call services directly under a low-privilege role |
| RB5 | Intended golden change mistaken for a regression | New RBAC tables/indexes land with ADR + CHANGELOG + DECISIONS in the same commit; golden diff reviewed explicitly (rule 12/13) |
| RB6 | Scope creep into F4/F7/custom-roles/row-level | Non-goals fixed here and in `SPRINT5_RECOMMENDATION.md`; layering test extended to bar out-of-scope tech |

## 14. Migration guidelines (once implementation is approved)

- `v0003_rbac` is additive and reversible; `down` drops only the four new
  tables. The migration runner (ADR-0008) is unchanged — hand-written
  SQLite DDL, no ORM/Alembic (ADR-002 Revision 6).
- The new tables/indexes change the regression golden's `TABLES:`/
  `INDEXES:` lines **once, intentionally**, recorded in ADR + CHANGELOG +
  DECISIONS in the same commit (exactly as ADR-0009 did for
  `consultations`). No silent golden edit.
- No credential or account data is modified by the migration.

---

## Decision

**Adopt a data-driven RBAC architecture:** a `roles` table (five seeded
predefined roles, Administrator marked `is_system`), a data-driven
`permissions` catalogue with module-declared `module.action` keys,
configurable `role_permissions`, and a `user_roles` binding enforcing a
single active role per user (multi-role left additive). Enforce
authorization at **two seams** — the **router** (route-level permission
guard, extending the existing session guard) and the **service/controller**
layer (action-level checks for sensitive operations) — with **fail-closed,
audited** denial; **defer** repository row-level access control until a
row-scoping requirement exists. Migrate additively via a lockout-safe
`v0003_rbac` seed that maps the existing `admin` account to the
Administrator role and guarantees at least one active Administrator. Ship
RBAC administration as a **separate Administrator-only surface** (gated by
`rbac.manage`), **not** a widening of the F2 clinic-profile Settings UI.
RBAC **does not** change any ADR-002 deployment tier and is a
**prerequisite for**, never an **enabler of**, networked/multi-user
deployment. The concrete permission catalogue and default role→permission
matrix are FINAL in `SPRINT5_TECHNICAL_PLAN.md` §5.2; the four-case
fail-closed denial model is FINAL in §8. **Per the Product Owner's final
Sprint 5 decisions (2026-09-19): the five predefined roles are the complete
set; runtime custom-role creation is out of scope; user↔role cardinality is
one active role per user (no multi-role/aggregation); F4 user management
beyond minimum RBAC administration, F7 encryption, and row-level access
control are out of scope.** Await Product Owner approval before any
implementation.
