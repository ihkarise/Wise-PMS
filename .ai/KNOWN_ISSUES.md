# .ai/KNOWN_ISSUES.md — Active issues & gaps

> Working list for the AI/engineer. Mirror of the user-facing
> [`../docs/KNOWN_LIMITATIONS.md`](../docs/KNOWN_LIMITATIONS.md) with backlog IDs.
> **Updated:** 2026-07-20.

## Must-fix foundation (block future modules)
- **F1 — ✅ Closed (Sprint 0).** DB migration framework delivered:
  `app/core/migrations/` — `schema_version` ledger + ordered, idempotent,
  forward-only runner with rollback; baseline `0001_initial`. (Was Ref: L1)
- **F3 — No RBAC.** `users.role` decorative; any user can do anything. (L4)
- **F7 — No encryption at rest.** DB/attachments/backups plaintext. (L5)
- **F2 — No Settings UI.** `settings` table unused; blocks Printer/WhatsApp. (L7)

## Correctness / robustness
- **L2 — String dates.** No validation on `followup_date` etc.; add pickers (F5).
- **L6 — Default creds `admin/admin123`, no lockout.** Force change on first use.
- Backup writes no audit row (minor; add `log_action`).

## Scale
- **L11 — Full view rebuild per action; no pagination.** Slow on large tables (F6).
- **L12 — SQLite single-writer.** Limits multi-user; factor into sync (F8).

## Housekeeping
- **L9 — `exports/` and `logs/` reserved but unused.** Wire up export (D3) /
  logging.
- **L14 — Dark theme token reserved, not implemented.** Don't ship partial dark.
- **L15 — No CI, no interaction/event tests.** Add a pytest CI + a Flet/
  Playwright harness for handlers.

## Not-a-bug, by design (do not "fix")
- Narrative-first: `prescription_items` is derived and non-authoritative.
- Audit swallows exceptions on purpose (never break clinical flow).
- Full rebuild from DB on navigation is intentional simplicity at current scale.

## How to use
When a phase closes an issue, move it to `../docs/CHANGELOG.md`, delete it here,
and update `../docs/KNOWN_LIMITATIONS.md`.
