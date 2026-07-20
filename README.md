# Wise PMS — Sprint 2
**Smart Healthcare Management** · Local-first · Offline · SQLite · ₹0/month

## What's new in Sprint 2
- **Case Records** — multiple cases per patient (e.g. Migraine, Allergic Rhinitis), narrative-first case notes, status (Open/Closed/Resolved/On Hold), Save + Start Visit
- **Visit Entry** — large narrative editors for Visit Notes, Investigation Notes, and Prescription Notes; follow-up date and outcome; link a visit to a case
- **Prescription intelligence** — medicines and potencies are auto-detected from your free-text prescription ("Bell 200", "Bry 30 TDS") for future analytics; your narrative is always the source of truth, and "Continue medicine / Review / Placebo" lines are left alone
- **Patient Timeline** — visits, cases and attachments merged newest-first; click any event to open it
- **Attachments** — upload PDFs, images, lab reports per patient (stored in attachments/patient_P000001/), open and delete with confirmation
- **Profile tabs** — Profile / Cases / Timeline / Attachments, with quick actions: New Visit, New Case, Upload File
- **Dashboard** — now shows Visits Today and Follow-ups Due
- **Backup** — now includes the attachments folder
- Existing Sprint 1 databases upgrade automatically on first launch — no data loss

## From Sprint 1
- Login (default: **admin / admin123** — change it after first use)
- New Case Registration (auto Reg No: P000001, P000002, …)
- Real-time Patient Search (Name / Phone / Reg No / Place)
- Patient Profile (read-only, with Edit)
- Dashboard (Total Patients, Added Today, Recent Patients)
- One-click Backup (cloud icon in the header → backups/backup_YYYY_MM_DD.zip)
- Audit log (Login, Logout, Patient Created/Updated)
- Soft delete only — patients are never physically removed

## Run on your laptop (Windows)
1. Install Python 3.10+ from python.org (tick "Add Python to PATH")
2. Open Command Prompt inside the WisePMS folder, then:
   ```
   pip install -r requirements.txt
   python main.py
   ```
3. Login with **admin / admin123**

All data is saved permanently in `data/wise_pms.db`. No internet needed.

## Build WisePMS.exe (optional)
```
pip install pyinstaller
pyinstaller --noconfirm --windowed --name WisePMS main.py
```
Then copy the `data/`, `backups/`, `attachments/`, `exports/` folders next to
`dist/WisePMS/WisePMS.exe`. Run the .exe — same app, no Python needed.

## Fonts
The design system uses Poppins. If Poppins isn't installed on the laptop,
Windows falls back to a default font automatically. To get the exact look,
install Poppins (free on Google Fonts) once.

## Folder map (domain-driven, Sprint 2 architecture refactor)
```
Wise-PMS/
├── main.py                     ← thin entrypoint → app.bootstrap.run()
├── requirements.txt            ← runtime deps (flet, bcrypt)
├── requirements-dev.txt        ← + pytest for the test suite
├── docs/                       ← architecture audit (see below)
├── tests/                      ← behavioral + structural test suite
└── app/
    ├── bootstrap.py            ← composition root: init DB, wire router, launch
    ├── config/                 ← paths.py (WISE_PMS_HOME) · constants.py
    ├── core/                   ← database.py · model.py · repository.py · router.py
    ├── shared/                 ← theme.py (design system) · shell.py · widgets.py
    ├── utils/                  ← prescription.py (pure helpers)
    └── modules/                ← one folder per BUSINESS module
        ├── authentication/     ← models · repository · service · controller · view
        ├── patients/           ← …incl. views/ (search, profile, edit)
        ├── registration/  cases/  visits/  attachments/
        ├── timeline/  dashboard/  audit/  backup/
        └── (Appointments, Billing, Inventory/WHIMS, … added the same way)
```
Each module is a self-contained vertical slice
(`models → repository → service → controller → view`). Runtime data lives under
`data/`, `backups/`, `attachments/`, `exports/`, `logs/` (created on first run;
relocate with the `WISE_PMS_HOME` environment variable).

## Architecture docs
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — full audit: startup, routing,
  UI hierarchy, DB schema (ERD), services, data flow, patterns, tech debt,
  scalability.
- [`docs/DEPENDENCY_MAP.md`](docs/DEPENDENCY_MAP.md) — module dependency graph.
- [`docs/TARGET_ARCHITECTURE.md`](docs/TARGET_ARCHITECTURE.md) — target layers,
  module registry, future-product mapping, and how to add a new module.

## Developer setup & tests
```
pip install -r requirements-dev.txt
pytest -q                 # regression (behavior), model/table parity,
                          # view-build, and router-contract tests
```
The test suite runs against an isolated temporary data directory and never
touches real clinic data.

Sprint 3 will add the Waiting Queue, Booking, and Online Consultation modules
by dropping new folders under `app/modules/` — no changes to existing modules.
