# WiseOS Health — UI Guidelines

> How to build screens consistently in Flet. Complements
> [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md). **Last updated:** 2026-07-20.

## Screen anatomy

Every authenticated screen is a module **view** returning an `ft.View`, wrapped
by the shared **shell** (`app/shared/shell.py`):

```
ft.View(route)
└── Column
    ├── header (shell)                       ← logo, workflow bar, backup,
    │                                          user chip, logout
    └── Container(padding=24, expand)
        └── body  ← the per-screen content the view supplies
```

`/login` is the **only** screen that does not use the shell (it renders its own
split-panel brand/login layout).

## Separation of concerns

- **View** = Flet controls only. Collect widget values into a plain `dict`; no
  SQL, no business rules.
- **Controller** = orchestration: call services, navigate (`page.go`), wrap in
  shell. Registers the module's routes (`ROUTES`).
- Business rules and data access live below the view (service → repository).

## Navigation

- Navigate with `page.go("/route")`; the router rebuilds the view from the DB.
- There is **no in-memory view cache** — state is reconstructed from SQLite on
  every navigation. Keep views cheap to rebuild.
- The header workflow bar gives global jumps (Dashboard / Search / Register /
  Backup / Logout) from anywhere.

## Shared widgets (`app/shared/widgets.py`)

Prefer these over re-implementing inline (they replaced Sprint-2 duplication):
`stat_card`, `empty_state`, `info_item`, patient `data_table`, and similar.
When you need a new composite that two screens share, add it here — do not
copy-paste between views.

## Feedback & errors

- Use `theme.snack(page, msg, error=?)` for all user feedback.
- Never surface a raw exception. The router already wraps dispatch in
  `try/except` and shows a friendly snackbar; keep views from leaking tracebacks.

## Forms

- Build fields with `theme.text_field` / `theme.dropdown`.
- Dropdown vocabularies come from `app/config/constants.py`
  (`GENDERS`, `BLOOD_GROUPS`, `CONSULTATION_TYPES`, `CASE_STATUSES`,
  `VISIT_OUTCOMES`) — never inline a list.
- Validate in the controller/service before persisting; show the first error via
  `snack`.

## Accessibility & sizing

- Minimum 14px text, 44px button height (enforced by the factories).
- Target window is 1366×768; design for that width without horizontal scroll.

## When adding a module's UI

1. Put controls in `modules/<domain>/view.py`.
2. Orchestrate in `controller.py`; export `ROUTES`.
3. Add its `ROUTES` to `app/bootstrap.py` and a nav entry in `shell.py` if it
   needs a top-level button.
4. Reuse theme factories and shared widgets — no new colors, no new fonts.
