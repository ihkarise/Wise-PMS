# Module: OCR (OCR Engine)

**Status:** 🔜 Planned — **not implemented** · planned table: `ocr_results`

## Purpose (target)
Turn uploaded documents (lab reports, images) into structured, comparable data.

## Every uploaded report should provide
- Original document (already stored by [`Attachments`](./Attachments.md))
- OCR text
- Structured values (test → value → unit → reference range)
- Timeline comparison (this vs. prior reports)
- Historical trend
- Doctor notes
- Future AI interpretation support

## Target design (planned — needs approval)
- `app/modules/ocr/` vertical slice.
- Table (migration F1): `ocr_results` (attachment_id, raw_text, structured JSON,
  extracted_at, engine, confidence, doctor_notes).
- Service: `process(attachment_id)` → runs OCR, stores text + structured values;
  `values_for_patient(patient_id, test)` → trend series.
- Engine abstraction so the OCR backend (local Tesseract vs. cloud vs. Holoscan
  vision) is swappable behind one interface — no assumption baked into callers.

## Integrations
- **Attachments** provides the source document; OCR augments it.
- **Timeline** report events carry structured values + trend.
- **Consultation Workspace** shows "OCR Results" inline.
- **AI Assistant / Holoscan** consume the structured JSON for interpretation.

## Dependencies
Migrations (F1); Attachments (built). Local-first: prefer an offline OCR engine
by default to preserve the ₹0/offline posture; cloud OCR is an opt-in.

## Notes
Structured values are a **derived, non-authoritative** layer over the original
document — consistent with the narrative-first principle.
