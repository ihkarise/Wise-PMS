"""Visits — controller (router dispatch target for visit screens)."""

from app.modules.visits.view import visit_view


def visit_controller(page, params, query=""):
    pre_case = None
    if query.startswith("case="):
        try:
            pre_case = int(query.split("=", 1)[1])
        except ValueError:
            pre_case = None
    vid_raw = params.get("vid")
    visit_id = int(vid_raw) if vid_raw and vid_raw != "new" else None
    return visit_view(page, int(params["pid"]), visit_id,
                      preselected_case=pre_case)


ROUTES = [
    # /patient/<pid>/visit  ·  /patient/<pid>/visit/new  ·  /patient/<pid>/visit/<vid>
    (r"^/patient/(?P<pid>\d+)/visit(?:/(?P<vid>new|\d+))?$", visit_controller),
]
