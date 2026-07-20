# WiseOS Health — Internal API (routes + service contracts)

> There is **no network/HTTP API** today — Wise PMS is a local desktop app. This
> document is the **internal contract**: navigation routes and the public
> service functions each module exposes. **Last updated:** 2026-07-20.

## Navigation routes

Routes are regex patterns registered by each module's `controller.py` and
assembled in `app/bootstrap.py`. Handlers are `handler(page, params, query)`.
The router enforces a **session guard** (all routes except `/login` require a
logged-in user) and falls back to `/dashboard`.

| Route | Module | Controller |
| ----- | ------ | ---------- |
| `^/login$` | authentication | `login_controller` |
| `^/dashboard$` | dashboard | `dashboard_controller` |
| `^/register$` | registration | `registration_controller` |
| `^/search$` | patients | `search_controller` |
| `^/patient/(?P<pid>\d+)$` | patients | `profile_controller` |
| `^/patient/(?P<pid>\d+)/edit$` | patients | `edit_controller` |
| `^/patient/(?P<pid>\d+)/case(?:/(?P<cid>new\|\d+))?$` | cases | `case_controller` |
| `^/patient/(?P<pid>\d+)/visit(?:/(?P<vid>new\|\d+))?$` | visits | `visit_controller` |

Query strings (e.g. `?case=<id>` on the visit route) are passed to the handler
as the `query` argument.

## Service contracts (public functions)

Services are module-level functions; each returns plain `dict`/`list[dict]`/`int`
and writes an audit row on mutation.

### authentication.service
- `authenticate(username, password) -> dict | None`
- `logout(user) -> None`

### patients.service
- `create_patient(data, user_id) -> dict` (returns saved, incl. `reg_no`)
- `update_patient(patient_id, data, user_id) -> None`
- `deactivate_patient(patient_id, user_id) -> None` (soft delete)
- `get_patient(patient_id) -> dict | None`
- `search_patients(query, limit=50) -> list[dict]`
- `recent_patients(limit=10) -> list[dict]`
- `patient_stats() -> dict`
- const `PATIENT_FIELDS`

### cases.service
- `create_case(patient_id, data, user_id) -> int`
- `update_case(case_id, data, user_id) -> None`
- `get_case(case_id) -> dict | None`
- `cases_for_patient(patient_id) -> list[dict]`

### visits.service
- `create_visit(patient_id, data, user_id) -> int`
- `update_visit(visit_id, data, user_id) -> None`
- `get_visit(visit_id) -> dict | None`
- `visits_for_patient(patient_id) -> list[dict]`
- `prescription_items_for_visit(visit_id) -> list[dict]`
- `visit_stats() -> dict`
- re-export `extract_prescription_items(text) -> list[dict]`

### attachments.service
- `add_attachment(patient_id, reg_no, source_path, user_id, visit_id=None) -> int`
- `attachments_for_patient(patient_id) -> list[dict]`
- `delete_attachment(attach_id, user_id) -> None`
- `absolute_path(attachment) -> str`

### timeline.service
- `timeline_for_patient(patient_id) -> list[dict]` (merged visits+cases+
  attachments, newest first; each event has `kind/id/ts/title/summary/extra`)

### audit.service
- `log_action(user_id, action_type, entity_type, entity_id, details="") -> None`
  (never raises)

### backup.service
- `backup_now() -> str` (path to `backups/backup_*.zip`)

## Future public API

A network API (REST/GraphQL) is a **planned** surface for Patient Portal, Mobile,
and integrations. Because services and repositories are UI-agnostic, an API
layer can call the same services without touching them. Not in scope until after
RBAC (F3) and encryption at rest (F7).
