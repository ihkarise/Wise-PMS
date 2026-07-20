# Waiting Queue — Specification

> **Status:** Design only (Phase 2). Not implemented. Planned table: `queue`.
> **Last updated:** 2026-07-20. Companion to
> [`APPOINTMENT_SYSTEM.md`](./APPOINTMENT_SYSTEM.md).

## 1. Purpose

The **live daily queue**: a token board of who is waiting, in what order, and
their state, so Reception and the Doctor share one real-time view of the clinic's
day. It is the operational heartbeat between check-in and consultation.

## 2. Concept

- A patient **checks in** (from a booked appointment, or as a walk-in) and
  receives a **token** (sequential for the day/location).
- The queue shows waiting patients ordered by token, with status.
- The Doctor calls the **next** patient, which opens the Consultation Workspace.

```
Check-in (Appointments)  ──►  queue token assigned (waiting)
        │
        ▼
Reception/Doctor view: [T1 done] [T2 in-consult] [T3 waiting] [T4 waiting] …
        │
        ▼
"Call next" ──► token → in_consult ──► opens Consultation Workspace
        │
        ▼
Complete Visit ──► token → done
```

## 3. Data model (planned — needs F1)

```
queue
  id · date · location_id (nullable) · token_no ·
  patient_id FK · appointment_id FK (nullable) ·
  status (waiting|called|in_consult|done|skipped|left) ·
  checked_in_at · called_at · started_at · done_at · priority (normal|urgent)
```

- `token_no` is sequential per `(date, location_id)`.
- `appointment_id` is nullable for walk-ins (drop-in).
- `priority = urgent` lets a patient jump the queue (doctor's discretion, audited).

## 4. Status lifecycle

```
waiting → called → in_consult → done
   │        │          │
   ├────────┴──────────┴──► skipped   (no response when called)
   └───────────────────────► left     (patient left before consult)
```

## 5. Service contract (target)

```
queue.service
  check_in(patient_id, appointment_id, location_id, user_id) -> int   # token
  current_queue(date=today, location_id=None) -> list[dict]
  call_next(location_id, user_id) -> dict | None       # next waiting → called
  call(token_id, user_id) -> None
  start_consult(token_id, user_id) -> None             # → in_consult
  complete(token_id, user_id) -> None                  # → done
  mark(token_id, status, user_id) -> None              # skipped | left
  set_priority(token_id, priority, user_id) -> None
```

All mutations audited. `current_queue` is the live read model for the board.

## 6. UI surfaces

- **Reception queue board** — full day view, add walk-in, set priority, re-order.
- **Doctor queue panel** — "next patient" + waiting count, one click into the
  Workspace.
- **Dashboard** — waiting count as a stat; **Waiting-room display** (optional,
  future) — a read-only token board screen.

All built from `shared/theme.py` + `shared/widgets.py` (Constitution Art. V).

## 7. Real-time behavior

- The queue is **rebuilt from the DB** on each action (current app model). A
  future lightweight polling/refresh keeps multiple views (reception + doctor)
  roughly in sync without a server (SQLite single-writer, L12) — acceptable for a
  desktop clinic; the sync story (F8) accounts for multi-device later.
- No websockets/servers in the offline core; refresh is on-action + optional
  interval.

## 8. Integrations

| With | For |
| ---- | --- |
| **Appointments** | check-in source; status mirroring |
| **Consultation Workspace** | "call next" opens the Workspace; complete closes the token |
| **Dashboard** | waiting count |
| **Analytics** | wait times, throughput |
| **Timeline** | check-in/consult events |

## 9. Dependencies & sequencing

- **Requires:** F1 (table). Best shipped **with** Appointments (check-in) and
  before/with the Consultation Workspace (call-next hand-off). RBAC (F3) so
  Reception/Doctor roles see the right controls.
- Date handling (F5) helps with per-day token scoping.

## 10. Manual test checklist (implementing phase)

- [ ] Check-in assigns a sequential token per day/location.
- [ ] Walk-in (no appointment) still gets a token.
- [ ] "Call next" advances the correct waiting token and opens the Workspace.
- [ ] Priority=urgent reorders correctly; the change is audited.
- [ ] Completing a visit closes the token to done.
- [ ] Two views (reception + doctor) converge after refresh.
- [ ] Model/table parity green for `queue`.

## 11. Risks

- **Multi-view consistency** without a server — mitigate with on-action refresh;
  true real-time waits for sync (F8).
- **Token scoping** across midnight/locations — key strictly on `(date,
  location_id)`.
</content>
