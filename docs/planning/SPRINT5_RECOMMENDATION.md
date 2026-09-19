# Sprint 5 — Recommendation

**Status:** Theme **APPROVED** (F3 RBAC); Product Owner scope decisions
**FINAL (2026-09-19)** and folded in below. Still **planning only —
implementation is NOT authorized** and begins only after the Product Owner
approves this revised package and the planning PR (#12) merges.
**Date:** 2026-09-18 · **Revision 1:** 2026-09-19 — Product Owner final
decisions applied (five-role set fixed; custom roles out; single active
role per user; F4/F7/row-level out; permission matrix finalized —
`SPRINT5_TECHNICAL_PLAN.md` §5.2).
**Theme:** **F3 RBAC — Role-Based Access Control**
**Depends on:** ADR-003 (RBAC), the F1 migration runner (Sprint 0), the
Sprint 4 `DatabaseAdapter`/`StorageProvider` seams (ADR-002).

---

## 1. Objective

Make `users.role` **enforced** instead of decorative: introduce a
data-driven role/permission model and a consistent, testable authorization
boundary so each staff type does only what its role permits — closing the
top security/compliance gap for a PHI system (L4) without changing the
database engine, storage backend, deployment tier, or adding any runtime
dependency.

## 2. Why RBAC is Sprint 5 (repository evidence)

This is the **documented recommendation**, consistent across every
authoritative source — not a model inference:

- `docs/planning/SPRINT4_RECOMMENDATION.md` §2: "**F3 RBAC is Sprint 5**,
  immediately following this phase."
- `.ai/NEXT_PHASE.md`: "Recommendation: Sprint 5 — RBAC (backlog F3)."
- `docs/architecture-decisions/ADR-002-Cloud-Ready-Architecture.md` §11:
  RBAC is sequenced *after* the Sprint 4 seams (so its enforcement is
  written against the final repository shape) and *before* F7 encryption
  and any Administrator/Security settings surface.
- `docs/SECURITY.md` rule 1: "RBAC (F3) and encryption at rest (F7) must
  land before any networked or multi-user surface."
- `docs/MASTER_BACKLOG.md` F3: "recommended next sprint (Sprint 5)."
- `docs/KNOWN_LIMITATIONS.md` L4 → F3.

RBAC is the only remaining **P1 foundation** item, the sole option **in
sequence** per ADR-002 §11, and the unlock for F7 encryption, the future
Administrator surface, and every networked/multi-user capability.

## 3. Problem statement

`users.role` is a free-text column that nothing enforces; the router's
only access control is a **session guard** (logged-in vs. not). Any
logged-in user can perform any action — a compliance gap for software
storing PHI (`docs/SECURITY.md`, `docs/KNOWN_LIMITATIONS.md` L4,
`docs/modules/Roles.md`). The Sprint 4 seams and the F1 migration runner
are now in place, so RBAC can be built once, against the final repository
and router shape, additively.

## 4. Product value

- Closes the highest-severity security/compliance gap (L4) for a PMS.
- Establishes least-privilege per staff role (Administrator/Doctor/
  Reception/Pharmacy/Accounts) mapped to the clinical workflow.
- Is a **hard prerequisite** for F7 encryption, the Administrator/Security
  configuration surface (ADR-002 §6.6), and any future Portal/Telemedicine/
  Sync/API surface.
- Makes future modules safer by default: a new module declares its
  permission keys and is gated from day one.

## 5. Scope (proposed — subject to Product Owner approval)

**In scope — F3 RBAC core:**
1. `roles` · `permissions` · `role_permissions` · `user_roles` tables via
   an additive `v0003_rbac` migration (F1 runner; ADR-0008).
2. Exactly five seeded predefined roles (Administrator/Doctor/Reception/
   Pharmacy/Accounts) — the complete Sprint 5 role set; Administrator marked
   `is_system`.
3. Data-driven permission catalogue with module-declared `module.action`
   keys and the **finalized default role→permission matrix**
   (`SPRINT5_TECHNICAL_PLAN.md` §5.2), derived only from functionality that
   exists today (no keys for unbuilt modules).
4. **One user → one active role**, enforced (no multi-role / aggregation;
   join-table shape leaves multi-role additive for a future phase).
5. **Route-level** authorization guard in `app/core/router.py` (extends the
   existing session guard); route→permission association in the per-module
   route registration.
6. **Action-level** authorization checks in services/controllers for
   sensitive operations (`backup.run`, `settings.edit`, RBAC
   administration, privileged/destructive mutations).
7. Fail-closed, **audited** denial behavior (friendly view/snackbar, never
   a raw error).
8. A **minimum Administrator-only RBAC management surface**
   (`app/modules/roles/`): view roles, edit role→permission assignments,
   assign an existing user to a role — gated by `rbac.manage`.
9. Lockout-safe migration mapping the existing `admin` account to
   Administrator, plus an at-least-one-active-Administrator invariant.
10. Tests (schema/domain, permission checks, route-coverage, denial/allow,
    migration + existing-admin migration, layering gate, intentional
    golden update).
11. Documentation (ADR-003; update `SECURITY.md`, `KNOWN_LIMITATIONS.md`
    L4, `CHANGELOG.md`, `DECISIONS.md`, `modules/Roles.md`,
    `TARGET_ARCHITECTURE.md`, `.ai/*`).

**Enforcement depth (per ADR-003 §7):** router (route-level) + service/
controller (action-level). **Repository row-level** access control is
**deferred** — no current row-scoping requirement; the seam is preserved
(`SECURITY.md` rule 4).

## 6. Non-goals (explicitly OUT OF SCOPE)

- **F4 user management** as a feature — creating/deactivating users,
  resetting credentials, editing account data. See §7 for the precise
  boundary between minimum RBAC administration and F4.
- **F7 encryption at rest**, `provider_credentials`, API-key/credential
  storage (ADR-002 §11 sequences these after RBAC).
- **Runtime administrator-created custom roles** — **OUT OF SCOPE**
  (Product Owner, FINAL 2026-09-19). Sprint 5 ships the five predefined
  roles with configurable permissions; no custom-role creation UI/workflow.
- **Multi-role per user** / role aggregation / permission union — **OUT OF
  SCOPE** (Product Owner, FINAL 2026-09-19). One user → one active role.
- **Repository row-level** access control (ADR-003 §7).
- AI, OCR, WhatsApp/messaging, payment, Cloud Sync, cloud/Docker/K8s
  deployment, PostgreSQL/MySQL/SQL Server or any second database adapter,
  non-local storage providers, ORM/Alembic, any new runtime dependency,
  any change to the Sprint 4 architecture or the deployment-tier table.

RBAC may **prepare** the architecture for future work (e.g. the
Administrator surface, the row-level seam) but must not **activate** those
future capabilities.

## 7. The F4 boundary — minimum RBAC administration vs. full user management

To make configurable RBAC **usable**, an Administrator must be able to:
(a) view roles, (b) edit role→permission assignments, and (c) assign an
**existing** user to a role. Item (c) requires *reading* the existing
users list and *writing* a `user_roles` row — it does **not** require
creating, deactivating, or editing user accounts or credentials.

| Capability | Sprint 5 (minimum RBAC admin) | F4 (deferred) |
| ---------- | :---------------------------: | :-----------: |
| View roles & permissions | ✅ | — |
| Edit role→permission assignments | ✅ | — |
| Assign an existing user to a role | ✅ | — |
| Create a new user account | ❌ | ✅ |
| Deactivate / reactivate a user | ❌ | ✅ |
| Reset / change another user's credentials | ❌ | ✅ |

**Rule:** Sprint 5 ships (a)–(c) only. Anything that creates or mutates
user *accounts/credentials* is F4 and stays out of scope. The minimum
capability must not silently grow into the full feature.

## 8. Dependencies

Satisfied prerequisites: F1 migration runner (Sprint 0 ✅), Sprint 4
`DatabaseAdapter`/`StorageProvider` seams (✅ — the reason RBAC was
sequenced to Sprint 5, ADR-002 §11).

Downstream (must follow, not precede): F7 encryption → `provider_credentials`
/ AI Gateway → the full Administrator/Security configuration surface →
networked/Portal/Sync surfaces.

## 9. Risks (summary)

Full analysis in `SPRINT5_RISK_ASSESSMENT.md`. Headline: authorization
bypass (unguarded route), migration lockout, privilege escalation via
unchecked action, UI/server enforcement mismatch, intended-golden-change
misread as regression, scope creep. Each has a mitigation and a
verification method.

## 10. Architectural constraints (preserved)

- Dependency direction and "SQL only in repositories" unchanged.
- Additive, reversible, idempotent migration; no destructive schema change;
  `users.role` kept (never dropped).
- No new runtime dependency (layering gate extended to keep
  `requirements.txt == {flet, bcrypt}`).
- **RBAC does not change any ADR-002 §8.0 deployment tier**; SQLite +
  Local Disk + Local Desktop stays the only Production-supported
  configuration; the SQLite-over-network prohibition (§8.1) is untouched.
- F2 clinic-profile Settings UI is **not** widened (ADR-002 §6.6).

## 11. Acceptance criteria

1. `users.role` is enforced: a non-Administrator role is denied a route/
   action outside its permission set, and allowed within it.
2. Every route in the assembled registry carries an explicit authorization
   intent (guarded with a permission key, or explicitly marked as
   requiring only a session) — proven by the route-coverage test.
3. Sensitive actions (`backup.run`, `settings.edit`, `rbac.manage`) are
   checked at the service/controller layer; denial is audited.
4. The `v0003_rbac` migration is additive and reversible; applying it to a
   database seeded by `v0001`/`v0002` maps the existing `admin` account to
   Administrator with full access (no lockout).
5. At least one active Administrator is always guaranteed; the last one
   cannot be removed/demoted.
6. RBAC administration lives on a separate Administrator-only surface, not
   the F2 Settings UI.
7. The regression golden changes **only** by the intentional new RBAC
   tables/indexes (and any documented new route), recorded in ADR +
   CHANGELOG + DECISIONS in the same commit.
8. `python3 -m pytest -q` green (56 prior + new RBAC tests); layering
   gates pass; no new runtime dependency; no out-of-scope tech imported.
9. Deployment-tier documentation is unchanged (RBAC does not make
   networked/multi-user SQLite Production-supported).

## 12. Sequencing (implementation order — see `SPRINT5_MILESTONE_CHECKLIST.md`)

ADR/schema decision → migration + domain foundation → permission
infrastructure (registry + permission-check API) → router guard +
action-level enforcement → RBAC management surface → tests → documentation
→ final verification. Each milestone leaves the app runnable and the suite
green.

## 13. Alternatives considered

1. **F7 encryption first** — also urgent, but ADR-002 §11 sequences it
   *after* RBAC. Rejected for Sprint 5.
2. **Consultation Workspace feeders (Protocol/Printer/OCR)** — higher
   clinical value, but `.ai/NEXT_PHASE.md` notes they are better built with
   RBAC already gating who can use them. Rejected for Sprint 5.
3. **RBAC bundled with F4 user management** — larger surface; violates the
   Constitution's "small, reviewable commits" and this document's risk
   discipline (mirrors `SPRINT4_RECOMMENDATION.md` CR6). F4 deferred.

## 14. Do not start until

The Product Owner approves this recommendation, ADR-003, and the Sprint 5
technical/file-map/risk/testing/milestone documents. Per the Constitution
(Article IX §3), no phase begins automatically.
