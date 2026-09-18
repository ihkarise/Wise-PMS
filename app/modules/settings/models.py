"""Settings — models."""

from dataclasses import dataclass
from typing import Optional

from app.core.model import RowModel


@dataclass
class Settings(RowModel):
    """Clinic settings (mirrors the `settings` table).

    Note: this model mirrors every column of the table, including
    `backup_path`, for model/table parity (tests/test_models.py). Only
    `SETTINGS_FIELDS` (in `settings/repository.py`) may be written through
    this module's public API — `backup_path` and any future non-profile
    column stay read-only here (ADR-002 §6.6).
    """

    id: Optional[int] = None
    clinic_name: Optional[str] = None
    doctor_name: Optional[str] = None
    clinic_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo_path: Optional[str] = None
    backup_path: Optional[str] = None
    created_at: Optional[str] = None
