"""Patients — controller (router dispatch targets for search/profile/edit)."""

from app.modules.patients.views.profile import edit_view, profile_view
from app.modules.patients.views.search import search_view


def search_controller(page, params=None, query=""):
    return search_view(page)


def profile_controller(page, params, query=""):
    return profile_view(page, int(params["pid"]))


def edit_controller(page, params, query=""):
    return edit_view(page, int(params["pid"]))


ROUTES = [
    (r"^/search$", search_controller),
    (r"^/patient/(?P<pid>\d+)$", profile_controller),
    (r"^/patient/(?P<pid>\d+)/edit$", edit_controller),
]
