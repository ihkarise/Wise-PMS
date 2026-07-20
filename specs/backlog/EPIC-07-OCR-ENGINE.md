# EPIC-07 — OCR Engine

> **Spec:** [`../OCR_ENGINE.md`](../OCR_ENGINE.md) · **Backlog:** D2 ·
> **Stage:** B — Clinical Core · **Depends on:** EPIC-01, EPIC-06, Attachments ·
> **Complexity:** L · **Risk:** High · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. II §2, VII §3.

## 1. Objective

Turn uploaded documents into structured, comparable data — **offline-first** and
**derived, non-authoritative**. OCR augments, never mutates, the original
document, and feeds structured values into the Investigation Engine.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E07-F1 | OCR result store | `ocr_results` augments an attachment (text + structured JSON) |
| E07-F2 | Provider interface | Swappable backend; LocalTesseract default (offline, ₹0) |
| E07-F3 | Processing pipeline | Process on upload/on demand; best-effort, async-friendly |
| E07-F4 | Confidence + review | Low-confidence → `review`; manual correction wins |
| E07-F5 | Value feed | Structured values → Investigation results (`source = ocr`) |
| E07-F6 | Doctor notes | Annotate an extraction |

## 3. User stories

- **E07-F3-S1** — As a doctor, I want uploaded reports read into structured values,
  so that I don't retype numbers.
- **E07-F2-S1** — As the clinic, I want OCR to run on-device by default, so that
  PHI stays local and there's no cost.
- **E07-F4-S1** — As a doctor, I want low-confidence extractions flagged for review,
  so that I confirm before trusting them.
- **E07-F3-S2** — As a doctor, I want uploads to succeed even if OCR fails, so that
  the document is never blocked by extraction.
- **E07-F4-S2** — As a doctor, I want my manual correction to override OCR, so that
  the record reflects reality.

## 4. Engineering tasks

- **E07-T1** — Migration: `ocr_results` (attachment_id, raw_text, structured JSON,
  engine, confidence, status, doctor_notes).
- **E07-T2** — `modules/ocr/` slice: models, repository, service (`process`,
  `reprocess`, `result_for_attachment`, `values_for_patient`, `set_doctor_notes`).
- **E07-T3** — `OcrProvider` interface + `LocalTesseractProvider` default;
  cloud/Holoscan providers stubbed behind the interface (opt-in, env secrets).
- **E07-T4** — Trigger hook on attachment upload (best-effort) + on-demand
  reprocess; offline-degrade (upload succeeds when OCR unavailable).
- **E07-T5** — Confidence thresholds → `review`; manual-override precedence into
  Investigation results.
- **E07-T6** — Workspace OCR Results panel + Comparison (with EPIC-06).
- **E07-T7** — Tests + docs (OCR module doc, CHANGELOG). Keep the OCR dependency
  optional so the `.exe` isn't bloated.

## 5. Dependencies

- **Upstream:** EPIC-01, Attachments (built), EPIC-06 (result sink).
- **Downstream:** EPIC-08 (report events with values), EPIC-14 (graphs), EPIC-19
  (Holoscan/AI interpretation).

## 6. Acceptance criteria

- **AC1** — *Given* an uploaded report, *when* processed, *then* an `ocr_results`
  row stores text + structured values and the original file is unchanged.
- **AC2** — *Given* the default config, *when* OCR runs, *then* it uses the
  on-device engine and no PHI leaves the machine.
- **AC3** — *Given* low confidence, *when* extracted, *then* status is `review` and
  values are not trusted downstream until confirmed.
- **AC4** — *Given* OCR unavailable, *when* a file is uploaded, *then* the upload
  succeeds and OCR can be retried.
- **AC5** — *Given* a manual correction, *when* saved, *then* it overrides the OCR
  value.

## 7. Regression tests

- **Must stay green:** golden, models, router, views.
- **New:** OCR service tests (process/reprocess, non-mutation of source,
  confidence→review, offline-degrade, manual override), provider-interface test
  with a fake provider, value-feed into Investigation, model/table parity.

## 8. Rollout phases

- **E07-R1** — Table + service + provider interface + LocalTesseract; process
  on-demand; offline-degrade.
- **E07-R2** — Confidence/review + manual override + doctor notes.
- **E07-R3** — Value feed into Investigation + Workspace panels.
- **E07-R4** — Cloud/Holoscan providers as opt-in; docs closeout.

## 9. Rollback

Revert module; documents remain viewable; Investigation manual entry intact.
`ocr_results` inert. No data destroyed.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: default engine on-device; source never
mutated; manual override provably wins; OCR dependency optional in packaging.
</content>
