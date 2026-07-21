"""Consultation domain tests (Sprint 2 / ADR-001 Option C).

Exercises the consultation aggregate + lifecycle service against a seeded,
isolated database: draft -> in_progress -> completed, the 1:1 visit invariant,
illegal-transition guards, audit rows, and draft isolation from the read model.
No display needed.
"""

import os
import tempfile

os.environ.setdefault("WISE_PMS_HOME",
                      tempfile.mkdtemp(prefix="wisepms_consult_"))


def _seed():
    from app.config import paths
    from app.core.database import init_db
    from app.modules.authentication.service import authenticate
    from app.modules.cases.service import create_case
    from app.modules.patients.service import create_patient

    if os.path.exists(paths.DB_PATH):
        os.remove(paths.DB_PATH)
    init_db()
    uid = authenticate("admin", "admin123")["id"]
    p = create_patient({"name": "Rt Test", "age": 30, "gender": "Male"}, uid)
    cid = create_case(p["id"], {"case_title": "Asthma", "status": "Open"}, uid)
    return uid, p["id"], cid


def _audit_actions():
    from app.core.database import get_connection
    conn = get_connection()
    try:
        return [r["action_type"] for r in conn.execute(
            "SELECT action_type FROM audit_logs ORDER BY id")]
    finally:
        conn.close()


def test_open_reuses_single_draft_per_case():
    from app.modules.consultation import service as cs
    uid, pid, cid = _seed()
    a = cs.open_or_create_draft(pid, cid, uid)
    b = cs.open_or_create_draft(pid, cid, uid)
    assert a["status"] == "draft"
    assert a["id"] == b["id"]          # reused, not duplicated
    assert a["visit_id"] == b["visit_id"]


def test_lifecycle_draft_to_inprogress_to_completed():
    from app.modules.consultation import service as cs
    uid, pid, cid = _seed()
    c = cs.open_or_create_draft(pid, cid, uid)
    saved = cs.save_consultation(c["id"], {"chief_complaint": "Wheeze",
                                           "diagnosis": "Asthma"}, uid)
    assert saved["status"] == "in_progress"
    assert saved["chief_complaint"] == "Wheeze"
    done = cs.complete_consultation(c["id"], uid)
    assert done["status"] == "completed"
    # Idempotent.
    assert cs.complete_consultation(c["id"], uid)["status"] == "completed"


def test_cannot_edit_completed():
    from app.modules.consultation import service as cs
    uid, pid, cid = _seed()
    c = cs.open_or_create_draft(pid, cid, uid)
    cs.complete_consultation(c["id"], uid)
    try:
        cs.save_consultation(c["id"], {"remarks": "late edit"}, uid)
        assert False, "expected ConsultationLifecycleError"
    except cs.ConsultationLifecycleError:
        pass


def test_illegal_transition_rejected():
    from app.modules.consultation import service as cs
    uid, pid, cid = _seed()
    c = cs.open_or_create_draft(pid, cid, uid)
    # completed -> completed handled by idempotent path; locked from draft is illegal
    try:
        cs.lock_consultation(c["id"], uid)   # draft -> locked not allowed
        assert False, "expected ConsultationLifecycleError"
    except cs.ConsultationLifecycleError:
        pass


def test_one_consultation_per_visit_invariant():
    import sqlite3

    from app.modules.consultation.repository import ConsultationRepository
    uid, pid, cid = _seed()
    from app.modules.consultation import service as cs
    c = cs.open_or_create_draft(pid, cid, uid)
    repo = ConsultationRepository()
    try:
        repo.create_draft(c["visit_id"], pid, cid)  # duplicate visit_id
        assert False, "expected IntegrityError"
    except sqlite3.IntegrityError:
        pass


def test_drafts_excluded_from_read_model():
    from app.modules.consultation import service as cs
    from app.modules.consultation.repository import ConsultationRepository
    uid, pid, cid = _seed()
    c = cs.open_or_create_draft(pid, cid, uid)
    repo = ConsultationRepository()
    assert repo.for_patient(pid) == []          # draft not in completed read model
    cs.save_consultation(c["id"], {"history": "x"}, uid)
    cs.complete_consultation(c["id"], uid)
    completed = repo.for_patient(pid)
    assert len(completed) == 1 and completed[0]["status"] == "completed"


def test_transitions_are_audited():
    from app.modules.consultation import service as cs
    uid, pid, cid = _seed()
    c = cs.open_or_create_draft(pid, cid, uid)
    cs.save_consultation(c["id"], {"diagnosis": "Asthma"}, uid)
    cs.complete_consultation(c["id"], uid)
    actions = _audit_actions()
    for expected in ("Consultation Started", "Consultation Updated",
                     "Consultation Completed"):
        assert expected in actions, expected


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
    print("[PASS] all consultation domain tests")
