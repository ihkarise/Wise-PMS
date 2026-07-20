"""Visits — repository (all SQL for `visits` and `prescription_items`)."""

from typing import List, Optional

from app.core.repository import BaseRepository
from app.modules.visits.models import PrescriptionItem, Visit


class VisitRepository(BaseRepository):
    @staticmethod
    def _insert_items(conn, visit_id: int, items: List[dict]) -> None:
        for item in items:
            conn.execute(
                "INSERT INTO prescription_items "
                "(visit_id, medicine_name, potency, dosage, instructions) "
                "VALUES (?, ?, ?, ?, ?)",
                (visit_id, item["medicine_name"], item["potency"],
                 item["dosage"], item["instructions"]),
            )

    def create(self, patient_id: int, data: dict, doctor_id: int,
               items: List[dict]) -> int:
        """Insert a visit and its extracted prescription items atomically."""
        with self.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO visits (patient_id, case_id, doctor_id, visit_type, "
                "visit_date, visit_notes, investigation_notes, prescription_notes, "
                "followup_date, outcome) "
                "VALUES (?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?, ?, ?)",
                (patient_id, data.get("case_id"), doctor_id,
                 data.get("visit_type"), data.get("visit_date"),
                 data.get("visit_notes"), data.get("investigation_notes"),
                 data.get("prescription_notes"), data.get("followup_date"),
                 data.get("outcome")),
            )
            visit_id = cur.lastrowid
            self._insert_items(conn, visit_id, items)
            return visit_id

    def update(self, visit_id: int, data: dict, items: List[dict]) -> None:
        """Update a visit and re-derive its prescription items atomically."""
        with self.transaction() as conn:
            conn.execute(
                "UPDATE visits SET case_id = ?, visit_type = ?, visit_notes = ?, "
                "investigation_notes = ?, prescription_notes = ?, "
                "followup_date = ?, outcome = ? WHERE id = ?",
                (data.get("case_id"), data.get("visit_type"),
                 data.get("visit_notes"), data.get("investigation_notes"),
                 data.get("prescription_notes"), data.get("followup_date"),
                 data.get("outcome"), visit_id),
            )
            conn.execute("DELETE FROM prescription_items WHERE visit_id = ?",
                         (visit_id,))
            self._insert_items(conn, visit_id, items)

    def get(self, visit_id: int) -> Optional[dict]:
        row = self._one("SELECT * FROM visits WHERE id = ?", (visit_id,))
        model = Visit.from_row(row)
        return model.to_dict() if model else None

    def for_patient(self, patient_id: int) -> List[dict]:
        """Visits newest-first, each augmented with its case_title (read model)."""
        return self._all(
            "SELECT v.*, c.case_title FROM visits v "
            "LEFT JOIN patient_cases c ON c.id = v.case_id "
            "WHERE v.patient_id = ? ORDER BY v.visit_date DESC",
            (patient_id,),
        )

    def items_for_visit(self, visit_id: int) -> List[dict]:
        rows = self._all(
            "SELECT * FROM prescription_items WHERE visit_id = ?", (visit_id,)
        )
        return [PrescriptionItem.from_row(r).to_dict() for r in rows]

    def stats(self) -> dict:
        today = self._scalar(
            "SELECT COUNT(*) FROM visits "
            "WHERE DATE(visit_date) = DATE('now', 'localtime')"
        )
        followups_due = self._scalar(
            "SELECT COUNT(*) FROM visits "
            "WHERE followup_date IS NOT NULL "
            "AND DATE(followup_date) <= DATE('now', 'localtime')"
        )
        return {"visits_today": today, "followups_due": followups_due}
