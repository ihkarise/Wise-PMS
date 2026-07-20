# Module: Settings

**Status:** 🟡 Schema only — **no module, no UI yet** · **Table:** `settings`

## Purpose (target)
Central place to configure the practice: business/clinic profile, branding,
templates (prescription, invoice), printer, WhatsApp, Google Meet, phone
numbers, backup/restore, and import/export.

## What exists today
- A single-row `settings` table (created by `init_db()` with a default
  `clinic_name` = "Wise Homeopathy Multispeciality Center").
- Columns: `clinic_name`, `doctor_name`, `clinic_address`, `phone`, `email`,
  `logo_path`, `backup_path`, `created_at`.
- **No repository, service, controller, or view.** Nothing edits it in-app.

## Target design (planned — needs approval)
Create `app/modules/settings/` following the standard vertical slice:
- `models.py` `Settings`; `repository.py` (get/update the single row);
  `service.py` (validation, audit); `controller.py` (route `^/settings$`, guard
  to Administrator once RBAC lands); `view.py` (tabbed form).
- Sections: **Business** · **Branding** (logo) · **Templates** (prescription,
  invoice) · **Printer** · **WhatsApp** (editable message templates + variables)
  · **Google Meet** · **Phone numbers** · **Backup/Restore** · **Import/Export**.
- WhatsApp templates and print templates are stored here and consumed by those
  modules — this is why Settings is an early foundation phase (backlog **F2**).

## Dependencies (target)
Consumed by Printer, WhatsApp, Billing (invoice branding), Backup (restore).
Depends on migrations (F1) for any new columns/tables and RBAC (F3) to gate edit
access.

## Known limitations
No UI (L7). Adding columns needs the migration runner (F1) first.
