# Module: Consultation Workspace

**Status:** 🟢 Domain model (Sprint 2) · **Path:** `app/modules/consultation/` ·
**Tables:** `consultations` (1:1 with `visits`) ·
**Spec:** [`../../specs/CONSULTATION_WORKSPACE.md`](../../specs/CONSULTATION_WORKSPACE.md) ·
**ADR:** [`../architecture-decisions/ADR-001-Consultation-Domain.md`](../architecture-decisions/ADR-001-Consultation-Domain.md)

## Sprint 2 — Consultation domain model (ADR-001 Option C)
The consultation is the **clinical document**, 1:1 with a **visit** (the event).
Full vertical slice: `models.py` (`Consultation`) · `repository.py` (only writer
of `consultations`) · `service.py` (lifecycle state machine + composition) ·
`controller.py` (create/open draft on workspace open) · `view.py` (status
read-back). Migration `v0002_consultations` (additive, reversible).

**Lifecycle:** `draft → in_progress → completed` (`amended`/`locked` reserved).
`consultation.service` is the sole authority validating transitions; every
transition is audited. `visit_id` UNIQUE enforces one consultation per visit;
`open_or_create_draft` reuses one open draft per case. Drafts are excluded from
the completed read model (`for_patient`).

**Service API:** `open_or_create_draft(patient_id, case_id, user_id)` ·
`save_consultation(id, fields, user_id)` · `complete_consultation(id, user_id)` ·
`amend_consultation` · `lock_consultation` · `consultation_for_visit(visit_id)` ·
`workspace_context(patient_id, case_id, visit_id)`.

**Not in Sprint 2:** live editors/autosave UI, Timeline source row (deferred),
Investigation/OCR/AI (seams only — no provider SDK imported).

## Purpose
The **central screen of WiseOS Health**. After a doctor opens (or creates) a
case, they run the *entire* consultation on one integrated surface instead of
jumping between Case Record, Visit Entry, and Profile tabs. The Workspace does
not replace those modules — it is a **coordinating view** composed over their
services.

## What Sprint 1 delivers (skeleton only)
Structure, navigation, and honest placeholders — **no business logic, no
persistence, no OCR/AI/Protocol/WhatsApp/Billing/Dispensing/Investigation
processing.**

- **Top header** — the shared app `shell` header (logo · workflow bar · backup ·
  user chip · logout).
- **Left rail** — section navigation: Patient Summary · Chief Complaint ·
  History · Diagnosis · Prescription · Remarks · Follow-up. Clicking a section
  deep-links via `?section=<key>` and highlights the active card.
- **Center** — one card per section. **Patient Summary** shows real read-only
  patient data (composition over `patients.service`); the other sections render
  a placeholder note (their narrative editors arrive in later sprints).
- **Right rail** — context panels, all placeholders: Timeline · Investigations ·
  OCR · Protocol Suggestions · AI Assistant.
- **Bottom status/action bar** — a draft-status label plus **disabled**
  terminal actions: Print · Invoice · Dispense · WhatsApp · Complete Visit.

## Layers
`service.py` (`workspace_context` — read-only composition) · `controller.py`
(`workspace_controller` + `ROUTES`) · `view.py` (`workspace_view`). **No
`models.py` and no `repository.py`** — the Workspace owns no table and writes no
SQL (spec §2 "Composition, not coupling").

## Public service API
- `workspace_context(patient_id, case_id=None) -> {"patient": …, "case": …}`
  — read-only; delegates to `patients.service.get_patient` and
  `cases.service.get_case`. No mutation, no SQL, no business logic.

## Route
`^/patient/(?P<pid>\d+)/case/(?P<cid>\d+)/workspace(?:/visit/(?P<vid>new|\d+))?$`
— optional `?section=<key>` deep-link. Session guard applies (RBAC to gate the
Doctor role lands with F3). A missing patient/case renders a friendly not-found
state, never a crash.

## How to reach it
From the **Case Record** screen: **Start Consultation** saves the case and
navigates to the Workspace on a new draft visit
(`app/modules/cases/view.py`). This is the only cross-module edit — a navigation
link, no logic change.

## Dependencies
`consultation.service → patients.service`, `consultation.service →
cases.service` (both read-only). The view uses only `shared/theme.py` and
`shared/widgets.py` for controls (no raw buttons/fields, no hex literals).

## Growth path
Panels light up incrementally as feeder modules ship — Investigation Engine,
OCR, Protocol Engine, Dispensing/Billing, Inventory (WHIMS), Printer,
WhatsApp, Appointments — each shippable independently. New narrative sub-fields
(chief complaint, examination) are additive columns gated on the migration
runner (F1, now in place). See the spec's phasing and integration contract
(§§5–8).
