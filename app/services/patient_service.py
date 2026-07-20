"""Compatibility shim → app.modules.patients.service."""

from app.modules.patients.service import (  # noqa: F401
    PATIENT_FIELDS,
    create_patient,
    deactivate_patient,
    get_patient,
    patient_stats,
    recent_patients,
    search_patients,
    update_patient,
)

__all__ = [
    "PATIENT_FIELDS", "create_patient", "update_patient", "deactivate_patient",
    "get_patient", "search_patients", "recent_patients", "patient_stats",
]
