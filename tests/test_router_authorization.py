"""Router-level authorization tests (Sprint 5 / F3, Milestone 3 — ADR-003).

Covers the router permission guard: fail-closed enforcement after the session
guard, per-role access against the approved matrix, and route-coverage of the
real assembled route table. Guard-behavior tests drive a synthetic single-route
Router with the *real* ``user_has_permission`` so the check is exercised end to
end without depending on individual screen handlers rendering under a mock.
"""

import os
import tempfile
from unittest.mock import MagicMock

os.environ.setdefault("WISE_PMS_HOME",
                      tempfile.mkdtemp(prefix="wisepms_routerauthz_"))

from app.modules.roles import permissions as reg  # noqa: E402
from app.modules.roles import service as rsvc  # noqa: E402

GRANTS = {
    "Administrator": set(reg.ALL_PERMISSIONS),
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

# Every route the application assembles, keyed by its handler name, with the
# permission it must require (None = public/session-only). Derived from the
# approved matrix and the routes that actually exist today.
EXPECTED_BY_HANDLER = {
    "login_controller": None,
    "dashboard_controller": reg.DASHBOARD_VIEW,
    "registration_controller": reg.REGISTRATION_CREATE,
    "search_controller": reg.PATIENTS_VIEW,
    "profile_controller": reg.PATIENTS_VIEW,
    "edit_controller": reg.PATIENTS_EDIT,
    "case_controller": reg.CASES_VIEW,
    "visit_controller": reg.VISITS_VIEW,
    "workspace_controller": reg.CONSULTATION_VIEW,
    "settings_controller": reg.SETTINGS_EDIT,
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


def _dispatch_guarded(session_user, permission):
    """Dispatch a synthetic '/x' route requiring ``permission`` as
    ``session_user``. Returns 'HANDLER' (allowed), 'DENIED' (permission guard),
    or 'LOGIN' (session guard)."""
    from app.core.router import Router

    def _view(name):
        v = MagicMock()
        v.route = name
        return v

    def handler(page, params, query):
        return _view("HANDLER")

    def denied(page, params, query):
        return _view("DENIED")

    def anon(page, params, query):
        return _view("LOGIN")

    page = MagicMock()
    page.route = "/x"
    page.views = []
    page.session.get.return_value = session_user
    page.overlay = []

    router = Router(
        page,
        [(r"^/x$", handler, permission)],
        anonymous_handler=anon,
        fallback_handler=denied,
        has_permission=rsvc.user_has_permission,
        denied_handler=denied,
    )
    router.dispatch()
    return page.views[-1].route


# --- authentication precedence --------------------------------------------

def test_unauthenticated_request_hits_session_guard_first():
    _fresh_db()
    assert _dispatch_guarded(None, reg.DASHBOARD_VIEW) == "LOGIN"


# --- fail-closed permission guard -----------------------------------------

def test_authorized_user_reaches_handler():
    _fresh_db()
    aid = _admin_id()
    assert _dispatch_guarded({"id": aid}, reg.SETTINGS_EDIT) == "HANDLER"


def test_unauthorized_user_is_denied():
    _fresh_db()
    doc = _user_with_role("doc1", "Doctor")
    assert _dispatch_guarded({"id": doc}, reg.SETTINGS_EDIT) == "DENIED"


def test_unknown_permission_metadata_fails_closed():
    _fresh_db()
    aid = _admin_id()
    assert _dispatch_guarded({"id": aid}, "does.not.exist") == "DENIED"


def test_inactive_user_is_denied():
    _fresh_db()
    uid = _insert_user("ghost", legacy_role="Administrator", active=0)
    rsvc.assign_role(uid, "Administrator")
    assert _dispatch_guarded({"id": uid}, reg.DASHBOARD_VIEW) == "DENIED"


def test_user_without_role_binding_is_denied():
    _fresh_db()
    uid = _insert_user("norole", legacy_role="Doctor")  # legacy hint only
    assert _dispatch_guarded({"id": uid}, reg.DASHBOARD_VIEW) == "DENIED"


def test_users_role_cannot_grant_access():
    _fresh_db()
    # Legacy users.role='Administrator' but bound to Reception via user_roles.
    uid = _insert_user("fakeadmin", legacy_role="Administrator")
    rsvc.assign_role(uid, "Reception")
    assert _dispatch_guarded({"id": uid}, reg.RBAC_MANAGE) == "DENIED"
    assert _dispatch_guarded({"id": uid}, reg.PATIENTS_VIEW) == "HANDLER"


def test_administrator_access_is_from_seeded_permissions_not_a_bypass():
    _fresh_db()
    aid = _admin_id()
    # Admin passes real permissions...
    assert _dispatch_guarded({"id": aid}, reg.RBAC_MANAGE) == "HANDLER"
    # ...but an unknown key is still denied — proving there is no is_admin bypass.
    assert _dispatch_guarded({"id": aid}, "totally.unknown") == "DENIED"


def test_session_only_route_passes_for_authenticated_user():
    _fresh_db()
    aid = _admin_id()
    assert _dispatch_guarded({"id": aid}, None) == "HANDLER"


# --- per-role matrix (representative, all five roles) ---------------------

def test_route_access_matches_matrix_for_all_roles():
    _fresh_db()
    # Representative route-level permissions actually used by the router.
    route_perms = [
        reg.DASHBOARD_VIEW, reg.PATIENTS_VIEW, reg.REGISTRATION_CREATE,
        reg.PATIENTS_EDIT, reg.CASES_VIEW, reg.VISITS_VIEW,
        reg.CONSULTATION_VIEW, reg.SETTINGS_EDIT,
    ]
    for role, granted in GRANTS.items():
        if role == "Administrator":
            uid = _admin_id()
        else:
            uid = _user_with_role(f"user_{role.lower()}", role)
        for perm in route_perms:
            expected = "HANDLER" if perm in granted else "DENIED"
            assert _dispatch_guarded({"id": uid}, perm) == expected, (role, perm)


# --- route coverage on the real assembled table ---------------------------

def test_every_route_has_intended_permission_metadata():
    from app.bootstrap import ROUTES
    actual = {h.__name__: perm for _pat, h, perm in ROUTES}
    assert actual == EXPECTED_BY_HANDLER


def test_only_login_is_public_all_others_protected_and_known():
    from app.bootstrap import ROUTES
    for pattern, handler, perm in ROUTES:
        if pattern == r"^/login$":
            assert perm is None, "login must be public"
        else:
            assert perm is not None, f"unprotected route: {pattern}"
            assert perm in reg.ALL_PERMISSIONS, f"unknown permission: {perm}"


def test_route_metadata_uses_approved_registry_keys_only():
    from app.bootstrap import ROUTES
    used = {perm for _pat, _h, perm in ROUTES if perm is not None}
    assert used <= set(reg.ALL_PERMISSIONS)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
    print("[PASS] all router-authorization tests")
