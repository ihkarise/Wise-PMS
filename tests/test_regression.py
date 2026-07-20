"""Behavioral regression golden test for Wise PMS.

This test pins the *observable behavior* of the entire service layer. It runs
against a throwaway data directory (via the WISE_PMS_HOME override) and compares
a deterministic snapshot of auth -> patients -> search -> cases -> visits ->
prescription extraction -> timeline -> attachments -> backup -> audit against a
golden string.

It exists to make the architecture refactor safe: the structure of the code may
change from stage to stage, but this snapshot must stay byte-identical.

Run standalone:   python tests/test_regression.py
Run with pytest:  pytest -q tests/
"""

import os
import tempfile
import zipfile

# WISE_PMS_HOME must be set BEFORE any app import so all runtime paths resolve
# into an isolated temp directory and the real clinic data is never touched.
os.environ.setdefault("WISE_PMS_HOME",
                      tempfile.mkdtemp(prefix="wisepms_regression_"))
_TMP_HOME = os.environ["WISE_PMS_HOME"]


def build_snapshot():
    lines = []

    def p(*a):
        lines.append(" ".join(str(x) for x in a))

    # Start from a clean database so the snapshot is order-independent when the
    # suite shares one isolated home directory.
    from app.config import paths
    from app.core.database import get_connection, init_db
    if os.path.exists(paths.DB_PATH):
        os.remove(paths.DB_PATH)
    init_db()

    # 1. Schema
    c = get_connection()
    tables = [r["name"] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    p("TABLES:", ",".join(tables))
    idx = [r["name"] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='index' "
        "AND name LIKE 'idx_%' ORDER BY name")]
    p("INDEXES:", ",".join(idx))
    p("ADMIN:", [dict(x) for x in c.execute(
        "SELECT username, full_name, role, is_active FROM users")])
    p("SETTINGS_COUNT:", c.execute(
        "SELECT COUNT(*) c FROM settings").fetchone()["c"])
    c.close()

    # 2. Authentication
    from app.modules.authentication.service import authenticate
    p("AUTH_ok:", (authenticate("admin", "admin123") or {}).get("username"))
    p("AUTH_bad:", authenticate("admin", "wrong"))
    p("AUTH_empty:", authenticate("", ""))
    uid = authenticate("admin", "admin123")["id"]

    # 3. Patients
    from app.modules.patients import service as ps
    a = ps.create_patient({"name": "Alice Kumar", "age": 30, "gender": "Female",
                           "phone": "9990001111", "place": "Kochi"}, uid)
    b = ps.create_patient({"name": "Bob Nair", "age": 45, "gender": "Male",
                           "phone": "8887776666", "place": "Trivandrum"}, uid)
    p("REG_NOS:", a["reg_no"], b["reg_no"])
    p("SEARCH_name:", [x["reg_no"] for x in ps.search_patients("Alice")])
    p("SEARCH_phone:", [x["reg_no"] for x in ps.search_patients("8887")])
    p("SEARCH_regno:", [x["reg_no"] for x in ps.search_patients("P000002")])
    p("SEARCH_place:", sorted(x["reg_no"] for x in ps.search_patients("Kochi")))
    p("STATS:", ps.patient_stats())
    ps.update_patient(a["id"], {**a, "place": "Ernakulam"}, uid)
    p("AFTER_UPDATE_place:", ps.get_patient(a["id"])["place"])

    # 4. Cases
    from app.modules.cases import service as cs
    cid = cs.create_case(a["id"], {"case_title": "Migraine",
                                   "diagnosis": "Chronic",
                                   "case_notes": "long notes",
                                   "status": "Open"}, uid)
    p("CASE_ID:", cid)
    p("CASES_FOR_PATIENT:", [(x["case_title"], x["visit_count"])
                             for x in cs.cases_for_patient(a["id"])])

    # 5. Visits + prescription extraction
    from app.modules.visits import service as vs
    rx = "Bell 200\nBry 30 TDS\nContinue medicine\nReview after 15 days\nNux Vomica 1M"
    items = vs.extract_prescription_items(rx)
    p("EXTRACT:", [(i["medicine_name"], i["potency"], i["dosage"])
                   for i in items])
    vid = vs.create_visit(a["id"], {"case_id": cid, "visit_type": "Walk-In",
                                    "visit_notes": "Better",
                                    "prescription_notes": rx,
                                    "followup_date": "2020-01-01",
                                    "outcome": "Improving"}, uid)
    p("VISIT_ID:", vid)
    p("RX_ITEMS_STORED:", [(i["medicine_name"], i["potency"])
                           for i in vs.prescription_items_for_visit(vid)])
    p("VISITS_FOR_PATIENT:", [(x["id"], x["case_title"])
                              for x in vs.visits_for_patient(a["id"])])
    p("VISIT_STATS:", vs.visit_stats())
    p("CASE_VISIT_COUNT_NOW:", cs.cases_for_patient(a["id"])[0]["visit_count"])

    # 6. Timeline
    from app.modules.timeline import service as ts
    tl = ts.timeline_for_patient(a["id"])
    p("TIMELINE_KINDS:", [e["kind"] for e in tl])
    p("TIMELINE_TITLES:", [e["title"] for e in tl])

    # 7. Attachments
    from app.modules.attachments import service as at
    src = os.path.join(_TMP_HOME, "lab.pdf")
    with open(src, "w") as fh:
        fh.write("dummy")
    aid = at.add_attachment(a["id"], a["reg_no"], src, uid)
    p("ATTACH_ID:", aid)
    p("ATTACH_LIST:", [(x["file_name"], x["file_type"])
                       for x in at.attachments_for_patient(a["id"])])

    # 8. Backup
    from app.modules.backup import service as bk
    bp = bk.backup_now()
    with zipfile.ZipFile(bp) as z:
        names = sorted(z.namelist())
    p("BACKUP_HAS_DB:", "wise_pms.db" in names)
    p("BACKUP_FILE_COUNT:", len(names))

    # 9. Audit trail
    c = get_connection()
    acts = [r["action_type"] for r in c.execute(
        "SELECT action_type FROM audit_logs ORDER BY id")]
    p("AUDIT_ACTIONS:", ",".join(acts))
    c.close()

    return "\n".join(lines)


EXPECTED = """\
TABLES: attachments,audit_logs,patient_cases,patients,prescription_items,schema_version,settings,sqlite_sequence,users,visits
INDEXES: idx_attach_patient,idx_case_patient,idx_patient_name,idx_patient_phone,idx_patient_place,idx_patient_regno,idx_visit_case,idx_visit_date,idx_visit_patient
ADMIN: [{'username': 'admin', 'full_name': 'Administrator', 'role': 'Admin', 'is_active': 1}]
SETTINGS_COUNT: 1
AUTH_ok: admin
AUTH_bad: None
AUTH_empty: None
REG_NOS: P000001 P000002
SEARCH_name: ['P000001']
SEARCH_phone: ['P000002']
SEARCH_regno: ['P000002']
SEARCH_place: ['P000001']
STATS: {'total': 2, 'today': 2}
AFTER_UPDATE_place: Ernakulam
CASE_ID: 1
CASES_FOR_PATIENT: [('Migraine', 0)]
EXTRACT: [('Bell', '200', None), ('Bry', '30', 'TDS'), ('Nux Vomica', '1M', None)]
VISIT_ID: 1
RX_ITEMS_STORED: [('Bell', '200'), ('Bry', '30'), ('Nux Vomica', '1M')]
VISITS_FOR_PATIENT: [(1, 'Migraine')]
VISIT_STATS: {'visits_today': 1, 'followups_due': 1}
CASE_VISIT_COUNT_NOW: 1
TIMELINE_KINDS: ['visit', 'case']
TIMELINE_TITLES: ['Visit — Migraine', 'Case Opened — Migraine']
ATTACH_ID: 1
ATTACH_LIST: [('lab.pdf', 'PDF')]
BACKUP_HAS_DB: True
BACKUP_FILE_COUNT: 2
AUDIT_ACTIONS: User Login,User Login,Patient Created,Patient Created,Patient Updated,Case Created,Visit Created,Attachment Uploaded"""


def test_regression_snapshot():
    assert build_snapshot() == EXPECTED


if __name__ == "__main__":
    snap = build_snapshot()
    print(snap)
    if snap == EXPECTED:
        print("\n[PASS] snapshot matches golden baseline")
    else:
        print("\n[FAIL] snapshot DIVERGED from golden baseline")
        raise SystemExit(1)
