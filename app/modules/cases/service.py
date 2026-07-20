"""Case Records — service (business rules + audit over the repository)."""

from typing import List, Optional

from app.modules.audit.service import log_action
from app.modules.cases.repository import CaseRepository

_repo = CaseRepository()


def create_case(patient_id: int, data: dict, user_id: int) -> int:
    case_id = _repo.create(patient_id, data, user_id)
    log_action(user_id, "Case Created", "case", case_id,
               data.get("case_title") or "")
    return case_id


def update_case(case_id: int, data: dict, user_id: int) -> None:
    _repo.update(case_id, data)
    log_action(user_id, "Case Updated", "case", case_id,
               data.get("case_title") or "")


def get_case(case_id: int) -> Optional[dict]:
    return _repo.get(case_id)


def cases_for_patient(patient_id: int) -> List[dict]:
    return _repo.for_patient(patient_id)
