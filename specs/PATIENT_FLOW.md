# Patient Flow — Specification

> **Status:** Design only (Phase 2). **Last updated:** 2026-07-20.
> Extends [`../docs/PATIENT_JOURNEY.md`](../docs/PATIENT_JOURNEY.md) with the
> target end-to-end operational flow across all modules.

## 1. Purpose

Describe the complete path a patient takes through the clinic — from first
contact to long-term continuity — and which module owns each stage. This is the
backbone every other spec plugs into. IDs (`patient_id`, `case_id`, `visit_id`)
are the contract between stages (Constitution Art. IV §4).

## 2. The flow (target, end-to-end)

```
                       ┌─────────────────────────────────────────────┐
   NEW PATIENT         │                RETURNING PATIENT             │
      │                │                      │                       │
      ▼                │                      ▼                       │
 (1) Contact / Booking ─────────────► (Appointment System)           │
      │  online form · phone · walk-in       │                       │
      ▼                                       ▼                       │
 (2) Registration ──────────────────► auto reg-no P000001…           │
      │  (Reception)                          │                       │
      ▼                                       ▼                       │
 (3) Arrival / Check-in ────────────► (Waiting Queue — token)        │
      │                                       │                       │
      ▼                                       ▼                       │
 (4) Case opened / reopened ────────► one clinical thread            │
      │  (Doctor)                             │                       │
      ▼                                       ▼                       │
 (5) CONSULTATION WORKSPACE ─────────────────────────────────────────┤
      │  summary · complaint · history · exam · diagnosis ·          │
      │  investigation · OCR · protocol · Rx · pricing · remarks     │
      ▼                                                              │
 (6) Investigations ordered ────────► (Investigation Engine)         │
      ▼                                                              │
 (7) Prescription ──────────────────► narrative + extracted items    │
      ▼                                                              │
 (8) Dispensing ────────────────────► (Dispensing / PillFill / WHIMS)│
      ▼                                                              │
 (9) Billing / Invoice ─────────────► (Billing)                      │
      ▼                                                              │
(10) Print & Communicate ───────────► (Wise Printer · WhatsApp)      │
      ▼                                                              │
(11) Follow-up scheduled ───────────► (Appointment System · Dashboard)│
      ▼                                                              │
(12) Documents / reports uploaded ──► (Attachments · OCR)            │
      ▼                                                              │
(13) Timeline updated ──────────────► (Timeline Engine)              │
      │                                                              │
      └──────────────── continuity ──► returns as RETURNING PATIENT ─┘
```

## 3. Stage-by-stage ownership

| # | Stage | Owner module | Status | Key data |
| - | ----- | ------------ | ------ | -------- |
| 1 | Contact / booking | Appointments | 🔜 | `appointments` |
| 2 | Registration | registration / patients | ✅ | `patients` (auto reg-no) |
| 3 | Check-in / token | Waiting Queue | 🔜 | `queue` |
| 4 | Case opened / reopened | cases | ✅ | `patient_cases` |
| 5 | Consultation | Consultation Workspace (over visits) | 🔜 / visits ✅ | `visits` |
| 6 | Investigation ordered | Investigation Engine | 🔜 | `investigation_*` |
| 7 | Prescription | visits + prescription intelligence | ✅ | `prescription_items` |
| 8 | Dispensing | Dispensing / PillFill / WHIMS | 🔜 | `dispense_*`, `inventory_*` |
| 9 | Billing | Billing | 🔜 | `invoices`, `payments` |
| 10 | Print & message | Wise Printer, WhatsApp | 🔜 | templates in Settings |
| 11 | Follow-up | Appointments, Dashboard | ✅ (seed) / 🔜 | `followup_date` → `appointments` |
| 12 | Documents | Attachments, OCR | ✅ / 🔜 | `attachments`, `ocr_results` |
| 13 | Timeline | Timeline | ✅ | read model |

## 4. Two primary entry paths

- **New patient, new case** — full flow, first consultation.
  See [`NEW_CASE_WORKFLOW.md`](./NEW_CASE_WORKFLOW.md).
- **Returning patient, follow-up** — search/queue → reopen case → follow-up
  consultation. See [`FOLLOWUP_WORKFLOW.md`](./FOLLOWUP_WORKFLOW.md).

Both converge on the **Consultation Workspace** (stage 5).

## 5. State transitions

- **Patient:** active ↔ soft-deleted (never physically removed).
- **Case:** Open → On Hold → Resolved / Closed (`CASE_STATUSES`). A case can be
  reopened; history is retained.
- **Visit:** draft → completed → (amended, audited). Never destroyed.
- **Appointment (planned):** booked → confirmed → checked-in → in-consult →
  done / no-show / cancelled.
- **Dispense order (planned):** created → fulfilled / cancelled.
- **Invoice (planned):** draft → issued → paid / part-paid / void.

## 6. Data continuity rules

1. Every downstream artifact references the upstream ID; no stage forks the
   record (Constitution Art. II §4, IV §4).
2. A returning patient always resolves to the *same* `patients` row (search by
   reg-no / phone). No duplicate patient store — the future Portal ties to this
   identity too.
3. The Timeline (stage 13) is the union read model over every stage that produced
   an event. New modules join it by adding a repository query, not by changing
   the timeline's contract. See [`TIMELINE_ENGINE.md`](./TIMELINE_ENGINE.md).

## 7. Roles across the flow (target, RBAC F3)

| Stage | Reception | Doctor | Pharmacy | Accounts | Admin |
| ----- | :-------: | :----: | :------: | :------: | :---: |
| Booking / check-in | ✅ | | | | ✅ |
| Registration | ✅ | ✅ | | | ✅ |
| Consultation | | ✅ | | | ✅ |
| Dispensing | | | ✅ | | ✅ |
| Billing / payment | | | | ✅ | ✅ |
| Messaging | ✅ | ✅ | ✅ | | ✅ |

See [`USER_ROLES.md`](./USER_ROLES.md). RBAC enforcement is F3; until then any
logged-in user can perform any stage.

## 8. Dependencies

Booking, queue, dispensing, billing, printing, and messaging are all planned
modules gated behind F1 (migrations) and, for patient-facing channels, F3/F7.
Registration, cases, visits, attachments, and timeline exist today and already
carry the patient through stages 2, 4, 5(core), 7, 12, 13.
</content>
