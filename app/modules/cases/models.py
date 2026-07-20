"""Case Records — models."""

from dataclasses import dataclass
from typing import Optional

from app.core.model import RowModel


@dataclass
class Case(RowModel):
    """A patient case / episode of care (mirrors the `patient_cases` table)."""

    id: Optional[int] = None
    patient_id: Optional[int] = None
    case_title: Optional[str] = None
    diagnosis: Optional[str] = None
    case_notes: Optional[str] = None
    status: Optional[str] = None
    doctor_id: Optional[int] = None
    created_at: Optional[str] = None
