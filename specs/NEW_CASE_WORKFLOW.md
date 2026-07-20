# New Case Workflow — Specification

> **Status:** Design only (Phase 2). **Last updated:** 2026-07-20.
> The first-visit path. Companion: [`FOLLOWUP_WORKFLOW.md`](./FOLLOWUP_WORKFLOW.md).

## 1. Purpose

Define the end-to-end flow when a patient presents with a **new complaint** — a
brand-new patient, or an existing patient opening a new clinical thread. The
target experience: **register → open case → land in the Consultation Workspace**,
with the fewest possible steps and no screen-hopping (Constitution Art. II §3).

## 2. Actors

Reception (registration, booking), Doctor (consultation). Under RBAC (F3) these
are enforced; today any user can do all steps.

## 3. Flow

```
(A) Entry
     ├─ New patient:  Dashboard/Header "+ New Case" → Registration (auto reg-no)
     └─ Existing patient, new complaint:  Search → Profile → "New Case"

(B) Open the case
     Case Record: case_title (e.g. "Migraine"), provisional diagnosis,
     status = Open.  → "Start Consultation"

(C) CONSULTATION WORKSPACE opens on a NEW draft visit for the case
     1. Patient Summary (read)         — demographics, allergy/red-flag chips
     2. Chief Complaint (narrative)
     3. History (narrative; HPI)
     4. Physical Examination (narrative + optional vitals)
     5. Diagnosis (narrative + optional coded)  → syncs to case.diagnosis
     6. Investigation Panel — order baseline tests (Investigation Engine)
     7. Protocol Suggestions — pull condition template (advisory)
     8. Prescription (narrative) → items auto-extracted; pricing (WHIMS)
     9. Remarks / advice
    10. Print (Wise Printer) · Dispense · Invoice · WhatsApp welcome
    11. Follow-up Planning — set review date/schedule

(D) Complete Visit
     Visit persisted · Timeline updated · Audit written · return to profile/queue
```

## 4. Step detail & data

| Step | Screen / panel | Service (target) | Writes |
| ---- | -------------- | ---------------- | ------ |
| Register | Registration view | `patients.service.create_patient` | `patients` (reg-no auto) |
| Open case | Case Record | `cases.service.create_case` | `patient_cases` (status Open) |
| Start consult | Workspace | `visits.service.create_visit` (draft) | `visits` (draft) |
| Author sections | Workspace center | draft autosave → `update_visit` | `visits` |
| Order tests | Investigation Panel | `investigation.service.order` (planned) | `investigation_orders` |
| Apply protocol | Protocol Suggestions | `protocols.service.apply_protocol` (planned) | none (advisory) |
| Prescribe | Prescription panel | `visits.service.update_visit` + extraction | `visits`, `prescription_items` |
| Price/dispense | Pricing/Dispense | `inventory.price_for`, `dispensing.create_order` (planned) | `dispense_*` |
| Print/message | Action bar | `printer.render_*`, `whatsapp.send` (planned) | `messages` |
| Follow-up | Follow-up panel | set `followup_date` / `appointments.book` (planned) | `visits`/`appointments` |
| Complete | Action bar | `visits.service.update_visit` (finalize) + audit | `visits`, `audit_logs` |

## 5. Today vs. target

**Today (built):** New Case → Register → Profile → New Case (Case Record) → Save
+ Start Visit → Visit Entry (three narrative editors + follow-up + outcome) →
Save → Profile. Prescription intelligence already extracts items.

**Target:** the Case Record and Visit Entry collapse into the **Consultation
Workspace**; new narrative sub-fields (chief complaint, exam) are additive
columns needing F1. The built path remains valid and is the fallback until the
Workspace ships.

## 6. Business rules

1. **Auto reg-no** `P000001…` with collision check (existing behavior).
2. A visit created from a case is **linked** (`visits.case_id`).
3. **Narrative is authoritative**; structured extraction is derived.
4. **Every mutation audited**; nothing physically deleted.
5. Draft autosave means an interrupted first visit is never lost.
6. Diagnosis entered in the Workspace **syncs to the case** so the case thread
   reflects the working diagnosis.

## 7. Edge cases

- **Patient already exists** (duplicate on registration): search-first; surface a
  likely match by phone/name before creating a new record.
- **Case belongs to an existing thread**: offer to add a visit to an open case
  instead of opening a new one.
- **Unbuilt feeder module** (protocol/OCR/printer not yet shipped): the panel
  shows an honest empty state; the consultation still completes on narrative +
  prescription.
- **Offline provider** (WhatsApp/print) unavailable: action degrades gracefully,
  visit still completes (Constitution Art. VII §4).

## 8. Manual test checklist (implementing phase)

- [ ] "+ New Case" from a cold start registers a patient and reaches a case.
- [ ] Opening a case starts a draft visit in the Workspace.
- [ ] Prescription narrative yields detected items; narrative unchanged.
- [ ] Completing writes one linked visit, updates timeline, audits.
- [ ] Diagnosis syncs to the case record.
- [ ] Duplicate-patient guard surfaces an existing match.

## 9. Dependencies

Registration, cases, visits, prescription intelligence exist today. Workspace,
Investigation, Protocol, Printer, Dispensing, WhatsApp are planned; the flow
lights up as they land. F1 gates new visit columns.
</content>
