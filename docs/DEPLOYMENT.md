# WiseOS Health — Deployment

> How to run, package, and relocate Wise PMS. **Last updated:** 2026-07-20.

## Run from source (developer / clinic laptop)

```bash
# 1. Install Python 3.10+ (tick "Add Python to PATH" on Windows)
pip install -r requirements.txt   # flet==0.28.3, bcrypt>=4.0
python main.py                    # thin entrypoint → app.bootstrap.run()
# Login: admin / admin123  (change after first use)
```

`main.py` calls `app.bootstrap.run()`, which runs `init_db()` (creates folders,
schema, seeds admin + settings) and launches the Flet desktop app.

## Developer setup + tests

```bash
pip install -r requirements-dev.txt   # + pytest
pytest -q                             # regression, model/table parity,
                                      # view-build, router-contract
```

Tests run against an isolated temp data dir (`WISE_PMS_HOME`) and never touch
real clinic data.

## Package as WisePMS.exe (Windows)

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name WisePMS main.py
```

Then place the runtime folders (`data/`, `backups/`, `attachments/`,
`exports/`) next to `dist/WisePMS/WisePMS.exe`. Run the `.exe` — same app, no
Python needed.

## Runtime data location

All runtime data lives under `BASE_DIR` (from `app/config/paths.py`):

- default `BASE_DIR` = the application/repo root;
- override with the **`WISE_PMS_HOME`** environment variable to relocate
  everything (used by packaging and by the test suite).

Folders created on first run: `data/` (SQLite DB), `attachments/`, `backups/`,
`exports/` (reserved), `logs/` (reserved).

## Backups

The header **Backup** button (`backup.service.backup_now`) writes
`backups/backup_YYYY_MM_DD.zip` containing `wise_pms.db` + the `attachments/`
tree. A same-day second backup gets a time suffix. Backups are **unencrypted**
(see [`SECURITY.md`](./SECURITY.md)).

## Fonts

The design system uses **Poppins**. If not installed, the OS falls back
automatically; install Poppins (free, Google Fonts) for the exact look.

## Deployment posture

- **Single desktop, offline** is the only fully supported deployment today.
- **Single-machine clinic server** (one process, one machine) is
  *conditionally permitted / temporary* — see the rule below. It is a
  transitional option, not the target architecture.
- Multi-user, networked, cloud, and mobile deployments are **not yet
  supported**. RBAC (F3) is now delivered (Sprint 5), but encryption at rest
  (F7), sync (F8), and a server-grade database adapter must still land first
  — see [`ROADMAP.md`](./ROADMAP.md)
  and [`architecture-decisions/ADR-002-Cloud-Ready-Architecture.md`](./architecture-decisions/ADR-002-Cloud-Ready-Architecture.md)
  §8.0 for the full deployment-tier table.
- CI/CD: none configured yet; a SessionStart hook / CI to run `pytest` on push
  is a recommended early addition.

### SQLite network-deployment rule (mandatory, non-negotiable)

> **SQLite is not a multi-user network database and must not be deployed
> as a shared database file over a network filesystem** (SMB/NFS/a shared
> network drive). Its file-level locking is not reliable in that
> configuration and risks silent data corruption. Single-machine clinic-
> server deployment with SQLite is permitted only where the database
> remains local to that one machine and is not concurrently accessed
> through a network filesystem — it is a transitional deployment option,
> never the target multi-user architecture (ADR-002 §8.0/§8.1).

Any deployment needing more than one concurrently-writing machine/process
requires a server-grade database (PostgreSQL/MySQL/SQL Server/Cloud SQL)
via a future `DatabaseAdapter` — none is built yet (ADR-002 §3).
