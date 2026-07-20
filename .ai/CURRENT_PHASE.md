# .ai/CURRENT_PHASE.md

**Phase:** Sprint 0 — Infrastructure Foundation (DB Migrations / backlog F1)
**Status:** Complete → committed; awaiting Product Owner approval before Sprint 1
**Branch:** `claude/wiseos-health-sprint-exec-w2jjvh`
**Updated:** 2026-07-20

## Goal
Deliver the schema-migration foundation that unlocks every future module. No
business logic, no user-facing features — infrastructure only.

## Scope (this sprint)
- New `app/core/migrations/` package:
  - `runner.py` — `Migration` dataclass + engine (`ensure_version_table`,
    `current_version`, `applied_versions`, `run_migrations`, `rollback`,
    `MigrationError`).
  - `registry.py` — the ordered, self-validating `MIGRATIONS` tuple.
  - `v0001_initial.py` — the baseline (former inline `SCHEMA`) + reversible down.
  - `__init__.py` — public API (`migrate`, `rollback_to`, `current_version`, …).
- `schema_version` ledger table (version · name · applied_at).
- `init_db()` now migrates then seeds (admin + settings unchanged).
- `tests/test_migrations.py` — idempotency, legacy stamping, rollback,
  fresh-vs-migrated parity, registry validation, init_db integration.
- Docs: `DATABASE.md`, `DECISIONS.md` (ADR-0008), `CHANGELOG.md`,
  `KNOWN_LIMITATIONS.md`, `.ai/` state files.

## Explicitly NOT in scope
- No Settings, Consultation Workspace, RBAC, or any other module.
- No new domain tables; no business-logic change. Baseline schema is byte-for-byte
  the prior schema (create-if-not-exists), so existing databases are untouched
  except for being stamped at version 1.

## Definition of done
- `python3 -m pytest -q` green (**16 passing**: 4 prior + 12 new).
- Regression golden updated for the internal `schema_version` table (documented
  in ADR-0008; no service-behaviour change).
- App imports and `init_db()` boot verified; migration ledger stamped.
- Every affected doc updated in the same commit.

## Verification
```bash
python3 -m pytest -q     # expect 16 passing
```

> Note: install dev deps first (`python3 -m pip install -r requirements-dev.txt`);
> the bare `pytest` on PATH runs under a uv-isolated interpreter without runtime
> deps — use `python3 -m pytest`.

See [`NEXT_TASK.md`](./NEXT_TASK.md) for the proposed Sprint 1 (Settings UI / F2).
