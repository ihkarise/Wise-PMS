# Module: WhatsApp (WhatsApp Automation)

**Status:** 🔜 Planned — **not implemented** · planned tables: `message_templates`,
`messages`

## Purpose (target)
Templated patient messaging: reusable, editable templates sent for key moments.

## Templates
Welcome · Appointment · Reminder · Google Meet · Medicine Ready · Follow-up ·
Birthday · Festival Greeting.

## Variables
`{regname}` · `{fileno}` · `{doctorContact}` · `{appointmentDate}` ·
`{doctorName}` · `{meetingLink}` · `{clinicName}`. These map onto existing
patient/settings fields.

## Target design (planned — needs approval)
- `app/modules/whatsapp/` vertical slice.
- Tables (migration F1): `message_templates` (key, name, body with variables,
  enabled) and `messages` (patient_id, template_key, rendered_body, status,
  sent_at, channel).
- Templates are **editable inside Settings** (per the charter).
- Service: `render(template_key, patient, context)` → substitutes variables;
  `send(patient, template_key, context)`; `templates()` / `save_template`.
- Provider behind an interface (WhatsApp Business API / link-based) so the
  backend is swappable and secrets stay in Settings/env (never committed).

## Integrations
- **Appointments** → reminders, Meet links.
- **Dispensing** → "Medicine Ready".
- **Patients** → welcome, birthday (needs `dob`), festival greetings.
- **Online Consultation** → `{meetingLink}`.

## Dependencies
Migrations (F1), Settings (F2, template editing). RBAC (F3) to gate who can send.

## Notes
Respect consent/opt-out; log every send to `messages` and audit it.
