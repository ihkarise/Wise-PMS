"""Case Records — controller (router dispatch target for case screens)."""

from app.modules.cases.view import case_view
from app.modules.roles.permissions import CASES_VIEW


def case_controller(page, params, query=""):
    cid_raw = params.get("cid")
    case_id = int(cid_raw) if cid_raw and cid_raw != "new" else None
    return case_view(page, int(params["pid"]), case_id)


ROUTES = [
    # /patient/<pid>/case  ·  /patient/<pid>/case/new  ·  /patient/<pid>/case/<cid>
    (r"^/patient/(?P<pid>\d+)/case(?:/(?P<cid>new|\d+))?$", case_controller,
     CASES_VIEW),
]
