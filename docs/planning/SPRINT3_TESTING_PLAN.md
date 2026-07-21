# Sprint 3 — Testing Plan: Narrative Editors + Autosave

**Status:** PLAN ONLY. Date: 2026-07-21.
**Baseline:** 26 tests passing (Sprint 2). Sprint 3 adds cases; **all 26 stay green**.

Autosave logic is tested **headlessly at the service/controller level** — no
GUI event loop needed. The debounce timer is UI-only; tests drive the underlying
`autosave` / `save_consultation` calls directly (the flush contract, not the
timer's milliseconds).

## 1. Autosave persistence round-trip — `tests/test_consultation_domain.py`

| Test | Assert |
| ---- | ------ |
| `test_autosave_persists_fields` | `open_or_create_draft` → `save_consultation(id, {chief_complaint, history})` → `get_consultation(id)` returns those exact values |
| `test_first_write_flips_draft_to_in_progress` | new draft status == `draft`; after first `save_consultation`, status == `in_progress` |
| `test_autosave_audits_each_real_save` | each field-changing save writes one "Consultation Updated" audit row (actor + entity id) |
| `test_noop_edit_writes_nothing` | saving the same field values again → **no** new audit row, `updated_at` unchanged (no-op guard) |
| `test_coalesced_fields_single_update` | one save carrying multiple dirty fields persists all in one call |

## 2. Lifecycle boundary — `tests/test_consultation_domain.py`

| Test | Assert |
| ---- | ------ |
| `test_complete_then_edit_rejected` | after `complete_consultation`, `save_consultation` raises `ConsultationLifecycleError` |
| `test_flush_before_complete_no_loss` | pending dirty fields saved, *then* complete → completed doc contains the last edits |
| `test_complete_is_idempotent` | Complete on an already-`completed` doc returns it, no error (Sprint 2 behavior preserved) |

## 3. View builds — `tests/test_views_build.py`

| Test | Assert |
| ---- | ------ |
| `test_workspace_builds_editable_draft` | workspace view builds with a `draft`/`in_progress` consultation; editable fields present (no exception) |
| `test_workspace_builds_readonly_completed` | workspace builds with a `completed` consultation rendered read-only (Complete disabled / editors non-editable) |

## 4. Regression — `tests/test_regression.py`

| Test | Assert |
| ---- | ------ |
| `test_golden_tables_unchanged` | golden `TABLES:` line is **identical** to Sprint 2 — **no schema drift** this sprint (the defining guardrail) |
| existing regression cases | remain green unchanged |

## 5. Untouched suites

`tests/test_migrations.py`, `tests/test_models.py`, `tests/test_router.py` —
**no change expected**; run green. Touch `test_router.py` only if `_setup` must
seed a draft.

## Manual test checklist (Product Owner / QA)

1. Open a case → workspace opens on a fresh **Draft**; bottom bar shows "Draft".
2. Type in Chief Complaint, pause ~1s → pill shows "Saving…" then "Saved HH:MM";
   status flips to "in progress".
3. Refresh / reopen the case → typed text is still there.
4. Edit History + Diagnosis, click **Complete Visit** → no keystroke lost; status
   → "Consultation completed"; editors read-only.
5. Try to edit a completed consultation → fields are read-only (no write path).
6. Switch sections mid-typing → prior section's edits are saved (flush on nav).
7. Right rail (Timeline/Investigations/OCR/Protocol/AI) still honest placeholders;
   Print/Invoice/Dispense/WhatsApp still disabled.

## Acceptance gate

- `python3 -m pytest -q` green; count ≥ 26 + new cases.
- Golden `TABLES:` line unchanged (assert R4).
- Every lifecycle/persistence path proven headlessly (no GUI dependency in CI).
- Manual checklist passes on a fresh DB and a legacy (Sprint 2) DB.
