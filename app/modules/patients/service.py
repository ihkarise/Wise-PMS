"""Patients — service (business rules + audit over the repository)."""

from typing import List, Optional

from app.modules.audit.service import log_action
from app.modules.patients.repository import PATIENT_FIELDS, PatientRepository

_repo = PatientRepository()

# PATIENT_FIELDS is re-exported here as the module's public writable-field list.
__all__ = [
    "PATIENT_FIELDS", "create_patient", "update_patient", "deactivate_patient",
    "get_patient", "search_patients", "recent_patients", "patient_stats",
]


def create_patient(data: dict, user_id: int) -> dict:
    """Create a patient. Returns the saved patient (with reg_no)."""
    patient_id = _repo.create(data)
    saved = _repo.get(patient_id)
    log_action(user_id, "Patient Created", "patient", patient_id,
               f"{saved['reg_no']} — {data.get('name', '')}")
    return saved


def update_patient(patient_id: int, data: dict, user_id: int) -> None:
    _repo.update(patient_id, data)
    log_action(user_id, "Patient Updated", "patient", patient_id,
               f"Updated {data.get('name', '')}")


def deactivate_patient(patient_id: int, user_id: int) -> None:
    """Soft delete — patients are never physically removed."""
    _repo.deactivate(patient_id)
    log_action(user_id, "Patient Deactivated", "patient", patient_id, "")


def get_patient(patient_id: int) -> Optional[dict]:
    return _repo.get(patient_id)


def search_patients(query: str, limit: int = 50) -> List[dict]:
    """Real-time search on Name, Phone, Reg No, Place. Active patients only."""
    return _repo.search(query, limit)


def recent_patients(limit: int = 10) -> List[dict]:
    return _repo.recent(limit)


def patient_stats() -> dict:
    return _repo.stats()
