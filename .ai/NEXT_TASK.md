# .ai/NEXT_TASK.md — The single next actionable task

> Keep this to **one** concrete task. When it's done, replace it with the next
> one. **Updated:** 2026-07-20.

## Now
**Sprint 0 (DB Migrations / F1) is complete and committed — await Product Owner
review.** Do not start Sprint 1 automatically (charter: one sprint, then stop).

Delivered this sprint:
- [x] `app/core/migrations/` package — runner, registry, baseline `0001_initial`
- [x] `schema_version` ledger table + rollback support
- [x] `init_db()` migrates then seeds
- [x] `tests/test_migrations.py` (idempotency, legacy stamping, rollback, parity)
- [x] Regression golden updated for `schema_version` (ADR-0008)
- [x] Docs updated (DATABASE, DECISIONS, CHANGELOG, KNOWN_LIMITATIONS, `.ai/`)
- [x] `python3 -m pytest -q` → 16 passing; committed + pushed (no PR)

## Blocked on
Product Owner approval before starting Sprint 1.

## After approval (proposed Sprint 1 = Settings UI / F2)
Per [`../specs/IMPLEMENTATION_PLAN.md`](../specs/IMPLEMENTATION_PLAN.md) the next
foundation phase is **F2 — Settings UI + templates** (spec:
[`../specs/SETTINGS_SYSTEM.md`](../specs/SETTINGS_SYSTEM.md)). It depends only on
F1, which is now in place, and unblocks Printer/WhatsApp. First slice:
1. Settings service/repository (read + update the single `settings` row).
2. Settings view + controller/route wired into `bootstrap.py` and `shell.py`.
3. Service tests + view-build test; regression golden stays green.
