# EPIC-16 — Patient Portal

> **Spec:** [`../PATIENT_PORTAL.md`](../PATIENT_PORTAL.md) · **Backlog:** — ·
> **Stage:** D — Insight & Reach · **Depends on:** EPIC-03 (RBAC), EPIC-15
> (encryption), public API + patient auth, EPIC-20 (if hosted off-device) ·
> **Complexity:** XL · **Risk:** High · **Status:** Backlog (planning only).
> **Late module by design.** Governed by
> [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. VI.

## 1. Objective

A patient-facing surface (web/mobile) over a public API where patients access
**their own** records — bookings, prescriptions, reports, timeline, invoices, and
(later) telemedicine. First time PHI leaves the trusted machine, so it ships only
after the security foundation is proven.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E16-F1 | Public API adapter | Reuses existing services/repositories, unmodified |
| E16-F2 | Patient auth | Separate principal from staff `users`; verified phone/reg-no |
| E16-F3 | Read surfaces | Profile, timeline, prescriptions, reports+OCR values, invoices |
| E16-F4 | Safe actions | Self-book appointment, join session, view/pay invoice |
| E16-F5 | Server-side authorization | Own-`patient_id` scope enforced at the repo seam |
| E16-F6 | Notifications | Portal + WhatsApp notifications |

## 3. User stories

- **E16-F3-S1** — As a patient, I want to see my prescriptions and reports, so
  that I have my records.
- **E16-F4-S1** — As a patient, I want to self-book an appointment, so that I don't
  have to call.
- **E16-F5-S1** — As a security reviewer, I want authorization enforced server-side,
  so that a manipulated client can't access others' data.
- **E16-F2-S1** — As the clinic, I want patient login separate from staff, so that
  principals and privileges don't mix.

## 4. Engineering tasks

- **E16-T1** — Public API layer (REST/GraphQL) over existing services; no domain
  logic change (Art. IV §6).
- **E16-T2** — Patient authentication (own store, verified contact); least-privilege
  scope.
- **E16-T3** — Repository-level own-`patient_id` scoping (defense in depth with
  EPIC-03).
- **E16-T4** — Read surfaces + safe actions; portal front-end (separate app).
- **E16-T5** — Transport security (TLS); audit every portal access.
- **E16-T6** — Tests (authz-cannot-be-bypassed) + docs (PatientPortal module doc,
  SECURITY, API).

## 5. Dependencies

- **Upstream (hard):** EPIC-03 (RBAC), EPIC-15 (encryption at rest + transport),
  API + patient auth; EPIC-20 if hosted off-device. Content: EPIC-10, EPIC-06/07,
  EPIC-12, EPIC-17.
- **Downstream:** EPIC-17 (join session), online payments.

## 6. Acceptance criteria

- **AC1** — *Given* a patient, *when* authenticated, *then* they access only their
  own `patient_id` scope (repository-enforced).
- **AC2** — *Given* a manipulated client, *when* it requests another patient's
  data, *then* the server refuses.
- **AC3** — *Given* patient auth, *when* used, *then* it is separate from staff
  auth.
- **AC4** — *Given* any portal access, *when* it occurs, *then* it is audited and
  transport-encrypted.
- **AC5** — *Given* the portal down/up, *when* toggled, *then* the offline clinic
  core is unaffected.

## 7. Regression tests

- **Must stay green:** golden, models, router, views (offline core unchanged).
- **New:** API authz tests (own-scope only, bypass attempts fail), patient-auth
  tests, audit-of-access tests, transport tests.

## 8. Rollout phases

- **E16-R1** — API layer + patient auth + own-scope enforcement (read-only).
- **E16-R2** — Read surfaces (timeline, prescriptions, reports, invoices).
- **E16-R3** — Safe actions (self-book, join, view/pay) + notifications.
- **E16-R4** — Hardening/audit review; docs closeout.

## 9. Rollback

Disable the API surface → offline core unaffected; the local copy stays
authoritative. No patient data is created that the core can't already produce.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: authorization provably server-side;
security review passed; offline core independent of portal state.
</content>
