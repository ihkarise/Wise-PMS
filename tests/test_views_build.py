"""View construction smoke test.

Builds every Flet screen against a fake page and a seeded database, asserting
each returns an ``ft.View`` without raising. This catches build-time breakage
(imports, helper signatures, shared-widget calls) that a display-less
environment otherwise can't verify. Event handlers are not exercised — they
require a live Flet runtime.
"""

import os
import tempfile

os.environ.setdefault("WISE_PMS_HOME",
                      tempfile.mkdtemp(prefix="wisepms_views_"))


def _seed():
    from app.config import paths
    from app.core.database import init_db
    from app.modules.attachments.service import add_attachment
    from app.modules.authentication.service import authenticate
    from app.modules.cases.service import create_case
    from app.modules.patients.service import create_patient
    from app.modules.visits.service import create_visit

    if os.path.exists(paths.DB_PATH):
        os.remove(paths.DB_PATH)
    init_db()

    uid = authenticate("admin", "admin123")["id"]
    patient = create_patient({"name": "Test Patient", "age": 40,
                              "gender": "Male", "phone": "9990001111",
                              "place": "Kochi"}, uid)
    case_id = create_case(patient["id"], {"case_title": "Migraine",
                                          "status": "Open"}, uid)
    visit_id = create_visit(patient["id"], {"case_id": case_id,
                                            "visit_notes": "Better",
                                            "prescription_notes": "Bell 200",
                                            "followup_date": "2020-01-01",
                                            "outcome": "Improving"}, uid)
    src = os.path.join(os.environ["WISE_PMS_HOME"], "lab.pdf")
    with open(src, "w") as fh:
        fh.write("x")
    add_attachment(patient["id"], patient["reg_no"], src, uid)
    return uid, patient["id"], case_id, visit_id


def _fake_page(uid):
    from unittest.mock import MagicMock
    page = MagicMock()
    page.session.get.return_value = {"id": uid, "full_name": "Administrator",
                                     "role": "Admin", "username": "admin"}
    page.client_storage.get.return_value = None
    page.overlay = []
    return page


def test_all_views_build():
    import flet as ft

    from app.modules.authentication.view import login_view
    from app.modules.cases.view import case_view
    from app.modules.dashboard.view import dashboard_view
    from app.modules.patients.views.profile import edit_view, profile_view
    from app.modules.patients.views.search import search_view
    from app.modules.registration.view import registration_view
    from app.modules.visits.view import visit_view

    uid, pid, cid, vid = _seed()

    def page():
        return _fake_page(uid)

    scenarios = [
        login_view(page()),
        dashboard_view(page()),
        registration_view(page()),
        search_view(page()),
        profile_view(page(), pid),
        profile_view(page(), 999999),          # not-found path
        edit_view(page(), pid),
        case_view(page(), pid, None),           # new case
        case_view(page(), pid, cid),            # existing case
        visit_view(page(), pid, None),          # new visit
        visit_view(page(), pid, None, preselected_case=cid),
        visit_view(page(), pid, vid),           # existing visit
    ]
    for v in scenarios:
        assert isinstance(v, ft.View)


if __name__ == "__main__":
    test_all_views_build()
    print("[PASS] all views build")
