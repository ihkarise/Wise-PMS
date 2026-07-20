# EPIC-14 — Analytics & Reports

> **Spec:** [`../../docs/modules/Analytics.md`](../../docs/modules/Analytics.md),
> [`../../docs/modules/Reports.md`](../../docs/modules/Reports.md) ·
> **Backlog:** B5, D3 · **Stage:** D — Insight & Reach ·
> **Depends on:** structured data from Stages B/C · **Complexity:** M ·
> **Risk:** Low · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. IV §5.

## 1. Objective

Insight over the practice — charts/KPIs (Analytics) and tabular, exportable
reports (Reports) — as **read models** over existing data. No new base tables;
the narrative-first + structured-extraction design pays off here.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E14-F1 | Read models | Aggregates over patients/visits/prescription_items/audit (+ billing/inventory) |
| E14-F2 | Analytics view | Charts/KPIs (design-system palette; `dataviz` guidance) |
| E14-F3 | Reports view | Parameterized tabular reports (date range, doctor, module) |
| E14-F4 | Export engine (D3) | CSV/PDF to `exports/` (reserved folder) |
| E14-F5 | Cross-module feeds | Protocol usage vs. outcome; lab trends; revenue; consumption |

## 3. User stories

- **E14-F2-S1** — As a practice owner, I want KPIs (patients, visits, follow-ups,
  outcomes), so that I understand the practice at a glance.
- **E14-F3-S1** — As accounts, I want a date-range report of visits/revenue, so
  that I can reconcile.
- **E14-F4-S1** — As an Administrator, I want to export a report, so that I can
  share or archive it.
- **E14-F5-S1** — As a doctor, I want protocol-vs-outcome insight, so that I refine
  my templates.

## 4. Engineering tasks

- **E14-T1** — `modules/analytics/` + `modules/reports/`: read models/query
  builders (shared), views, export.
- **E14-T2** — Charts per `DESIGN_SYSTEM.md` palette (load `dataviz` skill before
  building charts).
- **E14-T3** — Export to `exports/` (close D3); RBAC `reports.view`.
- **E14-T4** — Feeds from prescription_items, visits.outcome, cohorts, audit, and
  (when present) billing/inventory/OCR.
- **E14-T5** — Tests + docs (Analytics/Reports module docs, KNOWN_LIMITATIONS D3).

## 5. Dependencies

- **Upstream:** whichever data epics are live (visits/prescription built; billing/
  inventory/OCR enrich). Benefits from F5 (time series).
- **Downstream:** EPIC-19 (analytics features as AI inputs).

## 6. Acceptance criteria

- **AC1** — *Given* clinic data, *when* Analytics loads, *then* KPIs/charts compute
  from read models (no new base tables).
- **AC2** — *Given* a date range, *when* a report runs, *then* correct rows return.
- **AC3** — *Given* a report, *when* exported, *then* a file lands in `exports/`.
- **AC4** — *Given* protocol usage, *when* correlated, *then* outcome distributions
  render.
- **AC5** — *Given* RBAC, *when* an unauthorized role opens Analytics/Reports,
  *then* access is refused.

## 7. Regression tests

- **Must stay green:** golden, models, router, views.
- **New:** read-model query tests (deterministic aggregates), export round-trip,
  RBAC gating, view-build, router contract for `/analytics` + `/reports`.

## 8. Rollout phases

- **E14-R1** — Reports (tabular) over built data + export (D3).
- **E14-R2** — Analytics charts (KPIs, cohorts, outcomes).
- **E14-R3** — Billing/inventory/OCR feeds as those epics land.
- **E14-R4** — AI input hooks; docs closeout.

## 9. Rollback

Revert modules (read-only; no data risk). Routes/nav hidden.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: no new base tables; charts follow the
design system; exports land in `exports/`.
</content>
