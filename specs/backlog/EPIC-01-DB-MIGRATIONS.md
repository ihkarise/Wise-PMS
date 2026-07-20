# EPIC-01 — Database Migrations & Schema Versioning

> **Spec:** [`../IMPLEMENTATION_PLAN.md`](../IMPLEMENTATION_PLAN.md),
> [`../../docs/DATABASE.md`](../../docs/DATABASE.md) · **Backlog:** F1 ·
> **Stage:** A — Foundation · **Depends on:** none ·
> **Complexity:** S · **Risk:** Low · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. IV §2.

## 1. Objective

Give the schema a safe, versioned evolution path. Today the schema is
create-if-not-exists only: adding a *table* is safe, but **changing an existing
table has no upgrade path** (L1). This epic adds an ordered, idempotent,
forward-only migration runner so every later epic can evolve the DB on existing
clinic databases without data loss. It is the unlock for the entire roadmap.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E01-F1 | Schema version table | Track the applied migration version in the DB |
| E01-F2 | Migration runner | Ordered, idempotent, forward-only application at startup |
| E01-F3 | Initial migration | Convert current `SCHEMA` → `0001_initial`; stamp existing DBs without change |
| E01-F4 | Developer authoring API | A clear, tested way to add migration NNNN |
| E01-F5 | Parity & safety tests | "fresh DB == migrated DB"; idempotency; regression golden intact |

## 3. User stories

- **E01-F1-S1** — As a maintainer, I want the DB to record its schema version, so
  that the app knows which migrations still need to run.
- **E01-F2-S1** — As a maintainer, I want migrations to run automatically at
  startup before the app launches, so that the DB is always current when the UI
  opens.
- **E01-F2-S2** — As a maintainer, I want re-running the app to apply nothing when
  already current, so that startup is idempotent and safe.
- **E01-F3-S1** — As an existing clinic, I want my `data/wise_pms.db` to be stamped
  at the current version without any data change, so that upgrading is invisible
  and lossless.
- **E01-F4-S1** — As a developer of a later epic, I want a documented pattern to
  add migration NNNN, so that I can evolve a table safely.
- **E01-F5-S1** — As a reviewer, I want tests proving a freshly created DB is
  identical to a migrated one, so that the two paths never diverge.

## 4. Engineering tasks

- **E01-T1** — Add `schema_version` table (single row: `version`, `applied_at`) via
  `CREATE TABLE IF NOT EXISTS` in `core/database.py`.
- **E01-T2** — Implement `_apply_migrations(conn)` skeleton: read current version,
  iterate an **ordered list** of named migrations `> current`, run each inside a
  transaction, bump the version. Empty list stamps version 0 (no behavior change).
- **E01-T3** — Wire `_apply_migrations()` into `init_db()` **before** `ft.app`
  launch; keep it idempotent alongside the existing seed logic.
- **E01-T4** — Author `0001_initial`: capture the current `SCHEMA` as the first
  migration; for an **existing** DB (tables already present), stamp version 1
  without re-creating/altering anything.
- **E01-T5** — Define the migration record shape/convention (id `NNNN`, name, `up`
  callable/SQL) and document it in `IMPLEMENTATION_NOTES.md`.
- **E01-T6** — Tests: `tests/test_migrations.py` (idempotency, ordering, version
  bump) + a "fresh == migrated" parity assertion.
- **E01-T7** — Docs: update `DATABASE.md` (remove the ⚠️ migration gap),
  `KNOWN_LIMITATIONS.md` (close L1/F1), `CHANGELOG.md`, `DECISIONS.md` (new ADR),
  `.ai/KNOWN_ISSUES.md`, `.ai/CURRENT_PHASE.md`, `.ai/WORK_LOG.md`.

## 5. Dependencies

- **Upstream:** none (this is the first foundation epic).
- **Downstream (blocked until this lands):** EPIC-02…EPIC-22 — every epic that
  adds or alters a table.

## 6. Acceptance criteria

- **AC1** — *Given* a fresh environment, *when* the app starts, *then* the DB is
  created, migrations apply in order, and `schema_version` reflects the latest.
- **AC2** — *Given* an app already at the latest version, *when* it restarts,
  *then* no migration runs and no data changes (idempotent).
- **AC3** — *Given* an existing Sprint-2 `wise_pms.db`, *when* the app starts,
  *then* it is stamped at the current version with **zero** data or column change.
- **AC4** — *Given* a fresh DB and a DB built by running all migrations, *when*
  compared, *then* their schemas are identical.
- **AC5** — *Given* a migration raises mid-way, *when* applied, *then* it rolls
  back within its transaction and the version is not bumped.

## 7. Regression tests

- **Must stay green:** `test_regression.py` (byte-identical golden),
  `test_models.py`, `test_router.py`, `test_views_build.py`.
- **New:** `test_migrations.py` — runner idempotency, ordering, version stamping,
  fresh==migrated parity, transactional rollback on failure.

## 8. Rollout phases

- **E01-R1** — Version table + runner **skeleton** (empty list → stamps v0). No
  behavior change; regression golden must stay green. *(NEXT_TASK step 1.)*
- **E01-R2** — Add `test_migrations.py` (idempotency) before adding real
  migrations.
- **E01-R3** — Author `0001_initial`; stamp existing DBs; parity test.
- **E01-R4** — Docs closeout (L1/F1) + phase-end report; await approval.

## 9. Rollback

Forward-only + idempotent. Rollback = revert the app commit; the `schema_version`
stamp and any new empty tables are inert to the prior build. **Never** author a
migration that drops/renames a column an older build reads.

## 10. Definition of done

Per [`README.md`](./README.md) DoD. Additionally: migrations idempotent; existing
DB verified lossless on a copy before release.
</content>
