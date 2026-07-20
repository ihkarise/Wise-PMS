# .ai/CURRENT_PHASE.md

**Phase:** 2 — Product Architecture & Clinical Workflow Design
**Status:** Complete → committing; awaiting Product Owner approval before Phase 3
**Branch:** `claude/wiseos-phase-2-architecture-6knli6`
**Updated:** 2026-07-20

## Goal
Design the complete clinical workflow and every planned module **before** writing
feature code — the product blueprint. No implementation, no schema changes, no
migrations, no refactoring, no UI code. Specifications and product architecture
only.

## Scope (this phase)
- New `specs/` directory with 21 detailed specification documents + a README index.
- Foundation: `PRODUCT_CONSTITUTION.md` (permanent rulebook), `SCREEN_FLOW.md`,
  `PATIENT_FLOW.md`.
- Clinical workflow: `CONSULTATION_WORKSPACE.md` (anchor), `NEW_CASE_WORKFLOW.md`,
  `FOLLOWUP_WORKFLOW.md`.
- Engines: `PROTOCOL_ENGINE.md`, `INVESTIGATION_ENGINE.md`, `OCR_ENGINE.md`,
  `TIMELINE_ENGINE.md`.
- Systems: `WHATSAPP_SYSTEM.md`, `PRINTER_SYSTEM.md`, `DISPENSING_SYSTEM.md`,
  `APPOINTMENT_SYSTEM.md`, `WAITING_QUEUE.md`.
- Platform: `USER_ROLES.md`, `SETTINGS_SYSTEM.md`, `PATIENT_PORTAL.md`,
  `AI_ASSISTANT.md`.
- Planning: `IMPLEMENTATION_PLAN.md`, `MASTER_PHASE_PLAN.md`.
- Implementation backlog: `specs/backlog/` — 22 epic documents + README index,
  each broken into features → user stories → engineering tasks → dependencies →
  acceptance criteria → regression tests → rollout phases → rollback → DoD.
  `docs/MASTER_BACKLOG.md` updated with the epic map.

## Explicitly NOT in scope
- **No runtime code changes.** No schema, service, view, or route is modified.
- No new module implementation. The app's behavior is unchanged.

## Definition of done
- All 21 charter-required specs exist under `specs/`, consistent with the memory
  system (`docs/`, `.ai/`) and subordinate to the Product Constitution.
- Internal links resolve; naming/module/backlog references are consistent.
- `python3 -m pytest -q` green (docs-only change; verified 4 passing).
- Phase-end report produced; awaiting Product Owner approval for Phase 3.

## Verification
```bash
python3 -m pytest -q     # expect green (4 passing) — unchanged behavior
```

> Note: the `pytest` on PATH here runs under a uv-isolated interpreter without
> the app's runtime deps; use `python3 -m pytest` (installs from
> `requirements-dev.txt`).

See [`NEXT_PHASE.md`](./NEXT_PHASE.md) for the proposed Phase 3 (implementation
begins with Migrations / F1).
