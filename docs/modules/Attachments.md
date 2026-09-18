# Module: Attachments

**Status:** ✅ Built · **Path:** `app/modules/attachments/` · **Table:** `attachments`

## Purpose
Store patient documents (PDFs, images, lab reports) on disk and record them in
SQLite, per patient (and optionally per visit).

## Layers
`models.py` (`Attachment`) · `repository.py` (`AttachmentRepository`) ·
`service.py` (filesystem + DB). No dedicated view — surfaced in the patient
profile's Attachments tab.

## Public service API
- `add_attachment(patient_id, reg_no, source_path, user_id, visit_id=None) -> int`
- `attachments_for_patient(patient_id) -> list[dict]`
- `delete_attachment(attach_id, user_id)` — removes row + physical file (best effort)
- `absolute_path(attachment) -> str`

## Behavior
- Writes the source into `attachments/patient_<reg_no>/` with a timestamped
  filename (`<stem>_<YYYYMMDD_HHMMSS><ext>`), storing a **relative** `file_path`.
  As of Sprint 4, the write/delete goes through `app.core.storage.get_storage()`
  (`StorageProvider`, ADR-002 §5.1) instead of calling `os`/`shutil` directly —
  the on-disk layout and the stored `file_path` values are unchanged.
- `absolute_path()` calls `LocalDiskStorageProvider.local_path()` directly — a
  documented, known local-only dependency (ADR-002 §5.1), since a non-local
  provider has no equivalent filesystem path.
- Maps extension → `file_type` via `FILE_TYPES` (`app/config/constants.py`);
  unknown → "Other".
- Every add/delete writes an audit row.
- Paths resolve under `BASE_DIR` (`WISE_PMS_HOME`-aware).

## Dependencies
`attachments.service → audit.service`, `→ app.core.storage`, `→ config.constants`.

## Known limitations
Files are unencrypted on disk (L5); no size/type restriction enforced beyond the
type map; no de-duplication.

## Future
The source layer for **OCR** (structured values, trends) and **Holoscan** vision.
OCR results attach to the same document via `ocr_results.attachment_id`.
