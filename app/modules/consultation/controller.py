"""Consultation Workspace — controller (router dispatch target).

Parses the workspace route, resolves the optional draft-visit sentinel and the
``?section=`` deep-link, and hands off to the view. No business logic lives here
— it orchestrates only (arch rule 4).
"""

from app.modules.consultation.service import open_or_create_draft
from app.modules.consultation.view import workspace_view


def workspace_controller(page, params, query=""):
    pid = int(params["pid"])
    cid = int(params["cid"])

    vid_raw = params.get("vid")
    visit_id = int(vid_raw) if vid_raw and vid_raw not in (None, "new") else None

    # Ensure an open draft consultation exists for this case (create-on-open,
    # reused on reopen). A concrete /visit/<vid> in the route takes precedence.
    if visit_id is None:
        user = page.session.get("user") or {}
        draft = open_or_create_draft(pid, cid, user.get("id"))
        visit_id = draft["visit_id"]

    section = ""
    for part in query.split("&"):
        if part.startswith("section="):
            section = part.split("=", 1)[1]
            break

    return workspace_view(page, pid, cid, visit_id, section=section)


ROUTES = [
    # /patient/<pid>/case/<cid>/workspace
    #   · …/workspace/visit/new   (open on a new draft visit)
    #   · …/workspace/visit/<vid> (reopen an existing visit)
    (r"^/patient/(?P<pid>\d+)/case/(?P<cid>\d+)/workspace"
     r"(?:/visit/(?P<vid>new|\d+))?$", workspace_controller),
]
