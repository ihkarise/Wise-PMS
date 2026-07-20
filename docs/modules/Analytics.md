# Module: Analytics

**Status:** 🔜 Planned (basic aggregates exist in Dashboard) · read models

## Purpose (target)
Insight over the practice: clinical trends, prescription patterns, outcomes,
retention, revenue — as charts and KPIs.

## Today
The **Dashboard** already computes basic aggregates (total patients, added
today, visits today, follow-ups due) via `patient_stats()` / `visit_stats()`.
Analytics generalizes this into a dedicated module.

## Target design (planned — needs approval)
- `app/modules/analytics/` — read models + a charting view. No new base tables;
  aggregates over clinical + inventory + billing data.
- Feeds:
  - `prescription_items` → most-used medicines/potencies, seasonality.
  - `visits.outcome` → outcome distributions per condition/protocol.
  - Cohorts over `patients` (place, age, consultation_type).
  - `audit_logs` → staff activity.

## Integrations
- **Protocols** — protocol usage vs. outcomes.
- **OCR** — lab-value trends across the patient population.
- **Inventory/Billing** — consumption and revenue analytics.
- **AI Assistant** — analytics features as model inputs.
- Charts follow the [`../DESIGN_SYSTEM.md`](../DESIGN_SYSTEM.md) palette.

## Dependencies
Structured dates (F5) improve time-series; RBAC (F3) gates access.

## Notes
The **narrative-first + structured-extraction** design pays off here: analytics
runs on the derived structured layer while the narrative remains the record of
care.
