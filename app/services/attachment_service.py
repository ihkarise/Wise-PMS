"""Compatibility shim → app.modules.attachments.service."""

from app.config.constants import FILE_TYPES  # noqa: F401  (re-exported)
from app.modules.attachments.service import (  # noqa: F401
    absolute_path,
    add_attachment,
    attachments_for_patient,
    delete_attachment,
)

__all__ = [
    "FILE_TYPES", "add_attachment", "attachments_for_patient",
    "delete_attachment", "absolute_path",
]
