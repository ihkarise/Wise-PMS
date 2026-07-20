# Module: Reports

**Status:** 🔜 Planned — **not implemented** · read models over existing tables

## Purpose (target)
Operational and clinical reports: daily patient counts, follow-ups due, visit
volumes, prescriptions, revenue, stock — printable/exportable.

## Target design (planned — needs approval)
- `app/modules/reports/` — primarily **read models** (queries) plus a view and
  export. No new base tables; aggregates over `patients`, `visits`,
  `prescription_items`, `audit_logs`, and later billing/inventory.
- Service: parameterized report functions returning tabular results
  (date range, doctor, module) → rendered as tables and exportable to the
  `exports/` folder (currently reserved/unused, backlog D3).

## Reports (initial set)
- Patients registered (range), Visits (range), Follow-ups due, Outcomes mix,
  Top medicines (from `prescription_items`), Audit activity.

## Integrations
- **Printer** for printed reports; **exports/** for CSV/PDF.
- Shares query building with [`Analytics.md`](./Analytics.md) (Reports = tabular,
  Analytics = charts/insight).

## Dependencies
Benefits from structured dates (F5) and RBAC (F3, who can see what). Export
engine (D3).

## Notes
Keep report queries in repositories/read models so they can be reused by
Analytics and a future API without duplication.
