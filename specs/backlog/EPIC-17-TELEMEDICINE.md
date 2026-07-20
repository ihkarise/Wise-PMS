# EPIC-17 — Telemedicine (Online Consultation)

> **Spec:** [`../../docs/modules/Telemedicine.md`](../../docs/modules/Telemedicine.md) ·
> **Backlog:** E2 · **Stage:** D — Insight & Reach ·
> **Depends on:** EPIC-01, EPIC-10, EPIC-02 (Meet creds), EPIC-03 ·
> **Complexity:** M · **Risk:** Medium · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. III §9, VI.

## 1. Objective

Remote consultations: a video/Google Meet session tied to an appointment, running
the **same** consultation workflow for a remote patient. Telemedicine only adds a
session/link layer around the existing visit.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E17-F1 | Sessions | `sessions` (appointment/patient, meeting_link, provider, status, times) |
| E17-F2 | Meet provider | Link generation behind an interface (creds in Settings/env) |
| E17-F3 | Same visit workflow | Notes/prescription persist to `visits` as usual |
| E17-F4 | WhatsApp Meet invite | `{meetingLink}` via the Google Meet template (EPIC-11) |
| E17-F5 | Portal join | Patient joins from the portal (EPIC-16) |

## 3. User stories

- **E17-F1-S1** — As reception, I want a remote appointment to spawn a session, so
  that the patient gets a link.
- **E17-F3-S1** — As a doctor, I want the normal Workspace during a remote consult,
  so that the record is identical to in-person.
- **E17-F4-S1** — As a patient, I want the meeting link by WhatsApp, so that I can
  join easily.

## 4. Engineering tasks

- **E17-T1** — Migration: `sessions`.
- **E17-T2** — `modules/telemedicine/` slice: `create_session(appointment)`,
  `session_for_appointment`, `start`, `end`; `MeetingProvider` interface (Google
  Meet default; creds via Settings/env).
- **E17-T3** — Appointment (EPIC-10) `channel=online` spawns a session; Workspace
  runs normally.
- **E17-T4** — WhatsApp Meet template hook (EPIC-11); Portal join (EPIC-16).
- **E17-T5** — RBAC; tests + docs (Telemedicine module doc).

## 5. Dependencies

- **Upstream:** EPIC-01, EPIC-10, EPIC-02 (Meet creds), EPIC-03, transport
  security.
- **Downstream:** EPIC-16 (join), EPIC-11 (invite).

## 6. Acceptance criteria

- **AC1** — *Given* an online appointment, *when* created, *then* a session with a
  meeting link is generated.
- **AC2** — *Given* a remote consult, *when* conducted, *then* notes/prescription
  persist to `visits` identically to in-person.
- **AC3** — *Given* a session, *when* created, *then* the Meet template can send
  `{meetingLink}`.
- **AC4** — *Given* provider creds absent, *when* creating a session, *then* it
  fails gracefully with a clear message (no crash).

## 7. Regression tests

- **Must stay green:** golden, models, router, views.
- **New:** session lifecycle tests, provider-interface test (fake provider),
  Workspace-persist-parity test, model/table parity for `sessions`.

## 8. Rollout phases

- **E17-R1** — Sessions + Meet provider interface + link generation.
- **E17-R2** — Appointment→session + Workspace run; WhatsApp invite.
- **E17-R3** — Portal join; docs closeout.

## 9. Rollback

Revert module → in-person flow unaffected; `sessions` inert. No data destroyed.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: remote visit record identical to
in-person; provider swappable; creds never committed.
</content>
