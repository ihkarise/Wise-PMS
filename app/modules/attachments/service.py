"""Attachments — service.

Files are copied into ``attachments/patient_<reg_no>/`` and recorded in SQLite.
The filesystem work lives here; all DB access goes through the repository.
"""

import os
import shutil
from datetime import datetime
from typing import List, Optional

from app.config import paths
from app.config.constants import FILE_TYPES
from app.modules.attachments.repository import AttachmentRepository
from app.modules.audit.service import log_action

_repo = AttachmentRepository()


def add_attachment(patient_id: int, reg_no: str, source_path: str,
                   user_id: int, visit_id: Optional[int] = None) -> int:
    folder = os.path.join(paths.ATTACHMENTS_DIR, f"patient_{reg_no}")
    os.makedirs(folder, exist_ok=True)

    original = os.path.basename(source_path)
    stem, ext = os.path.splitext(original)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{stem}_{stamp}{ext}"
    dest = os.path.join(folder, file_name)
    shutil.copy2(source_path, dest)

    rel_path = os.path.join("attachments", f"patient_{reg_no}", file_name)
    file_type = FILE_TYPES.get(ext.lower(), "Other")

    attach_id = _repo.insert(patient_id, visit_id, original, rel_path, file_type)
    log_action(user_id, "Attachment Uploaded", "attachment", attach_id, original)
    return attach_id


def attachments_for_patient(patient_id: int) -> List[dict]:
    return _repo.for_patient(patient_id)


def delete_attachment(attach_id: int, user_id: int) -> None:
    row = _repo.get(attach_id)
    if row is None:
        return
    _repo.delete(attach_id)

    # Remove the physical file (best effort)
    try:
        full = os.path.join(paths.BASE_DIR, row["file_path"])
        if os.path.exists(full):
            os.remove(full)
    except Exception:
        pass
    log_action(user_id, "Attachment Deleted", "attachment", attach_id,
               row["file_name"])


def absolute_path(attachment: dict) -> str:
    return os.path.join(paths.BASE_DIR, attachment["file_path"])
