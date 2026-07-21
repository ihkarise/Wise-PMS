"""Consultation — service (clinical-document domain + read-only composition).

Two responsibilities, no SQL of its own (delegates to
``ConsultationRepository`` and other modules' services):

1. **Composition** — ``workspace_context`` gathers read-only context (patient,
   case, active consultation) for the Workspace view.
2. **Lifecycle** — the consultation state machine (ADR-001 §4). This service is
   the *single authority* that validates transitions and stamps status; the
   repository does dumb persistence and the view/controller never mutate status
   directly. Every transition writes an audit row.

Lifecycle states: draft -> in_progress -> completed -> amended -> locked.
Sprint 2 implements draft/in_progress/completed; amended/locked are present in
the guarded transition table (enforced fully in a later, approved phase).
"""

from typing import Optional

from app.modules.audit.service import log_action
from app.modules.cases.service import get_case
from app.modules.consultation.repository import ConsultationRepository
from app.modules.patients.service import get_patient
from app.modules.visits.service import create_visit

_repo = ConsultationRepository()

# Editable states — clinical fields may be written only in these.
_EDITABLE = ("draft", "in_progress")

# Allowed status transitions. Any transition not listed is rejected. ``locked``
# is terminal (medico-legal seal); ``amended``/``locked`` land fully later.
_ALLOWED = {
    "draft": {"in_progress", "completed"},
    "in_progress": {"completed"},
    "completed": {"amended", "locked"},
    "amended": {"completed", "locked"},
    "locked": set(),
}


class ConsultationLifecycleError(RuntimeError):
    """Raised on an illegal lifecycle transition or an edit to a sealed record."""


def _require(consultation_id: int) -> dict:
    c = _repo.get(consultation_id)
    if c is None:
        raise ConsultationLifecycleError(
            f"Consultation {consultation_id} not found.")
    return c


def _transition(consultation_id: int, to_status: str, user_id: int,
                action: str) -> dict:
    c = _require(consultation_id)
    current = c["status"]
    if to_status not in _ALLOWED.get(current, set()):
        raise ConsultationLifecycleError(
            f"Illegal transition {current} -> {to_status}.")
    _repo.set_status(consultation_id, to_status)
    log_action(user_id, action, "consultation", consultation_id, "")
    return _repo.get(consultation_id)


# -- lifecycle --------------------------------------------------------------
def open_or_create_draft(patient_id: int, case_id: int, user_id: int) -> dict:
    """Return the open draft for the case, creating a new visit + draft
    consultation if none exists. Reused on reopen (one open document per case)."""
    existing = _repo.open_draft_for_case(case_id)
    if existing is not None:
        return existing
    # A consultation is 1:1 with a visit event — provision the encounter first.
    visit_id = create_visit(patient_id, {"case_id": case_id,
                                          "visit_type": "Walk-In"}, user_id)
    consultation_id = _repo.create_draft(visit_id, patient_id, case_id)
    log_action(user_id, "Consultation Started", "consultation",
               consultation_id, "")
    return _repo.get(consultation_id)


def save_consultation(consultation_id: int, fields: dict, user_id: int) -> dict:
    """Persist clinical fields. First write flips draft -> in_progress. Editing a
    completed/locked record is rejected."""
    c = _require(consultation_id)
    if c["status"] not in _EDITABLE:
        raise ConsultationLifecycleError(
            f"Cannot edit a {c['status']} consultation.")
    if c["status"] == "draft":
        _repo.set_status(consultation_id, "in_progress")
    _repo.update(consultation_id, fields)
    log_action(user_id, "Consultation Updated", "consultation",
               consultation_id, "")
    return _repo.get(consultation_id)


def complete_consultation(consultation_id: int, user_id: int) -> dict:
    """Finalize the document (-> completed). Idempotent if already completed."""
    c = _require(consultation_id)
    if c["status"] == "completed":
        return c
    return _transition(consultation_id, "completed", user_id,
                       "Consultation Completed")


def amend_consultation(consultation_id: int, user_id: int) -> dict:
    """Reopen a completed document for amendment (audited). Later-phase surface;
    the transition is guarded here now."""
    return _transition(consultation_id, "amended", user_id,
                       "Consultation Amended")


def lock_consultation(consultation_id: int, user_id: int) -> dict:
    """Seal a document for medico-legal retention (terminal, immutable).
    Later-phase surface; the transition is guarded here now."""
    return _transition(consultation_id, "locked", user_id, "Consultation Locked")


def get_consultation(consultation_id: int) -> Optional[dict]:
    return _repo.get(consultation_id)


def consultation_for_visit(visit_id: int) -> Optional[dict]:
    return _repo.get_by_visit(visit_id)


# -- composition (read-only) ------------------------------------------------
def workspace_context(patient_id, case_id=None, visit_id=None):
    """Read-only context the Workspace renders: patient, case, and the active
    consultation (by visit, if any). Owns no SQL beyond the repository read."""
    return {
        "patient": get_patient(patient_id),
        "case": get_case(case_id) if case_id else None,
        "consultation": (_repo.get_by_visit(visit_id) if visit_id else None),
    }
