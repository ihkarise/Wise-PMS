"""Timeline — repository (read-only SQL across visits/cases/attachments)."""

from typing import List

from app.core.repository import BaseRepository


class TimelineRepository(BaseRepository):
    def visits(self, patient_id: int) -> List[dict]:
        return self._all(
            "SELECT v.id, v.visit_date AS ts, v.visit_notes, v.outcome, "
            "v.followup_date, c.case_title "
            "FROM visits v LEFT JOIN patient_cases c ON c.id = v.case_id "
            "WHERE v.patient_id = ?", (patient_id,),
        )

    def cases(self, patient_id: int) -> List[dict]:
        return self._all(
            "SELECT id, created_at AS ts, case_title, status "
            "FROM patient_cases WHERE patient_id = ?", (patient_id,),
        )

    def attachments(self, patient_id: int) -> List[dict]:
        return self._all(
            "SELECT id, uploaded_at AS ts, file_name, file_type "
            "FROM attachments WHERE patient_id = ?", (patient_id,),
        )
