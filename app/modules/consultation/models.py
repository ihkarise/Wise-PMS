"""Consultation — models (ADR-001 Option C: the clinical document)."""

from dataclasses import dataclass
from typing import Optional

from app.core.model import RowModel


@dataclass
class Consultation(RowModel):
    """A consultation clinical document, 1:1 with a visit (mirrors the
    ``consultations`` table). Narrative-first: every clinical field is optional.
    """

    id: Optional[int] = None
    visit_id: Optional[int] = None
    patient_id: Optional[int] = None
    case_id: Optional[int] = None
    chief_complaint: Optional[str] = None
    history: Optional[str] = None
    examination: Optional[str] = None
    diagnosis: Optional[str] = None
    remarks: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
