"""Registration — controller (router dispatch target for /register)."""

from app.modules.registration.view import registration_view
from app.modules.roles.permissions import REGISTRATION_CREATE


def registration_controller(page, params=None, query=""):
    return registration_view(page)


ROUTES = [
    (r"^/register$", registration_controller, REGISTRATION_CREATE),
]
