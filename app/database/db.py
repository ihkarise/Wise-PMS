"""
Wise PMS — Database Engine (Sprint 1)
Creates and manages the local SQLite database: wise_pms.db
Offline-first. No internet. No cloud.
"""

import os
import sqlite3

import bcrypt

# ------------------------------------------------------------------
# Paths — everything lives next to the application folder
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "wise_pms.db")

ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
LOGS_DIR = os.path.join(BASE_DIR, "logs")


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _ensure_folders() -> None:
    for folder in (DATA_DIR, ATTACHMENTS_DIR, BACKUPS_DIR, EXPORTS_DIR, LOGS_DIR):
        os.makedirs(folder, exist_ok=True)


# ------------------------------------------------------------------
# Schema — Sprint 1 tables only: users, patients, settings, audit_logs
# ------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reg_no TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    gender TEXT,
    age INTEGER,
    dob DATE,
    phone TEXT,
    whatsapp TEXT,
    email TEXT,
    address TEXT,
    place TEXT,
    occupation TEXT,
    blood_group TEXT,
    photo_path TEXT,
    doctor TEXT,
    consultation_type TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clinic_name TEXT,
    doctor_name TEXT,
    clinic_address TEXT,
    phone TEXT,
    email TEXT,
    logo_path TEXT,
    backup_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action_type TEXT,
    entity_type TEXT,
    entity_id INTEGER,
    action_details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patient_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    case_title TEXT,
    diagnosis TEXT,
    case_notes TEXT,
    status TEXT DEFAULT 'Open',
    doctor_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id)
);

CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    case_id INTEGER,
    doctor_id INTEGER,
    visit_type TEXT,
    visit_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    visit_notes TEXT,
    investigation_notes TEXT,
    prescription_notes TEXT,
    followup_date DATE,
    outcome TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id),
    FOREIGN KEY(case_id) REFERENCES patient_cases(id)
);

CREATE TABLE IF NOT EXISTS prescription_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER NOT NULL,
    medicine_name TEXT,
    potency TEXT,
    dosage TEXT,
    instructions TEXT,
    FOREIGN KEY(visit_id) REFERENCES visits(id)
);

CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    visit_id INTEGER,
    file_name TEXT,
    file_path TEXT,
    file_type TEXT,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id)
);

CREATE INDEX IF NOT EXISTS idx_case_patient  ON patient_cases(patient_id);
CREATE INDEX IF NOT EXISTS idx_visit_patient ON visits(patient_id);
CREATE INDEX IF NOT EXISTS idx_visit_date    ON visits(visit_date);
CREATE INDEX IF NOT EXISTS idx_visit_case    ON visits(case_id);
CREATE INDEX IF NOT EXISTS idx_attach_patient ON attachments(patient_id);

CREATE INDEX IF NOT EXISTS idx_patient_name  ON patients(name);
CREATE INDEX IF NOT EXISTS idx_patient_phone ON patients(phone);
CREATE INDEX IF NOT EXISTS idx_patient_regno ON patients(reg_no);
CREATE INDEX IF NOT EXISTS idx_patient_place ON patients(place);
"""


def init_db() -> None:
    """Create database, tables, indexes and the default admin user."""
    _ensure_folders()
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)

        # Default admin (admin / admin123) — created only once
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE username = ?", ("admin",)
        ).fetchone()
        if row["c"] == 0:
            password_hash = bcrypt.hashpw(
                "admin123".encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            conn.execute(
                "INSERT INTO users (username, password_hash, full_name, role) "
                "VALUES (?, ?, ?, ?)",
                ("admin", password_hash, "Administrator", "Admin"),
            )

        # Default clinic settings row
        row = conn.execute("SELECT COUNT(*) AS c FROM settings").fetchone()
        if row["c"] == 0:
            conn.execute(
                "INSERT INTO settings (clinic_name, doctor_name) VALUES (?, ?)",
                ("Wise Homeopathy Multispeciality Center", ""),
            )

        conn.commit()
    finally:
        conn.close()
