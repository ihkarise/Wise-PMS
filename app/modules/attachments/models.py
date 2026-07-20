"""Attachments — models."""

from dataclasses import dataclass
from typing import Optional

from app.core.model import RowModel


@dataclass
class Attachment(RowModel):
    """A file attached to a patient (mirrors the `attachments` table)."""

    id: Optional[int] = None
    patient_id: Optional[int] = None
    visit_id: Optional[int] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    uploaded_at: Optional[str] = None
