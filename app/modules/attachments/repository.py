"""Attachments — repository (all SQL for `attachments`)."""

from typing import List, Optional

from app.core.repository import BaseRepository
from app.modules.attachments.models import Attachment


class AttachmentRepository(BaseRepository):
    def insert(self, patient_id: int, visit_id, file_name: str,
               file_path: str, file_type: str) -> int:
        return self._execute(
            "INSERT INTO attachments "
            "(patient_id, visit_id, file_name, file_path, file_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (patient_id, visit_id, file_name, file_path, file_type),
        )

    def for_patient(self, patient_id: int) -> List[dict]:
        rows = self._all(
            "SELECT * FROM attachments WHERE patient_id = ? "
            "ORDER BY uploaded_at DESC",
            (patient_id,),
        )
        return [Attachment.from_row(r).to_dict() for r in rows]

    def get(self, attach_id: int) -> Optional[dict]:
        row = self._one("SELECT * FROM attachments WHERE id = ?", (attach_id,))
        model = Attachment.from_row(row)
        return model.to_dict() if model else None

    def delete(self, attach_id: int) -> None:
        self._execute("DELETE FROM attachments WHERE id = ?", (attach_id,))
