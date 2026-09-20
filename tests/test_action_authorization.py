"""Action-level authorization tests (Sprint 5 / F3, Milestone 4 — ADR-003).

Proves service/controller action-level enforcement: for every protected
operation, an authorized role succeeds, an unauthorized role is denied, and —
critically — the underlying mutation does NOT happen on denial (verified by
inspecting persisted state, not merely that an exception was raised). Also
covers the fail-closed edge cases (inactive / no-role / nonexistent user).

Grants follow the approved matrix (docs/planning/SPRINT5_TECHNICAL_PLAN.md
§5.2); authorization resolves through user_roles, never users.role.
"""

import os
import shutil
import tempfile

import pytest

os.environ.setdefault("WISE_PMS_HOME",
                      tempfile.mkdtemp(prefix="wisepms_actionauthz_"))

from app.modules.roles import permissions as perms  # noqa: E402
from app.modules.roles import service as rsvc  # noqa: E402


def _clear_fs():
    """Remove attachment/backup artifacts this module writes into the shared
    WISE_PMS_HOME so it never pollutes filesystem-sensitive tests (e.g. the
    regression golden's backup-archive file count) that run later in the same
    process. init_db recreates the folders on the next _fresh_db()."""
    from app.config import paths
    for d in (paths.ATTACHMENTS_DIR, paths.BACKUPS_DIR):
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(autouse=True)
def _isolate_fs():
    yield
    _clear_fs()


# --- helpers ---------------------------------------------------------------

def _fresh_db():
    from app.config import paths
    from app.core.database import init_db
    if os.path.exists(paths.DB_PATH):
        os.remove(paths.DB_PATH)
    _clear_fs()
    init_db()


def _conn():
    from app.core.database import get_connection
    return get_connection()


def _admin_id():
    c = _conn()
    try:
        return c.execute("SELECT id FROM users WHERE username='admin'").fetchone()[0]
    finally:
        c.close()


def _mk_user(username, role_name, active=1):
    c = _conn()
    try:
        cur = c.execute(
            "INSERT INTO users (username, password_hash, full_name, role, is_active) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, "x", username.title(), role_name, active),
        )
        c.commit()
        uid = cur.lastrowid
    finally:
        c.close()
    rsvc.assign_role(uid, role_name)
    return uid


def _count(table):
    c = _conn()
    try:
        return c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        c.close()


def _scalar(sql, params=()):
    c = _conn()
    try:
        row = c.execute(sql, params).fetchone()
        return row[0] if row else None
    finally:
        c.close()


def _denied(fn):
    """Call fn; assert it raised AuthorizationError. Returns True on denial."""
    try:
        fn()
        return False
    except rsvc.AuthorizationError:
        return True


# Seed clinical entities as the admin (authorized), returning ids.
def _seed_entities():
    from app.modules.cases.service import create_case
    from app.modules.patients.service import create_patient
    from app.modules.visits.service import create_visit
    aid = _admin_id()
    p = create_patient({"name": "Seed", "age": 30, "gender": "Male"}, aid)
    cid = create_case(p["id"], {"case_title": "Seed", "status": "Open"}, aid)
    vid = create_visit(p["id"], {"case_id": cid, "visit_type": "Walk-In"}, aid)
    return aid, p, cid, vid


# --- patients --------------------------------------------------------------

def test_create_patient_authorized_and_denied_no_mutation():
    from app.modules.patients.service import create_patient
    _fresh_db()
    reception = _mk_user("recep", "Reception")   # has registration.create
    pharmacy = _mk_user("pharm", "Pharmacy")     # lacks it
    before = _count("patients")
    # Authorized:
    create_patient({"name": "A", "age": 1, "gender": "Male"}, reception)
    assert _count("patients") == before + 1
    # Denied — and no new row is created:
    after_auth = _count("patients")
    assert _denied(lambda: create_patient(
        {"name": "Ghost", "age": 2, "gender": "Male"}, pharmacy))
    assert _count("patients") == after_auth  # mutation did NOT happen


def test_update_patient_denied_leaves_row_unchanged():
    from app.modules.patients.service import create_patient, update_patient
    _fresh_db()
    aid = _admin_id()
    pharmacy = _mk_user("pharm", "Pharmacy")
    p = create_patient({"name": "Orig", "age": 5, "gender": "Male",
                        "place": "Kochi"}, aid)
    assert _denied(lambda: update_patient(
        p["id"], {"name": "Orig", "place": "HACKED"}, pharmacy))
    assert _scalar("SELECT place FROM patients WHERE id=?", (p["id"],)) == "Kochi"


def test_deactivate_patient_denied_keeps_patient_active():
    from app.modules.patients.service import create_patient, deactivate_patient
    _fresh_db()
    aid = _admin_id()
    reception = _mk_user("recep", "Reception")  # lacks patients.deactivate
    p = create_patient({"name": "Keep", "age": 9, "gender": "Male"}, aid)
    assert _denied(lambda: deactivate_patient(p["id"], reception))
    assert _scalar("SELECT is_active FROM patients WHERE id=?", (p["id"],)) == 1
    # Authorized (Doctor has it) actually deactivates.
    doctor = _mk_user("doc", "Doctor")
    deactivate_patient(p["id"], doctor)
    assert _scalar("SELECT is_active FROM patients WHERE id=?", (p["id"],)) == 0


# --- cases -----------------------------------------------------------------

def test_create_case_denied_no_mutation_authorized_succeeds():
    from app.modules.cases.service import create_case
    from app.modules.patients.service import create_patient
    _fresh_db()
    aid = _admin_id()
    reception = _mk_user("recep", "Reception")  # lacks cases.manage
    doctor = _mk_user("doc", "Doctor")          # has cases.manage
    p = create_patient({"name": "P", "age": 3, "gender": "Male"}, aid)
    before = _count("patient_cases")
    assert _denied(lambda: create_case(
        p["id"], {"case_title": "X", "status": "Open"}, reception))
    assert _count("patient_cases") == before  # not created
    create_case(p["id"], {"case_title": "Y", "status": "Open"}, doctor)
    assert _count("patient_cases") == before + 1


# --- visits ----------------------------------------------------------------

def test_create_visit_denied_no_mutation():
    from app.modules.visits.service import create_visit
    _fresh_db()
    aid, p, cid, _vid = _seed_entities()
    reception = _mk_user("recep", "Reception")  # lacks visits.manage
    before = _count("visits")
    assert _denied(lambda: create_visit(
        p["id"], {"case_id": cid, "visit_type": "Walk-In"}, reception))
    assert _count("visits") == before  # not created


# --- consultation ----------------------------------------------------------

def test_consultation_edit_denied_no_mutation():
    from app.modules.consultation.service import (open_or_create_draft,
                                                  save_consultation)
    _fresh_db()
    aid, p, cid, _vid = _seed_entities()
    doctor = _mk_user("doc", "Doctor")          # has consultation.edit
    reception = _mk_user("recep", "Reception")  # lacks it
    draft = open_or_create_draft(p["id"], cid, doctor)   # Doctor may open
    # Denied edit does not change the stored field.
    assert _denied(lambda: save_consultation(
        draft["id"], {"chief_complaint": "HACKED"}, reception))
    stored = _scalar("SELECT chief_complaint FROM consultations WHERE id=?",
                     (draft["id"],))
    assert stored != "HACKED"
    # Authorized edit persists.
    save_consultation(draft["id"], {"chief_complaint": "Cough"}, doctor)
    assert _scalar("SELECT chief_complaint FROM consultations WHERE id=?",
                   (draft["id"],)) == "Cough"


# --- attachments -----------------------------------------------------------

def _tmp_file(name="lab.pdf"):
    src = os.path.join(os.environ["WISE_PMS_HOME"], name)
    with open(src, "w") as fh:
        fh.write("x")
    return src


def test_attachment_upload_denied_no_mutation():
    from app.modules.attachments.service import add_attachment
    from app.modules.patients.service import create_patient
    _fresh_db()
    aid = _admin_id()
    pharmacy = _mk_user("pharm", "Pharmacy")  # lacks attachments.upload
    p = create_patient({"name": "P", "age": 4, "gender": "Male"}, aid)
    before = _count("attachments")
    assert _denied(lambda: add_attachment(
        p["id"], p["reg_no"], _tmp_file(), pharmacy))
    assert _count("attachments") == before  # not created


def test_attachment_delete_denied_keeps_row():
    from app.modules.attachments.service import add_attachment, delete_attachment
    from app.modules.patients.service import create_patient
    _fresh_db()
    aid = _admin_id()
    reception = _mk_user("recep", "Reception")  # has upload, lacks delete
    p = create_patient({"name": "P", "age": 4, "gender": "Male"}, aid)
    att = add_attachment(p["id"], p["reg_no"], _tmp_file(), reception)  # upload OK
    before = _count("attachments")
    assert _denied(lambda: delete_attachment(att, reception))
    assert _count("attachments") == before  # still present


# --- settings --------------------------------------------------------------

def test_settings_edit_denied_leaves_settings_unchanged():
    from app.modules.settings.service import (get_clinic_settings,
                                              update_clinic_settings)
    _fresh_db()
    doctor = _mk_user("doc", "Doctor")  # lacks settings.edit
    original = get_clinic_settings()["clinic_name"]
    assert _denied(lambda: update_clinic_settings(
        {"clinic_name": "HACKED CLINIC"}, doctor))
    assert get_clinic_settings()["clinic_name"] == original
    # Admin may edit.
    update_clinic_settings({"clinic_name": "Real Clinic"}, _admin_id())
    assert get_clinic_settings()["clinic_name"] == "Real Clinic"


# --- backup (enforced at the shell action boundary) ------------------------

def test_backup_permission_decision_matches_matrix():
    _fresh_db()
    aid = _admin_id()
    doctor = _mk_user("doc", "Doctor")
    # The shell's do_backup calls require_permission(user, BACKUP_RUN) before
    # backup_now(); backup_now itself takes no user. Verify that decision.
    rsvc.require_permission(aid, perms.BACKUP_RUN)          # admin: no raise
    assert _denied(lambda: rsvc.require_permission(doctor, perms.BACKUP_RUN))


# --- fail-closed edge cases (representative op) ----------------------------

def test_action_fail_closed_for_inactive_norole_nonexistent_users():
    from app.modules.cases.service import create_case
    from app.modules.patients.service import create_patient
    _fresh_db()
    aid = _admin_id()
    p = create_patient({"name": "P", "age": 6, "gender": "Male"}, aid)
    before = _count("patient_cases")

    inactive = _mk_user("inact", "Doctor", active=0)  # has grant but inactive
    norole = None
    c = _conn()
    try:
        cur = c.execute(
            "INSERT INTO users (username, password_hash, role, is_active) "
            "VALUES ('norole','x','Doctor',1)")  # legacy role only, no binding
        c.commit()
        norole = cur.lastrowid
    finally:
        c.close()

    for uid in (inactive, norole, 999999):
        assert _denied(lambda uid=uid: create_case(
            p["id"], {"case_title": "Z", "status": "Open"}, uid))
    assert _count("patient_cases") == before  # none created


def test_users_role_does_not_grant_action_access():
    from app.modules.settings.service import (get_clinic_settings,
                                              update_clinic_settings)
    _fresh_db()
    # Legacy users.role='Administrator' but user_roles binding = Reception.
    c = _conn()
    try:
        cur = c.execute(
            "INSERT INTO users (username, password_hash, role, is_active) "
            "VALUES ('fake','x','Administrator',1)")
        c.commit()
        uid = cur.lastrowid
    finally:
        c.close()
    rsvc.assign_role(uid, "Reception")
    original = get_clinic_settings()["clinic_name"]
    assert _denied(lambda: update_clinic_settings(
        {"clinic_name": "HACKED"}, uid))
    assert get_clinic_settings()["clinic_name"] == original


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            _clear_fs()
            print(f"[PASS] {name}")
    print("[PASS] all action-authorization tests")
