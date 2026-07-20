# EPIC-02 — Settings System & Templates

> **Spec:** [`../SETTINGS_SYSTEM.md`](../SETTINGS_SYSTEM.md) · **Backlog:** F2 ·
> **Stage:** A — Foundation · **Depends on:** EPIC-01 (F1) ·
> **Complexity:** S–M · **Risk:** Low · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. V, VI, VIII.

## 1. Objective

Make the practice configurable in-app: clinic identity, branding, and the
**templates** (prescription, invoice, WhatsApp) that other modules consume. The
`settings` table exists but nothing edits it (L7). Settings is an early foundation
because Printer (EPIC-09) and WhatsApp (EPIC-11) depend on its templates.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E02-F1 | Settings module | `modules/settings/` vertical slice (models→repo→service→controller→view) |
| E02-F2 | Clinic info & branding | Name, address, phone, email, website, logo |
| E02-F3 | Templates store | Prescription/invoice/label print templates + protocol library hook |
| E02-F4 | WhatsApp templates | Editable message templates + variable palette (feeds EPIC-11) |
| E02-F5 | Secrets (env-backed) | Provider credentials referenced, never stored plaintext/committed |
| E02-F6 | Import / Export | Portable bundle of settings + templates (`exports/`, D3) |
| E02-F7 | Backup/Restore config | Backup path + (future) encryption toggle |

## 3. User stories

- **E02-F2-S1** — As an Administrator, I want to edit clinic name/address/logo, so
  that printed and messaged output shows my branding.
- **E02-F3-S1** — As a doctor, I want to edit the prescription template, so that
  printed scripts match my format.
- **E02-F4-S1** — As reception, I want to edit the WhatsApp welcome message, so
  that patients get the wording we want.
- **E02-F5-S1** — As an Administrator, I want provider API keys stored securely
  (env/keystore), so that secrets are never committed or exposed in the DB.
- **E02-F6-S1** — As an Administrator, I want to export/import my settings and
  templates, so that I can back them up or move to another machine.

## 4. Engineering tasks

- **E02-T1** — Migration: `print_templates`, `setting_secrets` tables; additive
  columns on `settings` (e.g. `website`) via EPIC-01 runner.
- **E02-T2** — `models.py` `Settings` (+ template/secret models); `repository.py`
  (get/update single row; template CRUD).
- **E02-T3** — `service.py`: `get_settings`, `update_settings` (validate + audit),
  template get/save, `export_all`/`import_all`; secret handling via env reference.
- **E02-T4** — `controller.py`: route `^/settings$`; guard to Administrator (once
  EPIC-03 lands; open to all until then).
- **E02-T5** — `view.py`: tabbed form (Business · Branding · Printer · Prescription
  · Invoice · Protocol · WhatsApp · Meet · Backup/Restore · Import/Export) using
  `theme.*` factories only.
- **E02-T6** — Nav entry in `shared/shell.py`.
- **E02-T7** — Tests: service behavior, view-build, model/table parity, router
  contract; docs update (Settings module doc, CHANGELOG, KNOWN_LIMITATIONS L7).

## 5. Dependencies

- **Upstream:** EPIC-01 (migrations for new columns/tables). Benefits from EPIC-03
  (gate edit to Administrator).
- **Downstream:** EPIC-09 (Printer templates), EPIC-11 (WhatsApp templates),
  EPIC-12 (invoice branding), EPIC-17 (Meet creds), Backup/Restore, Export (D3).

## 6. Acceptance criteria

- **AC1** — *Given* edited clinic info, *when* saved, *then* it persists to the
  single row and writes an audit entry.
- **AC2** — *Given* an edited prescription template, *when* a script is rendered
  (EPIC-09), *then* the output reflects the change.
- **AC3** — *Given* a provider API key, *when* saved, *then* the DB stores only a
  reference (env/keystore), never the raw secret, and nothing is committed.
- **AC4** — *Given* a settings export, *when* imported on another machine, *then*
  settings and templates are restored.
- **AC5** — *Given* RBAC is active, *when* a non-Administrator opens `/settings`,
  *then* they are refused with a friendly message.

## 7. Regression tests

- **Must stay green:** all existing suites (golden, models, router, views).
- **New:** settings service tests (validation, audit, template save/get,
  export/import round-trip), settings view-build, model/table parity for new
  tables, router contract for `^/settings$`.

## 8. Rollout phases

- **E02-R1** — Migration + module skeleton + clinic-info tab (read/write the
  existing row).
- **E02-R2** — Print templates (prescription/invoice/label) storage + editor.
- **E02-R3** — WhatsApp templates + variable palette; secrets via env reference.
- **E02-R4** — Import/Export + Backup/Restore config; docs closeout (L7).

## 9. Rollback

Revert the module + hide the nav/route; new tables are inert. No data destroyed.
Templates absent → consumers fall back to built-in defaults (EPIC-09/11 must ship
a default template).

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: secrets verified env-backed and absent
from the DB and git; export/import round-trips cleanly.
</content>
