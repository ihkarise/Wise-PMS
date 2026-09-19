# Sprint 5 — Testing Plan (F3 RBAC)

**Status:** PROPOSED — Product Owner review. **Planning only; no test is
written or modified now.** The golden snapshot is **not** touched during
planning.
**Date:** 2026-09-18

> Builds on the Sprint 4 suite (56 passing): `test_regression.py` (golden),
> `test_router.py` (routing contract), `test_layering.py` (boundary gates),
> `test_models.py`, `test_migrations.py`, plus the domain suites. RBAC adds
> two new files and extends three existing ones.

---

## 1. New test files

### `tests/test_rbac_domain.py`
| Test | Asserts |
| ---- | ------- |
| Role creation / seeding | The five predefined roles exist after migration; Administrator is `is_system`. |
| Permission creation / catalogue | The seeded permission keys exist; keys are `module.action`. |
| Role→permission assignment | `set_role_permissions` persists and reads back; Administrator has all permissions. |
| User→role assignment | `assign_user_role` binds a user; `permissions_for_user` returns the role's permissions; single active role enforced. |
| Administrator permissions | Administrator resolves to the full permission set. |
| Last-admin invariant | Removing/demoting the last active Administrator is denied and audited (R5). |
| Administrator role protection | Administrator role cannot be deleted / stripped below usable (R5). |
| Migration additivity/reversibility | `v0003_rbac` `up` then `down` leaves `users` (and its `role` column) intact; tables created then dropped. |
| **Existing-admin migration** | Applying `v0003_rbac` to a `v0001`/`v0002`-seeded DB maps the existing `admin` (legacy role `"Admin"`) to Administrator with full access — **no lockout** (R4). |
| Unrecognized legacy role | Maps to the documented non-locking default; never silent Administrator (R4). |

### `tests/test_rbac_enforcement.py`
| Test | Asserts |
| ---- | ------- |
| **Route coverage (anti-bypass keystone)** | Every route in `app.bootstrap.ROUTES` has an explicit authorization intent (a permission key or an explicit session-only mark). A route with neither fails this test (R1/R2). |
| Allowed access (matrix-driven) | For each of the five roles, every route/action **granted** in the final matrix (`SPRINT5_TECHNICAL_PLAN.md` §5.2) dispatches to the real handler / performs the op. Table-driven from the matrix so a matrix change updates the test data, not the logic. |
| Denied access (matrix-driven) | For each role, every route/action **not granted** in §5.2 renders the fail-closed denial (not the handler), under a `MagicMock` page like `test_router.py`. Explicitly asserts Pharmacy/Accounts reach only `dashboard.view`. |
| Denial cases (all four) | The four §8 denial cases: authenticated-without-permission (deny), unauthenticated (→ `/login`), unknown permission key (deny for all incl. admin), unknown legacy role (zero-permission landing). |
| Action-level allow/deny | `settings.edit`, `backup.run`, `rbac.manage` succeed for a permitted role and raise `AuthorizationError` for a denied one. |
| **Direct service/repository call denial** | Calling a guarded service **directly** (bypassing the UI/router) under a low-privilege user raises `AuthorizationError` and performs **no mutation** — proving UI hiding is not the enforcement (R3/R7). |
| Denial is audited | A denied attempt writes an `audit_logs` row (`SECURITY.md` rule 2). |
| Admin unchanged | Administrator reaches every route/action (behavior-preserving). |

## 2. Extended existing tests

### `tests/test_router.py`
- Keep the existing routing-contract cases (admin path unchanged).
- Add: a low-privilege user denied on a guarded route → denial outcome; a
  permitted user reaches the handler. Reuse the existing `MagicMock` page +
  `_setup()` seam.

### `tests/test_layering.py`
- Extend the boundary gates:
  - **Authorization single-source:** permission decisions are made only via
    `roles.service` (`user_has_permission`/`require_permission`) — no ad-hoc
    `role ==` string comparisons scattered across modules. **[UNRESOLVED —
    exact check]** (AST/grep for authoritative-check usage); decide at
    implementation.
  - **No new runtime dependency:** `requirements.txt == {flet, bcrypt}`
    (extends the existing assertion) (R9).
  - **Out-of-scope tech absent:** the existing banned-module set still holds
    (no ORM/cloud SDK) (R8).

### `tests/test_regression.py` (golden — intentional, documented change)
- The new RBAC tables and indexes change the `TABLES:` and `INDEXES:` lines
  **once, intentionally**. Concrete expected change:
  - **Current** `TABLES:`
    `attachments,audit_logs,consultations,patient_cases,patients,prescription_items,schema_version,settings,sqlite_sequence,users,visits`
  - **After Sprint 5** `TABLES:` (adds `permissions,role_permissions,roles,user_roles` in alphabetical position):
    `attachments,audit_logs,consultations,patient_cases,patients,permissions,prescription_items,role_permissions,roles,schema_version,settings,sqlite_sequence,user_roles,users,visits`
  - **Current** `INDEXES:`
    `idx_attach_patient,idx_case_patient,idx_consultation_patient,idx_consultation_visit,idx_patient_name,idx_patient_phone,idx_patient_place,idx_patient_regno,idx_visit_case,idx_visit_date,idx_visit_patient`
  - **After Sprint 5** `INDEXES:` adds the new RBAC indexes (e.g.
    `idx_role_permissions_role`, `idx_user_roles_user`) in alphabetical
    position; the **exact** index names are finalized with the `v0003_rbac`
    migration and this line is updated to match in the same commit.
- If the snapshot enumerates routes, the new `^/admin/roles$` route adds one
  documented line.
- The updated `EXPECTED` ships in the **same commit** as `v0003_rbac`, with
  ADR-003 + CHANGELOG + DECISIONS (rule 12/13) — exactly the pattern
  ADR-0009 used for `consultations`. **The rest of the snapshot stays
  byte-identical** (Administrator holds all permissions).
- **During planning the golden is not modified.**

## 3. Coverage map (every in-scope item has a test)

| In-scope item (`SPRINT5_RECOMMENDATION.md` §5) | Test(s) |
| ---------------------------------------------- | ------- |
| Tables/migration | `test_rbac_domain` (additivity/reversibility, migration) |
| Predefined roles | `test_rbac_domain` (role seeding) |
| Data-driven permissions | `test_rbac_domain` (catalogue, assignment) |
| Single active role | `test_rbac_domain` (user→role) |
| Route-level guard | `test_rbac_enforcement` (route coverage, allow/deny), `test_router` |
| Action-level checks | `test_rbac_enforcement` (action allow/deny, direct-call denial) |
| Fail-closed audited denial | `test_rbac_enforcement` (denied access, audited) |
| RBAC admin surface | `test_rbac_enforcement` (`rbac.manage` gate), route coverage of `^/admin/roles$` |
| Lockout-safe migration | `test_rbac_domain` (existing-admin migration) |
| Last-admin invariant | `test_rbac_domain` |
| No new dependency / in-scope | `test_layering` |
| Intentional golden | `test_regression` (documented update) |

## 4. Verification commands (implementation phase)

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q          # 56 prior + new RBAC tests, all green
python3 tests/test_layering.py    # boundary gates
python3 tests/test_regression.py  # golden matches the intended new baseline
```

## 5. Exit criteria
All of §1–§2 green; layering gates pass; the golden matches the intended
new baseline (and only by the documented RBAC delta); no new runtime
dependency; deployment-tier docs unchanged. Ties to
`SPRINT5_RECOMMENDATION.md` §11 acceptance criteria.
