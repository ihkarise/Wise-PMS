"""Authentication — controller (router dispatch target for /login)."""

from app.modules.authentication.view import login_view


def login_controller(page, params=None, query=""):
    return login_view(page)


ROUTES = [
    (r"^/login$", login_controller),
]
