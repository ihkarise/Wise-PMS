"""Migration 0001 — initial baseline schema.

This is the behaviour-preserving conversion of the original create-if-not-exists
``SCHEMA`` block that previously lived in :mod:`app.core.database`. Because every
statement is ``CREATE ... IF NOT EXISTS``, applying it to a **legacy** database
(created before the migration runner existed) is a safe no-op that simply stamps
the database at version 1 — no data is touched. On a fresh database it creates
the full baseline.

The ``down`` script drops the baseline objects **child-first** so foreign keys
stay satisfied while rolling back.
"""

from app.core.migrations.runner import Migration

_UP = """
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

# Drop child tables before their parents so foreign keys stay satisfied.
_DOWN = """
DROP INDEX IF EXISTS idx_patient_place;
DROP INDEX IF EXISTS idx_patient_regno;
DROP INDEX IF EXISTS idx_patient_phone;
DROP INDEX IF EXISTS idx_patient_name;
DROP INDEX IF EXISTS idx_attach_patient;
DROP INDEX IF EXISTS idx_visit_case;
DROP INDEX IF EXISTS idx_visit_date;
DROP INDEX IF EXISTS idx_visit_patient;
DROP INDEX IF EXISTS idx_case_patient;

DROP TABLE IF EXISTS attachments;
DROP TABLE IF EXISTS prescription_items;
DROP TABLE IF EXISTS visits;
DROP TABLE IF EXISTS patient_cases;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS settings;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS users;
"""

MIGRATION = Migration(version=1, name="initial", up=_UP, down=_DOWN)
