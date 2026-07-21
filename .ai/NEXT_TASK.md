# .ai/NEXT_TASK.md — The single next actionable task

> Keep this to **one** concrete task. When it's done, replace it with the next
> one. **Updated:** 2026-07-20.

## Now
**Sprint 2 (Consultation Domain Model / C3) implemented on
`claude/sprint-2-implementation` — awaiting Product Owner review before commit.**

Delivered:
- [x] `v0002_consultations` migration (additive, reversible, UNIQUE `visit_id`)
- [x] `consultation` slice: models + repository + service (lifecycle) + controller + view
- [x] Lifecycle `draft → in_progress → completed`; audited; 1:1 invariant
- [x] Tests: `test_consultation_domain.py` + migration/model/regression updates → 26 passing
- [x] Docs: DATABASE, DECISIONS (ADR-0009), CHANGELOG, module docs, MASTER_BACKLOG, `.ai`

## Blocked on
Product Owner review of the Sprint 2 implementation.

## After approval (deferred Sprint 2 tails / next)
- Timeline `consultations` source row (M5, optional — deferred).
- Live narrative editors + autosave UI (separate approved UI sprint).
- Then feeder phases per ADR-001: Settings (F2) → RBAC + encryption (F3) →
  Protocol/Investigation/OCR/AI (each behind the AI Gateway).
