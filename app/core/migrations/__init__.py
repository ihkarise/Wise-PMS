"""Wise PMS — schema migration framework (backlog F1).

Public surface for the migration engine. Callers import from this package, not
from the internal modules:

    from app.core.migrations import migrate, rollback_to, current_version

``migrate`` / ``rollback_to`` bind the ordered :data:`MIGRATIONS` registry to the
low-level runner so application code never has to pass the registry explicitly.
"""

import sqlite3

from app.core.migrations.registry import MIGRATIONS
from app.core.migrations.runner import (
    Migration,
    MigrationError,
    SCHEMA_VERSION_TABLE,
    applied_versions,
    current_version,
    ensure_version_table,
    rollback,
    run_migrations,
)

LATEST_VERSION = MIGRATIONS[-1].version if MIGRATIONS else 0

__all__ = [
    "Migration",
    "MigrationError",
    "MIGRATIONS",
    "LATEST_VERSION",
    "SCHEMA_VERSION_TABLE",
    "applied_versions",
    "current_version",
    "ensure_version_table",
    "migrate",
    "rollback_to",
]


def migrate(conn: sqlite3.Connection) -> list[int]:
    """Bring ``conn`` up to the latest registered schema version.

    Idempotent: returns the versions applied by this call (empty when already
    current).
    """
    return run_migrations(conn, MIGRATIONS)


def rollback_to(conn: sqlite3.Connection, to_version: int = 0) -> list[int]:
    """Reverse applied migrations down to (excluding) ``to_version``.

    Returns the versions rolled back (empty when already at/below the target).
    """
    return rollback(conn, to_version, MIGRATIONS)
