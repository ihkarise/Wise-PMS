"""Wise PMS — Attachment Service (Sprint 2).
Files are copied into attachments/patient_{reg_no}/ and recorded in SQLite.
"""

import os
import shutil
from datetime import datetime
from typing import List, Optional

from app.database.db import ATTACHMENTS_DIR, get_connection
from app.services.audit_service import log_action

FILE_TYPES = {
    ".pdf": "PDF", ".jpg": "Image", ".jpeg": "Image", ".png": "Image",
    ".gif": "Image", ".webp": "Image", ".bmp": "Image",
    ".doc": "Document", ".docx": "Document", ".txt": "Document",
}


def add_attachment(patient_id: int, reg_no: str, source_path: str,
                   user_id: int, visit_id: Optional[int] = None) -> int:
    folder = os.path.join(ATTACHMENTS_DIR, f"patient_{reg_no}")
    os.makedirs(folder, exist_ok=True)

    original = os.path.basename(source_path)
    stem, ext = os.path.splitext(original)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{stem}_{stamp}{ext}"
    dest = os.path.join(folder, file_name)
    shutil.copy2(source_path, dest)

    rel_path = os.path.join("attachments", f"patient_{reg_no}", file_name)
    file_type = FILE_TYPES.get(ext.lower(), "Other")

    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO attachments "
            "(patient_id, visit_id, file_name, file_path, file_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (patient_id, visit_id, original, rel_path, file_type),
        )
        conn.commit()
        attach_id = cur.lastrowid
    finally:
        conn.close()
    log_action(user_id, "Attachment Uploaded", "attachment", attach_id, original)
    return attach_id


def attachments_for_patient(patient_id: int) -> List[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM attachments WHERE patient_id = ? "
            "ORDER BY uploaded_at DESC",
            (patient_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_attachment(attach_id: int, user_id: int) -> None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM attachments WHERE id = ?", (attach_id,)
        ).fetchone()
        if row is None:
            return
        conn.execute("DELETE FROM attachments WHERE id = ?", (attach_id,))
        conn.commit()
    finally:
        conn.close()

    # Remove the physical file (best effort)
    try:
        from app.database.db import BASE_DIR
        full = os.path.join(BASE_DIR, row["file_path"])
        if os.path.exists(full):
            os.remove(full)
    except Exception:
        pass
    log_action(user_id, "Attachment Deleted", "attachment", attach_id,
               row["file_name"])


def absolute_path(attachment: dict) -> str:
    from app.database.db import BASE_DIR
    return os.path.join(BASE_DIR, attachment["file_path"])
