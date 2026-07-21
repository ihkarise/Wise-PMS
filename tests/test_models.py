"""Model/table parity test.

Each row-mapped model must define exactly the columns of its table. If they
drift (a column added to the schema but not the model, or vice versa), a read
path could silently drop or invent a field. This test fails loudly on drift.
"""

import os
import tempfile

os.environ.setdefault("WISE_PMS_HOME", tempfile.mkdtemp(prefix="wisepms_models_"))


def _columns(table):
    from app.core.database import get_connection, init_db
    init_db()
    conn = get_connection()
    try:
        return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


def test_model_columns_match_tables():
    from app.modules.attachments.models import Attachment
    from app.modules.authentication.models import User
    from app.modules.cases.models import Case
    from app.modules.consultation.models import Consultation
    from app.modules.patients.models import Patient
    from app.modules.visits.models import PrescriptionItem, Visit

    pairs = [
        (User, "users"),
        (Patient, "patients"),
        (Case, "patient_cases"),
        (Visit, "visits"),
        (PrescriptionItem, "prescription_items"),
        (Attachment, "attachments"),
        (Consultation, "consultations"),
    ]
    for model, table in pairs:
        assert set(model.field_names()) == _columns(table), (
            f"{model.__name__} fields != {table} columns"
        )


if __name__ == "__main__":
    test_model_columns_match_tables()
    print("[PASS] all models match their tables")
