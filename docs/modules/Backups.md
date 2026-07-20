# Module: Backups

**Status:** ✅ Built · **Path:** `app/modules/backup/` · **Storage:** filesystem

## Purpose
One-click local backup of the database and all attachments.

## Layers
`service.py` only (no table, no model, no view of its own). Triggered from the
shared shell's **Backup** icon.

## Public service API
- `backup_now() -> str` — returns the created zip path.

## Behavior
- Writes `backups/backup_YYYY_MM_DD.zip` containing `wise_pms.db` (arcname
  `wise_pms.db`) plus the entire `attachments/` tree.
- If a same-day backup already exists, a time-suffixed name is used
  (`backup_YYYY_MM_DD_HHMMSS.zip`) — never overwrites.
- Paths come from `app.config.paths`; honors `WISE_PMS_HOME`.
- The shell shows a success snackbar with the path, or a failure snackbar.

## Dependencies
`backup.service → config.paths`. No audit row today (candidate improvement).

## Known limitations
- **Backups are unencrypted** (L5 / [`../SECURITY.md`](../SECURITY.md)) — the zip
  contains full PHI in the clear.
- No scheduled/automatic backups; no off-device/cloud target.
- No restore UI (restore is manual: unzip into place).

## Future
Encrypted backups, scheduled backups, restore UI, and cloud backup as an
additive target once encryption at rest (F7) and sync (F8) land. Import/Export
(the reserved `exports/` folder) will live alongside.
