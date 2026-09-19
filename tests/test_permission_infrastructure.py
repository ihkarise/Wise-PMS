"""Permission infrastructure tests (Sprint 5 / F3, Milestone 2 — ADR-003).

Covers the read-side permission API only: the permission registry, its identity
with the seeded database permissions, ``user_has_permission``, and
``require_permission``. Grants follow the approved matrix
(``docs/planning/SPRINT5_TECHNICAL_PLAN.md`` §5.2). No route/controller
enforcement is exercised (that is a later milestone).
"""

import os
import tempfile

os.environ.setdefault("WISE_PMS_HOME",
                      tempfile.mkdtemp(prefix="wisepms_perm_"))

from app.modules.roles import permissions as reg  # noqa: E402
from app.modules.roles import service as rsvc  # noqa: E402

# The approved matrix (SPRINT5_TECHNICAL_PLAN.md §5.2), by role.
EXPECTED_PERMISSIONS = {
    "dashboard.view", "patients.view", "registration.create", "patients.edit",
    "patients.deactivate", "attachments.upload", "attachments.delete",
    "cases.view", "cases.manage", "visits.view", "visits.manage",
    "consultation.view", "consultation.edit", "settings.edit", "backup.run",
    "rbac.manage",
}

GRANTS = {
    "Administrator": set(EXPECTED_PERMISSIONS),
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

def _fresh_db():
    from app.config import paths
    from app.core.database import init_db
    if os.path.exists(paths.DB_PATH):
        os.remove(paths.DB_PATH)
    init_db()


def _admin_id():
    from app.core.database import get_connection
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT id FROM users WHERE username = 'admin'"
        ).fetchone()[0]
    finally:
        conn.close()


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


def _user_with_role(username, role_name, legacy_role="Reception", active=1):
    uid = _insert_user(username, legacy_role=legacy_role, active=active)
    rsvc.assign_role(uid, role_name)
    return uid


# --- registry --------------------------------------------------------------

def test_registry_represents_exactly_sixteen_approved_permissions():
    assert set(reg.ALL_PERMISSIONS) == EXPECTED_PERMISSIONS
    assert len(reg.ALL_PERMISSIONS) == 16


def test_registry_has_no_unexpected_permissions():
    assert set(reg.ALL_PERMISSIONS) - EXPECTED_PERMISSIONS == set()


def test_registry_matches_seeded_database_permissions():
    """The code-side registry must equal the DB-seeded permission keys."""
    _fresh_db()
    from app.core.database import get_connection
    conn = get_connection()
    try:
        db_keys = {r["key"] for r in conn.execute("SELECT key FROM permissions")}
    finally:
        conn.close()
    assert db_keys == set(reg.ALL_PERMISSIONS)


def test_is_known_permission():
    assert reg.is_known_permission("rbac.manage") is True
    assert reg.is_known_permission("does.not.exist") is False


# --- user_has_permission (per role, matrix-driven) ------------------------

def test_administrator_has_every_permission():
    _fresh_db()
    aid = _admin_id()
    for key in EXPECTED_PERMISSIONS:
        assert rsvc.user_has_permission({"id": aid}, key) is True, key


def test_each_role_matches_the_approved_matrix():
    _fresh_db()
    for role, granted in GRANTS.items():
        if role == "Administrator":
            uid = _admin_id()
        else:
            uid = _user_with_role(f"user_{role.lower()}", role)
        for key in EXPECTED_PERMISSIONS:
            expected = key in granted
            assert rsvc.user_has_permission({"id": uid}, key) is expected, (
                role, key
            )


def test_denied_permission_returns_false():
    _fresh_db()
    doc = _user_with_role("doc1", "Doctor")
    # Doctor is denied the admin/config keys.
    assert rsvc.user_has_permission({"id": doc}, "settings.edit") is False
    assert rsvc.user_has_permission({"id": doc}, "backup.run") is False
    assert rsvc.user_has_permission({"id": doc}, "rbac.manage") is False


def test_nonexistent_user_is_denied():
    _fresh_db()
    assert rsvc.user_has_permission({"id": 999999}, "dashboard.view") is False
    assert rsvc.user_has_permission(None, "dashboard.view") is False
    assert rsvc.user_has_permission({}, "dashboard.view") is False


def test_nonexistent_permission_is_denied_even_for_admin():
    _fresh_db()
    aid = _admin_id()
    assert rsvc.user_has_permission({"id": aid}, "does.not.exist") is False


def test_user_with_no_role_binding_is_denied():
    _fresh_db()
    uid = _insert_user("norole", legacy_role="Doctor")  # legacy hint only, no binding
    assert rsvc.user_has_permission({"id": uid}, "dashboard.view") is False


def test_inactive_user_is_denied_even_with_admin_binding():
    _fresh_db()
    uid = _insert_user("ghost", legacy_role="Administrator", active=0)
    rsvc.assign_role(uid, "Administrator")  # binding exists...
    assert rsvc.user_has_permission({"id": uid}, "dashboard.view") is False  # ...but inactive


def test_legacy_users_role_does_not_control_authorization():
    """A user whose legacy users.role='Administrator' but whose user_roles
    binding is Reception has only Reception permissions — proving users.role
    is not the authorization source."""
    _fresh_db()
    uid = _insert_user("fakeadmin", legacy_role="Administrator")  # legacy string
    # No binding yet: denied despite the legacy 'Administrator' string.
    assert rsvc.user_has_permission({"id": uid}, "rbac.manage") is False
    # Bind to Reception; authority comes from user_roles, not users.role.
    rsvc.assign_role(uid, "Reception")
    assert rsvc.user_has_permission({"id": uid}, "patients.view") is True
    assert rsvc.user_has_permission({"id": uid}, "rbac.manage") is False
    assert rsvc.user_has_permission({"id": uid}, "cases.manage") is False


def test_user_ref_accepts_dict_and_int():
    _fresh_db()
    aid = _admin_id()
    assert rsvc.user_has_permission(aid, "rbac.manage") is True          # bare int
    assert rsvc.user_has_permission({"id": aid}, "rbac.manage") is True  # session dict


# --- require_permission ----------------------------------------------------

def test_require_permission_allows_authorized():
    _fresh_db()
    aid = _admin_id()
    # Must not raise.
    rsvc.require_permission({"id": aid}, "rbac.manage")


def test_require_permission_raises_on_denied():
    _fresh_db()
    doc = _user_with_role("doc2", "Doctor")
    try:
        rsvc.require_permission({"id": doc}, "settings.edit")
        assert False, "expected AuthorizationError on a denied permission"
    except rsvc.AuthorizationError:
        pass


def test_require_permission_raises_on_unknown_permission():
    _fresh_db()
    aid = _admin_id()
    try:
        rsvc.require_permission({"id": aid}, "does.not.exist")
        assert False, "expected AuthorizationError (fail-closed) on unknown key"
    except rsvc.AuthorizationError:
        pass


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
    print("[PASS] all permission-infrastructure tests")
