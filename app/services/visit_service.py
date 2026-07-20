"""Compatibility shim → app.modules.visits.service."""

from app.modules.visits.service import (  # noqa: F401
    create_visit,
    extract_prescription_items,
    get_visit,
    prescription_items_for_visit,
    update_visit,
    visit_stats,
    visits_for_patient,
)

__all__ = [
    "extract_prescription_items", "create_visit", "update_visit", "get_visit",
    "visits_for_patient", "prescription_items_for_visit", "visit_stats",
]
