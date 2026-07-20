"""Wise PMS — Patient Service (Sprint 1)."""

from typing import List, Optional

from app.database.db import get_connection
from app.services.audit_service import log_action

PATIENT_FIELDS = [
    "name", "gender", "age", "dob", "phone", "whatsapp", "email",
    "address", "place", "occupation", "blood_group", "photo_path",
    "doctor", "consultation_type", "notes",
]


def _next_reg_no(conn) -> str:
    """Auto-generated registration number: P000001, P000002, ..."""
    row = conn.execute("SELECT MAX(id) AS m FROM patients").fetchone()
    next_id = (row["m"] or 0) + 1
    while True:
        reg_no = f"P{next_id:06d}"
        exists = conn.execute(
            "SELECT 1 FROM patients WHERE reg_no = ?", (reg_no,)
        ).fetchone()
        if not exists:
            return reg_no
        next_id += 1


def create_patient(data: dict, user_id: int) -> dict:
    """Create a patient. Returns the saved patient (with reg_no)."""
    conn = get_connection()
    try:
        reg_no = _next_reg_no(conn)
        values = [data.get(f) for f in PATIENT_FIELDS]
        cur = conn.execute(
            f"INSERT INTO patients (reg_no, {', '.join(PATIENT_FIELDS)}) "
            f"VALUES (?, {', '.join('?' * len(PATIENT_FIELDS))})",
            [reg_no] + values,
        )
        conn.commit()
        patient_id = cur.lastrowid
    finally:
        conn.close()

    log_action(user_id, "Patient Created", "patient", patient_id,
               f"{reg_no} — {data.get('name', '')}")
    return get_patient(patient_id)


def update_patient(patient_id: int, data: dict, user_id: int) -> None:
    conn = get_connection()
    try:
        sets = ", ".join(f"{f} = ?" for f in PATIENT_FIELDS)
        conn.execute(
            f"UPDATE patients SET {sets} WHERE id = ?",
            [data.get(f) for f in PATIENT_FIELDS] + [patient_id],
        )
        conn.commit()
    finally:
        conn.close()

    log_action(user_id, "Patient Updated", "patient", patient_id,
               f"Updated {data.get('name', '')}")


def deactivate_patient(patient_id: int, user_id: int) -> None:
    """Soft delete — patients are never physically removed."""
    conn = get_connection()
    try:
        conn.execute("UPDATE patients SET is_active = 0 WHERE id = ?", (patient_id,))
        conn.commit()
    finally:
        conn.close()
    log_action(user_id, "Patient Deactivated", "patient", patient_id, "")


def get_patient(patient_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def search_patients(query: str, limit: int = 50) -> List[dict]:
    """Real-time search on Name, Phone, Reg No, Place. Active patients only."""
    query = (query or "").strip()
    conn = get_connection()
    try:
        if not query:
            rows = conn.execute(
                "SELECT * FROM patients WHERE is_active = 1 "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        else:
            like = f"%{query}%"
            rows = conn.execute(
                "SELECT * FROM patients WHERE is_active = 1 AND ("
                "  name LIKE ? OR phone LIKE ? OR reg_no LIKE ? OR place LIKE ?"
                ") ORDER BY name COLLATE NOCASE LIMIT ?",
                (like, like, like, like, limit),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def recent_patients(limit: int = 10) -> List[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM patients WHERE is_active = 1 "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def patient_stats() -> dict:
    conn = get_connection()
    try:
        total = conn.execute(
            "SELECT COUNT(*) AS c FROM patients WHERE is_active = 1"
        ).fetchone()["c"]
        today = conn.execute(
            "SELECT COUNT(*) AS c FROM patients "
            "WHERE is_active = 1 AND DATE(created_at) = DATE('now', 'localtime')"
        ).fetchone()["c"]
        return {"total": total, "today": today}
    finally:
        conn.close()
