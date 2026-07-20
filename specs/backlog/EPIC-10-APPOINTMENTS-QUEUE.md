# EPIC-10 — Appointments & Waiting Queue

> **Spec:** [`../APPOINTMENT_SYSTEM.md`](../APPOINTMENT_SYSTEM.md),
> [`../WAITING_QUEUE.md`](../WAITING_QUEUE.md) · **Backlog:** F5 (dates) ·
> **Stage:** C — Operations · **Depends on:** EPIC-01, EPIC-03, EPIC-04 ·
> **Complexity:** M · **Risk:** Medium · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md).

## 1. Objective

Forward booking (calendar, schedules, online booking, Meet), plus a live daily
**waiting queue** with tokens driving the day from check-in to consult. Generalizes
`visits.followup_date` into scheduling with status. Includes structured date/time
handling (F5).

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E10-F1 | Appointments model | `appointments` + `doctor_schedules`; status lifecycle |
| E10-F2 | Calendar & slots | Day/week view; `available_slots` from schedules minus booked |
| E10-F3 | Waiting Queue | `queue` token board; check-in → token → call-next → done |
| E10-F4 | Drop-in / drop-off | Walk-in tokenization; sample/report drop-off |
| E10-F5 | Reminder integration | Confirmation + reminder via EPIC-11 |
| E10-F6 | Online booking + Meet | Portal/link booking (`source=online`); Meet link (EPIC-17) |
| E10-F7 | Multi-location | Nullable `location_id`; single-location ignores it |
| E10-F8 | Structured dates (F5) | Real date/time handling + pickers |

## 3. User stories

- **E10-F2-S1** — As reception, I want to book into an open slot, so that we avoid
  double-booking.
- **E10-F3-S1** — As reception, I want a live token board, so that everyone sees
  who's waiting and next.
- **E10-F3-S2** — As a doctor, I want "call next" to open the Workspace for that
  patient, so that I move from queue to consult in one click.
- **E10-F4-S1** — As reception, I want to tokenize a walk-in, so that drop-ins join
  the same queue.
- **E10-F5-S1** — As reception, I want confirmations/reminders sent, so that
  no-shows drop.
- **E10-F8-S1** — As the clinic, I want validated dates/times, so that scheduling
  isn't corrupted by typos (closes L2).

## 4. Engineering tasks

- **E10-T1** — Migration: `appointments`, `doctor_schedules`, `queue`.
- **E10-T2** — `modules/appointments/` slice: `book/reschedule/cancel/check_in/
  mark_no_show/day_schedule/available_slots`; route `^/appointments$`.
- **E10-T3** — `modules/queue/` (or within appointments): `check_in/current_queue/
  call_next/call/start_consult/complete/mark/set_priority`; route `^/queue$`.
- **E10-T4** — Structured date/time helpers + pickers (F5); apply to
  `followup_date` too.
- **E10-T5** — Call-next → Workspace hand-off; status mirroring (in_consult/done).
- **E10-T6** — Reminder hooks (EPIC-11); online-booking source + Meet (EPIC-17).
- **E10-T7** — On-action refresh for multi-view consistency (reception + doctor);
  optional interval.
- **E10-T8** — Dashboard: today's schedule + waiting count; Timeline events.
- **E10-T9** — RBAC keys (`appointments.manage`, `queue.manage`); tests + docs.

## 5. Dependencies

- **Upstream:** EPIC-01, EPIC-03 (Reception owns booking), EPIC-04 (call-next
  target).
- **Downstream:** EPIC-11 (reminders), EPIC-17 (Meet), EPIC-16 (self-book),
  EPIC-14 (no-show/utilization).

## 6. Acceptance criteria

- **AC1** — *Given* a booked slot, *when* another booking targets it, *then* the
  double-booking is prevented.
- **AC2** — *Given* check-in, *when* performed, *then* a sequential token per
  `(date, location)` is created and appears on the board.
- **AC3** — *Given* a walk-in, *when* checked in, *then* a same-day appointment +
  token are created.
- **AC4** — *Given* "call next", *when* clicked, *then* the correct waiting token
  advances and the Workspace opens.
- **AC5** — *Given* a past, un-checked-in appointment, *when* processed, *then* it
  is marked no-show.
- **AC6** — *Given* two views, *when* refreshed, *then* they converge.
- **AC7** — *Given* a bad date, *when* entered, *then* it is rejected (F5).

## 7. Regression tests

- **Must stay green:** golden, models, router, views.
- **New:** booking/slot/no-show tests, queue lifecycle + priority tests, date
  validation tests, call-next hand-off interaction test, model/table parity for 3
  tables, router contract for `/appointments` + `/queue`.

## 8. Rollout phases

- **E10-R1** — Structured dates (F5) + appointments model + calendar/slots.
- **E10-R2** — Waiting Queue board + tokens + call-next hand-off.
- **E10-R3** — Drop-in/drop-off + reminders (EPIC-11) + Dashboard/Timeline.
- **E10-R4** — Online booking + Meet (EPIC-17); multi-location; docs closeout.

## 9. Rollback

Revert routes/nav → `followup_date` remains the scheduling seed; tables inert. No
data destroyed.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: no double-booking; queue converges across
views; dates validated (L2 closed).
</content>
