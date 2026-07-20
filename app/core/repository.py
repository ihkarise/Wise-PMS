"""Wise PMS — Base repository (data-access layer).

`BaseRepository` centralizes the SQLite connection lifecycle so concrete
repositories contain SQL, not `get_connection()/try/finally/close` boilerplate
(previously repeated ~30 times across the services).

It keeps the app's existing "connection per operation" model — appropriate for a
single-writer desktop workload — and provides the single choke point through
which all reads and writes flow. That choke point is the seam a future cloud
sync layer plugs into without touching services or the UI.
"""

from contextlib import contextmanager

from app.core.database import get_connection


class BaseRepository:
    """Base class for all repositories."""

    # -- reads ------------------------------------------------------
    def _all(self, sql, params=()):
        """Return every matching row as a list of dicts."""
        conn = get_connection()
        try:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()

    def _one(self, sql, params=()):
        """Return the first matching row as a dict, or None."""
        conn = get_connection()
        try:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row is not None else None
        finally:
            conn.close()

    def _scalar(self, sql, params=()):
        """Return the first column of the first row, or None."""
        conn = get_connection()
        try:
            row = conn.execute(sql, params).fetchone()
            return row[0] if row is not None else None
        finally:
            conn.close()

    # -- writes -----------------------------------------------------
    def _execute(self, sql, params=()):
        """Run one write statement, commit, and return lastrowid."""
        with self.transaction() as conn:
            cur = conn.execute(sql, params)
            return cur.lastrowid

    @contextmanager
    def transaction(self):
        """Context manager yielding a connection wrapped in one transaction.

        Commits on success, rolls back on error, always closes. Use it when a
        single logical operation spans multiple statements (e.g. insert a visit
        and its prescription items atomically).
        """
        conn = get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
