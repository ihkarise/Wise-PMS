# Sprint 5 — Risk Assessment (F3 RBAC)

**Status:** PROPOSED — Product Owner review. **Planning only.**
**Date:** 2026-09-18

Likelihood × Impact each rated Low / Medium / High. Every risk carries a
mitigation and a **verification method** (how we prove the mitigation
holds).

---

## R1 — Authorization bypass (a sensitive route/action ships unguarded)
- **Likelihood:** Medium (many routes across eight modules; easy to miss one).
- **Impact:** High (an unguarded sensitive route defeats RBAC entirely).
- **Mitigation:** Route→permission association is part of route registration;
  the router treats an un-annotated route as **fail-closed** except where a
  route is *explicitly* whitelisted as session-only. Action-level checks on
  privileged mutations (`SPRINT5_TECHNICAL_PLAN.md` §7).
- **Verification:** `tests/test_rbac_enforcement.py` **route-coverage test**
  asserts every route in the assembled `bootstrap.ROUTES` has an explicit
  authorization intent (a permission key, or an explicit session-only mark);
  a new unannotated route fails the suite.

## R2 — Route-coverage drift (a future route added without a permission)
- **Likelihood:** Medium (new modules land over time).
- **Impact:** High (silent bypass introduced later).
- **Mitigation:** The route-coverage test is a standing gate, not a one-off;
  the un-annotated-route default is fail-closed.
- **Verification:** The same route-coverage test runs in the suite on every
  change; layering/registration convention documented in `Roles.md`.

## R3 — Privilege escalation via an unchecked service/repository action
- **Likelihood:** Medium.
- **Impact:** High (a low-privilege user performs a privileged mutation
  through a shared route or a direct service call).
- **Mitigation:** Sensitive operations call
  `roles.service.require_permission` at the service/controller layer
  (`backup.run`, `settings.edit`, `rbac.manage`, privileged mutations);
  the Administrator-only invariants live in the service.
- **Verification:** `tests/test_rbac_enforcement.py` calls those services
  **directly** under a low-privilege role and asserts `AuthorizationError`
  and no mutation (i.e. UI hiding is not relied upon).

## R4 — Migration lockout (no usable Administrator after upgrade)
- **Likelihood:** Low (with the lockout-safe seed) / High (if done naively).
- **Impact:** Critical (clinic cannot administer the system).
- **Mitigation:** Lockout-safe seed (`SPRINT5_TECHNICAL_PLAN.md` §6):
  Administrator role gets all permissions; existing `admin` (legacy role
  `"Admin"`) maps to Administrator; unrecognized legacy roles get a
  documented non-locking default (never silent Administrator, never a state
  that can lock the clinic out).
- **Verification:** A migration test applies `v0003_rbac` to a database
  seeded by `v0001`/`v0002` and asserts the `admin` account resolves to
  Administrator with full permissions and can reach every route.

## R5 — Administrator recovery / last-admin removal
- **Likelihood:** Low.
- **Impact:** Critical (an Administrator demotes/deactivates the last
  Administrator and no one can administer RBAC).
- **Mitigation:** At-least-one-active-Administrator invariant in the RBAC
  service denies removing/demoting the last active Administrator; the
  Administrator role is `is_system` and undeletable.
- **Verification:** Domain test asserts the invariant (attempt to remove the
  last admin is denied and audited); credentials/account data untouched
  (default `admin`/`admin123` posture unchanged).

## R6 — Regression risk (intended golden change mistaken for a regression, or
Administrator behavior accidentally altered)
- **Likelihood:** Medium.
- **Impact:** Medium.
- **Mitigation:** New RBAC tables/indexes change the golden `TABLES:`/
  `INDEXES:` lines **once, intentionally**, shipped with ADR-003 + CHANGELOG
  + DECISIONS in the same commit (rule 12/13, as ADR-0009 did). Administrator
  holds all permissions, so non-schema snapshot content stays byte-identical.
- **Verification:** Explicit review of the golden diff; the rest of the
  snapshot stays byte-identical; `test_router.py` admin path unchanged.

## R7 — UI/server enforcement mismatch (UI hides a control but the server
still allows the action)
- **Likelihood:** Medium.
- **Impact:** High (hiding ≠ enforcing).
- **Mitigation:** Server-side checks (router + service) are **authoritative**;
  UI hiding/disabling is convenience only and never the enforcement point
  (ADR-003 §7, RB4).
- **Verification:** Enforcement tests bypass the UI and call services/routes
  directly under a low-privilege role; denial must hold without any UI.

## R8 — Scope creep (RBAC pulls in F4 / F7 / custom roles / row-level)
- **Likelihood:** Medium (RBAC is a classic magnet — mirrors
  `SPRINT4_RECOMMENDATION.md` CR6).
- **Impact:** Medium (risk-budget and reviewability blown).
- **Mitigation:** Non-goals fixed in ADR-003 §11 and
  `SPRINT5_RECOMMENDATION.md` §6/§7; the F4 boundary table; enforcement
  depth capped at two seams.
- **Verification:** `test_layering.py` extended to bar out-of-scope tech and
  hold `requirements.txt == {flet, bcrypt}`; the milestone checklist's final
  gate checks the diff against the non-goals.

## R9 — New runtime dependency introduced
- **Likelihood:** Low.
- **Impact:** Medium (violates the ₹0/offline posture; ADR-002 constraints).
- **Mitigation:** RBAC needs no new library (plain SQL + `RowModel` +
  existing router/Flet).
- **Verification:** `test_layering.py`'s dependency assertion
  (`requirements.txt == {flet, bcrypt}`).

## R10 — Deployment-tier misstatement (RBAC read as enabling networked/
multi-user SQLite)
- **Likelihood:** Low.
- **Impact:** High (safety/compliance misstatement; contradicts ADR-002 §8).
- **Mitigation:** ADR-003 §10 documentation invariant: RBAC is a
  prerequisite for, not an enabler of, networked surfaces; the §8.0 tier
  table and §8.1 SQLite-over-network rule are untouched.
- **Verification:** Docs review confirms no deployment-tier change; the
  Sprint 5 doc set repeats the tier language verbatim.

---

## Risk summary

| ID | Risk | L | I | Residual after mitigation |
| -- | ---- | - | - | ------------------------- |
| R1 | Unguarded route (bypass) | M | H | Low (route-coverage test) |
| R2 | Coverage drift over time | M | H | Low (standing gate, fail-closed default) |
| R3 | Privilege escalation via action | M | H | Low (action checks + direct-call tests) |
| R4 | Migration lockout | L | Crit | Low (lockout-safe seed + test) |
| R5 | Last-admin removal | L | Crit | Low (invariant + test) |
| R6 | Golden/Administrator regression | M | M | Low (intentional documented golden) |
| R7 | UI/server mismatch | M | H | Low (server authoritative; bypass tests) |
| R8 | Scope creep | M | M | Low (non-goals + layering gate) |
| R9 | New dependency | L | M | Low (dependency assertion) |
| R10 | Deployment-tier misstatement | L | H | Low (doc invariant) |

The dominant risks (R1–R3, R7) all reduce to the same discipline: the
**server** is the enforcement point, and **tests bypass the UI** to prove
it. R4/R5 reduce to the lockout-safe seed and the last-admin invariant,
each with a dedicated test.
