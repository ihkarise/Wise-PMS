"""Compatibility shim → app.modules.cases.service."""

from app.modules.cases.service import (  # noqa: F401
    cases_for_patient,
    create_case,
    get_case,
    update_case,
)

__all__ = ["create_case", "update_case", "get_case", "cases_for_patient"]
