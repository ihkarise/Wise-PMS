# EPIC-22 — Multi-Clinic

> **Spec:** [`../USER_ROLES.md`](../USER_ROLES.md),
> [`../MASTER_PHASE_PLAN.md`](../MASTER_PHASE_PLAN.md) · **Backlog:** — ·
> **Stage:** E — Platform · **Depends on:** EPIC-01, EPIC-03 ·
> **Complexity:** L · **Risk:** Medium · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. VIII §5.

## 1. Objective

Scope data, users, and roles per clinic as an **additive dimension** (migration),
not a rewrite. Single-clinic remains the default (nullable scope). Enables group
practices / franchising.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E22-F1 | Clinic dimension | Additive `clinic_id` scoping across relevant tables |
| E22-F2 | Clinic-scoped RBAC | Roles clinic-scoped or global (Administrator) |
| E22-F3 | Repository-seam scoping | Enforce clinic scope at the choke point |
| E22-F4 | Single-clinic default | Nullable scope; existing deployments unchanged |

## 3. User stories

- **E22-F1-S1** — As a group owner, I want data scoped per clinic, so that clinics
  don't see each other's records.
- **E22-F2-S1** — As a group admin, I want clinic-scoped roles, so that staff act
  only within their clinic.
- **E22-F4-S1** — As an existing single clinic, I want no disruption, so that
  multi-clinic support doesn't change my setup.

## 4. Engineering tasks

- **E22-T1** — Migration: additive `clinic_id` on relevant tables (nullable →
  default clinic).
- **E22-T2** — Clinic-scoped RBAC (extend EPIC-03); global Administrator.
- **E22-T3** — Repository-seam scoping (reuse the RBAC/sync choke point).
- **E22-T4** — Clinic management (Administrator); tests + docs (USER_ROLES,
  ARCHITECTURE, DECISIONS ADR).

## 5. Dependencies

- **Upstream:** EPIC-01 (migration), EPIC-03 (RBAC). Pairs with EPIC-20 (sync
  across clinics).
- **Downstream:** none (terminal platform capability).

## 6. Acceptance criteria

- **AC1** — *Given* multiple clinics, *when* a user acts, *then* they see/act only
  within their clinic scope (repository-enforced).
- **AC2** — *Given* a global Administrator, *when* acting, *then* cross-clinic
  access is permitted per role.
- **AC3** — *Given* an existing single-clinic DB, *when* upgraded, *then* scope
  defaults transparently with no disruption.
- **AC4** — *Given* clinic-scoped roles, *when* assigned, *then* they apply only in
  that clinic.

## 7. Regression tests

- **Must stay green:** golden, models, router, views (single-clinic path
  unchanged).
- **New:** clinic-scoping tests (isolation), global-admin tests, default-scope
  upgrade test, model/table parity for new columns.

## 8. Rollout phases

- **E22-R1** — Additive `clinic_id` migration + default clinic (no behavior
  change).
- **E22-R2** — Repository-seam scoping + clinic-scoped RBAC.
- **E22-R3** — Clinic management screen; docs closeout.

## 9. Rollback

Revert scoping enforcement → single-clinic default (nullable scope). Additive
columns inert. No data destroyed.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: single-clinic behavior unchanged; scope
enforced at the repository seam; upgrade transparent.
</content>
