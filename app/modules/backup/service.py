"""Backup — service (database + attachments).

Backup boundary (ADR-002 §5.3 / SPRINT4_TECHNICAL_PLAN.md §4.4):

    Backup Builder (local filesystem walk: db file + attachments/ tree
                    -> zip bytes -- UNCHANGED from before Sprint 4)
      -> Backup Artifact (the zip bytes)
      -> StorageProvider.save()   <- Sprint 4 abstracts exactly this step
      -> Local Disk (today) / Cloud (later -- not built)

Archive *construction* stays a local filesystem operation (it depends on
the local SQLite file and the local attachments tree, not on the storage
destination). Only the archive's *destination write* goes through the
`StorageProvider` seam. This is not a cloud backup system.
"""

import os
import tempfile
import zipfile
from datetime import datetime

from app.config import paths
from app.core.storage import get_storage


def _build_archive(tmp_path: str) -> None:
    """Backup Builder: write the db file + attachments/ tree into a zip at
    `tmp_path`. Local filesystem operation, unchanged from before Sprint 4."""
    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(paths.DB_PATH, arcname="wise_pms.db")
        for root, _dirs, files in os.walk(paths.ATTACHMENTS_DIR):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, os.path.dirname(paths.ATTACHMENTS_DIR))
                zf.write(full, arcname=rel)


def backup_now() -> str:
    """Create backups/backup_YYYY_MM_DD.zip containing the database and
    attachments. Returns the backup file's absolute path."""
    os.makedirs(paths.BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y_%m_%d")
    filename = f"backup_{stamp}.zip"

    # If a backup already exists today, add a time suffix (unchanged
    # naming convention). This collision check is a local-disk-native
    # detail of naming the destination artifact, not a universal storage
    # capability (the StorageProvider Protocol has no exists() method).
    if os.path.exists(os.path.join(paths.BACKUPS_DIR, filename)):
        stamp_t = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        filename = f"backup_{stamp_t}.zip"

    fd, tmp_path = tempfile.mkstemp(suffix=".zip", dir=paths.BACKUPS_DIR)
    os.close(fd)
    try:
        _build_archive(tmp_path)  # Backup Builder
        with open(tmp_path, "rb") as fh:
            data = fh.read()  # Backup Artifact
    finally:
        os.remove(tmp_path)

    key = os.path.join("backups", filename)
    get_storage().save(key, data)  # destination write only
    return os.path.join(paths.BASE_DIR, key)
