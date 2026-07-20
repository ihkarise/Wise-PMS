# Investigation Engine — Specification

> **Status:** Design only (Phase 2). Not implemented. Backlog **C4**. Planned
> tables: `investigation_orders`, `investigation_results`. **Last updated:**
> 2026-07-20. Works with [`OCR_ENGINE.md`](./OCR_ENGINE.md),
> [`TIMELINE_ENGINE.md`](./TIMELINE_ENGINE.md), and
> [`../docs/modules/Attachments.md`](../docs/modules/Attachments.md).

## 1. Purpose

A complete investigation module: **order** tests during a consultation, **record
results** (uploaded reports + structured values), and **compare** them over time.
It turns "the patient did some tests" into a longitudinal, comparable dataset
that the Consultation Workspace surfaces inline.

## 2. What every uploaded report must support

Per the charter, each report supports:

| Facet | Provided by | Status |
| ----- | ----------- | ------ |
| Original PDF | Attachments (stores the file) | ✅ |
| Image Preview | Attachments + viewer | ✅ (open) / 🔜 (inline preview) |
| OCR Text | OCR Engine | 🔜 |
| Structured Values | OCR Engine (test → value → unit → range) | 🔜 |
| Doctor Notes | Investigation result note | 🔜 |
| Timeline | Timeline Engine (report events) | ✅ (event) / 🔜 (values) |
| Historical Comparison | Investigation Engine (this vs. prior) | 🔜 |
| Future AI Summary | AI Assistant | 🔜 |
| Future Graphs | Analytics / trend charts | 🔜 |

## 3. Two halves: ordering and results

### 3a. Ordering (during consultation)
The doctor selects investigations to order (free-text or from a catalog / a
protocol's recommended list). An order records *what was requested*, so the
follow-up can check *what came back*.

### 3b. Results (on return / upload)
A result links an uploaded report (attachment) — and, via OCR, its structured
values — back to the order and the patient. Results are comparable across visits.

## 4. Data model (planned — needs F1)

```
investigation_orders
  id · patient_id FK · case_id FK (nullable) · visit_id FK (nullable) ·
  test_name · panel (nullable) · status (ordered|collected|resulted|cancelled) ·
  ordered_by · ordered_at · notes

investigation_results
  id · order_id FK (nullable) · patient_id FK · attachment_id FK (nullable) ·
  test_name · value · unit · reference_range · abnormal_flag ·
  resulted_at · doctor_notes · source (manual | ocr) · created_at
```

- Results can exist **without** a prior order (a patient walks in with a report) —
  `order_id` is nullable.
- Structured values are populated by **OCR** (`source = ocr`) or entered manually
  (`source = manual`); OCR values are **derived, non-authoritative** (Constitution
  Art. II §2).
- `test_name`/`unit` normalization lets the same analyte trend across reports.

## 5. Service contract (target)

```
investigation.service
  order(patient_id, tests, case_id, visit_id, user_id) -> list[int]
  cancel_order(order_id, user_id) -> None
  record_result(order_id | patient_id, attachment_id, values, user_id) -> int
  results_for_patient(patient_id, test_name=None) -> list[dict]   # trend series
  compare(patient_id, test_name) -> ComparisonSeries              # this vs prior
  pending_orders(patient_id) -> list[dict]
```

All mutations audited. `compare` and `results_for_patient` are read models
suitable for the Workspace panels and future graphs.

## 6. Consultation Workspace integration

- **Investigation Panel** — order tests (typeahead over a catalog; a protocol can
  pre-fill recommended tests). Shows pending orders for the patient.
- **Investigation Timeline** — chronological results per analyte.
- **OCR Results** — structured values from the latest upload.
- **Comparison with Previous Reports** — side-by-side latest vs. prior, with
  abnormal flags and (later) trend graphs.

## 7. Comparison & trends

- **Comparison** aligns the same `test_name`/`unit` across results and highlights
  direction (↑/↓) and out-of-range values.
- **Trend series** (`results_for_patient`) is the data behind future Analytics
  graphs (Constitution Art. III §5 — read models, no new base tables for charts).
- Reference ranges come from the report (via OCR) or a catalog default; never
  fabricated.

## 8. Relationship to OCR and Attachments

- **Attachments** stores the original document (built).
- **OCR** extracts text + structured values from that document (planned).
- **Investigation** organizes those values into orders/results and comparisons.

The three form a pipeline: `upload (Attachments) → extract (OCR) → organize &
compare (Investigation) → surface (Workspace) → chart (Analytics)`.

## 9. Dependencies & sequencing

- **Requires:** F1 (tables). Best after/with **OCR** (for structured values) and
  the **Consultation Workspace** (its surface). Attachments already exists.
- **Feeds:** Timeline (report events with values), Analytics (trends), AI
  (interpretation), Protocol Engine (recommended investigations).

## 10. Manual test checklist (implementing phase)

- [ ] Ordering tests in a consultation records orders linked to patient/case/visit.
- [ ] A result can be recorded with or without a prior order.
- [ ] The same analyte trends across multiple reports (comparison shows ↑/↓).
- [ ] Abnormal values are flagged from the reference range, not invented.
- [ ] Manual and OCR-sourced values coexist; OCR values stay non-authoritative.
- [ ] Model/table parity + router contract green.

## 11. Risks

- **Analyte normalization** (units, names) is the hard part; start with a small
  catalog and grow, keep raw values verbatim.
- **OCR dependency** — the engine must be useful even with manual entry before
  OCR lands.
</content>
