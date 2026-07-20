# Module: Timeline

**Status:** ✅ Built · **Path:** `app/modules/timeline/` · **Table:** (read model)

## Purpose
A unified, newest-first event feed of everything that happened to a patient —
visits, cases, and attachments merged into one list.

## Layers
`repository.py` (`TimelineRepository` — one SELECT per source: visits, cases,
attachments) · `service.py` (merge/shape/sort). No models/controller/view of its
own — it is a **read model** consumed by the patient profile's Timeline tab.

## Public service API
- `timeline_for_patient(patient_id) -> list[dict]`

Each event: `kind` (`visit`/`case`/`attachment`), `id`, `ts`, `title`,
`summary`, `extra`, `followup`. Events are sorted by `ts` descending.

## Behavior
- Visit events summarize the first line of `visit_notes` (or "No notes"), show
  the linked case title and outcome.
- Case events show "Case Opened — {title}" and status.
- Attachment events show file type and name.
- Clicking an event opens the underlying record.

## Dependencies
`timeline.repository → core`. Pure read; writes nothing, audits nothing.

## Future
The workspace embeds the timeline inline. When OCR lands, report events will
carry structured values and trend comparison; when Billing/Dispensing land,
their events join the same feed via additional repository queries.
