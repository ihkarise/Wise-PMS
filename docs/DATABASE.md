# WiseOS Health — Database

> Source of truth for the schema is the migration set under
> `app/core/migrations/` (baseline: `v0001_initial.py`). This document mirrors it
> and records conventions. **Last updated:** 2026-07-20.

## Engine & conventions

- **SQLite**, single file `data/wise_pms.db` (path from `app.config.paths`,
  relocatable via `WISE_PMS_HOME`).
- One connection per operation via `core/database.get_connection()`:
  `row_factory = sqlite3.Row`, `PRAGMA foreign_keys = ON`.
- All SQL lives in **repositories** (`app/modules/<domain>/repository.py`) built
  on `core/repository.BaseRepository`. No SQL in services or views.
- **Idempotent bootstrap:** `init_db()` applies pending migrations via
  `app.core.migrations.migrate(conn)`, then seeds `admin`/`admin123` + one
  `settings` row only if absent.

## Tables (9 domain + 1 internal)

> **Sprint 2 (`v0002_consultations`):** `consultations` — the clinical *document*,
> 1:1 with a `visits` row (the *event*). Columns: `id`, `visit_id`
> (UNIQUE → `idx_consultation_visit`), `patient_id` (`idx_consultation_patient`),
> `case_id`, narrative `chief_complaint`/`history`/`examination`/`diagnosis`/
> `remarks`, `status` (`draft|in_progress|completed|amended|locked`, default
> `draft`), `created_at`, `updated_at`. FKs → `visits`/`patients`/`patient_cases`.
> Additive + reversible; `visits` unchanged (ADR-001 / ADR-0009).

The 8 domain tables below plus one internal bookkeeping table, `schema_version`
(`version` PK · `name` · `applied_at`), which records every applied migration.

### users
`id` PK · `username` UK · `password_hash` (bcrypt) · `full_name` · `role`
(free text today — RBAC not yet enforced) · `is_active` · `created_at`.

### patients
`id` PK · `reg_no` UK (`P000001…`, auto-generated with collision check) ·
`name` · `gender` · `age` · `dob` · `phone` · `whatsapp` · `email` · `address` ·
`place` · `occupation` · `blood_group` · `photo_path` · `doctor` (free text
name) · `consultation_type` · `notes` · `is_active` (**soft delete**) ·
`created_at`.

### settings
Single-row clinic profile: `clinic_name` · `doctor_name` · `clinic_address` ·
`phone` · `email` · `logo_path` · `backup_path` · `created_at`. **No UI yet.**

### audit_logs
`id` PK · `user_id` · `action_type` · `entity_type` · `entity_id` ·
`action_details` · `created_at`. Append-only; writes never raise.

### patient_cases
`id` PK · `patient_id` FK→patients · `case_title` · `diagnosis` · `case_notes` ·
`status` (`Open`/`Closed`/`Resolved`/`On Hold`) · `doctor_id` (acting user) ·
`created_at`.

### visits
`id` PK · `patient_id` FK→patients · `case_id` FK→patient_cases (nullable) ·
`doctor_id` · `visit_type` · `visit_date` · `visit_notes` ·
`investigation_notes` · `prescription_notes` · `followup_date` · `outcome` ·
`created_at`. The three `*_notes` fields are the **narrative source of truth**.

### prescription_items
`id` PK · `visit_id` FK→visits · `medicine_name` · `potency` · `dosage` ·
`instructions`. **Non-authoritative** extraction from `visits.prescription_notes`
(re-derived delete+insert on every visit write). See
[`../app/utils/prescription.py`](../app/utils/prescription.py).

### attachments
`id` PK · `patient_id` FK→patients · `visit_id` (nullable) · `file_name` ·
`file_path` (relative, under `attachments/patient_<reg_no>/`) · `file_type` ·
`uploaded_at`.

## Relationships

```
users        1─┬─* audit_logs
patients     1─┼─* patient_cases 1─* visits 1─* prescription_items
             1─┼─* visits (also directly)
             1─┴─* attachments
patient_cases  ─── visits.case_id (nullable)
visits         ─── attachments.visit_id (nullable)
```

## Indexes

`patient_cases(patient_id)`, `visits(patient_id)`, `visits(visit_date)`,
`visits(case_id)`, `attachments(patient_id)`, and
`patients(name|phone|reg_no|place)`.

## Migration framework (backlog F1 — delivered, Sprint 0)

Schema changes are managed by `app/core/migrations/`:

- **`schema_version` ledger** records every applied migration (`version`, `name`,
  `applied_at`).
- **Ordered, forward-only, idempotent runner.** `migrate(conn)` applies pending
  `vNNNN_*` migrations in ascending order, each stamped atomically with its DDL,
  and never re-applies one already recorded. Running it twice is a no-op.
- **Baseline `0001_initial`** is the behaviour-preserving conversion of the
  former inline `SCHEMA`. Because it is create-if-not-exists, applying it to a
  **legacy** clinic database simply stamps it at version 1 — no data touched.
- **Rollback support.** `rollback_to(conn, version)` runs each migration's
  `down` script in reverse. Used by tests and recovery; production upgrades are
  forward-only.

**Rule (Constitution Art. IV §2):** every new migration must be **additive and
idempotent** — `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE … ADD COLUMN` — and
must **never** drop or rename a column an older build reads.

### Adding a migration

1. Add `app/core/migrations/vNNNN_<name>.py` exporting a
   `MIGRATION = Migration(version=N, name="…", up="…", down="…")`.
2. Append it to `MIGRATIONS` in `registry.py` (validated to be sequential from 1).
3. Add its table(s) to this doc and a model/table-parity test where applicable.

## Planned tables (not yet created)

`appointments`, `queue`, `roles`/`permissions`, `invoices`/`invoice_items`/
`payments`, `dispense_*`, `inventory_*`, `protocols`/`protocol_items`,
`ocr_results`, `messages`/`message_templates`, telemedicine `sessions`. Each
arrives with its module as a new migration.
