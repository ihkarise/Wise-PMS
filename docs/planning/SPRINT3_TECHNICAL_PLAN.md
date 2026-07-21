# Sprint 3 — Technical Plan: Clinical Consultation Workspace
## Narrative Editors + Autosave

**Status:** PLAN ONLY — no code. Await Product Owner approval.
**Date:** 2026-07-21
**Depends on:** Sprint 2 lifecycle service (`consultation/service.py`), ADR-001 (frozen).

---

## 1. Objectives

1. Make the center column of the Consultation Workspace **editable** — Chief
   Complaint, History, Examination, Diagnosis, Remarks — over the existing
   `consultations` columns.
2. **Autosave** narrative edits on a debounce → `save_consultation`; no explicit
   Save button. First keystroke flips `draft → in_progress` via the service.
3. **Enable Complete Visit** → `complete_consultation`; document sews to
   `completed`, editors go read-only.
4. Surface **live save-state + lifecycle status** honestly in the bottom bar.
5. **Zero schema change. Zero new domain. No AI/OCR/Investigation/Protocol code.**
   The right rail stays placeholders.

Non-goals: RBAC, Settings, Prescription editor (visits-owned), amend/lock UI,
rich text, Print/Invoice/Dispense/WhatsApp, any provider SDK.

## 2. Where this sits (unchanged bounded contexts, ADR-001)

```
Visit          = ENCOUNTER event      (visits)          🔒 unchanged
Consultation   = CLINICAL DOCUMENT    (consultations)   editable UI added — NO schema change
Investigation / OCR / AI / Protocols                    seams only, still placeholders
Attachments / Timeline                                  🔒 unchanged this sprint
```

Rule holds: **only `consultation/repository.py` writes `consultations`.** The
view calls the **service**, never the repository, never SQL. The service remains
the single authority over `status`.

## 3. No data-model change

`consultations` already has `chief_complaint, history, examination, diagnosis,
remarks, status, updated_at` (Sprint 2). Sprint 3 writes into existing columns
through the existing `ConsultationRepository.update` + `save_consultation`.

**Regression golden `TABLES:` line is UNCHANGED** — no migration, no new table.
If the golden diff shows a table change in Sprint 3, that is a bug, not intent.

## 4. Autosave design

### 4a. Control flow

```
workspace opens (/patient/{pid}/case/{cid}/workspace)
  controller.open_workspace(pid, cid, user)
     → service.open_or_create_draft(pid, cid, user)   # returns draft (visit_id known)
     → view renders editors bound to consultation fields, status in bottom bar

doctor types in a field
  on_change → debounce timer (per workspace, single pending save)
     → after QUIET_MS idle: controller.autosave(consultation_id, dirty_fields, user)
          → service.save_consultation(id, fields, user)   # draft→in_progress on 1st write, audits
     → view: status pill "Saving…" → "Saved HH:MM:SS"

doctor clicks Complete Visit
  → flush any pending debounce FIRST (no lost keystrokes)
  → controller.complete(consultation_id, user)
       → service.complete_consultation(id, user)   # → completed
  → editors switch to read-only; bottom bar → "Consultation completed"
```

### 4b. Debounce rules

- **Quiet period:** `AUTOSAVE_QUIET_MS = 900` (typing pause) — new constant in
  `app/config/constants.py`. Single pending save per workspace; a new keystroke
  resets the timer (trailing-edge debounce).
- **Coalesce fields:** the pending save carries a dict of *all currently-dirty
  fields*, not one per field — one `UPDATE` per flush.
- **Flush points (force-save, cancel debounce):** Complete Visit click, section
  nav change, workspace close/route-away. Guarantees no silent data loss.
- **No autosave into non-editable states:** if `status ∉ {draft, in_progress}`,
  editors are read-only and the debounce never arms. The service *also* rejects
  it (`ConsultationLifecycleError`) — defense in depth; the UI simply never gets
  there.
- **Idempotent/no-op guard:** skip the save call when no field actually changed
  since the last successful save (avoid audit spam of identical "Updated" rows).

### 4b-bis. Lightweight UX (approved expansion — view/controller only)

All over Sprint 2 services; no new architecture, schema, or ADR.

- **Dirty-state indicator:** view tracks per-field dirty flags (ephemeral UI
  state). Marker shown while any field differs from last-saved snapshot; cleared
  on successful `save_consultation`.
- **Save status:** `idle → Saving… → Saved | Error`. "Saving…" on flush start;
  "Saved" on service return; "Error" on `ConsultationLifecycleError`/exception
  (edits kept in the field, retry on next debounce/Ctrl+S).
- **Last-saved timestamp:** read `updated_at` from the returned consultation dict
  after each save; render "Saved HH:MM:SS". No new column.
- **Unsaved-changes warning:** on route-away / workspace close while dirty →
  **flush first** (primary path); the warning is the safety net if a flush can't
  complete. No data lost silently.
- **Ctrl/Cmd+S:** keyboard handler → **force-flush** the pending debounce (calls
  the same `controller.autosave` → `save_consultation`). Not a separate save
  mechanism; identical persistence + audit path. No-op guard still applies.

None of these touch `status` or SQL — dirty flags, labels, timestamps are all
view-side; persistence stays `save_consultation`.

### 4c. State ownership (unchanged authority)

- **`consultation.service` still owns the state machine.** The view never sets
  `status`. `draft → in_progress` happens *inside* `save_consultation` on first
  write (already implemented Sprint 2). Complete goes through
  `complete_consultation`.
- **View owns only ephemeral UI state**: dirty flags, debounce timer, "Saving/
  Saved" label. None of it is persisted; all authority stays server-side.

### 4d. Concurrency / single-writer

Desktop single-user session per workspace → no multi-writer conflict this
sprint. `updated_at` is stamped on every `update` (Sprint 2) and reserved for
future Cloud Sync conflict handling; Sprint 3 does not add optimistic-locking UI
(documented as a known future item, not a gap).

## 5. Module layout — `consultation` slice gains UI wiring only

| File | Role in Sprint 3 |
| ---- | ---------------- |
| `consultation/view.py` | ✏️ replace placeholder section bodies with **editable `text_field` (multiline)** bound to consultation fields; add Examination section; **dirty-state indicator, save-status label, last-saved timestamp, Ctrl/Cmd+S handler, unsaved-changes guard**; enable Complete Visit; read-only render when `completed`/`locked` |
| `consultation/controller.py` | ✏️ `open_workspace`, `autosave(id, fields, user)`, `complete(id, user)`, `flush(id, user)` (force-save for Ctrl+S / route-away); owns debounce orchestration + flush; **no SQL, no status logic** (delegates to service) |
| `consultation/service.py` | 🔒 **no change** — API already complete (`open_or_create_draft`, `save_consultation`, `complete_consultation`). Touch only if a read helper is genuinely missing. |
| `consultation/repository.py` | 🔒 no change |
| `consultation/models.py` | 🔒 no change |
| `visits/*` | 🔒 unchanged — visit = event |
| `app/shared/theme.py` / `widgets.py` | ✏️(only if) a multiline editor helper is missing — prefer reusing `text_field`; no hex literals, no raw widgets (arch rule 11) |
| `app/config/constants.py` | ✏️ add `AUTOSAVE_QUIET_MS` |

All controls come from `shared/theme.py` + `shared/widgets.py` — no raw
buttons/fields, no hex literals (arch rule 11).

## 6. Extension seams (still defined, still NOT built)

- **Protocol Engine (Sprint 4):** will *prefill* narrative fields — the editors
  built now are its write target. Prefill = calling the same
  `save_consultation` path. No rework needed later.
- **AI Gateway:** `to_ai_context` (Sprint 2 seam) now returns *populated*
  fields once editors exist — the reason editors come first. Still no provider
  import.
- **Investigation / OCR:** untouched; right-rail placeholders remain honest.
- **Autosave revisions:** future `consultation_revisions` append-only table
  (its own additive migration) can snapshot per-save; the `save_consultation`
  hook is the insertion point. Not built now.

## 7. Testing strategy

See `SPRINT3_TESTING_PLAN.md`. Headline: editor→autosave→persistence round-trip
(headless service-level: dirty fields → `save_consultation` → re-read equal);
`draft→in_progress` flips on first save; Complete → `completed` → edits rejected;
flush-before-complete loses nothing; **regression golden UNCHANGED**; workspace
builds with editable widgets and with a completed (read-only) consultation.

## 8. Risks

See `SPRINT3_RISK_ASSESSMENT.md`. Top: debounce race losing the last keystroke
before Complete/navigation (→ mandatory flush); autosave audit-row spam (→ no-op
guard); editing a completed doc via stale UI (→ service already rejects +
read-only render); accidental schema/golden drift (→ none expected — flag if seen).

## 9. Rollback plan

- Code: revert the Sprint 3 commit → workspace returns to read-only skeleton;
  the Sprint 2 domain + lifecycle service remain fully intact.
- Schema: **nothing to roll back** — no migration in this sprint.

## 10. Acceptance criteria

1. `python3 -m pytest -q` green; **regression golden `TABLES:` line UNCHANGED**.
2. Opening a workspace creates/returns a draft via `open_or_create_draft`; editors
   render bound to its fields.
3. Typing then pausing persists via `save_consultation` with no Save button; first
   write flips `draft → in_progress`; every save audited.
4. No-op edits do not write / do not audit.
5. Complete Visit flushes pending edits, then `complete_consultation` → `completed`;
   editors become read-only; further edits rejected by the service.
6. Section-nav / route-away flushes pending edits (no data loss); unsaved-changes
   warning fires only when a flush cannot complete.
7. UX present: dirty indicator while editing, save status (Saving/Saved/Error),
   last-saved timestamp from `updated_at`, **Ctrl/Cmd+S force-flushes** via the
   same `save_consultation` path.
8. Right rail + Print/Invoice/Dispense/WhatsApp remain honest placeholders/disabled.
9. Docs + `.ai/` memory updated same commit; `MASTER_BACKLOG` C1 advanced.
