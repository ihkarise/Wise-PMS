# .ai/MEMORY.md — Durable working memory

> Read this first at the start of any session. It is the shortest path to
> "what is this and where are we." Keep it current. **Updated:** 2026-07-20.

## What this repo is
WiseOS Health — the intended operating system for a healthcare practice. Today
it ships one working module: **Wise PMS**, an offline-first, local, ₹0/month
desktop Patient Management System (Python 3.10+, Flet 0.28.3, SQLite, bcrypt).

## Where we are
- Architecture refactor (domain-driven modules, core/router, repo+model layers,
  tests) is **complete** (merged PR #1).
- **Phase 1 — Project Memory System** (this `docs/` + `.ai/` set) is the current
  phase.
- Nothing beyond the built modules exists yet; all future modules are documented
  as design specs, not code.

## Built modules
authentication · patients · registration · cases · visits (consultation) ·
attachments · timeline · dashboard · audit · backup.

## The rules that never change (charter)
1. **Phase 0 first:** read & understand before modifying.
2. **Documentation is part of implementation:** update every affected doc in the
   same change.
3. **Phased & approval-gated:** each phase is independently deployable, leaves
   the app working, ends with a report, and waits for Product Owner approval.
   Never merge/deploy/remove functionality automatically.
4. **Modular before featureful; narrative is source of truth; think 5 years
   ahead** (leave room for Portal, AI, Voice, Inventory, Billing, Analytics,
   Telemedicine, Cloud Sync, Mobile, API).

## Fast orientation links
- Product: [`../docs/PRODUCT_VISION.md`](../docs/PRODUCT_VISION.md),
  [`../docs/ROADMAP.md`](../docs/ROADMAP.md)
- System: [`../docs/SYSTEM_OVERVIEW.md`](../docs/SYSTEM_OVERVIEW.md),
  [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md),
  [`../docs/DATABASE.md`](../docs/DATABASE.md)
- Rules: [`ARCHITECTURE_RULES.md`](./ARCHITECTURE_RULES.md),
  [`PRODUCT_DIRECTION.md`](./PRODUCT_DIRECTION.md)
- Now/next: [`CURRENT_PHASE.md`](./CURRENT_PHASE.md),
  [`NEXT_PHASE.md`](./NEXT_PHASE.md), [`NEXT_TASK.md`](./NEXT_TASK.md)
- State: [`KNOWN_ISSUES.md`](./KNOWN_ISSUES.md), [`WORK_LOG.md`](./WORK_LOG.md),
  [`DECISION_LOG.md`](./DECISION_LOG.md)

## Verify quickly
```bash
pip install -r requirements-dev.txt && pytest -q   # expect: green (4 passing)
python main.py                                      # admin / admin123
```
