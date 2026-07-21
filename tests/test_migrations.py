"""Tests for the schema migration framework (backlog F1).

Covers the engine contract in isolation (idempotency, version stamping,
rollback, legacy-database stamping, registry validation) plus a "fresh DB ==
migrated DB" parity check that ties the runner to the real bootstrap.

The engine takes a connection, so most tests drive a throwaway in-memory
database with no filesystem or global state. The parity/integration tests use an
isolated ``WISE_PMS_HOME`` set before any app import.
"""

import os
import sqlite3
import tempfile

os.environ.setdefault("WISE_PMS_HOME",
                      tempfile.mkdtemp(prefix="wisepms_migrations_"))

from app.core.migrations import (  # noqa: E402
    LATEST_VERSION,
    MIGRATIONS,
    SCHEMA_VERSION_TABLE,
    Migration,
    MigrationError,
    applied_versions,
    current_version,
    migrate,
    rollback_to,
)
from app.core.migrations.runner import (  # noqa: E402
    ensure_version_table,
    rollback,
    run_migrations,
)


def _mem() -> sqlite3.Connection:
    """A fresh in-memory database mirroring the app's connection pragmas."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _table_names(conn: sqlite3.Connection) -> list[str]:
    return [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]


def _schema_objects(conn: sqlite3.Connection) -> list[tuple]:
    """(type, name, sql) for every user object — the comparable schema shape."""
    return [
        (r[0], r[1], r[2])
        for r in conn.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        )
    ]


# --- ledger + engine basics ------------------------------------------------

def test_ensure_version_table_is_idempotent():
    conn = _mem()
    ensure_version_table(conn)
    ensure_version_table(conn)
    assert SCHEMA_VERSION_TABLE in _table_names(conn)
    assert current_version(conn) == 0
    assert applied_versions(conn) == []


def test_run_migrations_applies_and_stamps():
    conn = _mem()
    applied = migrate(conn)
    assert applied == [m.version for m in MIGRATIONS]
    assert current_version(conn) == LATEST_VERSION
    assert applied_versions(conn) == sorted(m.version for m in MIGRATIONS)
    # Baseline tables exist.
    for table in ("users", "patients", "visits", "attachments"):
        assert table in _table_names(conn)


def test_run_migrations_is_idempotent():
    conn = _mem()
    first = migrate(conn)
    before = _schema_objects(conn)
    second = migrate(conn)
    after = _schema_objects(conn)
    assert first != []
    assert second == []  # nothing left to apply
    assert before == after  # schema unchanged on the second run
    assert current_version(conn) == LATEST_VERSION


def test_run_migrations_only_applies_pending():
    conn = _mem()
    a = Migration(1, "a", "CREATE TABLE IF NOT EXISTS a (id INTEGER);", "DROP TABLE a;")
    b = Migration(2, "b", "CREATE TABLE IF NOT EXISTS b (id INTEGER);", "DROP TABLE b;")
    assert run_migrations(conn, (a,)) == [1]
    # Registry now grows by one; only the new version is applied.
    assert run_migrations(conn, (a, b)) == [2]
    assert applied_versions(conn) == [1, 2]


# --- legacy database stamping ---------------------------------------------

def test_stamps_legacy_database_without_data_loss():
    """A DB created before the runner existed is stamped, not rebuilt."""
    conn = _mem()
    # Simulate a legacy DB: the baseline objects already exist, no ledger.
    conn.executescript(MIGRATIONS[0].up)
    conn.execute(
        "INSERT INTO users (username, password_hash) VALUES ('legacy', 'x')"
    )
    conn.commit()
    assert SCHEMA_VERSION_TABLE not in _table_names(conn)

    applied = migrate(conn)

    # v1 baseline already present (stamped, IF NOT EXISTS no-op); later
    # migrations (v2 consultations) still apply forward.
    assert applied == [m.version for m in MIGRATIONS]
    assert current_version(conn) == LATEST_VERSION
    # Existing row survived (IF NOT EXISTS made the baseline a no-op).
    row = conn.execute(
        "SELECT username FROM users WHERE username = 'legacy'"
    ).fetchone()
    assert row is not None


# --- v0002 consultations ---------------------------------------------------

def test_v0002_creates_consultations_and_indexes():
    conn = _mem()
    migrate(conn)
    assert LATEST_VERSION == 2
    assert "consultations" in _table_names(conn)
    idx = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' "
        "AND name LIKE 'idx_consultation_%' ORDER BY name")]
    assert idx == ["idx_consultation_patient", "idx_consultation_visit"]


def test_v0002_rollback_drops_consultations_keeps_visits():
    conn = _mem()
    migrate(conn)
    rolled = rollback_to(conn, 1)
    assert rolled == [2]
    assert current_version(conn) == 1
    assert "consultations" not in _table_names(conn)
    assert "visits" in _table_names(conn)  # v1 event table untouched
    # Forward again restores it.
    assert migrate(conn) == [2]
    assert "consultations" in _table_names(conn)


def test_v0002_visit_id_unique_enforced():
    conn = _mem()
    migrate(conn)
    conn.execute("PRAGMA foreign_keys = OFF;")  # isolate the UNIQUE constraint
    conn.execute("INSERT INTO consultations (visit_id, patient_id, status) "
                 "VALUES (1, 1, 'draft')")
    conn.commit()
    try:
        conn.execute("INSERT INTO consultations (visit_id, patient_id, status) "
                     "VALUES (1, 1, 'draft')")
        assert False, "expected IntegrityError on duplicate visit_id"
    except sqlite3.IntegrityError:
        pass


# --- rollback --------------------------------------------------------------

def test_rollback_reverses_to_zero_then_reapplies():
    conn = _mem()
    migrate(conn)
    assert "patients" in _table_names(conn)

    rolled = rollback_to(conn, 0)

    assert rolled == sorted((m.version for m in MIGRATIONS), reverse=True)
    assert current_version(conn) == 0
    assert applied_versions(conn) == []
    assert "patients" not in _table_names(conn)

    # Forward-only recovery: re-running rebuilds the schema.
    migrate(conn)
    assert current_version(conn) == LATEST_VERSION
    assert "patients" in _table_names(conn)


def test_rollback_to_current_is_noop():
    conn = _mem()
    migrate(conn)
    assert rollback_to(conn, LATEST_VERSION) == []
    assert current_version(conn) == LATEST_VERSION


def test_rollback_partial_stops_at_target():
    conn = _mem()
    a = Migration(1, "a", "CREATE TABLE IF NOT EXISTS a (id INTEGER);", "DROP TABLE a;")
    b = Migration(2, "b", "CREATE TABLE IF NOT EXISTS b (id INTEGER);", "DROP TABLE b;")
    run_migrations(conn, (a, b))
    assert rollback(conn, 1, (a, b)) == [2]
    assert applied_versions(conn) == [1]
    assert "a" in _table_names(conn)
    assert "b" not in _table_names(conn)


def test_rollback_of_irreversible_migration_raises():
    conn = _mem()
    a = Migration(1, "a", "CREATE TABLE IF NOT EXISTS a (id INTEGER);")  # no down
    run_migrations(conn, (a,))
    try:
        rollback(conn, 0, (a,))
        assert False, "expected MigrationError"
    except MigrationError:
        pass


def test_rollback_of_unknown_version_raises():
    conn = _mem()
    a = Migration(1, "a", "CREATE TABLE IF NOT EXISTS a (id INTEGER);", "DROP TABLE a;")
    run_migrations(conn, (a,))
    try:
        rollback(conn, 0, ())  # registry no longer defines version 1
        assert False, "expected MigrationError"
    except MigrationError:
        pass


# --- fresh == migrated parity + integration -------------------------------

def test_fresh_schema_equals_migrated_schema():
    """The migration path yields exactly the direct baseline schema."""
    migrated = _mem()
    migrate(migrated)

    direct = _mem()
    for m in MIGRATIONS:
        direct.executescript(m.up)
    ensure_version_table(direct)

    # Compare every schema object except the ledger's own contents.
    assert _schema_objects(migrated) == _schema_objects(direct)


def test_init_db_produces_latest_version_and_seeds():
    from app.config import paths
    from app.core.database import get_connection, init_db

    if os.path.exists(paths.DB_PATH):
        os.remove(paths.DB_PATH)
    init_db()

    conn = get_connection()
    try:
        assert current_version(conn) == LATEST_VERSION
        assert SCHEMA_VERSION_TABLE in _table_names(conn)
        # Seed data landed on top of the migrated schema.
        assert conn.execute(
            "SELECT COUNT(*) FROM users WHERE username = 'admin'"
        ).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM settings").fetchone()[0] == 1
    finally:
        conn.close()

    # init_db stays idempotent across launches.
    init_db()
    conn = get_connection()
    try:
        assert conn.execute(
            "SELECT COUNT(*) FROM users WHERE username = 'admin'"
        ).fetchone()[0] == 1
        assert current_version(conn) == LATEST_VERSION
    finally:
        conn.close()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
    print("[PASS] all migration tests")
