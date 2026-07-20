# Settings System — Specification

> **Status:** Design only (Phase 2). Schema exists (`settings` single row); **no
> module/UI yet**. Backlog **F2**. **Last updated:** 2026-07-20.
> Extends [`../docs/modules/Settings.md`](../docs/modules/Settings.md).

## 1. Purpose

A configurable central place for the practice to set its identity, branding, and
the **templates** that other modules consume (prescription, invoice, WhatsApp).
Settings is an **early foundation** because Printer and WhatsApp depend on it
(Constitution Art. VIII §3 — templates everywhere, editable in Settings).

## 2. What exists today

- A single-row `settings` table seeded by `init_db()` with `clinic_name =
  "Wise Homeopathy Multispeciality Center"`.
- Columns: `clinic_name`, `doctor_name`, `clinic_address`, `phone`, `email`,
  `logo_path`, `backup_path`, `created_at`.
- **No repository, service, controller, or view** — nothing edits it in-app.

## 3. Sections (target)

| Section | Contents | Consumed by |
| ------- | -------- | ----------- |
| **Clinic Information** | name, address, phone, email, website | Printer, WhatsApp, Portal |
| **Logo / Branding** | logo image, accent, letterhead | Printer, Portal |
| **Printer** | default printer/target, page size, margins | Wise Printer |
| **Prescription Templates** | layout + variables for scripts | Wise Printer, Protocols |
| **Invoice Templates** | layout + variables for invoices | Wise Printer, Billing |
| **Protocol Templates** | manage the protocol library | Protocol Engine |
| **WhatsApp** | editable message templates + variables + provider/creds | WhatsApp |
| **Google Meet** | provider + credentials (env-backed) | Telemedicine |
| **Backup** | backup path, schedule (future), encrypt (future) | Backup |
| **Restore** | restore from a backup zip | Backup |
| **Import / Export** | export/import data + templates (`exports/`) | Export engine (D3) |

## 4. Data model (planned)

The current single-row `settings` covers clinic identity. Templates and
credentials are **new** and need F1:

```
settings                 (existing single row — clinic identity + branding)
message_templates        (WhatsApp — see WHATSAPP_SYSTEM.md)
print_templates          key · kind (prescription|invoice|label|advice) ·
                          name · layout (JSON/markup) · enabled · updated_at
setting_secrets          key · value (env-backed reference, NOT the raw secret)
```

- **Secrets are never stored in the DB in the clear** and never committed — a
  `setting_secrets` row references an env var / OS keystore entry (Constitution
  Art. VI §6). The DB holds a reference, not the key.
- Adding columns to `settings` (e.g. `website`) needs the migration runner (F1);
  until then only new tables are safe.

## 5. Service contract (target)

```
settings.service
  get_settings() -> dict                     # the single clinic row (+ derived)
  update_settings(data, user_id) -> None     # validated + audited
  get_template(kind, key) -> dict | None
  save_template(kind, key, layout, user_id) -> None
  export_all(target_path) -> str             # data + templates
  import_all(source_path, user_id) -> None
```

- `update_settings` validates (e.g. email/phone format), audits, and writes the
  single row.
- Editing requires the `settings.edit` permission (Administrator) once RBAC lands.

## 6. UI (target)

A tabbed form (one tab per section, Constitution Art. V — theme factories only),
route `^/settings$`, guarded to Administrator under RBAC. Logo upload reuses the
attachment/file-copy pattern; template editors use a safe field/variable palette
(no code).

## 7. Why Settings is foundational

- **Wise Printer** needs branding + prescription/invoice templates.
- **WhatsApp** needs editable message templates + provider config.
- **Telemedicine** needs Meet credentials.
- **Backup/Restore/Export** need paths and (future) encryption config.

Shipping Settings early unblocks all of the above (roadmap Phase 3 candidate).

## 8. Dependencies & sequencing

- **Requires:** F1 for any new columns/tables (templates, secrets). RBAC (F3) to
  gate edit access — until then Settings is editable by any user (acceptable in
  the single-trusted-clinician posture).
- **Feeds:** Printer, WhatsApp, Billing (invoice branding), Telemedicine, Backup,
  Export.

## 9. Manual test checklist (implementing phase)

- [ ] Editing clinic info persists to the single row and audits.
- [ ] A prescription template edit changes the rendered script (Printer).
- [ ] A WhatsApp template edit changes the rendered message.
- [ ] Secrets are stored by reference (env), never in the DB in the clear, never
      committed.
- [ ] Export produces a portable bundle; import restores it.
- [ ] Only Administrator can edit once RBAC lands.
- [ ] Model/table parity + router contract green.

## 10. Risks

- **Secret handling** — must be env/keystore-backed from day one; a DB-plaintext
  key is a security regression (L5/F7).
- **Template safety** — editing must never allow code injection into printed/sent
  output; substitute variables into a fixed layout only.
</content>
