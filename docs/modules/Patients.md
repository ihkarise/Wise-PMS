# Module: Patients

**Status:** ✅ Built · **Path:** `app/modules/patients/` · **Table:** `patients`

## Purpose
Core patient registry: create, edit, soft-delete, search, and stats. The
longitudinal record (cases, visits, attachments) hangs off a patient.

## Layers
- `models.py` — `Patient` dataclass (mirrors the `patients` columns)
- `repository.py` — `PatientRepository` + `PATIENT_FIELDS`; SQL for CRUD,
  reg-no generation, search, recent, stats
- `service.py` — rules + audit (see below)
- `controller.py` — routes `search`, `profile`, `edit`
- `views/` — `search.py`, `profile.py` (profile + edit)

## Public service API
- `create_patient(data, user_id) -> dict` (returns saved incl. `reg_no`)
- `update_patient(patient_id, data, user_id)`
- `deactivate_patient(patient_id, user_id)` — **soft delete** (`is_active=0`)
- `get_patient(patient_id) -> dict | None`
- `search_patients(query, limit=50)` — Name/Phone/Reg No/Place, active only
- `recent_patients(limit=10)` · `patient_stats() -> dict`

## Routes
`^/search$` · `^/patient/(?P<pid>\d+)$` · `^/patient/(?P<pid>\d+)/edit$`

## Key behaviors
- **Auto reg-no** `P000001…` generated with collision checking.
- **Soft delete only** — patients are never physically removed.
- Profile screen has tabs: Profile · Cases · Timeline · Attachments, with quick
  actions New Case / New Visit / Upload File.
- Dropdown vocabularies (`GENDERS`, `BLOOD_GROUPS`, `CONSULTATION_TYPES`) come
  from `app/config/constants.py`.

## Dependencies
`patients.service → audit.service`, `patients.repository → core`. Consumed by
registration, dashboard, cases, visits, timeline, attachments views.

## Known limitations
Doctor is free text (L3); dates are string-typed (L2); no pagination on large
result sets (L11). See [`../KNOWN_LIMITATIONS.md`](../KNOWN_LIMITATIONS.md).

## Future
Feeds Patient Portal identity, WhatsApp variables (`{regname}`, `{fileno}`),
and analytics cohorts.
