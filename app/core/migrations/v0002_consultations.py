"""Migration 0002 — consultations aggregate (Sprint 2 / ADR-001 Option C).

Adds the ``consultations`` table: the **clinical document** of a consultation,
1:1 with a ``visits`` row (the encounter event). Per ADR-001 the ``visits`` table
is left untouched — consultation clinical data lives here, not as extra columns
on ``visits``.

The ``up`` is additive and idempotent (``CREATE TABLE IF NOT EXISTS`` +
``CREATE ... INDEX IF NOT EXISTS``), so applying it to any database is safe. The
1:1 invariant is enforced by the UNIQUE index ``idx_consultation_visit`` on
``visit_id``. The ``down`` fully reverses the migration (new table, no data
migration), so ``rollback_to(1)`` restores the exact Sprint 1 schema.
"""

from app.core.migrations.runner import Migration

_UP = """
CREATE TABLE IF NOT EXISTS consultations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    case_id INTEGER,
    chief_complaint TEXT,
    history TEXT,
    examination TEXT,
    diagnosis TEXT,
    remarks TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(visit_id) REFERENCES visits(id),
    FOREIGN KEY(patient_id) REFERENCES patients(id),
    FOREIGN KEY(case_id) REFERENCES patient_cases(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_consultation_visit
    ON consultations(visit_id);
CREATE INDEX IF NOT EXISTS idx_consultation_patient
    ON consultations(patient_id);
"""

_DOWN = """
DROP INDEX IF EXISTS idx_consultation_patient;
DROP INDEX IF EXISTS idx_consultation_visit;
DROP TABLE IF EXISTS consultations;
"""

MIGRATION = Migration(version=2, name="consultations", up=_UP, down=_DOWN)
