"""Consultation Workspace — service (read-only composition).

The Workspace is a coordinating surface, not a new domain. This service does
nothing but *compose* read-only context from modules that already own their
data (patients, cases). It writes no SQL, mutates nothing, and holds no business
logic — per the Consultation Workspace spec (§2 "Composition, not coupling") and
the architecture rules. As feeder modules ship, their read-only context is added
here (timeline peek, OCR values, protocol picks) so the view stays declarative.
"""

from app.modules.cases.service import get_case
from app.modules.patients.service import get_patient


def workspace_context(patient_id, case_id=None):
    """Return the read-only context the Workspace renders.

    Delegates to each module's own service — this function owns no SQL. Returns
    ``{"patient": <dict|None>, "case": <dict|None>}``. A missing patient (or
    case) yields ``None`` so the view can render a friendly not-found state
    instead of crashing.
    """
    return {
        "patient": get_patient(patient_id),
        "case": get_case(case_id) if case_id else None,
    }
