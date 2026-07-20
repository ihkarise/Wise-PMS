# EPIC-21 — Mobile App & Public API

> **Spec:** [`../../docs/API.md`](../../docs/API.md) · **Backlog:** — ·
> **Stage:** E — Platform · **Depends on:** EPIC-03, EPIC-15, EPIC-20 ·
> **Complexity:** XL · **Risk:** High · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. IV §6.

## 1. Objective

Reuse the UI-agnostic domain layer on new surfaces: a Flet mobile target and/or a
formal public API (REST/GraphQL). Additive surfaces — the desktop app is
unaffected.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E21-F1 | Public API | REST/GraphQL over existing services (no domain change) |
| E21-F2 | API auth + RBAC | Token auth mapped to roles/permissions (EPIC-03) |
| E21-F3 | Mobile target | Flet mobile reusing services/repositories |
| E21-F4 | Integration surface | Third-party integrations via the API |

## 3. User stories

- **E21-F3-S1** — As a doctor, I want a mobile version, so that I can work away
  from the desktop.
- **E21-F1-S1** — As an integrator, I want an API, so that external systems can
  interoperate with WiseOS.
- **E21-F2-S1** — As a security reviewer, I want API access mapped to RBAC, so that
  tokens carry least-privilege.

## 4. Engineering tasks

- **E21-T1** — API layer over services (contracts from `docs/API.md`); no domain
  logic change.
- **E21-T2** — Token auth + RBAC mapping (EPIC-03); audit every API call.
- **E21-T3** — Flet mobile target reusing the domain layer.
- **E21-T4** — Tests (API contract, authz) + docs (API, DEPLOYMENT).

## 5. Dependencies

- **Upstream (hard):** EPIC-03, EPIC-15, EPIC-20. Domain layer (built,
  UI-agnostic).
- **Downstream:** integrations, EPIC-16 (shared API).

## 6. Acceptance criteria

- **AC1** — *Given* the API, *when* called, *then* it reuses existing services
  without modifying them.
- **AC2** — *Given* a token, *when* used, *then* access maps to RBAC permissions
  and is audited.
- **AC3** — *Given* the mobile target, *when* built, *then* it reuses the domain
  layer unchanged.
- **AC4** — *Given* API/app up or down, *when* toggled, *then* the desktop app is
  unaffected.

## 7. Regression tests

- **Must stay green:** golden, models, router, views (desktop unchanged).
- **New:** API contract tests, authz/RBAC tests, audit-of-API tests.

## 8. Rollout phases

- **E21-R1** — Read-only API + auth + RBAC mapping.
- **E21-R2** — Write actions via API (guarded).
- **E21-R3** — Mobile target; docs closeout.

## 9. Rollback

Disable the API/app surface → desktop unaffected. Additive only; no data
destroyed.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: services unmodified; API access RBAC-
mapped and audited; desktop independent of API/app state.
</content>
