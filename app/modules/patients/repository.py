"""Patients — repository (all SQL for `patients`)."""

from typing import List, Optional

from app.core.repository import BaseRepository
from app.modules.patients.models import Patient

# Columns a caller may write (reg_no is generated, never supplied).
PATIENT_FIELDS = [
    "name", "gender", "age", "dob", "phone", "whatsapp", "email",
    "address", "place", "occupation", "blood_group", "photo_path",
    "doctor", "consultation_type", "notes",
]


class PatientRepository(BaseRepository):
    def _next_reg_no(self, conn) -> str:
        """Auto-generated registration number: P000001, P000002, ..."""
        row = conn.execute("SELECT MAX(id) AS m FROM patients").fetchone()
        next_id = (row["m"] or 0) + 1
        while True:
            reg_no = f"P{next_id:06d}"
            exists = conn.execute(
                "SELECT 1 FROM patients WHERE reg_no = ?", (reg_no,)
            ).fetchone()
            if not exists:
                return reg_no
            next_id += 1

    def create(self, data: dict) -> int:
        """Insert a patient (generating reg_no in the same transaction)."""
        with self.transaction() as conn:
            reg_no = self._next_reg_no(conn)
            values = [data.get(f) for f in PATIENT_FIELDS]
            cur = conn.execute(
                f"INSERT INTO patients (reg_no, {', '.join(PATIENT_FIELDS)}) "
                f"VALUES (?, {', '.join('?' * len(PATIENT_FIELDS))})",
                [reg_no] + values,
            )
            return cur.lastrowid

    def update(self, patient_id: int, data: dict) -> None:
        sets = ", ".join(f"{f} = ?" for f in PATIENT_FIELDS)
        self._execute(
            f"UPDATE patients SET {sets} WHERE id = ?",
            [data.get(f) for f in PATIENT_FIELDS] + [patient_id],
        )

    def deactivate(self, patient_id: int) -> None:
        self._execute(
            "UPDATE patients SET is_active = 0 WHERE id = ?", (patient_id,)
        )

    def get(self, patient_id: int) -> Optional[dict]:
        row = self._one("SELECT * FROM patients WHERE id = ?", (patient_id,))
        model = Patient.from_row(row)
        return model.to_dict() if model else None

    def search(self, query: str, limit: int = 50) -> List[dict]:
        query = (query or "").strip()
        if not query:
            rows = self._all(
                "SELECT * FROM patients WHERE is_active = 1 "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        else:
            like = f"%{query}%"
            rows = self._all(
                "SELECT * FROM patients WHERE is_active = 1 AND ("
                "  name LIKE ? OR phone LIKE ? OR reg_no LIKE ? OR place LIKE ?"
                ") ORDER BY name COLLATE NOCASE LIMIT ?",
                (like, like, like, like, limit),
            )
        return [Patient.from_row(r).to_dict() for r in rows]

    def recent(self, limit: int = 10) -> List[dict]:
        rows = self._all(
            "SELECT * FROM patients WHERE is_active = 1 "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [Patient.from_row(r).to_dict() for r in rows]

    def stats(self) -> dict:
        total = self._scalar(
            "SELECT COUNT(*) FROM patients WHERE is_active = 1"
        )
        today = self._scalar(
            "SELECT COUNT(*) FROM patients "
            "WHERE is_active = 1 AND DATE(created_at) = DATE('now', 'localtime')"
        )
        return {"total": total, "today": today}
