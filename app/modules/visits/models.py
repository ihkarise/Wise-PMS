"""Visits — models."""

from dataclasses import dataclass
from typing import Optional

from app.core.model import RowModel


@dataclass
class Visit(RowModel):
    """A single consultation/visit (mirrors the `visits` table)."""

    id: Optional[int] = None
    patient_id: Optional[int] = None
    case_id: Optional[int] = None
    doctor_id: Optional[int] = None
    visit_type: Optional[str] = None
    visit_date: Optional[str] = None
    visit_notes: Optional[str] = None
    investigation_notes: Optional[str] = None
    prescription_notes: Optional[str] = None
    followup_date: Optional[str] = None
    outcome: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class PrescriptionItem(RowModel):
    """A structured medicine line extracted from a prescription
    (mirrors the `prescription_items` table)."""

    id: Optional[int] = None
    visit_id: Optional[int] = None
    medicine_name: Optional[str] = None
    potency: Optional[str] = None
    dosage: Optional[str] = None
    instructions: Optional[str] = None
