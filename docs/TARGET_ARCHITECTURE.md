# Wise PMS — Target Architecture & Migration Plan

Companion to [`ARCHITECTURE.md`](./ARCHITECTURE.md) (as-built) and
[`DEPENDENCY_MAP.md`](./DEPENDENCY_MAP.md). This document defines **where the
codebase is going** and the **incremental, behavior-preserving** path to get
there.

## 0. Design principles

1. **Domain-driven, not screen-driven.** Code is organized around *business
   modules* (Patients, Visits, Billing…), each owning its full vertical slice.
2. **Clean layering inside each module.** A module may contain
   `models → repository → service → controller → views`, depending downward
   only.
3. **Preserve behavior.** The refactor changes *structure*, never *what the app
   does*. The regression harness (`tests/`) must print an identical snapshot at
   every step.
4. **No dead scaffolding.** We build layers/modules for domains that have real
   code, and provide a **registry + worked template** for future domains rather
   than committing 13 empty folders.
5. **Small, reviewable commits.** Each stage leaves the app runnable.

## 1. Target layer model

```
┌──────────────────────────────────────────────────────────────┐
│ views      Flet screens — build controls, no business logic   │  presentation
│ controllers  orchestrate a screen: call services, navigate    │
├──────────────────────────────────────────────────────────────┤
│ services   business rules, validation, cross-entity workflows │  domain
│ models     typed entities (dataclasses) + (de)serialization   │
├──────────────────────────────────────────────────────────────┤
│ repositories  all SQL / data access for one aggregate          │  data access
├──────────────────────────────────────────────────────────────┤
│ core       database engine, migrations, router, base classes   │  infrastructure
│ config     paths, constants, settings                          │
│ shared     theme (design system), shell, reusable widgets      │  cross-cutting
│ utils      pure helpers (text parsing, dates, formatting)      │
└──────────────────────────────────────────────────────────────┘
```

**Dependency rule:** `views → controllers → services → repositories → core`.
Nothing lower imports anything higher. `config`, `shared`, `utils` are leaf
dependencies anyone may use.

## 2. Target folder structure

```
Wise-PMS/
├── main.py                       # thin: bootstrap() only
├── requirements.txt
├── .gitignore
├── docs/                         # this audit
├── tests/
│   └── test_regression.py        # behavioral golden test (service layer)
└── app/
    ├── __init__.py
    ├── bootstrap.py              # init DB + run migrations + ft.app(target)
    ├── config/
    │   ├── paths.py              # BASE_DIR, DATA_DIR, DB_PATH, *_DIR
    │   └── constants.py          # GENDERS, BLOOD_GROUPS, CONSULTATION_TYPES,
    │                             #   CASE_STATUSES, VISIT_OUTCOMES, FILE_TYPES
    ├── core/
    │   ├── database.py           # get_connection, init_db, migrations runner
    │   ├── repository.py         # BaseRepository (connection lifecycle helper)
    │   └── router.py             # Router: route table + dispatch + guard
    ├── shared/
    │   ├── theme.py              # design tokens + component factories
    │   ├── shell.py              # app chrome (header/workflow bar)
    │   └── widgets.py            # stat_card, empty_state, info_item, data_table…
    ├── utils/
    │   └── prescription.py       # extract_prescription_items (pure)
    └── modules/
        ├── authentication/       # models, repository, service, controller, view
        ├── patients/             # models, repository, service, controller, views
        ├── registration/         # controller, view (uses patients.service)
        ├── cases/                # models, repository, service, controller, view
        ├── visits/               # models, repository, service, controller, view
        ├── attachments/          # models, repository, service
        ├── timeline/             # service  (read-model over visits/cases/attach)
        ├── dashboard/            # controller, view
        ├── audit/                # service   (cross-cutting, append-only)
        └── backup/               # service
```

> During migration the **old import paths remain valid** (`app.services.*`,
> `app.ui.*`, `app.database.db`) as thin re-export shims, so nothing breaks
> mid-flight. Shims are removed in the final cleanup commit once all references
> point at the new locations.

## 3. Module registry (existing + future)

Existing domains map 1:1 onto current code. Future domains are **documented
extension points**, not empty folders — each gets a folder only when it gets
real code, following the template in §5.

| Business module | Status | Backing tables (current or planned) | Notes |
| --------------- | ------ | ----------------------------------- | ----- |
| Authentication  | ✅ built | `users` | bcrypt; add RBAC later |
| Patients        | ✅ built | `patients` | CRUD, search, soft-delete |
| Registration    | ✅ built | `patients` | thin flow over Patients |
| Case Records    | ✅ built | `patient_cases` | narrative-first |
| Visits          | ✅ built | `visits`, `prescription_items` | consultation screen |
| Consultation    | ✅ built (=Visits) | `visits` | UI name for the visit workflow |
| Prescriptions   | ✅ built (partial) | `prescription_items` | extraction util |
| Attachments     | ✅ built | `attachments` | per-patient files |
| Timeline/Visits history | ✅ built | (read model) | merged event feed |
| Dashboard/Analytics (basic) | ✅ built | (aggregates) | stat cards |
| Audit           | ✅ built | `audit_logs` | cross-cutting |
| Backup          | ✅ built | (filesystem) | zip of db + attachments |
| Settings        | 🟡 schema only | `settings` | table exists, no UI |
| Appointments    | 🔜 planned | `appointments` (new) | booking |
| Waiting Queue   | 🔜 planned | `queue` (new) | live token/queue |
| Dispensing      | 🔜 planned | `dispense_*` (new) | pharmacy handoff |
| Inventory (WHIMS)| 🔜 planned | `inventory_*` (new) | stock/expiry |
| PillFill        | 🔜 planned | integration | dispensing automation |
| Billing         | 🔜 planned | `invoices`, `invoice_items` (new) | |
| Payments        | 🔜 planned | `payments` (new) | |
| Reports         | 🔜 planned | (read models) | |
| Analytics       | 🔜 planned | (read models) | prescription_items feed |
| Telemedicine    | 🔜 planned | `sessions` (new) | online consult |
| Patient Portal  | 🔜 planned | (separate front-end) | |
| AI Assistant    | 🔜 planned | (service + integrations) | clinical workflows |
| Administration  | 🔜 planned | `users`, `roles` | user mgmt + RBAC |

## 4. How this prepares the stated future products

| Future product | What the target architecture provides |
| -------------- | ------------------------------------- |
| **WiseOS** (platform) | `core/router` + module registry → each product surface is a set of modules mounted on one shell |
| **Wise WHIMS** (inventory) | drop-in `modules/inventory/` vertical slice; its own repo + tables + migration |
| **Wise Holoscan** | AI Assistant module + typed `models` give structured clinical data to feed vision/AI workflows |
| **PillFill** | Dispensing module + repository seam to integrate external dispensing hardware/service |
| **Mobile apps** | services + repositories are UI-agnostic; a Flet mobile target (or API) reuses the domain layer unchanged |
| **Cloud synchronization** | the **repository layer is the sync seam**: swap/extend repositories to push/pull without touching services or UI |
| **AI-assisted clinical workflows** | typed models + `utils/prescription` extraction + audit trail provide clean, structured, traceable inputs |

## 5. Worked template for a new module

To add e.g. **Appointments**, create `app/modules/appointments/` with:

```
appointments/
├── __init__.py
├── models.py       # @dataclass Appointment (+ from_row/to_dict)
├── repository.py   # class AppointmentRepository(BaseRepository): SQL only
├── service.py      # book(), reschedule(), cancel() — rules + audit
├── controller.py   # AppointmentsController — orchestrate view ↔ service
└── view.py         # appointments_view(page) — Flet controls only
```

Then:
1. Add the table(s) via a new migration in `core/database.py`.
2. Register routes in the module and mount them in `core/router.py`.
3. Add a nav entry in `shared/shell.py`.

No other module needs to change — that is the point of the structure.

## 6. Migration sequence (each = one commit, regression stays green)

| Stage | Change | Behavior risk |
| ----- | ------ | ------------- |
| 1 | Audit docs (`docs/`) | none (docs only) |
| 2 | Foundation hygiene: delete junk dirs, add `__init__.py`, `.gitignore`, `.gitkeep`, `tests/` | none |
| 3 | Extract `config/` (paths, constants) + `core/database.py`; `db.py` → shim | none (re-exports) |
| 4 | Add `repositories` + `models`; services delegate to repos, identical signatures/returns | none |
| 5 | Move code into `app/modules/<domain>/` + `shared/`; old paths become shims; `main.py` uses new paths | none (imports resolve; regression green) |
| 6 | Add `controllers` + `core/router`; `main.py` → `bootstrap.py`; remove shims | none |

**Verification at every stage:** `python -m pytest tests/` (or the standalone
regression runner) must produce a byte-identical snapshot to the Stage-0
baseline, and all modules must import cleanly.
