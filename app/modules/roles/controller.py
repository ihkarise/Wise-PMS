"""Roles / RBAC — controller (Administrator-only RBAC administration surface).

Router dispatch target for the minimum RBAC administration screen (Sprint 5 /
F3, Milestone 5). The route is gated by `rbac.manage` at the router (M3
pattern); the underlying mutations are independently gated at the service layer
(M4 pattern) — defense in depth. This is NOT the F2 clinic-profile Settings UI
(ADR-002 §6.6) and NOT full user management (F4).
"""

from app.modules.roles.permissions import RBAC_MANAGE
from app.modules.roles.view import rbac_admin_view


def rbac_admin_controller(page, params=None, query=""):
    return rbac_admin_view(page)


ROUTES = [
    (r"^/admin/roles$", rbac_admin_controller, RBAC_MANAGE),
]
