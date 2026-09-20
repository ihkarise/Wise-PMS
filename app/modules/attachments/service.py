"""Attachments — service.

Files are written under ``attachments/patient_<reg_no>/`` through the
`StorageProvider` seam (:mod:`app.core.storage`, ADR-002 §5.1) rather than
calling `os`/`shutil` directly; all DB access goes through the repository.
On-disk layout and stored `file_path` values are unchanged from the
pre-Sprint-4 implementation.
"""

import os
from datetime import datetime
from typing import List, Optional

from app.config.constants import FILE_TYPES
from app.core.storage import get_storage
from app.modules.attachments.repository import AttachmentRepository
from app.modules.audit.service import log_action
from app.modules.roles import permissions as perms
from app.modules.roles.service import require_permission

_repo = AttachmentRepository()


def add_attachment(patient_id: int, reg_no: str, source_path: str,
                   user_id: int, visit_id: Optional[int] = None) -> int:
    require_permission(user_id, perms.ATTACHMENTS_UPLOAD)
    original = os.path.basename(source_path)
    stem, ext = os.path.splitext(original)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{stem}_{stamp}{ext}"
    rel_path = os.path.join("attachments", f"patient_{reg_no}", file_name)

    with open(source_path, "rb") as fh:
        data = fh.read()
    get_storage().save(rel_path, data)

    file_type = FILE_TYPES.get(ext.lower(), "Other")

    attach_id = _repo.insert(patient_id, visit_id, original, rel_path, file_type)
    log_action(user_id, "Attachment Uploaded", "attachment", attach_id, original)
    return attach_id


def attachments_for_patient(patient_id: int) -> List[dict]:
    return _repo.for_patient(patient_id)


def delete_attachment(attach_id: int, user_id: int) -> None:
    require_permission(user_id, perms.ATTACHMENTS_DELETE)
    row = _repo.get(attach_id)
    if row is None:
        return
    _repo.delete(attach_id)

    get_storage().delete(row["file_path"])  # best-effort, per StorageProvider contract
    log_action(user_id, "Attachment Deleted", "attachment", attach_id,
               row["file_name"])


def absolute_path(attachment: dict) -> str:
    """Resolve a stored attachment's URI to a real filesystem path.

    Known local-only dependency (ADR-002 §5.1 / SPRINT4_TECHNICAL_PLAN.md
    §4.2): calls `LocalDiskStorageProvider.local_path()` directly rather
    than through the `StorageProvider` Protocol, since a non-local
    provider has no local filesystem path to return. Redesigning this
    call site (e.g. via a temporary local download) for a non-local
    provider is out of scope for Sprint 4.
    """
    return get_storage().local_path(attachment["file_path"])
