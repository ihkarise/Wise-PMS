"""Router behavior test.

Pins the routing contract that previously lived in main.py: the session guard,
static and dynamic route matching, path/param parsing (including the ``new``
sentinel and the ``?case=`` query), and the unmatched-route fallback. Runs
against a fake page so no display is needed.
"""

import os
import tempfile

os.environ.setdefault("WISE_PMS_HOME",
                      tempfile.mkdtemp(prefix="wisepms_router_"))


def _dispatch(route, user, pid):
    from unittest.mock import MagicMock

    from app.bootstrap import ROUTES
    from app.core.router import Router
    from app.modules.authentication.controller import login_controller
    from app.modules.dashboard.controller import dashboard_controller

    page = MagicMock()
    page.route = route
    page.views = []
    page.session.get.return_value = user
    page.client_storage.get.return_value = None
    page.overlay = []

    router = Router(page, ROUTES,
                    anonymous_handler=login_controller,
                    fallback_handler=dashboard_controller)
    router.dispatch()
    return page.views[-1].route if page.views else None


def _setup():
    from app.config import paths
    from app.core.database import init_db
    from app.modules.authentication.service import authenticate
    from app.modules.patients.service import create_patient

    if os.path.exists(paths.DB_PATH):
        os.remove(paths.DB_PATH)
    init_db()
    uid = authenticate("admin", "admin123")["id"]
    p = create_patient({"name": "Rt Test", "age": 22, "gender": "Female"}, uid)
    return uid, p["id"]


def test_router_contract():
    uid, pid = _setup()
    user = {"id": uid, "full_name": "Administrator", "role": "Admin",
            "username": "admin"}

    cases = [
        ("/login", None, "/login"),
        ("/dashboard", None, "/login"),          # guard: anonymous -> login
        ("/dashboard", user, "/dashboard"),
        ("/register", user, "/register"),
        ("/search", user, "/search"),
        (f"/patient/{pid}", user, f"/patient/{pid}"),
        (f"/patient/{pid}/edit", user, f"/patient/{pid}/edit"),
        (f"/patient/{pid}/case/new", user, f"/patient/{pid}/case"),
        (f"/patient/{pid}/case/1", user, f"/patient/{pid}/case"),
        (f"/patient/{pid}/visit/new?case=1", user, f"/patient/{pid}/visit"),
        ("/totally/unknown", user, "/dashboard"),  # fallback
    ]
    for route, who, expected in cases:
        assert _dispatch(route, who, pid) == expected, f"route {route!r}"


if __name__ == "__main__":
    test_router_contract()
    print("[PASS] router contract")
