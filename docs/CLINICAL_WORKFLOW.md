# WiseOS Health — Clinical Workflow

> How clinical work maps onto the software. Grounds the future Consultation
> Workspace (see [`modules/Visits.md`](./modules/Visits.md)).
> **Last updated:** 2026-07-20.

## Today's workflow (as built)

```
Login → Dashboard
   │
   ├── + New Case → Register patient (auto reg-no) ──► Patient Profile
   │
   └── Search ──► Patient Profile
                     │  tabs: Profile · Cases · Timeline · Attachments
                     ├── New Case  → Case Record ──► (Save + Start Visit)
                     ├── New Visit → Visit Entry (Consultation)
                     └── Upload File → Attachment
```

- **Case** = a clinical thread for one patient (e.g. "Migraine", "Allergic
  Rhinitis"), with `status` Open/Closed/Resolved/On Hold.
- **Visit** = one consultation event, optionally linked to a case. It carries
  three narrative editors — **Visit Notes**, **Investigation Notes**,
  **Prescription Notes** — plus `followup_date` and `outcome`.
- **Prescription intelligence** parses the free-text prescription into
  structured `prescription_items` for analytics, without constraining the
  doctor. Lines like `Bell 200`, `Bry 30 TDS` are detected; `continue`,
  `review`, `placebo`, etc. are skipped.

## Target workflow — Consultation Workspace (planned)

The charter's anchor feature: after creating a case, the doctor enters **one
integrated screen** containing, in order:

1. Patient Summary
2. Chief Complaint
3. History
4. Examination
5. Diagnosis
6. Investigation
7. OCR Results
8. Timeline
9. Protocol Suggestions
10. Prescription
11. Medicine Pricing
12. Remarks
13. Print · Dispense · Invoice
14. Follow-up

Everything above is authored on a single screen; today these are spread across
Case Record + Visit Entry + Profile tabs. The workspace composes existing
modules (visits, cases, timeline, attachments) plus new ones (Protocol Engine,
OCR, Printer, Billing, Dispensing).

## Clinical principles encoded in software

1. **Narrative is authoritative.** Structured data is always derived, never a
   gate on what the clinician may write.
2. **Nothing is destroyed.** Patients are soft-deleted; visits/cases are
   retained; every mutation is audited.
3. **Follow-up is first-class.** `followup_date` on visits drives the
   Dashboard's "Follow-ups Due" and future WhatsApp reminders.
4. **One patient, many cases, many visits** — the data model already supports
   the full longitudinal record.

## Roles in the workflow (target)

Administrator · Doctor · Reception · Pharmacy · Accounts. Reception registers &
books, Doctor runs the consultation, Pharmacy dispenses, Accounts invoices.
RBAC that enforces this is backlog **F3** (not yet implemented).
