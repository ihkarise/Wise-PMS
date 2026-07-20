# .ai/NEXT_TASK.md — The single next actionable task

> Keep this to **one** concrete task. When it's done, replace it with the next
> one. **Updated:** 2026-07-20.

## Now
**Finish & commit Phase 2 (Product Architecture & Clinical Workflow Design).**
- [x] Create `specs/` with all 21 required specification documents + README index
- [x] `PRODUCT_CONSTITUTION.md` as the permanent rulebook (all specs subordinate)
- [x] Consultation Workspace (anchor), workflows, engines, systems, platform,
      planning specs
- [x] Documentation consistency review (links resolve; naming/backlog refs
      consistent)
- [x] Verify `python3 -m pytest -q` green (docs-only, confirmed 4 passing)
- [ ] Commit on `claude/wiseos-phase-2-architecture-6knli6` and push
- [ ] Deliver phase-end report; **await Product Owner approval** (no PR)

## Blocked on
Product Owner approval before starting any Phase 3 **implementation**.

## After approval (proposed Phase 3 = Migrations / F1 — the foundation unlock)
First task of Phase 3:
1. Add `schema_version` table + `_apply_migrations()` runner skeleton in
   `app/core/database.py` (no behavior change yet; empty migration list stamps
   version 0).
2. Add `tests/test_migrations.py` asserting the runner is idempotent.
3. Then convert `SCHEMA` → migration `0001_initial` and stamp existing DBs.

See [`../specs/IMPLEMENTATION_PLAN.md`](../specs/IMPLEMENTATION_PLAN.md) for the
full ordered plan. Do **not** proceed past step 1 without the regression golden
staying green.
