# WiseOS Health — Roadmap

> **Status:** Living document. Reviewed at the end of every phase.
> **Last updated:** 2026-07-20.

Phases are **independently deployable** and **gated by Product Owner approval**.
No phase begins automatically. Each phase ships: architecture updates, doc
updates, tests, a manual test checklist, migration notes, and a changelog entry.

## Completed

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| Sprint 1 | Login, Registration, Search, Patient Profile, Dashboard, Backup, Audit | ✅ shipped |
| Sprint 2 | Cases, Visits, Prescription intelligence, Timeline, Attachments | ✅ shipped |
| Architecture Refactor | Domain-driven modules, core/router, repository + model layers, tests | ✅ shipped (PR #1) |
| Phase 1 | **Project Memory System** (this docs/ + .ai/ set) | ✅ this phase |

## Near-term (candidate order — needs approval per phase)

| Phase | Deliverable | Why now | Risk |
| ----- | ----------- | ------- | ---- |
| 2 | **DB migrations + schema versioning** | Highest-severity code gap; unblocks every future table | Low |
| 3 | **Settings UI** (clinic/branding, over existing `settings` table) | Table exists, no UI; needed by print/WhatsApp | Low |
| 4 | **RBAC** (Administrator/Doctor/Reception/Pharmacy/Accounts + custom) | `role` column decorative today; compliance | Medium |
| 5 | **Consultation Workspace** (one integrated screen after case creation) | "The heart of the software" | High |
| 6 | **Protocol Engine** (reusable clinical templates) | Powers consultation + prescriptions | Medium |
| 7 | **Wise Printer** (prescription/invoice/label templates) | Consultation output | Medium |
| 8 | **OCR Engine** (structured values + timeline comparison) | Attachments → data | High |
| 9 | **WhatsApp Automation** (templated messaging) | Retention / follow-up | Medium |
| 10 | **Billing & Dispensing** | Revenue + pharmacy handoff | Medium |

## Later horizons

- WHIMS (Inventory), PillFill (dispensing automation)
- Analytics & Reports
- Patient Portal, Online Consultation (Telemedicine)
- AI Assistant, Holoscan
- Cloud Sync, Mobile app, public API

## Sequencing rules

1. Foundation before features: **migrations → settings → RBAC** precede large
   feature modules, because features depend on all three.
2. The **Consultation Workspace** is the anchor feature; Protocol Engine,
   Printer, and OCR are built to feed it.
3. Cloud/Mobile/API come only after the repository seam and RBAC are proven.

See [`MASTER_BACKLOG.md`](./MASTER_BACKLOG.md) for the itemized backlog and
[`.ai/NEXT_PHASE.md`](../.ai/NEXT_PHASE.md) for the immediate proposal.
