"""SQLiteAdapter — the sole `DatabaseAdapter` implementation in Sprint 4.

A line-for-line move of the connection/transaction logic that previously
lived directly in `app.core.database.get_connection` and
`app.core.repository.BaseRepository.transaction`. Behavior is unchanged:
same `row_factory`, same `PRAGMA foreign_keys`, same commit-on-success /
rollback-on-error / always-close semantics.

This is the only file outside `app.core.migrations` allowed to import
`sqlite3` directly (ADR-002 §3/§4; enforced by `tests/test_layering.py`).
"""

import sqlite3
from contextlib import contextmanager

from app.config import paths
from app.core.db_adapters.base import Dialect

SQLITE_DIALECT = Dialect(name="sqlite", placeholder="?")


class SQLiteAdapter:
    """DatabaseAdapter backed by the local SQLite file at `paths.DB_PATH`."""

    dialect = SQLITE_DIALECT

    def connect(self) -> sqlite3.Connection:
        """Return a SQLite connection with row access by column name."""
        conn = sqlite3.connect(paths.DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def execute(self, conn, sql, params=()):
        return conn.execute(sql, params)

    @contextmanager
    def transaction(self):
        """Commits on success, rolls back on error, always closes."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
