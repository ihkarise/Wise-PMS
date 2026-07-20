# EPIC-08 — Timeline Engine (unified)

> **Spec:** [`../TIMELINE_ENGINE.md`](../TIMELINE_ENGINE.md) · **Backlog:** — ·
> **Stage:** B — Clinical Core · **Depends on:** timeline (built); each source
> module as it ships · **Complexity:** M · **Risk:** Low ·
> **Status:** Backlog (planning only). Governed by
> [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. IV §5.

## 1. Objective

Grow the existing timeline (visits + cases + attachments) into **one continuous
medical timeline** spanning every module — a read model with a stable event
contract that new modules join by adding a repository query, never by changing the
contract.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E08-F1 | Stable event contract | `kind/id/ts/title/summary/extra/followup/ref`; unknown-kind fallback |
| E08-F2 | Filtering | `kinds=` and `since=` (additive; default contract unchanged) |
| E08-F3 | Source contributions | Appointments, Investigation, OCR, Dispense, Billing, Print, Protocol, AI events |
| E08-F4 | Workspace integration | Right-rail peek + filtered Investigation Timeline |
| E08-F5 | Pagination (F6) | Top-N + "load more" for long histories |

## 3. User stories

- **E08-F1-S1** — As a doctor, I want one feed of everything that happened to a
  patient, so that I regain context fast before a consult.
- **E08-F2-S1** — As a doctor, I want to filter to reports only, so that I can
  scan investigations quickly.
- **E08-F3-S1** — As a maintainer, I want a new module to add its events by a
  single repository query, so that the timeline grows without rewrites.
- **E08-F5-S1** — As a doctor with a long-history patient, I want the timeline to
  load quickly and page, so that it stays responsive.

## 4. Engineering tasks

- **E08-T1** — Freeze the event shape in `timeline.service`; centralize merge/sort;
  add unknown-kind fallback for consumers.
- **E08-T2** — Add `kinds`/`since` params (default call unchanged → golden green).
- **E08-T3** — Contribution pattern: each source module adds a `TimelineRepository`
  query when it ships (Appointments/Investigation/OCR/Dispense/Billing/Print/
  Protocol/AI) — tracked as sub-tasks under each epic.
- **E08-T4** — Workspace peek + filtered Investigation Timeline.
- **E08-T5** — Pagination/top-N (F6) for long histories.
- **E08-T6** — Tests + docs (Timeline module doc, CHANGELOG).

## 5. Dependencies

- **Upstream:** timeline (built).
- **Grows with:** EPIC-10, EPIC-06, EPIC-07, EPIC-12, EPIC-09, EPIC-05, EPIC-19 —
  each contributes events when it ships (no big-bang).

## 6. Acceptance criteria

- **AC1** — *Given* a new source module, *when* it adds events, *then* they appear
  with correct `kind/ts/title` and open the right record via `ref`.
- **AC2** — *Given* existing consumers, *when* a new `kind` appears, *then* they
  render gracefully (unknown-kind fallback).
- **AC3** — *Given* the default `timeline_for_patient(pid)`, *when* called, *then*
  its contract is unchanged (regression golden green).
- **AC4** — *Given* `kinds`/`since`, *when* passed, *then* the expected subset
  returns.
- **AC5** — *Given* a long history, *when* loaded, *then* it pages (top-N + load
  more) and stays responsive.

## 7. Regression tests

- **Must stay green:** golden (default timeline contract byte-identical), models,
  router, views.
- **New:** event-shape contract test, filtering tests, unknown-kind fallback test,
  per-source contribution tests (added under each contributing epic), pagination
  test.

## 8. Rollout phases

- **E08-R1** — Freeze contract + add filtering (no behavior change to default).
- **E08-R2** — Wire contributions as source epics ship (ongoing).
- **E08-R3** — Workspace peek + filtered view.
- **E08-R4** — Pagination (F6) when histories grow.

## 9. Rollback

Filtering/pagination are additive; revert to the current merged feed. No table, no
data risk (pure read model).

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: default contract byte-identical; each
contributing epic adds its events without altering the timeline core.
</content>
