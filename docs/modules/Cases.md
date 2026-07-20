# Module: Cases (Case Records)

**Status:** ✅ Built · **Path:** `app/modules/cases/` · **Table:** `patient_cases`

## Purpose
A **case** is a clinical thread for one patient (e.g. "Migraine", "Allergic
Rhinitis"). One patient → many cases; one case → many visits.

## Layers
`models.py` (`Case`) · `repository.py` (`CaseRepository`, incl. visit-count
subquery) · `service.py` · `controller.py` · `view.py`.

## Public service API
- `create_case(patient_id, data, user_id) -> int`
- `update_case(case_id, data, user_id)`
- `get_case(case_id) -> dict | None`
- `cases_for_patient(patient_id) -> list[dict]`

## Route
`^/patient/(?P<pid>\d+)/case(?:/(?P<cid>new|\d+))?$` (`new` sentinel = create).

## Fields
`case_title`, `diagnosis`, `case_notes` (narrative), `status`
(`Open`/`Closed`/`Resolved`/`On Hold` from `CASE_STATUSES`), `doctor_id`
(acting user), `created_at`.

## Key behaviors
- Narrative-first: `case_notes` is free text and authoritative.
- "Save + Start Visit" flows straight into the Visit screen with the case
  preselected (`?case=<id>`).
- Every create/update writes an audit row.

## Dependencies
`cases.service → audit.service`. Used by patient profile (Cases tab) and the
visit view (case linkage).

## Future
The Consultation Workspace opens **on** a case; Protocol Engine suggestions and
case-level follow-up schedules attach here.
