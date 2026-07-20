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

## Folder map
```
WisePMS/
├── main.py              ← start here
├── requirements.txt
├── app/
│   ├── ui/              ← login, dashboard, registration, search, profile
│   ├── services/        ← auth, patient, backup, audit
│   └── database/db.py   ← creates wise_pms.db automatically
├── data/wise_pms.db     ← all patient data (created on first run)
├── backups/             ← zip backups
├── attachments/         ← ready for Sprint 2
└── exports/
```

Sprint 3 will add the Waiting Queue, Booking, and Online Consultation modules
on top of this foundation.
