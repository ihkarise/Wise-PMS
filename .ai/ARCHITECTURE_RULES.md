# .ai/ARCHITECTURE_RULES.md — Hard rules for touching the code

> Violating these breaks the ecosystem's growth path. **Updated:** 2026-07-20.

## Layering (must hold)
1. Dependency direction is **`views → controllers → services → repositories →
   core`**. Nothing lower may import anything higher. No import cycles.
2. **SQL lives only in repositories** (`modules/*/repository.py` on
   `core.repository.BaseRepository`). Services and views must not open
   connections or write SQL.
3. **Views are Flet-only.** No business rules, no SQL. Collect widget values into
   a plain dict and call a service via the controller.
4. **Controllers orchestrate**: call services, navigate, wrap in the shared
   shell, and register the module's `ROUTES`.

## Modules
5. A new business capability = a new folder under `app/modules/<domain>/` with the
   full vertical slice. **No other module is edited** except:
   - add its `ROUTES` to `app/bootstrap.py`,
   - add a nav entry in `app/shared/shell.py` if it needs a top-level button,
   - add its table via a **migration** (once the migration runner exists).
6. Do not add code to a "planned" module doc's design without implementing it —
   docs must never claim code that doesn't exist.

## Data
7. **Narrative is authoritative.** Structured/extracted/derived data (e.g.
   `prescription_items`, future OCR values, AI suggestions) is non-authoritative
   and must never gate what a clinician writes.
8. **Never physically delete** clinical data — soft delete + retain history.
9. **Every mutation writes an audit row** via `audit.service.log_action`.
10. Domain vocabularies live in `app/config/constants.py` — never inline a list
    in a view.

## Design
11. Colors, fonts, radii, and components come from `app/shared/theme.py` and
    `app/shared/widgets.py`. **No hex literals or raw buttons/fields in views.**

## Behavior safety
12. The **regression golden** (`tests/test_regression.py`) must stay
    byte-identical unless a behavior change is intentional and documented (update
    the golden + CHANGELOG + DECISIONS in the same commit).
13. Model/table parity and router-contract tests must stay green.
14. The router must never leak a raw exception to the user (friendly snackbar +
    fallback).

## Future-proofing (charter)
15. **No assumption may block** Patient Portal, AI, Voice, Inventory, Billing,
    Analytics, Telemedicine, Cloud Sync, Mobile, or a public API.
16. External providers (WhatsApp, Meet, AI, OCR, cloud) go **behind an
    interface**; secrets live in Settings/env and are **never committed**.
17. Default to the **offline, ₹0** posture; cloud/network features are additive,
    opt-in, and gated behind RBAC (F3) + encryption at rest (F7).
