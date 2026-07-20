# EPIC-06 — Investigation Engine

> **Spec:** [`../INVESTIGATION_ENGINE.md`](../INVESTIGATION_ENGINE.md) ·
> **Backlog:** C4 · **Stage:** B — Clinical Core ·
> **Depends on:** EPIC-01, EPIC-04 · **Complexity:** M · **Risk:** Medium ·
> **Status:** Backlog (planning only). Governed by
> [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. II §2.

## 1. Objective

Order tests during a consultation, record results (uploaded reports + structured
values), and compare them over time. Turns "the patient did some tests" into a
longitudinal, comparable dataset the Workspace surfaces inline. Works with manual
entry before OCR (EPIC-07) exists.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E06-F1 | Orders | Order tests (free-text/catalog/protocol) linked to patient/case/visit |
| E06-F2 | Results | Record results (manual or OCR-sourced); link to attachment |
| E06-F3 | Trend series | Same analyte across reports (`results_for_patient`) |
| E06-F4 | Comparison | This vs. prior; abnormal flags from reference range |
| E06-F5 | Workspace panels | Investigation Panel · Investigation Timeline · Comparison |
| E06-F6 | Catalog | Small, growable test/unit catalog for normalization |

## 3. User stories

- **E06-F1-S1** — As a doctor, I want to order tests in the consultation, so that
  the follow-up knows what to expect back.
- **E06-F2-S1** — As a doctor, I want to record a result even without a prior
  order, so that walk-in reports are captured.
- **E06-F3-S1** — As a doctor, I want to see an analyte trend across visits, so
  that I can judge response over time.
- **E06-F4-S1** — As a doctor, I want abnormal values flagged from the report's
  reference range, so that I notice out-of-range results.

## 4. Engineering tasks

- **E06-T1** — Migration: `investigation_orders`, `investigation_results`
  (nullable `order_id`, `attachment_id`, `source = manual|ocr`).
- **E06-T2** — `modules/investigation/` slice: models, repository, service
  (`order`, `cancel_order`, `record_result`, `results_for_patient`, `compare`,
  `pending_orders`), controller, view/panels.
- **E06-T3** — Analyte/unit normalization catalog (start small).
- **E06-T4** — Workspace panels wiring (order typeahead, trend, comparison).
- **E06-T5** — Manual result entry (pre-OCR); accept OCR values later (EPIC-07).
- **E06-T6** — Tests + docs (Investigation module doc, CHANGELOG).

## 5. Dependencies

- **Upstream:** EPIC-01, EPIC-04 (surface); Attachments (built) for report links.
- **Downstream / with:** EPIC-07 (auto structured values), EPIC-08 (report events
  with values), EPIC-14 (graphs), EPIC-05 (recommended investigations), EPIC-19
  (interpretation).

## 6. Acceptance criteria

- **AC1** — *Given* a consultation, *when* tests are ordered, *then* orders link to
  patient/case/visit with status `ordered`.
- **AC2** — *Given* a report, *when* a result is recorded with no prior order,
  *then* it is stored (nullable `order_id`).
- **AC3** — *Given* multiple results for one analyte, *when* viewed, *then* a trend
  shows direction (↑/↓).
- **AC4** — *Given* a reference range, *when* a value is out of range, *then* it is
  flagged (never invented when absent).
- **AC5** — *Given* OCR values (EPIC-07), *when* present, *then* they populate as
  `source = ocr` and stay non-authoritative (manual override wins).

## 7. Regression tests

- **Must stay green:** golden, models, router, views.
- **New:** order/result service tests, trend/compare tests, abnormal-flag logic,
  manual-vs-OCR precedence, view-build, model/table parity, router contract.

## 8. Rollout phases

- **E06-R1** — Tables + order/result service + manual entry.
- **E06-R2** — Trend series + comparison + abnormal flags + catalog.
- **E06-R3** — Workspace panels (Panel · Timeline · Comparison).
- **E06-R4** — Accept OCR-sourced values (after EPIC-07); docs closeout.

## 9. Rollback

Revert module + hide panels; tables inert. Reports remain viewable via Attachments.
No data destroyed.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: useful with manual entry alone; abnormal
flags never fabricated.
</content>
