# WiseOS Health — Known Limitations

> Honest inventory of what the software does not do yet, and where it will bite.
> Cross-referenced to backlog IDs in [`MASTER_BACKLOG.md`](./MASTER_BACKLOG.md)
> and the tech-debt table in [`ARCHITECTURE.md`](./ARCHITECTURE.md) §11.
> **Last updated:** 2026-07-20.

## Data & schema

| # | Limitation | Impact | Backlog |
| - | ---------- | ------ | ------- |
| ~~L1~~ | ~~No DB migrations / schema versioning.~~ **Closed (Sprint 0, F1):** `app/core/migrations/` — `schema_version` ledger + ordered idempotent runner with rollback; see [`DATABASE.md`](./DATABASE.md#migration-framework-backlog-f1--delivered-sprint-0). | — | ✅ F1 |
| L2 | **Date handling is string-based** (`YYYY-MM-DD` typed by hand). | No validation; `followup_date` typos stored silently. | F5 |
| L3 | **Doctor is not a modeled entity.** `patients.doctor` is free text; `doctor_id` is the acting user. | Can't report per-doctor cleanly. | — |

## Access & security

| # | Limitation | Impact | Backlog |
| - | ---------- | ------ | ------- |
| L4 | **No RBAC.** `users.role` is decorative; any logged-in user can do anything. | Compliance risk for a PMS. | F3 |
| L5 | **No encryption at rest.** DB, attachments, backups are plaintext. | PHI exposed to anyone with file access. | F7 |
| L6 | **Default credentials** `admin`/`admin123`; **no lockout/rate limiting.** | Must be changed manually; brute-forceable. | — |

## Features not yet built

| # | Limitation | Backlog |
| - | ---------- | ------- |
| L7 | **No Settings UI** — the `settings` table exists but is uneditable in-app. | F2 |
| L8 | **No user-management screen.** | F4 |
| L9 | `exports/` and `logs/` folders are **reserved but unused.** | D3 |
| L10 | None of the future modules exist: Consultation Workspace, Protocol Engine, OCR, WhatsApp, Printer, Inventory/WHIMS, PillFill, Billing, Analytics, Portal, Telemedicine, AI. | see backlog |

## Scale & performance

| # | Limitation | Impact | Backlog |
| - | ---------- | ------ | ------- |
| L11 | **Full view rebuild on every action**, no pagination. | Fine for one clinician; slow on large tables (search rebuilds per keystroke over 50k patients). | F6 |
| L12 | **SQLite single-writer.** | Blocks multi-user/multi-device concurrency; the sync story must account for it. | F8 |

## Platform

| # | Limitation | Impact |
| - | ---------- | ------ |
| L13 | Desktop-only (Flet); no mobile/web target yet. | Domain layer is UI-agnostic, so a future target reuses it — but it doesn't exist. |
| L14 | Dark theme token reserved (`DARK_BG`) but **not implemented.** | Don't ship partial dark styling. |
| L15 | No CI; no interaction/event tests. | Manual verification of UI event handlers. |

## How this list is used

Every phase must **either** not worsen these **or** explicitly close one and move
it to the changelog. New limitations discovered during a phase are added here in
the same commit.
