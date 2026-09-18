"""DatabaseAdapter behavior-parity tests (Sprint 4, ADR-002 §3).

Asserts `SQLiteAdapter` and the `BaseRepository`-facing seam behave
identically to the pre-Sprint-4 direct-`sqlite3` implementation: same
connection setup, same commit/rollback/close semantics, same read/write
return shapes through `BaseRepository`.
"""

import os
import tempfile

os.environ.setdefault("WISE_PMS_HOME", tempfile.mkdtemp(prefix="wisepms_dbadapter_"))


def _fresh_db():
    from app.config import paths
    from app.core.database import init_db
    if os.path.exists(paths.DB_PATH):
        os.remove(paths.DB_PATH)
    init_db()


def test_sqlite_adapter_connect_matches_get_connection():
    import sqlite3

    from app.core.db_adapters import get_adapter
    from app.core.database import get_connection

    _fresh_db()
    adapter = get_adapter()

    conn_a = adapter.connect()
    conn_b = get_connection()
    try:
        assert isinstance(conn_a, sqlite3.Connection)
        assert conn_a.row_factory is sqlite3.Row
        assert conn_b.row_factory is sqlite3.Row
        # PRAGMA foreign_keys = ON on both connections
        assert conn_a.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conn_b.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn_a.close()
        conn_b.close()


def test_transaction_commits_on_success():
    from app.core.db_adapters import get_adapter

    _fresh_db()
    adapter = get_adapter()
    with adapter.transaction() as conn:
        conn.execute(
            "INSERT INTO settings (clinic_name) VALUES (?)", ("Committed Clinic",)
        )
    conn = adapter.connect()
    try:
        row = conn.execute(
            "SELECT COUNT(*) c FROM settings WHERE clinic_name = ?",
            ("Committed Clinic",),
        ).fetchone()
        assert row["c"] == 1
    finally:
        conn.close()


def test_transaction_rolls_back_on_exception():
    from app.core.db_adapters import get_adapter

    _fresh_db()
    adapter = get_adapter()
    try:
        with adapter.transaction() as conn:
            conn.execute(
                "INSERT INTO settings (clinic_name) VALUES (?)",
                ("Should Not Persist",),
            )
            raise RuntimeError("forced failure mid-transaction")
    except RuntimeError:
        pass

    conn = adapter.connect()
    try:
        row = conn.execute(
            "SELECT COUNT(*) c FROM settings WHERE clinic_name = ?",
            ("Should Not Persist",),
        ).fetchone()
        assert row["c"] == 0
    finally:
        conn.close()


def test_base_repository_read_write_shapes_unchanged():
    from app.core.repository import BaseRepository

    _fresh_db()
    repo = BaseRepository()

    new_id = repo._execute(
        "INSERT INTO patients (reg_no, name, gender, age) VALUES (?, ?, ?, ?)",
        ("P999999", "Adapter Test Patient", "Female", 30),
    )
    assert isinstance(new_id, int)

    one = repo._one("SELECT * FROM patients WHERE id = ?", (new_id,))
    assert isinstance(one, dict)
    assert one["name"] == "Adapter Test Patient"

    all_rows = repo._all("SELECT * FROM patients WHERE id = ?", (new_id,))
    assert isinstance(all_rows, list)
    assert all_rows[0]["id"] == new_id

    scalar = repo._scalar("SELECT COUNT(*) FROM patients WHERE id = ?", (new_id,))
    assert scalar == 1


def test_no_second_engine_branch_exists():
    """Sprint 4 ships exactly one adapter. This test documents that
    boundary so a future change to add a second engine is a deliberate,
    reviewed diff to this test, not a silent scope change."""
    from app.core.db_adapters import SQLiteAdapter, get_adapter

    assert isinstance(get_adapter(), SQLiteAdapter)
    assert get_adapter().dialect.name == "sqlite"


if __name__ == "__main__":
    test_sqlite_adapter_connect_matches_get_connection()
    test_transaction_commits_on_success()
    test_transaction_rolls_back_on_exception()
    test_base_repository_read_write_shapes_unchanged()
    test_no_second_engine_branch_exists()
    print("[PASS] db adapter parity")
