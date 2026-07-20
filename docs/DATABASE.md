# WiseOS Health — Database

> Source of truth for the schema is `app/core/database.py` (`SCHEMA`).
> This document mirrors it and records conventions. **Last updated:** 2026-07-20.

## Engine & conventions

- **SQLite**, single file `data/wise_pms.db` (path from `app.config.paths`,
  relocatable via `WISE_PMS_HOME`).
- One connection per operation via `core/database.get_connection()`:
  `row_factory = sqlite3.Row`, `PRAGMA foreign_keys = ON`.
- All SQL lives in **repositories** (`app/modules/<domain>/repository.py`) built
  on `core/repository.BaseRepository`. No SQL in services or views.
- **Idempotent bootstrap:** `init_db()` runs `CREATE TABLE IF NOT EXISTS` and
  seeds `admin`/`admin123` + one `settings` row only if absent.

## Tables (8)

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

## Migration story — ⚠️ gap

Schema is **create-if-not-exists only**. There is **no version table and no
`ALTER TABLE` path**. Adding *new tables* is safe (auto-created); **changing an
existing table's columns has no upgrade path**. Closing this is backlog **F1**
and the recommended next code phase — see [`ROADMAP.md`](./ROADMAP.md).

## Planned tables (not yet created)

`appointments`, `queue`, `roles`/`permissions`, `invoices`/`invoice_items`/
`payments`, `dispense_*`, `inventory_*`, `protocols`/`protocol_items`,
`ocr_results`, `messages`/`message_templates`, telemedicine `sessions`. Each
arrives with its module via a migration (once F1 lands).
