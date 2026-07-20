"""Dashboard — controller (router dispatch target for /dashboard)."""

from app.modules.dashboard.view import dashboard_view


def dashboard_controller(page, params=None, query=""):
    return dashboard_view(page)


ROUTES = [
    (r"^/dashboard$", dashboard_controller),
]
