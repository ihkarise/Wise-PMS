# EPIC-11 — WhatsApp Automation

> **Spec:** [`../WHATSAPP_SYSTEM.md`](../WHATSAPP_SYSTEM.md) · **Backlog:** E1 ·
> **Stage:** C — Operations · **Depends on:** EPIC-01, EPIC-02, EPIC-03 ·
> **Complexity:** M · **Risk:** Medium · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. VI §5.

## 1. Objective

Templated patient messaging for key moments — reusable, editable-in-Settings
templates with variable substitution and consent/opt-out. Drives retention and
follow-up. Ships link-based (₹0) first; Business API is an opt-in.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E11-F1 | Templates + variables | 8 templates; `{regname}/{fileno}/…` mapped to fields |
| E11-F2 | Render + send | Substitute + provider send + log to `messages` |
| E11-F3 | Provider interface | LinkProvider default; BusinessApiProvider opt-in (env creds) |
| E11-F4 | Consent / opt-out | Opted-out patients skipped + logged, never sent |
| E11-F5 | Trigger integrations | Registration, booking, dispense, follow-up, birthday, festival |
| E11-F6 | Settings editing | Templates editable in Settings (EPIC-02) |

## 3. User stories

- **E11-F2-S1** — As reception, I want to send a welcome message, so that new
  patients feel looked after.
- **E11-F5-S1** — As the clinic, I want follow-up reminders sent when due, so that
  patients return.
- **E11-F3-S1** — As the clinic, I want a ₹0 link-based option by default, so that
  messaging costs nothing to start.
- **E11-F4-S1** — As a patient, I want to opt out, so that I stop receiving
  messages — and the clinic must respect it.
- **E11-F6-S1** — As reception, I want to edit message wording, so that it matches
  our voice.

## 4. Engineering tasks

- **E11-T1** — Migration: `message_templates`, `messages` (E11 tables live with
  Settings per spec; seed the 8 templates).
- **E11-T2** — `modules/whatsapp/` slice: `templates/get_template/save_template/
  render/send`.
- **E11-T3** — `WhatsAppProvider` interface + `LinkProvider` (default) +
  `BusinessApiProvider` (opt-in; secret via env, EPIC-02).
- **E11-T4** — Variable substitution (empty vars render blank, never leak `{...}`).
- **E11-T5** — Consent/opt-out model + skip logging.
- **E11-T6** — Trigger hooks: registration/booking/dispense/follow-up/birthday
  (needs `dob`)/festival.
- **E11-T7** — Settings → WhatsApp editor (EPIC-02); RBAC `whatsapp.send`.
- **E11-T8** — Timeline message events + audit; tests + docs (WhatsApp module doc).

## 5. Dependencies

- **Upstream:** EPIC-01, EPIC-02 (templates/secrets), EPIC-03 (gate send). Birthday
  needs `dob`.
- **With:** EPIC-10 (confirmations/reminders), EPIC-12 (medicine ready), EPIC-17
  (`{meetingLink}`), EPIC-16 (portal notifications).

## 6. Acceptance criteria

- **AC1** — *Given* a template + patient, *when* rendered, *then* variables
  substitute and empty ones render blank.
- **AC2** — *Given* an edited template, *when* saved, *then* rendered output
  changes.
- **AC3** — *Given* a send, *when* performed, *then* a `messages` row + audit are
  written.
- **AC4** — *Given* an opted-out patient, *when* a send is attempted, *then* it is
  skipped and logged, never sent.
- **AC5** — *Given* the link provider, *when* used, *then* it works with no
  credentials and no committed secret.

## 7. Regression tests

- **Must stay green:** golden, models, router, views.
- **New:** render/substitution tests, provider-interface test (fake provider),
  opt-out skip test, send-logging test, template save/get, model/table parity.

## 8. Rollout phases

- **E11-R1** — Tables + seed templates + render + LinkProvider (₹0).
- **E11-R2** — Send logging + consent/opt-out + Settings editor.
- **E11-R3** — Trigger integrations (registration/booking/dispense/follow-up).
- **E11-R4** — Business API opt-in + birthday/festival; docs closeout.

## 9. Rollback

Revert module → no messages sent; tables inert. No data destroyed.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: opt-out always honored; every send/skip
logged; link provider works at ₹0 offline-adjacent; no secret committed.
</content>
