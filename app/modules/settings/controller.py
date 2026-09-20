"""Settings — controller (router dispatch target for /settings)."""

from app.modules.roles.permissions import SETTINGS_EDIT
from app.modules.settings.view import settings_view


def settings_controller(page, params=None, query=""):
    return settings_view(page)


ROUTES = [
    (r"^/settings$", settings_controller, SETTINGS_EDIT),
]
