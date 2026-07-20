"""Registration — controller (router dispatch target for /register)."""

from app.modules.registration.view import registration_view


def registration_controller(page, params=None, query=""):
    return registration_view(page)


ROUTES = [
    (r"^/register$", registration_controller),
]
