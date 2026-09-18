# Sprint 5 — Milestone Checklist (F3 RBAC)

**Status:** PROPOSED — Product Owner review. **Planning only.** These are
the *implementation* milestones, in dependency order. **None is started;
implementation is not authorized.**
**Date:** 2026-09-18

Each milestone leaves the app runnable and the suite green (except the one
intentional, documented golden update in M2, shipped with its ADR/CHANGELOG/
DECISIONS in the same commit). Follows the Constitution's "small,
reviewable, runnable commits."

---

## M0 — Planning approval (this phase)
- [x] ADR-003 drafted (role/permission model, enforcement seams, migration,
      admin handling, denial, Settings/deployment relationships;
      DECIDED-NOW vs DEFERRED separated).
- [x] `SPRINT5_RECOMMENDATION.md`, `SPRINT5_TECHNICAL_PLAN.md`,
      `SPRINT5_FILE_MAP.md`, `SPRINT5_RISK_ASSESSMENT.md`,
      `SPRINT5_TESTING_PLAN.md`, this checklist drafted.
- [ ] **Product Owner approves** ADR-003 + the planning package, and
      resolves the open decisions (custom roles; user↔role cardinality;
      permission→role default mapping).
- [ ] Planning PR merged. *(Gate: implementation does not begin until here.)*

## M1 — Migration + domain foundation
- [ ] `v0003_rbac` migration: `roles`/`permissions`/`role_permissions`/
      `user_roles` (+ indexes), additive/idempotent/reversible; registered.
- [ ] `app/modules/roles/models.py` (`RowModel`).
- [ ] Idempotent seed: five roles, permission catalogue, Administrator ←
      all permissions, scoped grants, existing-user mapping (legacy `"Admin"`
      → Administrator).
- [ ] `test_rbac_domain.py`: migration additivity/reversibility + existing-
      admin migration (no lockout) green.
- [ ] Intentional golden update (`TABLES:`/`INDEXES:`) shipped **in this
      commit** with ADR-003 + CHANGELOG + DECISIONS (rule 12/13).

## M2 — Permission infrastructure
- [ ] `app/modules/roles/permissions.py` — data-driven registry; modules
      declare their keys.
- [ ] `app/modules/roles/repository.py` — RBAC SQL.
- [ ] `app/modules/roles/service.py` — `user_has_permission` /
      `require_permission`, `AuthorizationError`, assignment rules,
      **at-least-one-active-Administrator** invariant, audit.
- [ ] `test_rbac_domain.py` invariants green.

## M3 — Authorization enforcement
- [ ] Router permission guard in `app/core/router.py` (after the session
      guard); route→permission association in registration + `bootstrap.py`.
- [ ] Fail-closed audited denial outcome.
- [ ] Action-level checks: `settings.edit`, `backup.run`, and privileged
      mutations.
- [ ] Permission-set resolution at login (session-stashed).
- [ ] `test_rbac_enforcement.py`: **route-coverage** + allow/deny +
      action-level + **direct-service-call denial** green; `test_router.py`
      extended.

## M4 — RBAC management surface (minimum admin, gated by `rbac.manage`)
- [ ] `app/modules/roles/controller.py` + `view.py`: roles list,
      role→permission matrix editor, assign existing user to a role.
- [ ] Route (e.g. `^/admin/roles$`) registered; **not** a widening of the F2
      Settings UI.
- [ ] Boundary held: **no** user create/deactivate/credential change (F4
      stays out — `SPRINT5_RECOMMENDATION.md` §7).

## M5 — Tests & layering gates
- [ ] Full `pytest -q` green (56 prior + new).
- [ ] `test_layering.py` extended: authorization single-source; no new
      runtime dependency (`{flet, bcrypt}`); out-of-scope tech absent.

## M6 — Documentation
- [ ] `docs/DECISIONS.md` — ADR-0011 ledger entry (Accepted, Sprint 5).
- [ ] `docs/SECURITY.md` — RBAC implemented; seams; keep row-level as future.
- [ ] `docs/KNOWN_LIMITATIONS.md` — close **L4**.
- [ ] `docs/CHANGELOG.md`, `docs/modules/Roles.md`,
      `docs/TARGET_ARCHITECTURE.md`, `docs/MASTER_BACKLOG.md` (close **F3**).
- [ ] `.ai/*` updated.
- [ ] **Deployment-tier docs unchanged** — verify RBAC did not alter any
      ADR-002 §8.0 tier or the §8.1 SQLite-over-network rule.

## M7 — Final verification
- [ ] `main`-parity check; working tree clean.
- [ ] `pytest -q` green; layering gates pass; golden matches the intended
      new baseline (only the documented RBAC delta).
- [ ] Acceptance criteria (`SPRINT5_RECOMMENDATION.md` §11) all met.
- [ ] No scope creep vs. the non-goals (F4/F7/custom-roles/row-level/
      multi-role absent unless the Product Owner elected them).
- [ ] Implementation PR opened for Product Owner review (not self-merged).

---

**Dependency order:** M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7. M3 depends on
M2's permission-check API; M4 depends on M3's guard; M1's golden change is
the only intentional regression-baseline edit and is self-contained in its
commit.
