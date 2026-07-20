# WiseOS Health — Phase 2 Specifications

> **Status:** Phase 2 — Product Architecture & Clinical Workflow Design.
> **Nature:** Design & specification only. **No production code, no schema
> changes, no migrations, no refactoring, no UI implementation.**
> **Last updated:** 2026-07-20. Awaiting Product Owner approval before any
> Phase 3 implementation.

This folder is the **product blueprint** for WiseOS Health. It designs the
complete clinical workflow and every planned module *before* a line of feature
code is written, so implementation phases (gated by Owner approval) build against
an agreed picture instead of improvising.

Every document here obeys the existing **Project Memory System** (`/docs`,
`/.ai`) and the hard rules in
[`.ai/ARCHITECTURE_RULES.md`](../.ai/ARCHITECTURE_RULES.md). Nothing in these
specs may contradict [`PRODUCT_CONSTITUTION.md`](./PRODUCT_CONSTITUTION.md) — the
constitution wins in any conflict.

## How to read this folder

Read in this order:

1. **[`PRODUCT_CONSTITUTION.md`](./PRODUCT_CONSTITUTION.md)** — the permanent
   rulebook. Every other spec is subordinate to it.
2. **[`SCREEN_FLOW.md`](./SCREEN_FLOW.md)** — the map of every screen and how the
   doctor moves between them.
3. **[`PATIENT_FLOW.md`](./PATIENT_FLOW.md)** — the patient's journey through the
   clinic, present and future.
4. **[`CONSULTATION_WORKSPACE.md`](./CONSULTATION_WORKSPACE.md)** — the anchor
   feature; the single screen the whole product is built to feed.
5. The workflow specs, then the engine specs, then the system specs.
6. **[`MASTER_PHASE_PLAN.md`](./MASTER_PHASE_PLAN.md)** and
   **[`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md)** — the long-term
   roadmap and the near-term build sequence.

## Index

### Foundation
| File | What it defines |
| ---- | --------------- |
| [`PRODUCT_CONSTITUTION.md`](./PRODUCT_CONSTITUTION.md) | Permanent product/engineering/clinical/UX/data rulebook |
| [`SCREEN_FLOW.md`](./SCREEN_FLOW.md) | Every screen, route, and navigation edge (built + planned) |
| [`PATIENT_FLOW.md`](./PATIENT_FLOW.md) | End-to-end patient journey across all modules |

### Clinical workflow
| File | What it defines |
| ---- | --------------- |
| [`CONSULTATION_WORKSPACE.md`](./CONSULTATION_WORKSPACE.md) | The central consultation screen — anchor feature |
| [`NEW_CASE_WORKFLOW.md`](./NEW_CASE_WORKFLOW.md) | First-visit (new case) end-to-end flow |
| [`FOLLOWUP_WORKFLOW.md`](./FOLLOWUP_WORKFLOW.md) | Return-visit (follow-up) end-to-end flow |

### Engines (clinical intelligence)
| File | What it defines |
| ---- | --------------- |
| [`PROTOCOL_ENGINE.md`](./PROTOCOL_ENGINE.md) | Reusable per-condition clinical templates |
| [`INVESTIGATION_ENGINE.md`](./INVESTIGATION_ENGINE.md) | Ordering, results, structured values, comparison |
| [`OCR_ENGINE.md`](./OCR_ENGINE.md) | Document → text → structured data |
| [`TIMELINE_ENGINE.md`](./TIMELINE_ENGINE.md) | One continuous medical timeline per patient |

### Systems (operations & output)
| File | What it defines |
| ---- | --------------- |
| [`WHATSAPP_SYSTEM.md`](./WHATSAPP_SYSTEM.md) | Templated patient messaging |
| [`PRINTER_SYSTEM.md`](./PRINTER_SYSTEM.md) | Prescription / invoice / label rendering & printing |
| [`DISPENSING_SYSTEM.md`](./DISPENSING_SYSTEM.md) | Pharmacy handoff & automated fill |
| [`APPOINTMENT_SYSTEM.md`](./APPOINTMENT_SYSTEM.md) | Calendar, booking, tokens, Meet, schedules |
| [`WAITING_QUEUE.md`](./WAITING_QUEUE.md) | Live daily queue / token board |

### Platform
| File | What it defines |
| ---- | --------------- |
| [`USER_ROLES.md`](./USER_ROLES.md) | Roles, permission matrix, audit, multi-clinic |
| [`SETTINGS_SYSTEM.md`](./SETTINGS_SYSTEM.md) | Configurable practice settings & templates |
| [`PATIENT_PORTAL.md`](./PATIENT_PORTAL.md) | Future patient-facing surface |
| [`AI_ASSISTANT.md`](./AI_ASSISTANT.md) | Advisory clinical intelligence layer |

### Planning
| File | What it defines |
| ---- | --------------- |
| [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) | Near-term, ordered build plan with gates |
| [`MASTER_PHASE_PLAN.md`](./MASTER_PHASE_PLAN.md) | Five-year phased roadmap |

## Grounding facts (from the Project Memory System)

- **Stack:** Python 3.10+, Flet 0.28.3 (desktop), SQLite (`data/wise_pms.db`),
  bcrypt. Offline, local, ₹0/month. Relocatable via `WISE_PMS_HOME`.
- **Architecture:** domain-driven vertical slices under `app/modules/<domain>/`
  (`models → repository → service → controller → view`); shared `core/`,
  `config/`, `shared/`, `utils/`. Dependency rule:
  `views → controllers → services → repositories → core`.
- **Built today:** authentication, patients, registration, cases, visits
  (consultation), attachments, timeline, dashboard, audit, backup.
- **Hard prerequisites for most of these specs:** migrations (F1), Settings UI
  (F2), RBAC (F3). See [`MASTER_PHASE_PLAN.md`](./MASTER_PHASE_PLAN.md).

> These specs describe the **target**. They do not assert that any planned code
> exists. Implementation happens only in later, individually-approved phases.
</content>
</invoke>
