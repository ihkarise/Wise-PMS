# Patient Portal — Specification

> **Status:** Design only (Phase 2). Not implemented. **Late module by design.**
> Separate front-end + public API. **Last updated:** 2026-07-20.
> Extends [`../docs/modules/PatientPortal.md`](../docs/modules/PatientPortal.md).

## 1. Purpose

A patient-facing surface where patients access **their own** records: bookings,
prescriptions, reports, timeline, invoices, and (later) telemedicine. This is the
first time PHI leaves the single trusted clinic machine — so it must not ship
before the security foundation is proven (Constitution Art. VI §3).

## 2. Capabilities (target)

| Capability | Source module |
| ---------- | ------------- |
| Appointments (view + self-book) | Appointments |
| Reports (uploaded documents) | Attachments |
| Investigations (structured values + trends) | Investigation / OCR |
| Timeline (own medical timeline) | Timeline |
| Medicine List (current + history) | visits / Dispensing |
| Progress (outcomes over time) | visits / Analytics |
| Invoices | Billing |
| Payments (view / online pay, future) | Payments |
| Telemedicine (join session) | Telemedicine |
| Notifications | WhatsApp / Portal notifications |

## 3. Architecture

- A **separate front-end** (web/mobile) talking to WiseOS through a **public API**
  layer (not yet built). The API **reuses existing services/repositories** — which
  are UI-agnostic — without modifying them (Constitution Art. IV §6).
- Patient identity ties to the existing `patients` record (reg-no / verified
  phone). **No duplicate patient store.**
- Patient authentication is **separate** from the staff `users` table — a patient
  is a distinct principal (own login, own least-privilege scope).

```
Patient device (web/mobile front-end)
        │  HTTPS (transport security required)
        ▼
Public API layer  ──►  existing services  ──►  repositories (RBAC + row scoping)
                                                     │
                                                     ▼
                                              SQLite / synced store
```

## 4. Hard prerequisites (non-negotiable)

Per the constitution and the module doc, the Portal **must not ship before**:

1. **RBAC (F3)** — patient is a distinct principal with least-privilege access.
2. **Encryption at rest (F7)** and **transport security** — PHI leaves the trusted
   machine for the first time.
3. **Public API layer** + patient authentication (not the staff `users` table).
4. **Cloud sync (F8)** if the portal is hosted off the clinic device.

## 5. Security stance

- Treat the portal as an **untrusted client**: **all authorization decisions
  happen server-side** at the service/repository seam, never in the portal UI
  (Constitution Art. VI §5).
- A patient can only ever read/act on **their own** `patient_id` scope — enforced
  at the repository, not the UI.
- Consent, opt-out, and data-access logging apply; every portal read/write is
  audited.

## 6. Service reuse (no new domain logic)

The Portal introduces **no new clinical logic** — it exposes read models and a few
patient-safe actions (book appointment, join session, view/pay invoice) over the
existing services. The domain layer is untouched; only an API adapter + patient
auth are new.

## 7. Dependencies & sequencing

- **Requires:** everything above (F3, F7, API, patient auth, and F8 if hosted
  remotely). Depends on Appointments, Investigation/OCR, Billing, Telemedicine
  being present for meaningful content.
- **Sequencing:** one of the **last** modules — after the security foundation and
  the clinical/business modules it surfaces (see
  [`MASTER_PHASE_PLAN.md`](./MASTER_PHASE_PLAN.md)).

## 8. Manual test checklist (implementing phase)

- [ ] A patient can only access their own records (repository-enforced scope).
- [ ] Authorization cannot be bypassed by manipulating the client.
- [ ] Patient auth is separate from staff auth.
- [ ] All portal access is audited.
- [ ] Transport is encrypted; data at rest is encrypted (F7).
- [ ] The offline clinic core is unaffected whether the portal is up or down.

## 9. Risks

- **Security surface** — the highest-risk module; gate it hard behind F3/F7 and a
  reviewed API.
- **Hosting posture** — hosting off-device conflicts with offline-first; keep it
  opt-in and consented, and keep the clinic's local copy authoritative
  (Constitution Art. VII).
</content>
