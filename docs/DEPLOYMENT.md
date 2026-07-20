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

- **Single desktop, offline** is the only supported deployment today.
- Multi-user, cloud, and mobile deployments are **not supported** until RBAC
  (F3), encryption at rest (F7), and sync (F8) land — see [`ROADMAP.md`](./ROADMAP.md).
- CI/CD: none configured yet; a SessionStart hook / CI to run `pytest` on push
  is a recommended early addition.
