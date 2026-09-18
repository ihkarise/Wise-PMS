"""Wise PMS — Base repository (data-access layer).

`BaseRepository` centralizes connection lifecycle so concrete repositories
contain SQL, not `connect()/try/finally/close` boilerplate (previously
repeated ~30 times across the services).

It depends on the `DatabaseAdapter` seam (:mod:`app.core.db_adapters`,
ADR-002 §3) rather than importing an engine driver directly — that seam is
what lets a future server-grade engine be added additively, without
touching any repository's SQL or a single service/controller/view.
`SQLiteAdapter` is the sole implementation in Sprint 4; behavior here is
unchanged from the previous direct-`sqlite3`-import version.
"""

from contextlib import contextmanager

from app.core.db_adapters import get_adapter


class BaseRepository:
    """Base class for all repositories."""

    # -- reads ------------------------------------------------------
    def _all(self, sql, params=()):
        """Return every matching row as a list of dicts."""
        adapter = get_adapter()
        conn = adapter.connect()
        try:
            return [dict(r) for r in adapter.execute(conn, sql, params).fetchall()]
        finally:
            conn.close()

    def _one(self, sql, params=()):
        """Return the first matching row as a dict, or None."""
        adapter = get_adapter()
        conn = adapter.connect()
        try:
            row = adapter.execute(conn, sql, params).fetchone()
            return dict(row) if row is not None else None
        finally:
            conn.close()

    def _scalar(self, sql, params=()):
        """Return the first column of the first row, or None."""
        adapter = get_adapter()
        conn = adapter.connect()
        try:
            row = adapter.execute(conn, sql, params).fetchone()
            return row[0] if row is not None else None
        finally:
            conn.close()

    # -- writes -----------------------------------------------------
    def _execute(self, sql, params=()):
        """Run one write statement, commit, and return lastrowid."""
        with self.transaction() as conn:
            cur = get_adapter().execute(conn, sql, params)
            return cur.lastrowid

    @contextmanager
    def transaction(self):
        """Context manager yielding a connection wrapped in one transaction.

        Commits on success, rolls back on error, always closes. Use it when a
        single logical operation spans multiple statements (e.g. insert a visit
        and its prescription items atomically).
        """
        with get_adapter().transaction() as conn:
            yield conn
