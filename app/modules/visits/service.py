"""Visits — service.

Narrative first: visit_notes, investigation_notes and prescription_notes are the
heart of the system and are stored exactly as written. Structured prescription
items are an optional extraction layer (see app.utils.prescription) for
analytics.
"""

from typing import List, Optional

from app.modules.audit.service import log_action
from app.modules.visits.repository import VisitRepository
from app.utils.prescription import extract_prescription_items

_repo = VisitRepository()

# extract_prescription_items is re-exported for backwards compatibility
# (was app.services.visit_service.extract_prescription_items, used by the UI).
__all__ = [
    "extract_prescription_items", "create_visit", "update_visit", "get_visit",
    "visits_for_patient", "prescription_items_for_visit", "visit_stats",
]


def create_visit(patient_id: int, data: dict, user_id: int) -> int:
    items = extract_prescription_items(data.get("prescription_notes"))
    visit_id = _repo.create(patient_id, data, user_id, items)
    log_action(user_id, "Visit Created", "visit", visit_id, "")
    return visit_id


def update_visit(visit_id: int, data: dict, user_id: int) -> None:
    items = extract_prescription_items(data.get("prescription_notes"))
    _repo.update(visit_id, data, items)
    log_action(user_id, "Visit Updated", "visit", visit_id, "")


def get_visit(visit_id: int) -> Optional[dict]:
    return _repo.get(visit_id)


def visits_for_patient(patient_id: int) -> List[dict]:
    return _repo.for_patient(patient_id)


def prescription_items_for_visit(visit_id: int) -> List[dict]:
    return _repo.items_for_visit(visit_id)


def visit_stats() -> dict:
    return _repo.stats()
