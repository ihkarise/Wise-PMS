# EPIC-04 — Consultation Workspace

> **Spec:** [`../CONSULTATION_WORKSPACE.md`](../CONSULTATION_WORKSPACE.md),
> [`../NEW_CASE_WORKFLOW.md`](../NEW_CASE_WORKFLOW.md),
> [`../FOLLOWUP_WORKFLOW.md`](../FOLLOWUP_WORKFLOW.md),
> [`../SCREEN_FLOW.md`](../SCREEN_FLOW.md),
> [`../PATIENT_FLOW.md`](../PATIENT_FLOW.md) · **Backlog:** C1, C3, C6 ·
> **Stage:** B — Clinical Core · **Depends on:** EPIC-01, EPIC-02, EPIC-03 ·
> **Complexity:** L · **Risk:** High · **Status:** Backlog (planning only).
> The **anchor feature**. Governed by
> [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. II.

## 1. Objective

One integrated screen where the doctor runs the entire consultation after opening
a case — no screen-hopping. Built as a **skeleton first** (Patient Summary +
narrative sections + follow-up over `visits`), then panels light up as feeder
epics (Protocol, Investigation, OCR, Printer, Dispensing/Billing) land. Narrative
stays authoritative; structured panels are advisory.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E04-F1 | Workspace shell & layout | Left rail (sections) · center (active section) · right rail (context) · action bar |
| E04-F2 | Patient Summary + flags | Demographics + allergy/red-flag chips (right rail, always visible) |
| E04-F3 | Narrative sections | Chief Complaint · History · Examination · Diagnosis · Remarks (C3) |
| E04-F4 | Draft autosave | Incremental save so an interruption never loses work |
| E04-F5 | Prescription panel | Narrative Rx + live detected items (reuse `utils.prescription`) |
| E04-F6 | Follow-up planning | Set review date/outcome (C6); feeds Dashboard + EPIC-10 |
| E04-F7 | Panel mounts (feeders) | Investigation/OCR/Protocol/Pricing/Dispense/Print/Invoice slots with honest empty states |
| E04-F8 | Complete/amend flow | Finalize visit; reopen for audited amendment |
| E04-F9 | Diagnosis→case sync | Working diagnosis syncs to `patient_cases.diagnosis` |

## 3. User stories

- **E04-F1-S1** — As a doctor, I want everything in one screen, so that I don't
  jump between Case, Visit, and Profile mid-consult.
- **E04-F2-S1** — As a doctor, I want allergies/red flags always visible, so that
  safety context is where I prescribe.
- **E04-F3-S1** — As a doctor, I want free-text sections for complaint/history/
  exam/diagnosis, so that I record care in my own words.
- **E04-F4-S1** — As a doctor, I want my consultation autosaved, so that a crash
  never loses my notes.
- **E04-F5-S1** — As a doctor, I want detected medicines shown as I type, so that
  structure is captured without constraining me.
- **E04-F6-S1** — As a doctor, I want to set the next review in the same screen, so
  that follow-up is planned before the patient leaves.
- **E04-F7-S1** — As a doctor, I want unbuilt panels to show "not available yet"
  rather than break, so that I can still finish the visit.
- **E04-F8-S1** — As a doctor, I want to reopen and amend a completed visit with an
  audit trail, so that corrections are safe and traceable.

## 4. Engineering tasks

- **E04-T1** — Migration: additive narrative columns on `visits` (chief_complaint,
  examination, remarks) + optional `applied_protocol_id`, `draft` flag (EPIC-01).
- **E04-T2** — Workspace controller + route
  `^/patient/(?P<pid>\d+)/case/(?P<cid>\d+)/workspace(?:/visit/(?P<vid>new|\d+))?$`
  with `?section=` deep-link; RBAC `visits.consult`.
- **E04-T3** — Workspace view: left rail nav, center section renderer, right-rail
  context, action bar — all via `theme.*` + `shared/widgets.py`; new shared
  composites (section card, chip row) added to `widgets.py`.
- **E04-T4** — Draft autosave via `visits.service.update_visit` (debounced,
  section-level; avoid whole-screen rebuild per keystroke — see L11/F6).
- **E04-T5** — Prescription panel reusing `utils.prescription`; "Continue/Review/
  Placebo" lines respected.
- **E04-T6** — Feeder panel interfaces: each panel calls a feeder service if
  present, else renders an empty state (Protocol/Investigation/OCR/Pricing/
  Dispense/Print/Invoice).
- **E04-T7** — Complete/amend: finalize visit, update timeline, audit; reopen
  read-back + audited edit.
- **E04-T8** — Diagnosis→case sync in the service.
- **E04-T9** — Introduce **interaction/event test harness** (Flet/Playwright) — the
  current suite doesn't exercise handlers (L15).
- **E04-T10** — Tests + docs (CLINICAL_WORKFLOW, Visits module doc, SCREEN_FLOW
  realized routes, CHANGELOG, DECISIONS ADR).

## 5. Dependencies

- **Upstream:** EPIC-01 (columns), EPIC-02 (print/WhatsApp templates for actions),
  EPIC-03 (Doctor gating).
- **Downstream / feeders (light up panels):** EPIC-05 Protocol, EPIC-06
  Investigation, EPIC-07 OCR, EPIC-08 Timeline peek, EPIC-09 Printer, EPIC-12
  Billing/Dispensing, EPIC-13 pricing (WHIMS), EPIC-10 follow-up scheduling.

## 6. Acceptance criteria

- **AC1** — *Given* an open case, *when* "Start Consultation" is clicked, *then*
  the Workspace opens on a new draft visit for that case.
- **AC2** — *Given* content typed in sections, *when* the app is killed, *then* on
  reopen the draft content is present (autosave).
- **AC3** — *Given* a prescription narrative, *when* typed, *then* detected items
  appear live and the narrative remains authoritative.
- **AC4** — *Given* Complete Visit, *when* clicked, *then* exactly one visit row is
  written (linked to the case), the timeline updates, and an audit row is written.
- **AC5** — *Given* a completed visit reopened, *when* edited, *then* changes are
  audited and no history is destroyed.
- **AC6** — *Given* a feeder epic not yet shipped, *when* its panel renders, *then*
  it shows an honest empty state and never crashes.
- **AC7** — *Given* 1366×768, *when* the Workspace renders, *then* there is no
  horizontal page scroll.

## 7. Regression tests

- **Must stay green:** golden, models, router, views.
- **New:** Workspace controller/route contract; visit finalize/amend service tests;
  autosave test; view-build; **first interaction/event tests** (call-next →
  section edit → complete); model/table parity for new `visits` columns.

## 8. Rollout phases

- **E04-R1** — Skeleton: layout + Patient Summary + narrative sections + follow-up
  over existing `visits`; complete/amend; autosave.
- **E04-R2** — Prescription panel + detected items + diagnosis→case sync.
- **E04-R3** — Feeder panel mounts with empty states + timeline peek (EPIC-08).
- **E04-R4** — Enable panels as each feeder epic ships (incremental, no big-bang).

## 9. Rollback

Revert the Workspace route/nav → the built Case Record + Visit Entry screens remain
the working fallback path (they are not removed). New `visits` columns are inert to
the old screens. No data destroyed.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: skeleton is usable end-to-end without any
feeder epic; interaction tests exist; no clicks lost vs. the old Case+Visit flow.
</content>
