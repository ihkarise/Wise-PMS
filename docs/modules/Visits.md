# Module: Visits (Consultation)

**Status:** ✅ Built · **Path:** `app/modules/visits/` ·
**Tables:** `visits`, `prescription_items`

## Purpose
A **visit** is one consultation **event** (encounter), optionally linked to a
case. Per ADR-001 / ADR-0009 the visit stays the *event*; the clinical *document*
now lives in the separate **`consultations`** aggregate (1:1 via `visit_id`), so
`visits` is **not** widened with narrative consultation fields. See
[`Consultation.md`](./Consultation.md).

## Layers
`models.py` (`Visit`) · `repository.py` (`VisitRepository` — inserts a visit and
its prescription items atomically in one transaction) · `service.py` ·
`controller.py` · `view.py`.

## Public service API
- `create_visit(patient_id, data, user_id) -> int`
- `update_visit(visit_id, data, user_id)`
- `get_visit(visit_id) -> dict | None`
- `visits_for_patient(patient_id) -> list[dict]`
- `prescription_items_for_visit(visit_id) -> list[dict]`
- `visit_stats() -> dict`
- re-export `extract_prescription_items(text) -> list[dict]`

## Route
`^/patient/(?P<pid>\d+)/visit(?:/(?P<vid>new|\d+))?$`, optional `?case=<id>`.

## Fields
Three **narrative** editors — `visit_notes`, `investigation_notes`,
`prescription_notes` — plus `visit_type` (`CONSULTATION_TYPES`), `visit_date`,
`followup_date`, `outcome` (`VISIT_OUTCOMES`), `case_id` (nullable).

## Prescription intelligence
On every create/update the service runs `app.utils.prescription.
extract_prescription_items` over `prescription_notes`, re-deriving
`prescription_items` (delete + insert). Detects `Bell 200`, `Bry 30 TDS`; skips
lines starting with `continue`, `review`, `placebo`, etc. **The narrative stays
the source of truth.** The view renders a live "detected medicines" panel from
the same helper.

## Dependencies
`visits.service → audit.service`, `visits.service → utils.prescription`. Used by
profile, dashboard, timeline.

## Future — Consultation Workspace
This module is the seed of the single integrated consultation screen
(see [`../CLINICAL_WORKFLOW.md`](../CLINICAL_WORKFLOW.md)): chief complaint,
history, examination, diagnosis, investigation, OCR results, timeline, protocol
suggestions, prescription, pricing, remarks, print/dispense/invoice, follow-up.
Medicine pricing depends on WHIMS; suggestions on the Protocol Engine.
