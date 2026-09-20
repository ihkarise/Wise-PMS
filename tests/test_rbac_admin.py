"""RBAC administration tests (Sprint 5 / F3, Milestone 5 — ADR-003).

Covers the minimum rbac.manage administration surface: role listing, permission
listing, role->permission editing, and existing-user->role assignment. Every
mutation is exercised through the service boundary (which enforces rbac.manage
and preserves the single-role and last-Administrator invariants). Denied
mutations are verified to leave the database unchanged, not merely to raise.
Also verifies the route-level rbac.manage guard on /admin/roles.
"""

import os
import tempfile
from unittest.mock import MagicMock

os.environ.setdefault("WISE_PMS_HOME",
                      tempfile.mkdtemp(prefix="wisepms_rbacadmin_"))

from app.modules.roles import permissions as reg  # noqa: E402
from app.modules.roles import service as svc  # noqa: E402


# --- helpers ---------------------------------------------------------------

def _fresh_db():
    from app.config import paths
    from app.core.database import init_db
    if os.path.exists(paths.DB_PATH):
        os.remove(paths.DB_PATH)
    init_db()


def _conn():
    from app.core.database import get_connection
    return get_connection()


def _admin_id():
    c = _conn()
    try:
        return c.execute("SELECT id FROM users WHERE username='admin'").fetchone()[0]
    finally:
        c.close()


def _mk_user(username, role_name, active=1):
    c = _conn()
    try:
        cur = c.execute(
            "INSERT INTO users (username, password_hash, full_name, role, is_active) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, "x", username.title(), role_name, active),
        )
        c.commit()
        uid = cur.lastrowid
    finally:
        c.close()
    svc.assign_role(uid, role_name)
    return uid


def _role_perm_count(role_name, key):
    c = _conn()
    try:
        return c.execute(
            "SELECT COUNT(*) FROM role_permissions rp "
            "JOIN roles r ON r.id = rp.role_id "
            "JOIN permissions p ON p.id = rp.permission_id "
            "WHERE r.name = ? AND p.key = ?", (role_name, key)).fetchone()[0]
    finally:
        c.close()


def _role_of(user_id):
    roles = svc.roles_for_user(user_id)
    return roles[0]["name"] if roles else None


def _denied(fn):
    try:
        fn()
        return False
    except svc.AuthorizationError:
        return True


# --- listing (rbac.manage gated) ------------------------------------------

def test_admin_can_list_five_roles():
    _fresh_db()
    roles = svc.list_roles_with_permissions(_admin_id())
    names = [r["name"] for r in roles]
    assert names == ["Administrator", "Doctor", "Reception", "Pharmacy", "Accounts"]
    # Administrator lists all 16 permissions.
    admin_role = next(r for r in roles if r["name"] == "Administrator")
    assert set(admin_role["permissions"]) == set(reg.ALL_PERMISSIONS)


def test_admin_can_list_sixteen_permissions():
    _fresh_db()
    cat = svc.list_permission_catalogue(_admin_id())
    assert {p["key"] for p in cat} == set(reg.ALL_PERMISSIONS)
    assert len(cat) == 16


def test_non_rbac_manage_user_cannot_list():
    _fresh_db()
    doctor = _mk_user("doc", "Doctor")
    assert _denied(lambda: svc.list_roles_with_permissions(doctor))
    assert _denied(lambda: svc.list_permission_catalogue(doctor))
    assert _denied(lambda: svc.list_users_with_roles(doctor))


# --- role -> permission editing -------------------------------------------

def test_admin_can_grant_and_revoke_permission():
    _fresh_db()
    aid = _admin_id()
    # Reception lacks cases.manage by default.
    assert _role_perm_count("Reception", "cases.manage") == 0
    svc.grant_permission(aid, "Reception", "cases.manage")
    assert _role_perm_count("Reception", "cases.manage") == 1
    svc.revoke_permission(aid, "Reception", "cases.manage")
    assert _role_perm_count("Reception", "cases.manage") == 0


def test_grant_unknown_permission_rejected_no_mutation():
    _fresh_db()
    aid = _admin_id()
    try:
        svc.grant_permission(aid, "Reception", "does.not.exist")
        assert False, "expected RoleError"
    except svc.RoleError:
        pass
    # No stray grant row was created for the bogus key.
    c = _conn()
    try:
        assert c.execute(
            "SELECT COUNT(*) FROM role_permissions rp JOIN roles r "
            "ON r.id=rp.role_id WHERE r.name='Reception'").fetchone()[0] == 5
    finally:
        c.close()


def test_grant_unknown_role_rejected():
    _fresh_db()
    aid = _admin_id()
    try:
        svc.grant_permission(aid, "Wizard", "cases.manage")
        assert False, "expected RoleError"
    except svc.RoleError:
        pass


def test_unauthorized_user_cannot_edit_permissions_no_mutation():
    _fresh_db()
    doctor = _mk_user("doc", "Doctor")  # lacks rbac.manage
    before = _role_perm_count("Reception", "cases.manage")
    assert _denied(lambda: svc.grant_permission(doctor, "Reception", "cases.manage"))
    assert _role_perm_count("Reception", "cases.manage") == before  # unchanged


def test_cannot_revoke_rbac_manage_from_administrator():
    _fresh_db()
    aid = _admin_id()
    assert _role_perm_count("Administrator", "rbac.manage") == 1
    try:
        svc.revoke_permission(aid, "Administrator", "rbac.manage")
        assert False, "expected RoleError protecting usable Administrator"
    except svc.RoleError:
        pass
    assert _role_perm_count("Administrator", "rbac.manage") == 1  # still granted


# --- user -> role assignment ----------------------------------------------

def test_admin_assigns_existing_user_to_role():
    _fresh_db()
    aid = _admin_id()
    uid = _mk_user("recep", "Reception")
    svc.admin_assign_user_role(aid, uid, "Doctor")
    assert _role_of(uid) == "Doctor"


def test_reassignment_replaces_single_active_role():
    _fresh_db()
    aid = _admin_id()
    uid = _mk_user("staff", "Reception")
    svc.admin_assign_user_role(aid, uid, "Pharmacy")
    svc.admin_assign_user_role(aid, uid, "Accounts")
    # Exactly one active binding remains.
    c = _conn()
    try:
        assert c.execute("SELECT COUNT(*) FROM user_roles WHERE user_id=?",
                         (uid,)).fetchone()[0] == 1
    finally:
        c.close()
    assert _role_of(uid) == "Accounts"


def test_unauthorized_user_cannot_assign_roles_no_mutation():
    _fresh_db()
    doctor = _mk_user("doc", "Doctor")       # lacks rbac.manage
    target = _mk_user("recep", "Reception")
    assert _denied(lambda: svc.admin_assign_user_role(doctor, target, "Doctor"))
    assert _role_of(target) == "Reception"   # unchanged


def test_assign_nonexistent_user_rejected():
    _fresh_db()
    aid = _admin_id()
    try:
        svc.admin_assign_user_role(aid, 999999, "Doctor")
        assert False, "expected RoleError for nonexistent user"
    except svc.RoleError:
        pass


def test_assign_unknown_role_rejected_no_mutation():
    _fresh_db()
    aid = _admin_id()
    uid = _mk_user("recep", "Reception")
    try:
        svc.admin_assign_user_role(aid, uid, "Wizard")
        assert False, "expected RoleError for unknown role"
    except svc.RoleError:
        pass
    assert _role_of(uid) == "Reception"  # unchanged


def test_admin_assign_preserves_last_administrator_invariant():
    _fresh_db()
    aid = _admin_id()  # the sole active Administrator
    try:
        svc.admin_assign_user_role(aid, aid, "Doctor")
        assert False, "expected RoleError demoting the last Administrator"
    except svc.RoleError:
        pass
    assert _role_of(aid) == "Administrator"  # unchanged


def test_admin_assignment_still_routes_through_assign_role_invariants():
    # With a second Administrator, demoting the first is allowed.
    _fresh_db()
    aid = _admin_id()
    second = _mk_user("admin2", "Administrator")
    svc.admin_assign_user_role(aid, aid, "Doctor")  # now allowed
    assert _role_of(aid) == "Doctor"
    assert _role_of(second) == "Administrator"


# --- users.role cannot grant rbac.manage ----------------------------------

def test_users_role_string_cannot_grant_rbac_manage():
    _fresh_db()
    # Legacy users.role='Administrator' but user_roles binding = Reception.
    c = _conn()
    try:
        cur = c.execute(
            "INSERT INTO users (username, password_hash, role, is_active) "
            "VALUES ('fake','x','Administrator',1)")
        c.commit()
        uid = cur.lastrowid
    finally:
        c.close()
    svc.assign_role(uid, "Reception")
    # Cannot use any rbac.manage-gated admin operation.
    assert _denied(lambda: svc.list_roles_with_permissions(uid))
    assert _denied(lambda: svc.grant_permission(uid, "Reception", "cases.manage"))
    assert _denied(lambda: svc.admin_assign_user_role(uid, uid, "Doctor"))


# --- route-level guard on /admin/roles ------------------------------------

def _dispatch(route, session_user):
    from app.bootstrap import ROUTES, denied_controller
    from app.core.router import Router
    from app.modules.authentication.controller import login_controller
    from app.modules.dashboard.controller import dashboard_controller
    page = MagicMock()
    page.route = route
    page.views = []
    page.session.get.return_value = session_user
    page.overlay = []
    router = Router(page, ROUTES,
                    anonymous_handler=login_controller,
                    fallback_handler=dashboard_controller,
                    has_permission=svc.user_has_permission,
                    denied_handler=denied_controller)
    router.dispatch()
    return page.views[-1].route if page.views else None


def test_admin_roles_route_allowed_for_admin_denied_for_others():
    _fresh_db()
    aid = _admin_id()
    doc = _mk_user("doc", "Doctor")
    assert _dispatch("/admin/roles", {"id": aid}) == "/admin/roles"   # renders
    assert _dispatch("/admin/roles", {"id": doc}) == "/dashboard"     # denied


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
    print("[PASS] all RBAC admin tests")
