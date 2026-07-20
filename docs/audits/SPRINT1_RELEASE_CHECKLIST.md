# Sprint 1 — Release Checklist

**Feature:** Consultation Workspace Skeleton (C1)
**Branch:** `claude/consultation-workspace-skeleton-qi1nfx` → `origin/main`
**Date:** 2026-07-20

Legend: ✅ verified · ⚠️ requires human/display · ⬜ to do before merge

---

## Automated gates (verified by this audit)

- ✅ Application boots — `init_db()` + `import app.bootstrap.ROUTES` (9 routes) clean
- ✅ `python3 -m pytest -q` → **16 passed**
- ✅ Regression golden **byte-identical** (no behaviour drift)
- ✅ Router contract covers the new workspace route (base, `/visit/new`, `/visit/<id>`, `?section=`)
- ✅ View-build covers workspace (new draft, reopened, deep-link, case-not-found)
- ✅ No new dependencies; `requirements*.txt` unchanged
- ✅ No `TODO`/`FIXME`, no hex literals, no raw widgets, no secrets in the diff
- ✅ No DB migration / schema change; Sprint 0 untouched
- ✅ Git diff vs `origin/main` = 1 commit, 17 intended files, no binaries/temp

## Mandatory manual UI pass (⚠️ — gating, do on a real 1366×768 window)

Run `python main.py`, login `admin` / `admin123`, then:

- ⬜ **R1** Layout holds at 1366×768 — **no horizontal page scroll**
- ⬜ **R1** Center sections **scroll internally**; the bottom action bar stays visible/reachable
- ⬜ **R2** Bottom bar shows all 5 actions without clipping ("Complete Visit" fully visible)
- ⬜ Left rail lists all 7 sections; clicking one highlights it (`?section=` deep-link works)
- ⬜ Patient Summary shows real demographics + case title
- ⬜ Right rail shows 5 placeholder panels (Timeline, Investigations, OCR, Protocol, AI)
- ⬜ All 5 bottom actions render **disabled** (not clickable)
- ⬜ Reach the Workspace **new case**: New Case → title → *Start Consultation*
- ⬜ Reach the Workspace **existing case**: Profile → Cases → open case → *Start Consultation*
- ⬜ Bad URL `/patient/<id>/case/999999/workspace` → friendly not-found, no crash

## Documentation / memory

- ✅ `docs/modules/Consultation.md`, `CHANGELOG`, `ARCHITECTURE` route row, spec status
- ✅ `.ai/CURRENT_PHASE`, `NEXT_TASK`, `WORK_LOG`
- ⬜ **DOC-1** Advance **C1** status in `docs/MASTER_BACKLOG.md` (optional pre-merge)
- ⬜ **DOC-2/3** `docs/DEPENDENCY_MAP.md` + ARCHITECTURE routing prose are pre-existing stale (not caused by this branch) — schedule a docs refresh (non-blocking)

## Process guardrails (per sprint charter)

- ✅ Committed to the designated branch, **no PR opened**
- ⬜ Product Owner review & approval before merge
- ℹ️ Reviewers: diff against **`origin/main`**, not the stale local `main`

---

## Sign-off

| Gate | Status |
| ---- | ------ |
| Automated | ✅ PASS |
| Manual UI (R1/R2) | ⬜ PENDING (display required) |
| Docs/memory | ✅ PASS (2 optional refreshes noted) |
| Decision | 🟡 **APPROVED WITH MINOR ISSUES** — merge after the manual UI pass |

> No Critical/High issues. All open items are Low or verification-only. Once the
> ⬜ manual UI boxes are checked, this branch is cleared to merge.
