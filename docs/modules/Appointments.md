# Module: Appointments

**Status:** 🔜 Planned — **not implemented** · planned tables: `appointments`,
`queue`

## Purpose (target)
Booking and the live waiting queue: schedule patient visits, manage a
token/queue on arrival, and drive reminders.

## Target design (planned — needs approval)
- `app/modules/appointments/` vertical slice
  (`models → repository → service → controller → view`).
- Tables (via migration F1): `appointments` (patient_id, doctor_id, scheduled_at,
  status, channel, notes) and `queue` (live token/status for the day).
- Routes e.g. `^/appointments$`, `^/queue$`; nav entry in the shell.
- Service: `book`, `reschedule`, `cancel`, `check_in`, `next_in_queue` — each
  audited.

## Integrations
- **WhatsApp** reminders use `{appointmentDate}`, `{meetingLink}` etc.
- **Online Consultation** creates a Meet link for remote appointments.
- **Patient Portal** lets patients self-book (after RBAC + API).
- Feeds Dashboard "today's schedule" and Analytics (no-show rates).

## Dependencies
Migrations (F1); benefits from RBAC (F3) so Reception owns booking. References
existing `patients` / doctor (acting user) IDs — does not replace them.

## Notes
The existing `visits.followup_date` is the seed of scheduling; Appointments
generalizes it into forward booking with status and queue.
