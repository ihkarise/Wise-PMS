# OCR Engine — Specification

> **Status:** Design only (Phase 2). Not implemented. Backlog **D2**. Planned
> table: `ocr_results`. **Last updated:** 2026-07-20.
> Extends [`../docs/modules/OCR.md`](../docs/modules/OCR.md). Feeds
> [`INVESTIGATION_ENGINE.md`](./INVESTIGATION_ENGINE.md).

## 1. Purpose

Turn uploaded documents (lab reports, images) into **structured, comparable data**
without changing the fact that the **original document is the source of truth**.
OCR output is a *derived, non-authoritative* layer (Constitution Art. II §2).

## 2. What OCR produces per document

| Output | Detail |
| ------ | ------ |
| **Original document** | Already stored by Attachments (`attachments`); OCR never mutates it |
| **OCR text** | Full raw extracted text |
| **Structured values** | test → value → unit → reference range (as JSON) |
| **Confidence** | Per-extraction confidence for review triage |
| **Engine metadata** | Which engine/version produced it (for reproducibility) |
| **Doctor notes** | Clinician annotation over the extraction |
| **Future AI interpretation** | Hook for AI summary/flagging (advisory) |

## 3. Data model (planned — needs F1)

```
ocr_results
  id · attachment_id FK · raw_text · structured (JSON) ·
  engine · engine_version · confidence · status (pending|done|failed|review) ·
  doctor_notes · extracted_at · created_at
```

- One `ocr_results` row augments one `attachments` row. The document is never
  altered.
- `structured` is JSON: a list of `{test, value, unit, reference_range, flag}`.
  It flows into `investigation_results` (`source = ocr`).

## 4. Engine abstraction (swappable backend)

Per Constitution Art. III §9 and VII §3, the OCR backend hides behind **one
interface** so it is swappable and offline-preferred:

```
OcrProvider (interface)
  extract(file_path) -> OcrExtraction { text, structured, confidence, engine }

Implementations (planned):
  • LocalTesseractProvider   (default — offline, ₹0, on-device)
  • CloudOcrProvider         (opt-in, consented, encrypted)
  • HoloscanVisionProvider   (imaging/vision, future)
```

Default is a **local/offline** engine to preserve the ₹0/offline posture. Cloud
OCR is an explicit opt-in with secrets in Settings/env, never committed.

## 5. Service contract (target)

```
ocr.service
  process(attachment_id, user_id) -> int        # runs provider, stores result
  reprocess(attachment_id, user_id, engine=None) -> int
  result_for_attachment(attachment_id) -> dict | None
  values_for_patient(patient_id, test_name=None) -> list[dict]   # trend feed
  set_doctor_notes(ocr_result_id, notes, user_id) -> None
```

- `process` runs the provider, stores `raw_text` + `structured`, sets `status`.
- Low-confidence extractions get `status = review` so a human confirms before the
  values are trusted downstream.
- All mutations audited (`entity_type = ocr_result`).

## 6. Pipeline

```
Attachment uploaded (built)
        │
        ▼
ocr.service.process(attachment_id)     ← triggered on upload or on demand
        │  (LocalTesseractProvider by default)
        ▼
ocr_results row: raw_text + structured (+ confidence)
        │
        ├─► Investigation Engine: values → investigation_results (source=ocr)
        ├─► Timeline: report event carries structured values + trend
        ├─► Consultation Workspace: "OCR Results" + "Comparison" panels
        └─► AI Assistant (future): summarize/flag (advisory)
```

Processing is **best-effort and asynchronous-friendly**: an upload succeeds even
if OCR fails or is unavailable (offline degrade — Constitution Art. VII §4). The
document remains fully usable; OCR can be retried.

## 7. Consultation Workspace integration

- **OCR Results** panel shows structured values for the latest report.
- **Comparison with Previous Reports** panel (Investigation Engine) uses the
  normalized values across reports.
- Doctor can annotate (`doctor_notes`) and, if extraction is wrong, correct values
  manually — manual corrections take precedence over OCR (narrative-first spirit).

## 8. Privacy & safety

- OCR runs **on-device by default**; PHI never leaves the machine unless a cloud
  provider is explicitly enabled and consented.
- Every OCR run (inputs referenced, outputs, engine) is auditable.
- Structured values are **advisory** until confirmed; they never auto-alter the
  clinical narrative.

## 9. Dependencies & sequencing

- **Requires:** F1 (table), Attachments (built). Prefer an offline engine first.
- **Feeds:** Investigation Engine, Timeline, Analytics (graphs), AI/Holoscan.
- **Sequencing:** ship with a local engine and manual-correction fallback before
  any cloud/AI interpretation.

## 10. Manual test checklist (implementing phase)

- [ ] Uploading a report can trigger OCR; the document is unchanged.
- [ ] Structured values appear and flow into Investigation results.
- [ ] Low-confidence extraction is marked for review, not silently trusted.
- [ ] Upload still succeeds when OCR is unavailable (offline degrade).
- [ ] Manual correction overrides OCR values.
- [ ] Model/table parity green for `ocr_results`.

## 11. Risks

- **Extraction accuracy** varies by report format — hence confidence + review +
  manual override.
- **Engine footprint** — a heavy local OCR dependency must not bloat the `.exe`;
  keep it behind the provider interface and optional.
</content>
