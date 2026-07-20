# Sprint 1 — Risk Report

**Feature:** Consultation Workspace Skeleton (C1)
**Branch:** `claude/consultation-workspace-skeleton-qi1nfx`
**Date:** 2026-07-20 · Read-only audit

Severity: 🔴 Critical · 🟠 High · 🟡 Medium · 🟢 Low
Likelihood × Impact drives severity. "Gating" = must resolve/verify before merge.

---

## Risk register

| ID | Risk | Severity | Likelihood | Impact | Gating? | Mitigation |
| -- | ---- | -------- | ---------- | ------ | ------- | ---------- |
| **R1** | Center section list combines `scroll=AUTO` + `expand` inside a `Row(CrossAxisAlignment.START)`; internal scroll bounding and no-horizontal-scroll at 1366×768 are **unverified** (headless env can't render Flet). | 🟡 Medium | Medium | Sections could overflow/clip or push the bottom action bar off-screen instead of scrolling internally. | **YES** | Manual UI pass on a 1366×768 window (checklist §UI). If it mis-renders, switch the center to a bounded height / `CrossAxisAlignment.STRETCH` — a one-line view change. |
| **R2** | Bottom action bar packs a status label + 5 icon buttons on one non-wrapping `Row`; may overflow horizontally on narrow/scaled displays. | 🟢 Low | Low | Right-most action ("Complete Visit") could clip. | No | Verify in manual pass; wrap or shrink labels if needed. |
| **R3** | `workspace_context` does not assert the case belongs to the patient; a crafted `/patient/A/case/B/workspace` renders A's demographics beside B's case title. | 🟢 Low | Low | Cosmetic mismatch now (read-only). Becomes a **data-integrity** risk once the Workspace writes visits. | No (now) | Add a patient↔case ownership check when the module becomes writable (next sprint). |
| **R4** | No RBAC/Doctor-role gate on the Workspace route. | 🟢 Low | — | Any authenticated user opens it. Consistent with the whole app; spec defers to F3. | No | Track under F3 (RBAC). Not a regression. |
| **R5** | Section nav / draft is **not persisted**; navigating away or closing loses any (future) in-progress content. | 🟢 Low | — | None this sprint (no editable content). Must be solved before editors ship. | No | The next sprint must land draft autosave *with* the editors (spec §5, "persist continuously"). |
| **R6** | Full-view rebuild + fresh DB read on every section click (L11 model). | 🟢 Low | — | Negligible at skeleton size; could matter once panels do real work. | No | Growth sprint: section-level updates instead of whole-screen rebuilds. |
| **R7** | Reviewers diffing against the **stale local `main`** will see the entire project history and may misjudge scope. | 🟢 Low | Medium | Confusion, not a code risk. | No | Review against `origin/main` (1 commit). Noted in the audit. |
| **R8** | Event handlers (nav, disabled buttons) are unexercised by tests; a future refactor could silently break navigation without a failing test. | 🟢 Low | Low | Latent nav breakage. | No | Add a structural build assertion (sections/panels/disabled state) in the growth sprint. |

---

## Residual risk after mitigations

With **R1 verified** on a real display, residual risk is **Low**. Every other
item is a Low-severity follow-up that does not affect correctness, data safety,
or security of the current skeleton. No Critical or High risk exists on this
branch.

## Risks explicitly *not* present

- No schema/migration change → **no data-loss or legacy-DB risk**.
- No new dependency, no network call → **no supply-chain / offline-posture risk**.
- No SQL constructed in this branch → **no injection surface added**.
- No secrets/credentials/binaries in the diff.
- Regression golden byte-identical → **no behavioural-regression risk** to Sprint 0/2 features.
