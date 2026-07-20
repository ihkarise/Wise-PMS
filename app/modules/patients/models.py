"""Patients — models."""

from dataclasses import dataclass
from typing import Optional

from app.core.model import RowModel


@dataclass
class Patient(RowModel):
    """A patient record (mirrors the `patients` table)."""

    id: Optional[int] = None
    reg_no: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    dob: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    place: Optional[str] = None
    occupation: Optional[str] = None
    blood_group: Optional[str] = None
    photo_path: Optional[str] = None
    doctor: Optional[str] = None
    consultation_type: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[int] = None
    created_at: Optional[str] = None
