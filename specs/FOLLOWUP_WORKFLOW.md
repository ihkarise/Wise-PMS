# Follow-up Workflow — Specification

> **Status:** Design only (Phase 2). **Last updated:** 2026-07-20.
> The return-visit path. Companion: [`NEW_CASE_WORKFLOW.md`](./NEW_CASE_WORKFLOW.md).

## 1. Purpose

Define the flow when a patient **returns** for an existing complaint. Follow-up is
first-class (Constitution Art. II §5): the system should make the return visit
faster than the first, because prior context (case, last prescription, timeline,
reports) is already available.

## 2. Actors

Reception (check-in), Doctor (follow-up consultation). RBAC (F3) enforces; today
unrestricted.

## 3. Flow

```
(A) Identify the returning patient
     ├─ Waiting Queue (checked-in today)  ── or ──
     ├─ Dashboard "Follow-ups Due" (followup_date ≤ today)  ── or ──
     └─ Search (name/phone/reg-no)  →  Patient Profile

(B) Reopen the case
     Profile → Cases tab → open the relevant Open case (e.g. "Migraine")
     (or Timeline → last visit)

(C) CONSULTATION WORKSPACE opens on a NEW draft follow-up visit, PRELOADED with:
     • Patient Summary + allergy/red-flag chips
     • Last visit's prescription (to Continue / Modify / Stop)
     • Outcome of last visit (Improving / Same / Worse …)
     • Investigation timeline + previous-report comparison (OCR)
     • Open protocol (if the case used one) and its review schedule

(D) Conduct follow-up
     1. Progress note (narrative) — response since last visit
     2. Re-examine / update diagnosis if needed
     3. Review new reports (Attachments → OCR → comparison)
     4. Continue / modify / stop prescription (narrative authoritative)
     5. Set outcome (VISIT_OUTCOMES)
     6. Print · Dispense · Invoice · WhatsApp (Medicine Ready / Follow-up)
     7. Schedule next follow-up (or Resolve/Close the case)

(E) Complete Visit
     Visit persisted (linked to same case) · Timeline updated · Audit written
```

## 4. What is preloaded (the follow-up advantage)

| Panel | Preloaded from | Service (target) |
| ----- | -------------- | ---------------- |
| Last prescription | previous visit | `visits.service.visits_for_patient` / `prescription_items_for_visit` |
| Last outcome | previous visit | `visits.service.get_visit` |
| Investigation trend | prior reports | `ocr.service.values_for_patient` (planned) |
| Report comparison | prior vs. new | Investigation Engine (planned) |
| Timeline | all events | `timeline.service.timeline_for_patient` |
| Active protocol + review due | case | `protocols.service` (planned) |

Preloading is **read-only context**; the doctor's new narrative is what gets
saved. "Continue medicine" lines are respected by prescription intelligence
(they are skip-words and are not re-extracted as new items).

## 5. Today vs. target

**Today (built):** Dashboard "Follow-ups Due" and Search reach the profile; New
Visit opens Visit Entry with the case selectable; timeline and attachments are
visible on the profile. The three narrative editors + `followup_date` + `outcome`
capture the follow-up.

**Target:** the Workspace preloads last-visit context automatically and shows
report comparison inline; WhatsApp follow-up reminders (planned) drive the return
before the patient even arrives.

## 6. Business rules

1. A follow-up visit **links to the same case** (`visits.case_id`), continuing
   the thread — never a new case for the same complaint.
2. Setting `outcome = Cured/Resolved` should prompt (not force) resolving the
   case; the doctor decides.
3. `followup_date` on the completed visit feeds Dashboard "Follow-ups Due" and
   (later) a WhatsApp Follow-up reminder.
4. Narrative-first and audit rules apply identically.

## 7. Reminder loop (target, retention)

```
Visit completed with followup_date
        │
        ▼
Dashboard surfaces it when due  ──►  WhatsApp "Follow-up Reminder" (planned)
        │                                   │
        ▼                                   ▼
Patient books/returns  ◄────────────  {appointmentDate}, {doctorName}, {clinicName}
```

See [`WHATSAPP_SYSTEM.md`](./WHATSAPP_SYSTEM.md) and
[`APPOINTMENT_SYSTEM.md`](./APPOINTMENT_SYSTEM.md).

## 8. Edge cases

- **No prior case** (patient thought to be returning but no open thread): fall
  back to the New Case workflow.
- **Multiple open cases**: the doctor picks which thread this visit belongs to.
- **New complaint during a follow-up**: open a *new* case rather than blurring the
  existing thread; both cases remain in the same continuous timeline.
- **Missed follow-up**: remains on "Follow-ups Due" until addressed; reminders may
  escalate (config in Settings, planned).

## 9. Manual test checklist (implementing phase)

- [ ] A due follow-up appears on the Dashboard and opens the right case.
- [ ] The Workspace preloads last prescription/outcome/timeline as read context.
- [ ] "Continue" lines are not re-extracted as new prescription items.
- [ ] The follow-up visit links to the same case; timeline shows both visits.
- [ ] Setting outcome=Cured prompts (not forces) case resolution.

## 10. Dependencies

Dashboard, Search, cases, visits, timeline, attachments exist today. Workspace
preloading, OCR comparison, WhatsApp reminders, and appointment scheduling are
planned. F1 gates any new fields.
</content>
