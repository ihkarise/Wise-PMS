# Module: Settings

**Status:** ✅ Built (Sprint 4, clinic-profile scope) · **Path:**
`app/modules/settings/` · **Table:** `settings` (existing since Sprint 1)

## Purpose
Let an authenticated user edit the clinic's identity — the fields shown
on printed documents and the app header. This is deliberately **not** a
general application-settings screen.

## Layers
`models.py` (`Settings`) · `repository.py` (`SettingsRepository`,
`SETTINGS_FIELDS` whitelist) · `service.py` (validation + audit +
whitelist enforcement) · `controller.py` · `view.py`.

## Public service API
- `get_clinic_settings() -> dict | None`
- `update_clinic_settings(data, user_id) -> dict` — rejects (`ValueError`)
  any key outside `SETTINGS_FIELDS`; requires non-empty `clinic_name`;
  writes an audit row (`"Settings Updated"`).
- `upload_logo(source_path, user_id) -> dict` — writes the logo through
  `app.core.storage.get_storage()` (ADR-002 §5.1), then persists
  `logo_path` through the same whitelist/audit path.

## Security boundary (ADR-002 §6.6 — do not weaken)
Only six clinic-profile fields are exposed, here or anywhere in this
module: `clinic_name`, `doctor_name`, `clinic_address`, `phone`, `email`,
`logo_path`. **Explicitly excluded, this sprint and until a future,
separately approved phase:**

- Database configuration (engine, connection string)
- Storage-provider configuration
- Backup-destination configuration (`settings.backup_path` — the column
  already existed pre-Sprint-4; it stays present in the schema and
  **read-only** through this module; nothing here writes it)
- API keys / provider credentials
- RBAC / permissions / any other security setting

These require a future Administrator/Security surface, gated behind RBAC
(F3) and, for secrets, encryption at rest (F7) — neither exists today.
`update_clinic_settings` enforces this at the service layer (not just the
UI): passing a disallowed key raises `ValueError`, verified by
`tests/test_settings_domain.py::test_update_clinic_settings_rejects_unsupported_fields`.

## Route & nav
`^/settings$`, reachable from the header workflow bar (gear icon). Session
guard applies like every other route. **Known accepted gap** (Security.md:
"any logged-in user can do anything" until F3): any authenticated user can
reach this route, but the field whitelist above limits what they can
change to clinic-profile text/logo — never security-sensitive
configuration.

## Dependencies
`settings.service → audit.service`, `settings.service → app.core.storage`
(logo upload only). No cross-module SQL; no other module's table is
touched.

## Future
An Administrator/Security settings surface (post-RBAC, post-encryption)
will host database/storage-provider/backup-destination selection and BYO
AI-provider API keys (ADR-002 §6). It is a distinct module, not an
extension of this one.
