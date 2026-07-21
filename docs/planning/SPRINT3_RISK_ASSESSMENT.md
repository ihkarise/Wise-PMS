# Sprint 3 — Risk Assessment: Clinical Consultation Workspace
## Narrative Editors + Autosave

**Status:** PLAN ONLY. Date: 2026-07-21.

Severity × Likelihood → mitigation. This sprint is **low-risk overall** — no
schema change, no new domain, service API already proven in Sprint 2.

| # | Risk | Sev | Lik | Mitigation |
| - | ---- | :-: | :-: | ---------- |
| R1 | **Lost last keystroke** — debounce still pending when doctor clicks Complete or navigates away | High | Med | **Mandatory flush** at every exit point: Complete Visit, section-nav, route-away, workspace close. Flush cancels the timer and forces the save *before* the transition. Tested explicitly. |
| R2 | **Autosave audit spam** — identical "Consultation Updated" rows on every debounce | Med | High | **No-op guard**: skip `save_consultation` when no field changed since last successful save. Compare dirty snapshot vs last-saved snapshot. |
| R3 | **Edit into a sealed doc via stale UI** — completed/locked consultation still shows editors | Med | Low | Two layers: view renders **read-only** when status ∉ {draft, in_progress}; service **already rejects** the write (`ConsultationLifecycleError`). Defense in depth. |
| R4 | **Accidental schema / golden drift** — a stray migration or table touch | High | Low | **No migration in this sprint by design.** Regression golden asserted UNCHANGED; any `TABLES:` diff is a bug to stop on, not rubber-stamp. |
| R5 | **View reaches into repository/SQL** — bypassing the service authority | Med | Low | Controller calls **service only**; file-map marks repo/models 🔒. Code review + arch rule: only `consultation/repository.py` writes the table. |
| R6 | **Status set from the view** — UI mutating `status` directly | Med | Low | `draft→in_progress` happens inside `save_consultation`; Complete via `complete_consultation`. View never touches `status`. Service is sole authority (unchanged Sprint 2 invariant). |
| R7 | **Debounce race / double-fire** — overlapping saves reorder writes | Med | Low | Single pending save per workspace; trailing-edge timer reset; coalesce all dirty fields into one UPDATE. Sequential, no overlap. |
| R8 | **Scope creep into right rail** — "just wire AI/OCR/Protocol while we're here" | Med | Med | Non-goals frozen in Recommendation + Technical Plan. Right rail stays placeholders; Prescription stays visits-owned. Seams documented, not built. |
| R9 | **Multi-writer edit conflict** (future Cloud Sync) | Low | Low | Out of scope — single-user desktop. `updated_at` reserved; documented in KNOWN_LIMITATIONS as a future optimistic-locking item, not a Sprint 3 gap. |
| R10 | **Examination section mismatch** — column exists, no nav entry today | Low | Low | Add Examination to `_SECTIONS`; it maps to the existing `examination` column. No schema change. |
| R11 | **Ctrl/Cmd+S hijacks browser/native Save** — default not prevented | Low | Med | Keyboard handler intercepts + prevents default; maps to force-flush only. No new save mechanism — same `save_consultation` path. |
| R12 | **Stale "Saved" / wrong timestamp** — label not synced to actual persistence | Low | Med | Save-status + last-saved driven off the service **return value** (`updated_at` from returned dict), not fired optimistically before the call succeeds. "Error" state on exception; edits kept for retry. |
| R13 | **Unsaved-changes warning false-positive/negative** — dirty flag out of sync | Low | Low | Dirty flags cleared only on successful save; warning is secondary to mandatory flush (R1). Worst case = extra prompt, never silent loss. |

## Guardrails (carry from Sprint 2)

- Only `consultation/repository.py` writes `consultations`.
- Service is the single status authority; view/controller never stamp status.
- No provider SDK import anywhere.
- All widgets via `shared/theme.py` + `widgets.py`; no hex literals (rule 11).
- Additive & reversible: revert the commit → clean return to skeleton; no schema
  to unwind.

## Stop-the-line conditions

- Regression golden `TABLES:` line changes → **stop, investigate** (nothing in
  this sprint should change it).
- Any test that was green in Sprint 2 goes red → fix before proceeding.
- A save path that writes SQL outside `consultation/repository.py` → reject.
