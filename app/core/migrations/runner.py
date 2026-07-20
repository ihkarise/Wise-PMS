"""Wise PMS — schema migration engine.

Forward-only, ordered, **idempotent** SQLite migrations with a version ledger
(``schema_version``) and rollback support. This is core infrastructure and lives
below the repository layer, alongside :mod:`app.core.database`; it is the single
place allowed to run schema DDL.

Design contract (see ``specs/IMPLEMENTATION_PLAN.md`` §6):

- Each :class:`Migration` is a small, named, versioned unit with an ``up`` script
  and (optionally) a reversible ``down`` script.
- ``up`` scripts **must be additive and idempotent** — use
  ``CREATE TABLE IF NOT EXISTS`` / ``ALTER TABLE ... ADD COLUMN`` so applying a
  migration onto a legacy database that already has the objects is a safe no-op.
- The runner applies pending migrations in ascending version order, each stamped
  atomically with its DDL, and never re-applies one that is already recorded.
- ``down`` scripts power :func:`rollback` (and tests); a migration without a
  ``down`` is treated as irreversible.

The engine takes a ``sqlite3.Connection`` (dependency injection) so it can be
driven against the live database, a legacy database, or an isolated test
connection with no global state.
"""

from dataclasses import dataclass
import sqlite3

SCHEMA_VERSION_TABLE = "schema_version"


class MigrationError(RuntimeError):
    """Raised when the migration ledger and the registry cannot be reconciled."""


@dataclass(frozen=True)
class Migration:
    """One ordered, named schema change.

    ``up`` and ``down`` are executed with :meth:`sqlite3.Connection.executescript`
    and may contain multiple statements. ``down`` defaults to empty, marking the
    migration irreversible.
    """

    version: int
    name: str
    up: str
    down: str = ""

    @property
    def reversible(self) -> bool:
        """True when a non-empty ``down`` script is defined."""
        return bool(self.down.strip())


def ensure_version_table(conn: sqlite3.Connection) -> None:
    """Create the ``schema_version`` ledger if it does not already exist."""
    conn.executescript(
        f"CREATE TABLE IF NOT EXISTS {SCHEMA_VERSION_TABLE} ("
        " version INTEGER PRIMARY KEY,"
        " name TEXT NOT NULL,"
        " applied_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        ");"
    )
    conn.commit()


def applied_versions(conn: sqlite3.Connection) -> list[int]:
    """Return every recorded schema version, ascending."""
    ensure_version_table(conn)
    return [
        row[0]
        for row in conn.execute(
            f"SELECT version FROM {SCHEMA_VERSION_TABLE} ORDER BY version"
        )
    ]


def current_version(conn: sqlite3.Connection) -> int:
    """Return the highest applied schema version, or ``0`` when none applied."""
    ensure_version_table(conn)
    row = conn.execute(
        f"SELECT MAX(version) FROM {SCHEMA_VERSION_TABLE}"
    ).fetchone()
    return row[0] or 0


def run_migrations(
    conn: sqlite3.Connection, migrations: "tuple[Migration, ...]" = ()
) -> list[int]:
    """Apply every not-yet-recorded migration in ascending version order.

    Each migration's DDL and its ledger row are committed together, so an
    interrupted run leaves the database at a consistent recorded version.
    Returns the versions applied by *this* call (empty when already up to date).
    """
    ensure_version_table(conn)
    done = set(applied_versions(conn))
    newly_applied: list[int] = []
    for migration in sorted(migrations, key=lambda m: m.version):
        if migration.version in done:
            continue
        try:
            conn.executescript(migration.up)
            conn.execute(
                f"INSERT INTO {SCHEMA_VERSION_TABLE} (version, name) "
                "VALUES (?, ?)",
                (migration.version, migration.name),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        newly_applied.append(migration.version)
    return newly_applied


def rollback(
    conn: sqlite3.Connection,
    to_version: int = 0,
    migrations: "tuple[Migration, ...]" = (),
) -> list[int]:
    """Reverse applied migrations down to (and excluding) ``to_version``.

    Runs each ``down`` script in descending version order and removes its ledger
    row atomically. Raises :class:`MigrationError` if a recorded version has no
    definition in ``migrations`` or is irreversible. Returns the versions rolled
    back (empty when already at or below ``to_version``).
    """
    ensure_version_table(conn)
    by_version = {m.version: m for m in migrations}
    rolled_back: list[int] = []
    for version in sorted(applied_versions(conn), reverse=True):
        if version <= to_version:
            break
        migration = by_version.get(version)
        if migration is None:
            raise MigrationError(
                f"Recorded version {version} has no migration definition; "
                "cannot roll back."
            )
        if not migration.reversible:
            raise MigrationError(
                f"Migration {version} ({migration.name}) is irreversible "
                "(no down script)."
            )
        try:
            conn.executescript(migration.down)
            conn.execute(
                f"DELETE FROM {SCHEMA_VERSION_TABLE} WHERE version = ?",
                (version,),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        rolled_back.append(version)
    return rolled_back
