"""Wise PMS — Database Engine.

Creates and manages the local SQLite database (``data/wise_pms.db``).
Offline-first. No internet. No cloud.

Paths come from :mod:`app.config.paths` (relocatable via ``WISE_PMS_HOME``);
connections are resolved dynamically so a relocated data root is always
honoured.

Connection lifecycle is delegated to the active `DatabaseAdapter`
(:mod:`app.core.db_adapters` — `SQLiteAdapter` today, ADR-002 §3).
`get_connection` is kept as a compatibility shim: callers (``init_db``, the
migration runner, tests) are unaffected by the introduction of the adapter
seam.

The schema itself is owned by the migration framework
(:mod:`app.core.migrations`): ``init_db`` brings the database up to the latest
schema version, then seeds the first-run data (default admin + clinic settings).
The seed step stays in Python because the admin password is bcrypt-hashed with a
random salt and cannot be expressed as a static SQL migration.
"""

import bcrypt

from app.config import paths
from app.core.db_adapters import get_adapter
from app.core.migrations import migrate


def get_connection():
    """Return a database connection (delegates to the active DatabaseAdapter)."""
    return get_adapter().connect()


def init_db() -> None:
    """Create/upgrade the database schema and seed first-run data.

    Idempotent and safe on every launch: :func:`app.core.migrations.migrate`
    applies any pending migrations (stamping a legacy database at the current
    version without data loss), and the seed inserts run only when absent.
    """
    paths.ensure_folders()
    conn = get_connection()
    try:
        migrate(conn)

        # Default admin (admin / admin123) — created only once
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE username = ?", ("admin",)
        ).fetchone()
        if row["c"] == 0:
            password_hash = bcrypt.hashpw(
                "admin123".encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            conn.execute(
                "INSERT INTO users (username, password_hash, full_name, role) "
                "VALUES (?, ?, ?, ?)",
                ("admin", password_hash, "Administrator", "Admin"),
            )

        # Default clinic settings row
        row = conn.execute("SELECT COUNT(*) AS c FROM settings").fetchone()
        if row["c"] == 0:
            conn.execute(
                "INSERT INTO settings (clinic_name, doctor_name) VALUES (?, ?)",
                ("Wise Homeopathy Multispeciality Center", ""),
            )

        conn.commit()
    finally:
        conn.close()
