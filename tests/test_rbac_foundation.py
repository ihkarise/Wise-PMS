"""RBAC foundation tests (Sprint 5 / F3, Milestone 1 — ADR-003).

Covers the database/domain foundation only: the v0003 schema + seed, the exact
approved role→permission matrix, the legacy-admin migration, the one-active-role
and at-least-one-active-Administrator invariants, and migration
idempotence/reversibility. No route-guard / authorization-enforcement tests here
(those belong to a later milestone).

Schema/seed/migration facts are checked against throwaway in-memory databases;
the service and init_db integration checks use an isolated ``WISE_PMS_HOME``
file database, mirroring ``tests/test_migrations.py`` conventions.
"""

import os
import sqlite3
import tempfile

os.environ.setdefault("WISE_PMS_HOME",
                      tempfile.mkdtemp(prefix="wisepms_rbac_"))

from app.core.migrations import (  # noqa: E402
    LATEST_VERSION,
    MIGRATIONS,
    migrate,
    rollback_to,
)
from app.core.migrations.runner import run_migrations  # noqa: E402

RBAC_TABLES = {"roles", "permissions", "role_permissions", "user_roles"}

EXPECTED_ROLES = ["Administrator", "Doctor", "Reception", "Pharmacy", "Accounts"]

EXPECTED_PERMISSIONS = {
    "dashboard.view", "patients.view", "registration.create", "patients.edit",
    "patients.deactivate", "attachments.upload", "attachments.delete",
    "cases.view", "cases.manage", "visits.view", "visits.manage",
    "consultation.view", "consultation.edit", "settings.edit", "backup.run",
    "rbac.manage",
}

# The approved default role→permission matrix (SPRINT5_TECHNICAL_PLAN.md §5.2).
GRANTS = {
    "Administrator": set(EXPECTED_PERMISSIONS),  # all 16
    "Doctor": {
        "dashboard.view", "patients.view", "registration.create",
        "patients.edit", "patients.deactivate", "attachments.upload",
        "attachments.delete", "cases.view", "cases.manage", "visits.view",
        "visits.manage", "consultation.view", "consultation.edit",
    },
    "Reception": {
        "dashboard.view", "patients.view", "registration.create",
        "patients.edit", "attachments.upload",
    },
    "Pharmacy": {"dashboard.view"},
    "Accounts": {"dashboard.view"},
}


# --- helpers ---------------------------------------------------------------

def _mem() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _table_names(conn) -> set:
    return {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }


def _schema_objects(conn):
    return [
        (r[0], r[1], r[2])
        for r in conn.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        )
    ]


def _perm_keys(conn, role_name) -> set:
    return {
        r[0]
        for r in conn.execute(
            "SELECT p.key FROM permissions p "
            "JOIN role_permissions rp ON rp.permission_id = p.id "
            "JOIN roles r ON r.id = rp.role_id WHERE r.name = ?",
            (role_name,),
        )
    }


# --- schema + seed (in-memory) --------------------------------------------

def test_rbac_tables_exist():
    conn = _mem()
    migrate(conn)
    assert RBAC_TABLES.issubset(_table_names(conn))


def test_latest_version_is_three():
    assert LATEST_VERSION == 3


def test_exactly_five_roles_seeded():
    conn = _mem()
    migrate(conn)
    names = [r[0] for r in conn.execute("SELECT name FROM roles ORDER BY id")]
    assert names == EXPECTED_ROLES
    # Administrator is the only protected system role.
    sys_roles = [r[0] for r in conn.execute(
        "SELECT name FROM roles WHERE is_system = 1")]
    assert sys_roles == ["Administrator"]


def test_exactly_sixteen_permissions_seeded():
    conn = _mem()
    migrate(conn)
    keys = {r[0] for r in conn.execute("SELECT key FROM permissions")}
    assert keys == EXPECTED_PERMISSIONS
    assert len(keys) == 16


def test_role_permission_grants_exact():
    conn = _mem()
    migrate(conn)
    for role, expected in GRANTS.items():
        assert _perm_keys(conn, role) == expected, role


def test_administrator_has_all_sixteen_permissions():
    conn = _mem()
    migrate(conn)
    assert _perm_keys(conn, "Administrator") == EXPECTED_PERMISSIONS
    assert len(_perm_keys(conn, "Administrator")) == 16


def test_one_active_role_per_user_enforced_by_unique_index():
    conn = _mem()
    migrate(conn)
    conn.execute("PRAGMA foreign_keys = OFF;")  # isolate the UNIQUE constraint
    conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES (1, 1)")
    conn.commit()
    try:
        conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES (1, 2)")
        assert False, "expected IntegrityError on a second role for one user"
    except sqlite3.IntegrityError:
        pass


# --- legacy migration + credential safety ---------------------------------

def test_legacy_admin_maps_to_administrator():
    """An existing 'Admin' user is bound to Administrator when v0003 applies."""
    conn = _mem()
    run_migrations(conn, tuple(m for m in MIGRATIONS if m.version <= 2))
    conn.execute(
        "INSERT INTO users (username, password_hash, full_name, role) "
        "VALUES ('legacyadmin', 'hash', 'Legacy Admin', 'Admin')"
    )
    conn.commit()
    migrate(conn)  # applies v0003, which maps the pre-existing admin
    row = conn.execute(
        "SELECT r.name FROM user_roles ur "
        "JOIN roles r ON r.id = ur.role_id "
        "JOIN users u ON u.id = ur.user_id WHERE u.username = 'legacyadmin'"
    ).fetchone()
    assert row is not None and row[0] == "Administrator"


def test_migration_does_not_alter_credentials():
    conn = _mem()
    run_migrations(conn, tuple(m for m in MIGRATIONS if m.version <= 2))
    conn.execute(
        "INSERT INTO users (username, password_hash, role) "
        "VALUES ('u', 'SECRET_HASH', 'Admin')"
    )
    conn.commit()
    before = conn.execute(
        "SELECT password_hash FROM users WHERE username = 'u'"
    ).fetchone()[0]
    migrate(conn)
    after = conn.execute(
        "SELECT password_hash FROM users WHERE username = 'u'"
    ).fetchone()[0]
    assert before == after == "SECRET_HASH"


# --- idempotence + reversibility ------------------------------------------

def test_v0003_idempotent_and_reversible():
    conn = _mem()
    migrate(conn)
    before = _schema_objects(conn)
    assert migrate(conn) == []          # nothing left to apply
    assert _schema_objects(conn) == before

    assert rollback_to(conn, 2) == [3]  # reverse only v0003
    names = _table_names(conn)
    assert RBAC_TABLES.isdisjoint(names)
    assert "consultations" in names     # v0002 intact
    assert "users" in names             # v0001 intact

    assert migrate(conn) == [3]         # forward-only recovery
    assert RBAC_TABLES.issubset(_table_names(conn))


# --- service + init_db integration (isolated file database) ---------------

def _fresh_db():
    from app.config import paths
    from app.core.database import init_db
    if os.path.exists(paths.DB_PATH):
        os.remove(paths.DB_PATH)
    init_db()


def _query_one(sql, params=()):
    from app.core.database import get_connection
    conn = get_connection()
    try:
        row = conn.execute(sql, params).fetchone()
        return row
    finally:
        conn.close()


def _admin_id():
    return _query_one("SELECT id FROM users WHERE username = 'admin'")[0]


def _insert_user(username, legacy_role="Reception", active=1):
    from app.core.database import get_connection
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role, is_active) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, "x", username.title(), legacy_role, active),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def test_init_db_binds_default_admin_to_administrator():
    _fresh_db()
    from app.modules.roles import service as rsvc
    roles = rsvc.roles_for_user(_admin_id())
    assert [r["name"] for r in roles] == ["Administrator"]


def test_default_admin_has_all_sixteen_permissions_via_binding():
    _fresh_db()
    from app.modules.roles import service as rsvc
    perms = rsvc.permission_keys_for_user(_admin_id())
    assert set(perms) == EXPECTED_PERMISSIONS
    assert len(perms) == 16


def test_init_db_idempotent_and_credentials_stable():
    from app.core.database import init_db
    from app.modules.authentication.service import authenticate
    _fresh_db()
    before = _query_one(
        "SELECT password_hash FROM users WHERE username = 'admin'"
    )[0]
    init_db()  # second launch — must not change credentials or duplicate rows
    after = _query_one(
        "SELECT password_hash FROM users WHERE username = 'admin'"
    )[0]
    assert before == after
    assert (authenticate("admin", "admin123") or {}).get("username") == "admin"
    # Still exactly one binding for admin (idempotent).
    count = _query_one(
        "SELECT COUNT(*) FROM user_roles ur JOIN users u ON u.id = ur.user_id "
        "WHERE u.username = 'admin'"
    )[0]
    assert count == 1


def test_assign_role_replaces_to_a_single_active_role():
    _fresh_db()
    from app.modules.roles import service as rsvc
    uid = _insert_user("recep1")
    rsvc.assign_role(uid, "Reception")
    rsvc.assign_role(uid, "Doctor")  # replaces, not adds
    roles = rsvc.roles_for_user(uid)
    assert [r["name"] for r in roles] == ["Doctor"]


def test_last_active_administrator_cannot_be_demoted():
    _fresh_db()
    from app.modules.roles import service as rsvc
    aid = _admin_id()
    try:
        rsvc.assign_role(aid, "Doctor")
        assert False, "expected RoleError demoting the last Administrator"
    except rsvc.RoleError:
        pass
    # Admin remains Administrator.
    assert [r["name"] for r in rsvc.roles_for_user(aid)] == ["Administrator"]


def test_demotion_allowed_once_a_second_administrator_exists():
    _fresh_db()
    from app.modules.roles import service as rsvc
    aid = _admin_id()
    uid = _insert_user("admin2")
    rsvc.assign_role(uid, "Administrator")   # now two active administrators
    rsvc.assign_role(aid, "Doctor")          # first can now be demoted
    assert [r["name"] for r in rsvc.roles_for_user(aid)] == ["Doctor"]
    assert [r["name"] for r in rsvc.roles_for_user(uid)] == ["Administrator"]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
    print("[PASS] all RBAC foundation tests")
