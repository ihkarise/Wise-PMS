"""DatabaseAdapter selection point (ADR-002 §3 and the Configuration
boundary, ADR-002 §5.2).

Exactly one adapter exists in Sprint 4: `SQLiteAdapter`. There is no
environment variable and no Settings UI control for this selection —
adding a second adapter (Postgres/MySQL/SQL Server) is a future,
separately approved phase, not built here.
"""

from app.core.db_adapters.base import DatabaseAdapter, Dialect
from app.core.db_adapters.sqlite_adapter import SQLiteAdapter

_adapter = SQLiteAdapter()


def get_adapter() -> DatabaseAdapter:
    """Return the active DatabaseAdapter. Single hardcoded ``sqlite``
    branch today (Sprint 4 Configuration boundary)."""
    return _adapter


__all__ = ["DatabaseAdapter", "Dialect", "SQLiteAdapter", "get_adapter"]
