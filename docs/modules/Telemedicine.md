# Module: Telemedicine (Online Consultation)

**Status:** 🔜 Planned — **not implemented** · planned table: `sessions`

## Purpose (target)
Remote consultations: create a video/Google Meet session tied to an appointment
and run the same consultation workflow for a remote patient.

## Target design (planned — needs approval)
- `app/modules/telemedicine/` vertical slice.
- Table (migration F1): `sessions` (appointment_id/patient_id, meeting_link,
  provider, scheduled_at, started_at, ended_at, status).
- Service: `create_session(appointment)` → generates a Meet link;
  `session_for_appointment`, `start`, `end`.
- Meeting provider (Google Meet or other) behind an interface; credentials in
  Settings/env, never committed.

## Integrations
- **Appointments** — a remote appointment spawns a session.
- **WhatsApp** — sends `{meetingLink}` via the Google Meet template.
- **Consultation Workspace** — the doctor runs the normal visit workflow during
  the session; notes/prescription persist to `visits` as usual.
- **Patient Portal** — patient joins from their portal.

## Dependencies
Migrations (F1), Appointments, Settings (F2, Meet config). Networked feature →
requires RBAC (F3) and transport security.

## Notes
The clinical record is identical to an in-person visit — telemedicine only adds
the session/link layer around the existing consultation.
