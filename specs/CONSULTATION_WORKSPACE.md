# Consultation Workspace — Specification

> **Status:** Design only (Phase 2). Not implemented. Anchor feature of WiseOS
> Health. Backlog **C1**. **Last updated:** 2026-07-20.
> Subordinate to [`PRODUCT_CONSTITUTION.md`](./PRODUCT_CONSTITUTION.md).

## 1. Purpose

The Consultation Workspace is **the central screen of WiseOS Health**. After the
doctor creates (or opens) a case, they enter one integrated screen and run the
*entire* consultation there — from reading the patient summary to printing the
prescription and planning the follow-up — **without jumping between screens**.

Today the same work is spread across Case Record + Visit Entry + Profile tabs
(see [`../docs/CLINICAL_WORKFLOW.md`](../docs/CLINICAL_WORKFLOW.md)). The
Workspace **composes** the existing built modules (visits, cases, timeline,
attachments) and the planned engines (Protocol, Investigation, OCR, Printer,
Dispensing, Billing) into a single surface. It does **not** replace them — it is
a coordinating view over their services.

## 2. Design principles (from the Constitution)

- **One screen, one consultation.** Everything the doctor needs is reachable
  without leaving the Workspace.
- **Narrative is authoritative.** Every structured panel (diagnosis, prescription
  items, protocol suggestions, OCR values) is derived/advisory. The free-text
  editors are the record of care.
- **Persist continuously, never lose work.** Autosave draft state so a crash or
  interruption never loses a half-written consultation.
- **Advisory, never automatic.** Protocol/AI suggestions are pulled in on the
  doctor's action, never injected silently.
- **Composition, not coupling.** The Workspace calls each module's *service*; it
  owns no SQL and no new base table beyond what `visits` already provides.

## 3. Anatomy — the panels

The Workspace is a single scrolling/section-navigated screen. Panels, in clinical
order (mirrors the charter list):

| # | Panel | Backed by | Built? |
| - | ----- | --------- | ------ |
| 1 | **Patient Summary** | `patients.service`, demographics + flags (allergies, chronic) | ✅ (data) |
| 2 | **Chief Complaint** | narrative field (new) on the visit | 🔜 |
| 3 | **History** | narrative (maps to `visit_notes` / structured HPI later) | ✅/🔜 |
| 4 | **Physical Examination** | narrative + optional vitals | 🔜 |
| 5 | **Diagnosis** | narrative + optional coded diagnosis (maps to `patient_cases.diagnosis`) | ✅/🔜 |
| 6 | **Investigation Panel** | [`INVESTIGATION_ENGINE.md`](./INVESTIGATION_ENGINE.md) — order tests | 🔜 |
| 7 | **Investigation Timeline** | [`INVESTIGATION_ENGINE.md`](./INVESTIGATION_ENGINE.md) — results over time | 🔜 |
| 8 | **OCR Results** | [`OCR_ENGINE.md`](./OCR_ENGINE.md) — structured values from uploads | 🔜 |
| 9 | **Comparison with Previous Reports** | OCR + Investigation trend | 🔜 |
| 10 | **Protocol Suggestions** | [`PROTOCOL_ENGINE.md`](./PROTOCOL_ENGINE.md) | 🔜 |
| 11 | **Medicine Prescription** | `visits.prescription_notes` + `prescription_items` extraction | ✅ |
| 12 | **Dispensing** | [`DISPENSING_SYSTEM.md`](./DISPENSING_SYSTEM.md) | 🔜 |
| 13 | **Pricing** | WHIMS `price_for(item)` | 🔜 |
| 14 | **Remarks** | narrative field | ✅ (via notes) |
| 15 | **Review Status** | `visits.outcome` + review workflow | ✅/🔜 |
| 16 | **Print** | [`PRINTER_SYSTEM.md`](./PRINTER_SYSTEM.md) | 🔜 |
| 17 | **Invoice** | [`DISPENSING_SYSTEM.md`](./DISPENSING_SYSTEM.md) / Billing | 🔜 |
| 18 | **Wise Printer Integration** | [`PRINTER_SYSTEM.md`](./PRINTER_SYSTEM.md) | 🔜 |
| 19 | **Follow-up Planning** | `visits.followup_date` + [`APPOINTMENT_SYSTEM.md`](./APPOINTMENT_SYSTEM.md) | ✅/🔜 |

> **Note on data source of truth:** the visit record (`visits`) already carries
> `visit_notes`, `investigation_notes`, `prescription_notes`, `followup_date`,
> `outcome`, `case_id`. New narrative sub-fields (chief complaint, examination)
> are *additive columns* and require the migration runner (F1) before they exist.
> Until F1, the Workspace can group today's three narrative editors and defer the
> finer split.

## 4. Layout model

Target layout for 1366×768 (no horizontal page scroll):

```
┌───────────────────────────────────────────────────────────────────────┐
│ shell header (logo · workflow bar · backup · user chip · logout)        │
├──────────────┬────────────────────────────────────────┬────────────────┤
│ LEFT RAIL    │ CENTER — active section (scrolls)       │ RIGHT RAIL     │
│ (section nav)│                                         │ (context)      │
│              │  Chief Complaint / History / Exam /     │                │
│ • Summary    │  Diagnosis / Investigation / Rx / …     │ Patient card   │
│ • Complaint  │                                         │ Allergy flags  │
│ • History    │  Large narrative editors +              │ Protocol picks │
│ • Exam       │  advisory structured panels             │ Timeline peek  │
│ • Diagnosis  │                                         │ OCR compare    │
│ • Investig.  │                                         │                │
│ • Rx         │                                         │                │
│ • Dispense   │                                         │                │
│ • Follow-up  │                                         │                │
├──────────────┴────────────────────────────────────────┴────────────────┤
│ ACTION BAR:  Save Draft · Print · Dispense · Invoice · WhatsApp ·        │
│              Schedule Follow-up · Complete Visit                          │
└───────────────────────────────────────────────────────────────────────┘
```

- **Left rail** = section jump list (also a completeness indicator: which
  sections have content).
- **Center** = the active section's editors/panels.
- **Right rail** = always-visible context (who the patient is, allergy/red-flag
  chips, current protocol picks, a peek at the timeline and the latest report
  comparison).
- **Action bar** = the terminal actions; always reachable.

All controls come from `shared/theme.py` + `shared/widgets.py` (Constitution
Art. V). No new colors or fonts.

## 5. Lifecycle

```
Open case  ──►  Workspace opens on a NEW visit (draft) for that case
                 │
                 ├─ doctor authors sections (autosaved as draft)
                 ├─ orders investigations (Investigation Engine)
                 ├─ reviews uploads/OCR + previous-report comparison
                 ├─ pulls Protocol suggestions (advisory) into Rx
                 ├─ writes prescription (narrative) → items auto-extracted
                 ├─ prices against WHIMS (if available) → dispense order
                 ├─ Print (Wise Printer) · Invoice · WhatsApp "Medicine Ready"
                 └─ schedules follow-up (date → Appointment/Dashboard)
                 │
                 ▼
           Complete Visit  ──►  visit persisted, timeline updated,
                                 audit row written, return to profile/queue
```

- **Draft autosave** writes to the visit record incrementally (or a draft field)
  so nothing is lost. Only **Complete Visit** finalizes review status.
- **Reopening** a completed visit shows the same Workspace read-back for
  amendment (audited), never a destructive overwrite.

## 6. Integration contract (services the Workspace calls)

The Workspace is a **controller + view** composed over existing/planned services.
It never writes SQL directly.

| Panel action | Service call (target) |
| ------------ | --------------------- |
| Load patient | `patients.service.get_patient(pid)` |
| Load/attach case | `cases.service.get_case(cid)` / `create_case` |
| Save consultation | `visits.service.create_visit/update_visit` |
| Extract Rx items | `utils.prescription.extract_prescription_items` (auto) |
| Order investigation | `investigation.service.order(...)` (planned) |
| Show OCR values | `ocr.service.values_for_patient(...)` (planned) |
| Timeline peek | `timeline.service.timeline_for_patient(pid)` |
| Protocol suggestions | `protocols.service.apply_protocol(...)` (planned) |
| Price a medicine | `inventory.service.price_for(item)` (planned) |
| Create dispense order | `dispensing.service.create_order(visit)` (planned) |
| Print prescription | `printer.service.render_prescription(visit)` (planned) |
| Create invoice | `billing.service.create_invoice(...)` (planned) |
| Send WhatsApp | `whatsapp.service.send(patient, key, ctx)` (planned) |
| Schedule follow-up | `appointments.service.book(...)` / set `followup_date` |
| Audit | every mutation → `audit.service.log_action` |

## 7. Routing

Target route (regex, per router contract):
`^/patient/(?P<pid>\d+)/case/(?P<cid>\d+)/workspace(?:/visit/(?P<vid>new|\d+))?$`

- Opening a case with "Start Consultation" navigates here on a new draft visit.
- `?section=diagnosis` (query) may deep-link to a section.
- Session guard applies; RBAC (F3) later restricts to Doctor role.

## 8. Dependencies & sequencing

- **Hard prerequisites:** F1 (migrations, for any new visit columns), and ideally
  F2 (Settings, for print/WhatsApp templates) and F3 (RBAC, to gate Doctor).
- **Feeder modules:** Protocol Engine, Investigation Engine, OCR, Printer,
  Dispensing/Billing, Inventory (WHIMS), Appointments — each shippable
  independently; the Workspace lights up panels as they land.
- **Phasing:** the Workspace is built as a **skeleton first** (Patient Summary +
  today's narrative editors + follow-up), then panels are enabled incrementally
  as feeder modules ship. See [`MASTER_PHASE_PLAN.md`](./MASTER_PHASE_PLAN.md).

## 9. Manual test checklist (for the implementing phase)

- [ ] Creating a case opens the Workspace on a new draft visit for that case.
- [ ] Narrative sections autosave; killing the app mid-consult loses no content.
- [ ] Prescription narrative produces detected items live; narrative stays
      authoritative.
- [ ] Completing the visit writes one visit row, updates the timeline, and audits.
- [ ] Reopening a completed visit shows content read-back; edits are audited.
- [ ] Panels for unbuilt modules render an honest "not available yet" empty state,
      never a crash.
- [ ] Layout holds at 1366×768 with no horizontal page scroll.
- [ ] `pytest -q` green; router-contract test covers the new route.

## 10. Risks

- **Scope/complexity** — the Workspace touches the most modules; must be built as
  a skeleton and grown, not big-bang (Constitution Art. IX §3).
- **Performance** — many panels on one screen vs. the full-rebuild-on-navigation
  model (L11). Mitigate with section-level lazy loads and draft autosave rather
  than whole-screen rebuilds per keystroke.
- **Premature structure** — over-splitting narrative into rigid fields could
  violate narrative-first. Keep new fields optional and additive.
</content>
