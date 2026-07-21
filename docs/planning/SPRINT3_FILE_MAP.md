# Sprint 3 — File Map: Narrative Editors + Autosave

Legend: 🆕 new · ✏️ modify · 🔒 must NOT change
Architecture per ADR-001 (frozen). No migration this sprint.

## Application code

| File | Action | Change |
| ---- | ------ | ------ |
| `app/modules/consultation/view.py` | ✏️ | Replace placeholder section bodies with editable multiline fields (Complaint, History, Examination, Diagnosis, Remarks) bound to consultation values; add Examination nav entry; save-state pill ("Saving…/Saved HH:MM"); enable **Complete Visit**; render read-only when status ∈ {completed, amended, locked} |
| `app/modules/consultation/controller.py` | ✏️ | `open_workspace(pid, cid, user)`; `autosave(id, dirty_fields, user)`; `complete(id, user)`; owns debounce + flush orchestration; delegates ALL persistence/status to service (no SQL, no status logic) |
| `app/config/constants.py` | ✏️ | add `AUTOSAVE_QUIET_MS = 900` |
| `app/shared/theme.py` or `widgets.py` | ✏️(only if needed) | reuse `text_field` (multiline) — add a helper only if a multiline/read-only variant is genuinely missing; no hex literals, no raw widgets (rule 11) |
| `app/modules/consultation/service.py` | 🔒 | API already complete (Sprint 2) — no change unless a missing read helper is proven |
| `app/modules/consultation/repository.py` | 🔒 | no change — writes already exist |
| `app/modules/consultation/models.py` | 🔒 | no change |
| `app/core/migrations/*` | 🔒 | **no new migration** — no schema change |
| `app/core/database.py`, `app/bootstrap.py` | 🔒 | no change — route already exists |
| `app/modules/visits/*` | 🔒 | unchanged — visit = event |
| `app/modules/{cases,patients,attachments,audit,timeline}/*` | 🔒 | no change |

## Tests

| File | Action | Change |
| ---- | ------ | ------ |
| `tests/test_consultation_domain.py` | ✏️ | autosave round-trip (dirty fields → `save_consultation` → re-read equal); `draft→in_progress` on first write; no-op edit writes/audits nothing; Complete → `completed` → edit rejected |
| `tests/test_views_build.py` | ✏️ | workspace builds with an editable draft **and** with a completed (read-only) consultation |
| `tests/test_regression.py` | 🔒 | golden `TABLES:` line **UNCHANGED** — assert no drift |
| `tests/test_router.py` | 🔒/✏️ | stay green; touch only if `_setup` needs a draft |
| `tests/test_migrations.py`, `tests/test_models.py` | 🔒 | no change |

## Documentation & memory

| File | Action | Change |
| ---- | ------ | ------ |
| `docs/modules/Consultation.md` | ✏️ | status → live editors + autosave; document debounce + flush contract |
| `docs/CLINICAL_WORKFLOW.md` | ✏️ | narrative-authoring loop (open → type → autosave → complete) |
| `docs/CHANGELOG.md` | ✏️ | Sprint 3 entry; note golden UNCHANGED (no schema change) |
| `docs/DECISIONS.md` | ✏️ | autosave debounce + flush + no-op-guard decision (references ADR-001 §4e) |
| `docs/MASTER_BACKLOG.md` | ✏️ | advance C1 (workspace now editable); note C6 fast-follow |
| `docs/KNOWN_LIMITATIONS.md` | ✏️ | no optimistic-locking UI yet (single-user desktop); future Cloud Sync item |
| `.ai/CURRENT_PHASE.md`, `NEXT_TASK.md`, `WORK_LOG.md` | ✏️ | Sprint 3 state |
| `docs/architecture-decisions/ADR-001-Consultation-Domain.md` | 🔒 | frozen — reference only |
| `docs/planning/SPRINT2_*.md` | 🔒 | reference only |
| `docs/planning/SPRINT3_*.md` | 🔒 | these plans — reference once approved |

## Expected diff

2 modified app files (`view.py`, `controller.py`) + 1 constant + 2 modified test
files + ~7 docs. **No migration, no new table, golden UNCHANGED.** Single commit,
no PR until approved.
