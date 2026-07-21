"""Consultation — repository (all SQL for the ``consultations`` table).

The single writer of ``consultations`` (ADR-001 / arch rule 2). Persistence only
— the lifecycle state machine and audit live in the service, not here.
"""

from typing import List, Optional

from app.core.repository import BaseRepository
from app.modules.consultation.models import Consultation

# Editable clinical fields written by ``update`` (status/visit/patient/case are
# managed by dedicated methods, never mass-updated).
_EDITABLE_FIELDS = ("chief_complaint", "history", "examination", "diagnosis",
                    "remarks")


class ConsultationRepository(BaseRepository):
    def create_draft(self, visit_id: int, patient_id: int,
                     case_id: Optional[int]) -> int:
        """Insert a new draft consultation for a visit. Returns its id.

        The UNIQUE index on ``visit_id`` enforces one consultation per visit —
        a second insert for the same visit raises ``sqlite3.IntegrityError``.
        """
        return self._execute(
            "INSERT INTO consultations (visit_id, patient_id, case_id, status) "
            "VALUES (?, ?, ?, 'draft')",
            (visit_id, patient_id, case_id),
        )

    def update(self, consultation_id: int, fields: dict) -> None:
        """Persist editable clinical fields and bump ``updated_at``.

        Only known clinical fields are written; unknown keys are ignored.
        """
        sets = [f"{col} = ?" for col in _EDITABLE_FIELDS if col in fields]
        params = [fields[col] for col in _EDITABLE_FIELDS if col in fields]
        set_clause = ", ".join(sets + ["updated_at = CURRENT_TIMESTAMP"])
        self._execute(
            f"UPDATE consultations SET {set_clause} WHERE id = ?",
            (*params, consultation_id),
        )

    def set_status(self, consultation_id: int, status: str) -> None:
        """Set the lifecycle status and bump ``updated_at`` (dumb persistence —
        the service validates the transition first)."""
        self._execute(
            "UPDATE consultations SET status = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ?",
            (status, consultation_id),
        )

    def get(self, consultation_id: int) -> Optional[dict]:
        row = self._one("SELECT * FROM consultations WHERE id = ?",
                        (consultation_id,))
        model = Consultation.from_row(row)
        return model.to_dict() if model else None

    def get_by_visit(self, visit_id: int) -> Optional[dict]:
        row = self._one("SELECT * FROM consultations WHERE visit_id = ?",
                        (visit_id,))
        model = Consultation.from_row(row)
        return model.to_dict() if model else None

    def open_draft_for_case(self, case_id: int) -> Optional[dict]:
        """The latest still-editable (draft|in_progress) consultation for a case,
        or None. Lets the workspace reuse an open draft instead of starting a new
        one every time it opens."""
        row = self._one(
            "SELECT * FROM consultations "
            "WHERE case_id = ? AND status IN ('draft', 'in_progress') "
            "ORDER BY id DESC LIMIT 1",
            (case_id,),
        )
        model = Consultation.from_row(row)
        return model.to_dict() if model else None

    def for_patient(self, patient_id: int) -> List[dict]:
        """Completed consultations for a patient, newest-first (read model for
        timeline/reporting — drafts excluded)."""
        return self._all(
            "SELECT * FROM consultations "
            "WHERE patient_id = ? AND status = 'completed' "
            "ORDER BY id DESC",
            (patient_id,),
        )
