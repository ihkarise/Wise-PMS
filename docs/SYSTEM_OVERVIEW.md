# WiseOS Health — System Overview

> A one-page orientation. For depth see [`ARCHITECTURE.md`](./ARCHITECTURE.md),
> [`DATABASE.md`](./DATABASE.md), and the per-module docs in
> [`modules/`](./modules/). **Last updated:** 2026-07-20.

## What it is

Wise PMS is the first module of WiseOS Health: an **offline-first, local,
₹0/month desktop** Patient Management System for a homeopathy clinic.

| Concern | Choice |
| ------- | ------ |
| Language | Python 3.10+ |
| UI | Flet `0.28.3` (Flutter renderer for Python) |
| Storage | SQLite — one file `data/wise_pms.db` |
| Auth | bcrypt password hashing |
| Packaging | PyInstaller → `WisePMS.exe` (Windows) |
| Network | none required |

## How it is organized

```
app/
├── bootstrap.py     composition root: init_db() → assemble ROUTES → ft.app()
├── config/          paths.py (WISE_PMS_HOME) · constants.py (vocabularies)
├── core/            database.py · router.py · repository.py · model.py
├── shared/          theme.py (design system) · shell.py (chrome) · widgets.py
├── utils/           prescription.py (pure extraction helper)
└── modules/         one vertical slice per business domain:
    authentication · patients · registration · cases · visits ·
    attachments · timeline · dashboard · audit · backup
```

Each module owns `models → repository → service → controller → view`, depending
only downward. The dependency graph is an acyclic
`views → controllers → services → repositories → core`.

## How a request flows

1. `page.go("/route")` → `core/router.Router.dispatch`.
2. Router applies the **session guard** (everything but `/login` requires a
   logged-in user), matches the route regex, and calls the module **controller**.
3. Controller builds the screen via the module **view**, wrapped in the shared
   **shell** (header + workflow bar).
4. User actions call module **services** (business rules + audit), which call
   **repositories** (SQL only), which use `core/database.get_connection()`.
5. On save, the view navigates; the next screen re-reads from SQLite. **The
   database is the single source of truth** — there is no in-memory store.

## Runtime data

Created on first run under `BASE_DIR` (default = repo root, relocatable via
`WISE_PMS_HOME`): `data/`, `attachments/`, `backups/`, `exports/` (reserved),
`logs/` (reserved).

## Current capabilities

Login · Registration (auto reg-no) · Search · Patient Profile (+ Edit) · Cases ·
Visits/Consultation · Prescription intelligence · Timeline · Attachments ·
Dashboard · Audit · Backup.

## Not yet built

Settings UI, RBAC, DB migrations, and every future module (Consultation
Workspace, Protocol Engine, OCR, WhatsApp, Printer, Inventory/WHIMS, PillFill,
Billing, Analytics, Portal, Telemedicine, AI). See [`ROADMAP.md`](./ROADMAP.md).
