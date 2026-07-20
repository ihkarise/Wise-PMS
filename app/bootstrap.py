"""Wise PMS — Application bootstrap (composition root).

Wires the app together: initialize the database, assemble the route table from
every module's own registration, install the router, and launch the desktop UI.
This is the single place that knows about all modules; everything else stays
decoupled.
"""

import flet as ft

from app.core.database import init_db
from app.core.router import Router
from app.modules.authentication.controller import ROUTES as AUTH_ROUTES
from app.modules.authentication.controller import login_controller
from app.modules.cases.controller import ROUTES as CASE_ROUTES
from app.modules.dashboard.controller import ROUTES as DASHBOARD_ROUTES
from app.modules.dashboard.controller import dashboard_controller
from app.modules.patients.controller import ROUTES as PATIENT_ROUTES
from app.modules.registration.controller import ROUTES as REGISTRATION_ROUTES
from app.modules.visits.controller import ROUTES as VISIT_ROUTES
from app.shared import theme

# Route table assembled from every module's own registration. Adding a module
# means adding its ROUTES here — no conditional logic to edit.
ROUTES = (
    AUTH_ROUTES
    + DASHBOARD_ROUTES
    + REGISTRATION_ROUTES
    + PATIENT_ROUTES
    + CASE_ROUTES
    + VISIT_ROUTES
)


def _start(page: ft.Page) -> None:
    theme.apply_theme(page)
    router = Router(
        page,
        ROUTES,
        anonymous_handler=login_controller,
        fallback_handler=dashboard_controller,
    )
    page.on_route_change = router.dispatch
    page.on_view_pop = router.on_view_pop
    page.go("/login")


def run() -> None:
    """Initialize the database and launch the desktop application."""
    init_db()
    ft.app(target=_start)
