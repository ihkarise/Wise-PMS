# Module: Dashboard

**Status:** ✅ Built · **Path:** `app/modules/dashboard/` · **Storage:** (aggregates)

## Purpose
The landing screen after login: at-a-glance practice stats and quick entry to
the core workflows.

## Layers
`controller.py` (route `^/dashboard$`) · `view.py`. No table/model/repository of
its own — it reads aggregates from other modules' services.

## Shows
- Total patients, Added today (`patients.service.patient_stats`).
- Visits today, Follow-ups due (`visits.service.visit_stats`).
- Recent patients (`patients.service.recent_patients`) — click to open a profile.

## Route
`^/dashboard$` — also the router's **fallback** for unmatched routes and recovered
errors (when authenticated).

## Dependencies
`dashboard → patients.service`, `→ visits.service`, `→ shared.shell/theme/widgets`.

## Future
Grows into (or links to) the full [`Analytics.md`](./Analytics.md) module: charts,
KPIs, revenue, stock alerts. Stat cards use `app/shared/widgets.py` so the look
stays consistent as tiles are added.
