"""Authentication — controller (router dispatch target for /login)."""

from app.modules.authentication.view import login_view


def login_controller(page, params=None, query=""):
    return login_view(page)


ROUTES = [
    # Public / session-only: no permission required (the login screen itself).
    (r"^/login$", login_controller, None),
]
