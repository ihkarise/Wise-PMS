# .ai/NEXT_TASK.md — The single next actionable task

> Keep this to **one** concrete task. When it's done, replace it with the next
> one. **Updated:** 2026-07-20.

## Now
**Finish & commit Phase 1 (Project Memory System).**
- [x] `docs/` product & system docs
- [x] `docs/modules/` built + planned module docs
- [x] `.ai/` memory files
- [ ] Verify `pytest -q` green (docs-only, but confirm)
- [ ] Commit on `claude/wiseos-health-architecture-1yumsy` and push
- [ ] Deliver phase-end report; **await Product Owner approval**

## Blocked on
Product Owner approval before starting any Phase 2 code.

## After approval (only if Phase 2 = Migrations is approved)
First task of Phase 2:
1. Add `schema_version` table + `_apply_migrations()` runner skeleton in
   `app/core/database.py` (no behavior change yet; empty migration list stamps
   version 0).
2. Add `tests/test_migrations.py` asserting the runner is idempotent.
3. Then convert `SCHEMA` → migration `0001_initial` and stamp existing DBs.

Do **not** proceed past step 1 without the regression golden staying green.
