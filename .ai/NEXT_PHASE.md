# .ai/NEXT_PHASE.md — Proposed next phase (needs approval)

**Updated:** 2026-07-20

## Recommendation: Phase 2 — DB Migrations & Schema Versioning (backlog F1)

### Why this next
It is the **highest-severity code gap** and a hard prerequisite for almost every
future module. Today the schema is create-if-not-exists only: adding a *table* is
safe, but **changing an existing table has no upgrade path**. Settings UI, RBAC,
Appointments, Protocols, OCR, Billing, Inventory — all need to alter or add
tables safely on existing clinic databases. Small, low-risk, high-leverage.

### Scope
- Add a `schema_version` table and a **migration runner** in `core/database.py`
  (ordered, idempotent, forward-only migrations; each migration is a small,
  named unit).
- Convert the current `SCHEMA` into migration `0001_initial` (behavior-preserving
  — existing DBs are stamped at the current version without data loss).
- Migrations run inside `init_db()` before the app launches.
- Tests: migration-runner unit tests + a "fresh DB == migrated DB" parity test;
  regression golden stays green.
- Docs: update `DATABASE.md` (remove the ⚠️ migration gap), `KNOWN_LIMITATIONS.md`
  (close L1/F1), `CHANGELOG.md`, `DECISIONS.md` (new ADR), and this file.

### Risk
Low. No feature change; the runner is additive and must leave an existing
`data/wise_pms.db` untouched except for stamping its version.

### Alternatives (if the Owner prefers)
1. **Settings UI (F2)** — small, visible value; unblocks Printer/WhatsApp.
2. **RBAC (F3)** — compliance; larger; needs F1 first for new tables.
3. **Consultation Workspace (C1)** — the anchor feature; higher risk; best after
   F1/F2/F3 foundation.

### Do not start until
The Product Owner approves. Per the charter, no phase begins automatically.
