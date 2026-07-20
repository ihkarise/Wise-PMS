# WiseOS Health — Implementation Backlog (Epics)

> **Status:** Planning artifact (Phase 2 output). Converts the approved `specs/`
> into an executable, structured backlog. **No production code.** Every epic is
> approval-gated per [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md)
> Art. IX and sequenced by [`../IMPLEMENTATION_PLAN.md`](../IMPLEMENTATION_PLAN.md)
> and [`../MASTER_PHASE_PLAN.md`](../MASTER_PHASE_PLAN.md).
> **Last updated:** 2026-07-20.

## Purpose

This folder decomposes each approved specification into:

- **Epics** — one shippable module/phase (one implementation doc each).
- **Features** — coherent capabilities inside an epic.
- **User stories** — `As a <role>, I want <goal>, so that <benefit>`.
- **Engineering tasks** — the concrete build steps (models, repo, service,
  controller, view, migration, tests, docs).
- **Dependencies** — upstream epics/backlog IDs that must land first.
- **Acceptance criteria** — Given/When/Then, testable.
- **Regression tests** — what must stay green + new tests to add.
- **Rollout phases** — the incremental, always-runnable delivery slices.

## ID conventions

| Artifact | Format | Example |
| -------- | ------ | ------- |
| Epic | `EPIC-NN` | `EPIC-01` |
| Feature | `ENN-Fk` | `E01-F1` |
| Story | `ENN-Fk-Sm` | `E01-F1-S1` |
| Task | `ENN-Tk` | `E01-T3` |
| Rollout slice | `ENN-Rk` | `E01-R1` |

Existing backlog IDs (F1, F2, F3, C1…, D1…, E1, B1…, A1…) from
[`../../docs/MASTER_BACKLOG.md`](../../docs/MASTER_BACKLOG.md) are preserved and
mapped onto each epic.

## Epic map

Grouped by the Master Phase Plan stages. Order = recommended build order.

### Stage A — Foundation
| Epic | Title | Spec | Backlog | Doc |
| ---- | ----- | ---- | ------- | --- |
| EPIC-01 | Database Migrations & Schema Versioning | IMPLEMENTATION_PLAN, DATABASE | F1 | [EPIC-01](./EPIC-01-DB-MIGRATIONS.md) |
| EPIC-02 | Settings System & Templates | SETTINGS_SYSTEM | F2 | [EPIC-02](./EPIC-02-SETTINGS.md) |
| EPIC-03 | User Roles, RBAC & User Management | USER_ROLES | F3, F4 | [EPIC-03](./EPIC-03-RBAC.md) |

### Stage B — Clinical Core
| Epic | Title | Spec | Backlog | Doc |
| ---- | ----- | ---- | ------- | --- |
| EPIC-04 | Consultation Workspace | CONSULTATION_WORKSPACE, NEW_CASE_WORKFLOW, FOLLOWUP_WORKFLOW, SCREEN_FLOW, PATIENT_FLOW | C1, C3, C6 | [EPIC-04](./EPIC-04-CONSULTATION-WORKSPACE.md) |
| EPIC-05 | Protocol Engine | PROTOCOL_ENGINE | C2 | [EPIC-05](./EPIC-05-PROTOCOL-ENGINE.md) |
| EPIC-06 | Investigation Engine | INVESTIGATION_ENGINE | C4 | [EPIC-06](./EPIC-06-INVESTIGATION-ENGINE.md) |
| EPIC-07 | OCR Engine | OCR_ENGINE | D2 | [EPIC-07](./EPIC-07-OCR-ENGINE.md) |
| EPIC-08 | Timeline Engine (unified) | TIMELINE_ENGINE | — | [EPIC-08](./EPIC-08-TIMELINE-ENGINE.md) |
| EPIC-09 | Wise Printer | PRINTER_SYSTEM | D1 | [EPIC-09](./EPIC-09-WISE-PRINTER.md) |

### Stage C — Operations
| Epic | Title | Spec | Backlog | Doc |
| ---- | ----- | ---- | ------- | --- |
| EPIC-10 | Appointments & Waiting Queue | APPOINTMENT_SYSTEM, WAITING_QUEUE | — | [EPIC-10](./EPIC-10-APPOINTMENTS-QUEUE.md) |
| EPIC-11 | WhatsApp Automation | WHATSAPP_SYSTEM | E1 | [EPIC-11](./EPIC-11-WHATSAPP.md) |
| EPIC-12 | Billing & Dispensing | DISPENSING_SYSTEM | B1, B2 | [EPIC-12](./EPIC-12-BILLING-DISPENSING.md) |
| EPIC-13 | Inventory (WHIMS) | modules/Inventory | B3 | [EPIC-13](./EPIC-13-INVENTORY-WHIMS.md) |

### Stage D — Insight & Reach
| Epic | Title | Spec | Backlog | Doc |
| ---- | ----- | ---- | ------- | --- |
| EPIC-14 | Analytics & Reports | modules/Analytics, modules/Reports | B5, D3 | [EPIC-14](./EPIC-14-ANALYTICS-REPORTS.md) |
| EPIC-15 | Encryption at Rest | SECURITY | F7 | [EPIC-15](./EPIC-15-ENCRYPTION-AT-REST.md) |
| EPIC-16 | Patient Portal | PATIENT_PORTAL | — | [EPIC-16](./EPIC-16-PATIENT-PORTAL.md) |
| EPIC-17 | Telemedicine | modules/Telemedicine | E2 | [EPIC-17](./EPIC-17-TELEMEDICINE.md) |
| EPIC-18 | PillFill (Dispensing Automation) | DISPENSING_SYSTEM | B4 | [EPIC-18](./EPIC-18-PILLFILL.md) |
| EPIC-19 | AI Assistant & Holoscan | AI_ASSISTANT | A1, A2, A3 | [EPIC-19](./EPIC-19-AI-ASSISTANT.md) |

### Stage E — Platform
| Epic | Title | Spec | Backlog | Doc |
| ---- | ----- | ---- | ------- | --- |
| EPIC-20 | Cloud Sync | ARCHITECTURE (repo seam) | F8 | [EPIC-20](./EPIC-20-CLOUD-SYNC.md) |
| EPIC-21 | Mobile App & Public API | API | — | [EPIC-21](./EPIC-21-MOBILE-API.md) |
| EPIC-22 | Multi-Clinic | USER_ROLES, MASTER_PHASE_PLAN | — | [EPIC-22](./EPIC-22-MULTI-CLINIC.md) |

## Cross-cutting (governance, not epics)

- [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) — every epic is
  subordinate to it.
- Structured date handling (**F5**) and pagination (**F6**) are cross-cutting
  tasks folded into the epics that first need them (F5 → EPIC-10; F6 → EPIC-04/08).

## Definition of Ready (before an epic starts)

- Product Owner has approved the epic's phase.
- Upstream epics/backlog dependencies are merged.
- The spec is current; open questions in the spec are answered.

## Definition of Done (every epic — from Constitution Art. IX §5)

- [ ] `python3 -m pytest -q` green; regression golden byte-identical (or an
      intentional, documented behavior change).
- [ ] New module ships its own tests (service behavior + view-build min).
- [ ] Model/table parity for new tables; router contract for new routes.
- [ ] Imports clean; app starts; DB initializes; migrations idempotent.
- [ ] Every affected doc updated in the same commit (docs = implementation).
- [ ] Phase-end report delivered; **await Product Owner approval**.
- [ ] Rollback strategy documented and verified.

> **This is a plan, not code.** Epics list tasks and tests to *write*; no
> production code is created by this backlog.
</content>
