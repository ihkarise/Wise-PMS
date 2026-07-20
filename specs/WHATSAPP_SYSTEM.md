# WhatsApp System — Specification

> **Status:** Design only (Phase 2). Not implemented. Backlog **E1**. Planned
> tables: `message_templates`, `messages`. **Last updated:** 2026-07-20.
> Extends [`../docs/modules/WhatsApp.md`](../docs/modules/WhatsApp.md).

## 1. Purpose

Templated patient messaging for the key moments in the patient journey —
reusable, **editable-in-Settings** templates with variable substitution. Messaging
drives retention and follow-up (Constitution Art. II §5).

## 2. Supported templates

| Key | Template | Trigger |
| --- | -------- | ------- |
| `welcome` | Welcome | New patient registered |
| `appointment_confirmation` | Appointment Confirmation | Booking created |
| `reminder` | Reminder | Before an appointment |
| `google_meet` | Google Meet Invitation | Telemedicine session created |
| `medicine_ready` | Medicine Ready | Dispense order fulfilled |
| `followup_reminder` | Follow-up Reminder | `followup_date` due |
| `birthday` | Birthday Greeting | Patient `dob` matches today |
| `festival` | Festival Greeting | Configured festival date |

All templates are seeded but **fully editable** by the clinician in Settings.

## 3. Variables

Supported variables map onto existing patient/settings fields:

| Variable | Source |
| -------- | ------ |
| `{regname}` | `patients.name` |
| `{fileno}` | `patients.reg_no` |
| `{doctorContact}` | `settings.phone` / doctor contact |
| `{appointmentDate}` | appointment / `followup_date` |
| `{doctorName}` | `settings.doctor_name` |
| `{clinicName}` | `settings.clinic_name` |
| `{meetingLink}` | telemedicine session link |

Rendering substitutes variables from the patient + settings + a per-send context
dict. Unknown/empty variables render blank (never leak `{...}` to the patient).

## 4. Data model (planned — needs F1)

```
message_templates
  id · key (UK) · name · body (with {variables}) · channel (whatsapp) ·
  enabled · updated_at

messages
  id · patient_id FK · template_key · rendered_body · channel ·
  status (queued|sent|failed|skipped) · provider_ref · sent_at · created_at
```

- `message_templates` is edited in Settings (F2).
- `messages` logs every send (or skip) for audit and to avoid duplicates.

## 5. Provider abstraction (swappable, secrets external)

Per Constitution Art. III §9:

```
WhatsAppProvider (interface)
  send(phone, body) -> SendResult { status, provider_ref }

Implementations (planned):
  • LinkProvider          (wa.me link / click-to-send — ₹0, manual send)
  • BusinessApiProvider   (WhatsApp Business API — opt-in, key in Settings/env)
```

Default is the **link-based** approach (no cost, no committed secret). The
Business API is an opt-in with credentials in Settings/env, never committed.

## 6. Service contract (target)

```
whatsapp.service
  templates() -> list[dict]
  get_template(key) -> dict | None
  save_template(key, body, user_id) -> None            # from Settings
  render(key, patient, context) -> str                 # variable substitution
  send(patient, key, context, user_id) -> int          # render + provider + log
```

- `send` renders, calls the provider, writes a `messages` row, and audits.
- **Consent/opt-out** is respected: a patient who opted out is `skipped` (logged),
  never sent (Constitution Art. VI §5).

## 7. Integration points

| Moment | Template | Module |
| ------ | -------- | ------ |
| Registration | `welcome` | patients |
| Booking | `appointment_confirmation` | Appointments |
| Pre-visit | `reminder` | Appointments |
| Telemedicine | `google_meet` (`{meetingLink}`) | Telemedicine |
| Dispense done | `medicine_ready` | Dispensing |
| Follow-up due | `followup_reminder` | visits / Dashboard |
| Birthday | `birthday` (needs `dob`) | patients |
| Festival | `festival` | scheduler / Settings |

## 8. Settings integration

Templates live in **Settings → WhatsApp** (F2): edit body, insert variables from
a palette, enable/disable per template, choose provider, store API credentials
(env-backed). This is why Settings is an early foundation phase — WhatsApp and
Printer both consume its templates. See [`SETTINGS_SYSTEM.md`](./SETTINGS_SYSTEM.md).

## 9. Dependencies & sequencing

- **Requires:** F1 (tables), F2 (Settings for templates), F3 (RBAC to gate who
  can send). Birthday needs `dob` populated.
- **Feeds:** retention loop with Appointments, Dispensing, Follow-up, Telemedicine.
- **Sequencing:** ship link-based (₹0) first; Business API later as opt-in.

## 10. Manual test checklist (implementing phase)

- [ ] A template renders with all variables substituted; empty vars render blank.
- [ ] Editing a template in Settings changes the rendered output.
- [ ] Every send/skip is logged to `messages` and audited.
- [ ] Opted-out patients are skipped, never sent.
- [ ] Link provider works with no credentials and no network dependency at ₹0.
- [ ] Model/table parity green for new tables.

## 11. Risks

- **Consent & compliance** — messaging PHI-adjacent content requires opt-out and
  logging; never message without a recorded basis.
- **Provider lock-in** — the interface keeps the backend swappable; keep secrets
  external.
</content>
