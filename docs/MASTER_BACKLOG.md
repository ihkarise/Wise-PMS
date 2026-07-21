# WiseOS Health — Master Backlog

> **Status:** Living document. The single ordered list of everything not yet
> built. Items move to a phase in [`ROADMAP.md`](./ROADMAP.md) when approved.
> **Last updated:** 2026-07-20.

Legend: **P1** must-do foundation · **P2** high-value feature · **P3** later.

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
| C3 | Chief complaint / history / examination / diagnosis fields | P2 | Structured + narrative · **Sprint 2: `consultations` aggregate + lifecycle done** |
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
