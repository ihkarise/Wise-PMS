"""Wise PMS — Centralized filesystem paths.

All runtime data lives under a single home directory. Set the ``WISE_PMS_HOME``
environment variable to relocate it (used by the desktop packaging and by the
test suite for an isolated data directory). The default is the application
root, so behaviour is unchanged from Sprint 1/2.
"""

import os

# Application/repository root (…/Wise-PMS) unless WISE_PMS_HOME overrides it.
BASE_DIR = os.environ.get("WISE_PMS_HOME") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "wise_pms.db")

ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Folders that must exist before the app reads or writes anything.
RUNTIME_DIRS = (DATA_DIR, ATTACHMENTS_DIR, BACKUPS_DIR, EXPORTS_DIR, LOGS_DIR)


def ensure_folders() -> None:
    """Create every runtime folder if it does not already exist."""
    for folder in RUNTIME_DIRS:
        os.makedirs(folder, exist_ok=True)
