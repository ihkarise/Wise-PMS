"""Wise PMS — Database compatibility shim.

The database engine moved to :mod:`app.core.database` and the filesystem paths
moved to :mod:`app.config.paths` as part of the Sprint 2 architecture refactor.

This module re-exports the previous public surface so that existing imports
(``from app.database.db import get_connection`` / path constants / ``init_db``)
keep working unchanged. New code should import from ``app.core.database`` and
``app.config.paths`` directly.
"""

from app.config.paths import (  # noqa: F401  (re-exported)
    ATTACHMENTS_DIR,
    BACKUPS_DIR,
    BASE_DIR,
    DATA_DIR,
    DB_PATH,
    EXPORTS_DIR,
    LOGS_DIR,
)
from app.core.database import (  # noqa: F401  (re-exported)
    SCHEMA,
    get_connection,
    init_db,
)

__all__ = [
    "BASE_DIR", "DATA_DIR", "DB_PATH", "ATTACHMENTS_DIR", "BACKUPS_DIR",
    "EXPORTS_DIR", "LOGS_DIR", "SCHEMA", "get_connection", "init_db",
]
