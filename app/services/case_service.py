"""Wise PMS — Case Service (Sprint 2).
One patient can have multiple cases (e.g. Migraine, Allergic Rhinitis).
Case notes are narrative-first — never forced into structure.
"""

from typing import List, Optional

from app.database.db import get_connection
from app.services.audit_service import log_action


def create_case(patient_id: int, data: dict, user_id: int) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO patient_cases "
            "(patient_id, case_title, diagnosis, case_notes, status, doctor_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (patient_id, data.get("case_title"), data.get("diagnosis"),
             data.get("case_notes"), data.get("status") or "Open", user_id),
        )
        conn.commit()
        case_id = cur.lastrowid
    finally:
        conn.close()
    log_action(user_id, "Case Created", "case", case_id,
               data.get("case_title") or "")
    return case_id


def update_case(case_id: int, data: dict, user_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE patient_cases SET case_title = ?, diagnosis = ?, "
            "case_notes = ?, status = ? WHERE id = ?",
            (data.get("case_title"), data.get("diagnosis"),
             data.get("case_notes"), data.get("status") or "Open", case_id),
        )
        conn.commit()
    finally:
        conn.close()
    log_action(user_id, "Case Updated", "case", case_id,
               data.get("case_title") or "")


def get_case(case_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM patient_cases WHERE id = ?", (case_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def cases_for_patient(patient_id: int) -> List[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT c.*, "
            " (SELECT COUNT(*) FROM visits v WHERE v.case_id = c.id) AS visit_count "
            "FROM patient_cases c WHERE c.patient_id = ? "
            "ORDER BY c.created_at DESC",
            (patient_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
