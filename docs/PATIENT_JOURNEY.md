# WiseOS Health — Patient Journey

> The patient's path through the ecosystem, present and future.
> **Last updated:** 2026-07-20.

## Today (single desktop, staff-operated)

| Stage | What happens | Module |
| ----- | ------------ | ------ |
| 1. Arrival | Reception registers the patient; auto reg-no `P000001…` | registration/patients |
| 2. Identification | Search by name/phone/reg-no/place opens the profile | patients |
| 3. Case opened | A clinical thread (e.g. "Migraine") is created | cases |
| 4. Consultation | Doctor records visit notes, investigation, prescription | visits |
| 5. Documents | Lab reports / images attached to the patient/visit | attachments |
| 6. History | Timeline merges visits, cases, attachments newest-first | timeline |
| 7. Follow-up | `followup_date` set; surfaces on Dashboard "Follow-ups Due" | dashboard |
| 8. Continuity | Return visit reopens the same patient/case record | patients/cases |

The patient never touches the software directly today — all interaction is
staff-mediated.

## Future journey (ecosystem)

| Stage | Added capability | Module (planned) |
| ----- | ---------------- | ---------------- |
| Booking | Patient books online; token/queue on arrival | Appointments, Waiting Queue |
| Reminders | WhatsApp welcome / appointment / follow-up messages | WhatsApp Automation |
| Consultation | Single integrated workspace; protocol suggestions | Consultation Workspace, Protocol Engine |
| Investigations | Uploaded reports OCR'd into structured trends | OCR Engine, Holoscan |
| Prescription | Printed script; priced against inventory | Wise Printer, WHIMS |
| Dispensing | Pharmacy hands off medicine; automated fill | Dispensing, PillFill |
| Billing | Invoice + payment | Billing |
| Telemedicine | Video/Meet consultation for remote patients | Online Consultation |
| Self-service | Patient views records, reports, prescriptions online | Patient Portal |
| Insight | Clinical & practice analytics; AI assistance | Analytics, AI Assistant |

## Design implications

- The **longitudinal record** (patient → cases → visits → items/attachments)
  must remain stable as modules are added; new modules reference these IDs, they
  do not replace them.
- Any patient-facing surface (Portal, WhatsApp, Telemedicine) depends on **RBAC
  (F3)** and **encryption at rest (F7)** landing first.
- WhatsApp variables (`{regname}`, `{fileno}`, `{appointmentDate}`, …) map
  directly onto existing patient fields — see
  [`modules/WhatsApp.md`](./modules/WhatsApp.md).
