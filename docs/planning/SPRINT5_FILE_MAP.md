# Sprint 5 — File Map (F3 RBAC)

**Status:** PROPOSED — Product Owner review. **Planning only.** This maps
what a Sprint 5 *implementation* would create/modify. **None of these files
is modified by the planning PR** (the planning PR touches only the
planning/documentation artifacts in the last table).
**Date:** 2026-09-18

> Grounded in the current tree (verified `main` HEAD `eb9fb92`). Route
> inventory assembled in `app/bootstrap.py`; enforcement seams are
> `app/core/router.py` (route-level) and services/controllers
> (action-level).

---

## 1. Files to CREATE (implementation phase — not now)

| Path | Purpose |
| ---- | ------- |
| `app/core/migrations/v0003_rbac.py` | Additive/reversible migration: `roles`, `permissions`, `role_permissions`, `user_roles` (+ indexes) and idempotent seed (roles/permissions/grants + existing-user mapping). Registered in `app/core/migrations/registry.py`. |
| `app/modules/roles/__init__.py` | New vertical slice package. |
| `app/modules/roles/models.py` | `Role`, `Permission`, `RolePermission`, `UserRole` (`RowModel`). |
| `app/modules/roles/repository.py` | All RBAC SQL (list/get, permissions-for-user, set-role-permissions, assign-user-role, count-active-admins). |
| `app/modules/roles/service.py` | `user_has_permission`/`require_permission`, assignment rules, at-least-one-active-Administrator invariant, audit; raises `AuthorizationError`. |
| `app/modules/roles/permissions.py` | The permission-key registry + module-declared keys (data-driven catalogue). |
| `app/modules/roles/controller.py` | `ROUTES` for the Administrator-only RBAC surface (e.g. `^/admin/roles$`); orchestrates view ↔ service; gated by `rbac.manage`. |
| `app/modules/roles/view.py` | Flet view: roles list, role→permission matrix editor, assign-existing-user-to-role. |
| `app/shared/errors.py` *(or reuse an existing home)* | `AuthorizationError` type. **[UNRESOLVED — placement]** may live in `roles/service.py` or a shared module; decide at implementation. |
| `tests/test_rbac_domain.py` | Role/permission/assignment + invariants + migration + existing-admin migration. |
| `tests/test_rbac_enforcement.py` | Allow/deny per role, route-coverage, action-level, direct-service-call denial. |

## 2. Files to MODIFY (implementation phase — not now)

| Path | Change |
| ---- | ------ |
| `app/core/router.py` | Add the **permission guard** after the existing session guard; resolve a route's required permission; render fail-closed denial (§8) on failure. Keep the router generic (no per-route conditionals). |
| `app/bootstrap.py` | Import and append `ROLES_ROUTES`; carry route→permission association into the assembled `ROUTES` table (mechanism per `SPRINT5_TECHNICAL_PLAN.md` §7.1). |
| `app/modules/*/controller.py` (each with `ROUTES`) | Declare each route's required permission (or explicitly mark session-only). Modules: `authentication`, `dashboard`, `registration`, `patients`, `cases`, `visits`, `consultation`, `settings`. |
| `app/modules/settings/service.py` | Add `require_permission(user, "settings.edit")` on write. |
| `app/modules/backup/service.py` | Add `require_permission(user, "backup.run")` on the backup action. |
| `app/modules/authentication/service.py` and/or the login controller | Resolve and stash the user's permission set at login (per `SPRINT5_TECHNICAL_PLAN.md` §4.2). **[UNRESOLVED — placement]**. |
| `app/core/database.py` | **Only if** the RBAC seed lives in the Python `init_db()` seed rather than the migration (`SPRINT5_TECHNICAL_PLAN.md` §2.4 — unresolved). Preferred: seed in the migration, leaving this file untouched. |
| `tests/test_regression.py` | Intentional, documented golden update: new RBAC tables/indexes in `TABLES:`/`INDEXES:` (and any new route line). **Same commit** as the migration, with ADR + CHANGELOG + DECISIONS (rule 12/13). |
| `tests/test_router.py` | Add permission-guard cases (admin path unchanged; low-privilege denial added). |
| `tests/test_layering.py` | Extend the boundary gates for RBAC (e.g. authorization only via `roles.service`; no new runtime dependency; no out-of-scope tech) — see `SPRINT5_TESTING_PLAN.md` §Layering. |

## 3. Files explicitly NOT to modify

| Path | Why |
| ---- | --- |
| `app/core/db_adapters/*`, `app/core/storage/*` | Sprint 4 seams; RBAC is additive above them. No engine/storage change. |
| `app/core/migrations/runner.py` | Migration runner unchanged (ADR-0008; ADR-002 Revision 6 — no ORM/Alembic). Only a new `v0003_*` migration + its registry line. |
| `app/core/migrations/v0001_initial.py`, `v0002_consultations.py` | Never edit an applied migration (additive-only history). `users.role` column stays. |
| `app/modules/settings/view.py` / Settings UI scope | F2 clinic-profile Settings UI is **not** widened (ADR-002 §6.6). RBAC admin is a separate surface. |
| `requirements.txt` / `requirements-dev.txt` | No new runtime dependency (layering gate asserts `{flet, bcrypt}`). |
| Deployment docs (`docs/DEPLOYMENT.md` tiers) | RBAC does not change any ADR-002 §8.0 deployment tier. |

## 4. Documentation to UPDATE (implementation phase — not now)

| Path | Change |
| ---- | ------ |
| `docs/DECISIONS.md` | Add the **ADR-0011** ledger entry (summary of ADR-003), "Accepted (Sprint 5)", at implementation — matching how ADR-0010 recorded ADR-002. |
| `docs/SECURITY.md` | Move "No RBAC" from "NOT protected" to implemented; note the two enforcement seams; keep rule 4 (repository = future row-level seam). |
| `docs/KNOWN_LIMITATIONS.md` | Close **L4**; move to changelog. |
| `docs/CHANGELOG.md` | Sprint 5 entry (RBAC; intentional golden change). |
| `docs/modules/Roles.md` | Status: implemented; final role/permission model, seams, admin surface, F4 boundary. |
| `docs/TARGET_ARCHITECTURE.md` | Mark Administration/RBAC row built; add `app/modules/roles/` to the folder map. |
| `docs/MASTER_BACKLOG.md` | Close **F3**; note F4 still depends on it. |
| `.ai/CURRENT_PHASE.md`, `.ai/NEXT_PHASE.md`, `.ai/NEXT_TASK.md`, `.ai/DECISION_LOG.md` | Reflect Sprint 5 implementation state. |

## 5. Planning PR — the ONLY files changed now

| Path | Status |
| ---- | ------ |
| `docs/architecture-decisions/ADR-003-Role-Based-Access-Control.md` | CREATE |
| `docs/planning/SPRINT5_RECOMMENDATION.md` | CREATE |
| `docs/planning/SPRINT5_TECHNICAL_PLAN.md` | CREATE |
| `docs/planning/SPRINT5_FILE_MAP.md` | CREATE (this file) |
| `docs/planning/SPRINT5_RISK_ASSESSMENT.md` | CREATE |
| `docs/planning/SPRINT5_TESTING_PLAN.md` | CREATE |
| `docs/planning/SPRINT5_MILESTONE_CHECKLIST.md` | CREATE |
| `.ai/CURRENT_PHASE.md`, `.ai/NEXT_PHASE.md`, `.ai/NEXT_TASK.md` | MODIFY (planning-state pointers only) |

**No `app/` code, no `tests/`, no migration, no golden is modified by the
planning PR.**
