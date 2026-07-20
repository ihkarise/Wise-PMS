"""Backup — service (database + attachments)."""

import os
import zipfile
from datetime import datetime

from app.config import paths


def backup_now() -> str:
    """Create backups/backup_YYYY_MM_DD.zip containing the database and
    attachments. Returns the backup file path."""
    os.makedirs(paths.BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y_%m_%d")
    base = os.path.join(paths.BACKUPS_DIR, f"backup_{stamp}.zip")

    # If a backup already exists today, add a time suffix
    path = base
    if os.path.exists(path):
        stamp_t = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        path = os.path.join(paths.BACKUPS_DIR, f"backup_{stamp_t}.zip")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(paths.DB_PATH, arcname="wise_pms.db")
        for root, _dirs, files in os.walk(paths.ATTACHMENTS_DIR):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, os.path.dirname(paths.ATTACHMENTS_DIR))
                zf.write(full, arcname=rel)
    return path
