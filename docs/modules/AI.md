# Module: AI (AI Assistant & Holoscan)

**Status:** 🔜 Planned — **not implemented** · service + integrations

## Purpose (target)
Clinical decision support and document interpretation over the structured,
audited data the ecosystem already produces.

## Scope
- **AI Assistant** — suggestions from typed models + prescription extraction +
  timeline + OCR values (e.g. protocol suggestions, drug-interaction flags,
  summarization of long histories).
- **Holoscan** — imaging/vision interpretation of uploaded reports/images,
  feeding structured findings back into OCR/timeline.
- **Voice dictation** — speech-to-text into the narrative fields.

## Target design (planned — needs approval)
- `app/modules/ai/` — primarily a **service seam**: typed clinical data in,
  suggestions out. Provider (local model or hosted API) behind one interface so
  the backend is swappable; secrets in Settings/env, never committed.
- Outputs are **advisory only** and clearly labeled — they never auto-commit to
  the record, mirroring the narrative-first, doctor-authoritative principle.
- Every AI call and its inputs/outputs are auditable.

## Why the current architecture is ready
- **Typed models** (`RowModel`) give clean, structured entities to feed models.
- **`utils/prescription`** already produces structured medicine items.
- **Audit trail** provides traceability for any AI-influenced decision.
- **Repository seam** lets AI read data without new coupling.

## Dependencies
Best after OCR (structured values), Protocols (suggestion surface), and RBAC/
security (F3/F7) — since AI may involve external providers and PHI.

## Notes
Default to privacy-preserving options (on-device/local) to protect the offline,
₹0 posture; any cloud AI is an explicit, consented, encrypted opt-in.
