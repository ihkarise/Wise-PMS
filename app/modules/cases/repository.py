"""Case Records — repository (all SQL for `patient_cases`)."""

from typing import List, Optional

from app.core.repository import BaseRepository
from app.modules.cases.models import Case


class CaseRepository(BaseRepository):
    def create(self, patient_id: int, data: dict, doctor_id: int) -> int:
        return self._execute(
            "INSERT INTO patient_cases "
            "(patient_id, case_title, diagnosis, case_notes, status, doctor_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (patient_id, data.get("case_title"), data.get("diagnosis"),
             data.get("case_notes"), data.get("status") or "Open", doctor_id),
        )

    def update(self, case_id: int, data: dict) -> None:
        self._execute(
            "UPDATE patient_cases SET case_title = ?, diagnosis = ?, "
            "case_notes = ?, status = ? WHERE id = ?",
            (data.get("case_title"), data.get("diagnosis"),
             data.get("case_notes"), data.get("status") or "Open", case_id),
        )

    def get(self, case_id: int) -> Optional[dict]:
        row = self._one("SELECT * FROM patient_cases WHERE id = ?", (case_id,))
        model = Case.from_row(row)
        return model.to_dict() if model else None

    def for_patient(self, patient_id: int) -> List[dict]:
        """Cases newest-first, each augmented with its visit_count (read model)."""
        return self._all(
            "SELECT c.*, "
            " (SELECT COUNT(*) FROM visits v WHERE v.case_id = c.id) AS visit_count "
            "FROM patient_cases c WHERE c.patient_id = ? "
            "ORDER BY c.created_at DESC",
            (patient_id,),
        )
