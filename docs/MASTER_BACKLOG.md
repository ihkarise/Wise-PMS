# WiseOS Health — Master Backlog

> **Status:** Living document. The single ordered list of everything not yet
> built. Items move to a phase in [`ROADMAP.md`](./ROADMAP.md) when approved.
> **Last updated:** 2026-07-20.

Legend: **P1** must-do foundation · **P2** high-value feature · **P3** later.

## Structured implementation backlog (Epics)

Phase 2 converted the approved specifications into a structured, executable
backlog — **epics → features → user stories → engineering tasks**, each with
dependencies, acceptance criteria, regression tests, and rollout phases. One
implementation document exists per epic under
[`../specs/backlog/`](../specs/backlog/README.md). The item table below remains
the flat inventory; each item maps onto an epic.

| Epic | Title | Backlog IDs | Stage | Doc |
| ---- | ----- | ----------- | ----- | --- |
| EPIC-01 | Database Migrations & Schema Versioning | F1 | A Foundation | [link](../specs/backlog/EPIC-01-DB-MIGRATIONS.md) |
| EPIC-02 | Settings System & Templates | F2 | A Foundation | [link](../specs/backlog/EPIC-02-SETTINGS.md) |
| EPIC-03 | User Roles, RBAC & User Management | F3, F4 | A Foundation | [link](../specs/backlog/EPIC-03-RBAC.md) |
| EPIC-04 | Consultation Workspace | C1, C3, C6 | B Clinical | [link](../specs/backlog/EPIC-04-CONSULTATION-WORKSPACE.md) |
| EPIC-05 | Protocol Engine | C2 | B Clinical | [link](../specs/backlog/EPIC-05-PROTOCOL-ENGINE.md) |
| EPIC-06 | Investigation Engine | C4 | B Clinical | [link](../specs/backlog/EPIC-06-INVESTIGATION-ENGINE.md) |
| EPIC-07 | OCR Engine | D2 | B Clinical | [link](../specs/backlog/EPIC-07-OCR-ENGINE.md) |
| EPIC-08 | Timeline Engine (unified) | — | B Clinical | [link](../specs/backlog/EPIC-08-TIMELINE-ENGINE.md) |
| EPIC-09 | Wise Printer | D1 | B Clinical | [link](../specs/backlog/EPIC-09-WISE-PRINTER.md) |
| EPIC-10 | Appointments & Waiting Queue | F5 | C Operations | [link](../specs/backlog/EPIC-10-APPOINTMENTS-QUEUE.md) |
| EPIC-11 | WhatsApp Automation | E1 | C Operations | [link](../specs/backlog/EPIC-11-WHATSAPP.md) |
| EPIC-12 | Billing & Dispensing | B1, B2 | C Operations | [link](../specs/backlog/EPIC-12-BILLING-DISPENSING.md) |
| EPIC-13 | Inventory (WHIMS) | B3 | C Operations | [link](../specs/backlog/EPIC-13-INVENTORY-WHIMS.md) |
| EPIC-14 | Analytics & Reports | B5, D3 | D Insight | [link](../specs/backlog/EPIC-14-ANALYTICS-REPORTS.md) |
| EPIC-15 | Encryption at Rest | F7 | D Insight | [link](../specs/backlog/EPIC-15-ENCRYPTION-AT-REST.md) |
| EPIC-16 | Patient Portal | — | D Insight | [link](../specs/backlog/EPIC-16-PATIENT-PORTAL.md) |
| EPIC-17 | Telemedicine | E2 | D Insight | [link](../specs/backlog/EPIC-17-TELEMEDICINE.md) |
| EPIC-18 | PillFill (Dispensing Automation) | B4 | D Insight | [link](../specs/backlog/EPIC-18-PILLFILL.md) |
| EPIC-19 | AI Assistant & Holoscan | A1, A2, A3 | D Insight | [link](../specs/backlog/EPIC-19-AI-ASSISTANT.md) |
| EPIC-20 | Cloud Sync | F8 | E Platform | [link](../specs/backlog/EPIC-20-CLOUD-SYNC.md) |
| EPIC-21 | Mobile App & Public API | — | E Platform | [link](../specs/backlog/EPIC-21-MOBILE-API.md) |
| EPIC-22 | Multi-Clinic | — | E Platform | [link](../specs/backlog/EPIC-22-MULTI-CLINIC.md) |

Cross-cutting: **F5** (structured dates) folds into EPIC-10; **F6** (pagination)
into EPIC-04/EPIC-08. See [`../specs/backlog/README.md`](../specs/backlog/README.md).

## Foundation / platform

| ID | Item | Priority | Notes |
| -- | ---- | -------- | ----- |
| F1 | Schema version table + migration runner in `core/database.py` | P1 | No `ALTER TABLE` path today |
| F2 | Settings UI over existing `settings` table | P1 | Table exists, unused |
| F3 | RBAC: roles, permissions, route/action guards | P1 | `users.role` decorative |
| F4 | User management screen (create/deactivate users) | P2 | Depends on F3 |
| F5 | Structured date handling (validation, pickers) | P2 | Dates are hand-typed strings |
| F6 | Pagination/virtualization for large patient tables | P3 | Rebuild-per-keystroke today |
| F7 | Encryption at rest for PHI | P2 | Needed before any sync |
| F8 | Cloud sync via repository seam | P3 | Repository is the seam |

## Clinical features

| ID | Item | Priority | Notes |
| -- | ---- | -------- | ----- |
| C1 | Consultation Workspace (integrated single screen) | P2 | Anchor feature |
| C2 | Protocol Engine (templates per condition) | P2 | Feeds C1 |
| C3 | Chief complaint / history / examination / diagnosis fields | P2 | Structured + narrative |
| C4 | Investigation ordering + results | P2 | Links OCR |
| C5 | Prescription pricing inside consultation | P3 | Needs inventory pricing |
| C6 | Follow-up scheduling surfaced in workspace | P2 | Visit already has followup_date |

## Documents & I/O

| ID | Item | Priority | Notes |
| -- | ---- | -------- | ----- |
| D1 | Wise Printer: prescription/invoice/label templates | P2 | |
| D2 | OCR Engine: original + text + structured values + trends | P2 | Over attachments |
| D3 | Export engine (`exports/` folder is reserved, unused) | P3 | |

## Communication & engagement

| ID | Item | Priority | Notes |
| -- | ---- | -------- | ----- |
| E1 | WhatsApp templates (welcome, reminder, follow-up, greetings) | P2 | Editable in Settings |
| E2 | Google Meet link generation for telemedicine | P3 | |
| E3 | Patient Portal (separate front-end) | P3 | |

## Business modules

| ID | Item | Priority | Notes |
| -- | ---- | -------- | ----- |
| B1 | Billing (invoices, invoice_items, payments) | P2 | |
| B2 | Dispensing / pharmacy handoff | P2 | Feeds PillFill |
| B3 | WHIMS inventory (stock, batch, expiry) | P2 | |
| B4 | PillFill dispensing automation | P3 | Hardware integration |
| B5 | Analytics & Reports (over prescription_items etc.) | P3 | |

## AI

| ID | Item | Priority | Notes |
| -- | ---- | -------- | ----- |
| A1 | AI Assistant service seam (typed models in, suggestions out) | P3 | |
| A2 | Holoscan imaging/vision | P3 | |
| A3 | Voice dictation into narrative fields | P3 | |

## Tech debt (from ARCHITECTURE.md §11)

Tracked in [`KNOWN_LIMITATIONS.md`](./KNOWN_LIMITATIONS.md): migrations (F1),
RBAC (F3), date handling (F5), scale/pagination (F6), settings UI (F2).
