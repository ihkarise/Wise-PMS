"""Wise PMS — Visit Service (Sprint 2).
Narrative first: visit_notes, investigation_notes, prescription_notes are the
heart of the system and are stored exactly as written, never modified.
Structured prescription items are an optional extraction layer for analytics.
"""

import re
from typing import List, Optional

from app.database.db import get_connection
from app.services.audit_service import log_action

# ------------------------------------------------------------------
# Optional prescription intelligence (assists, never restricts)
# ------------------------------------------------------------------
_POTENCY = r"(?:\d+\s*[CXM]\b|\d+\b|CM\b|1M\b|10M\b|50M\b|LM\s*\d*|Q\b|3X|6X|12X|30|200)"
_LINE_RE = re.compile(
    rf"^\s*([A-Za-z][A-Za-z .\-']{{1,40}}?)\s+({_POTENCY})\s*(.*)$",
    re.IGNORECASE,
)
_SKIP_WORDS = (
    "continue", "review", "placebo", "repeat", "follow", "stop", "same",
    "advice", "diet", "report", "after", "next",
)


def extract_prescription_items(prescription_notes: str) -> List[dict]:
    """Best-effort extraction of medicine/potency from free-text prescription.
    The doctor's narrative remains the source of truth."""
    items = []
    for line in (prescription_notes or "").splitlines():
        line = line.strip()
        if not line:
            continue
        first_word = line.split()[0].lower().rstrip(":,")
        if first_word in _SKIP_WORDS:
            continue
        m = _LINE_RE.match(line)
        if m:
            name, potency, rest = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            if name.lower() in _SKIP_WORDS:
                continue
            items.append({
                "medicine_name": name,
                "potency": potency.upper().replace(" ", ""),
                "dosage": rest or None,
                "instructions": None,
            })
    return items


# ------------------------------------------------------------------
# CRUD
# ------------------------------------------------------------------
def create_visit(patient_id: int, data: dict, user_id: int) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO visits (patient_id, case_id, doctor_id, visit_type, "
            "visit_date, visit_notes, investigation_notes, prescription_notes, "
            "followup_date, outcome) "
            "VALUES (?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?, ?, ?)",
            (patient_id, data.get("case_id"), user_id, data.get("visit_type"),
             data.get("visit_date"), data.get("visit_notes"),
             data.get("investigation_notes"), data.get("prescription_notes"),
             data.get("followup_date"), data.get("outcome")),
        )
        visit_id = cur.lastrowid

        for item in extract_prescription_items(data.get("prescription_notes")):
            conn.execute(
                "INSERT INTO prescription_items "
                "(visit_id, medicine_name, potency, dosage, instructions) "
                "VALUES (?, ?, ?, ?, ?)",
                (visit_id, item["medicine_name"], item["potency"],
                 item["dosage"], item["instructions"]),
            )
        conn.commit()
    finally:
        conn.close()
    log_action(user_id, "Visit Created", "visit", visit_id, "")
    return visit_id


def update_visit(visit_id: int, data: dict, user_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE visits SET case_id = ?, visit_type = ?, visit_notes = ?, "
            "investigation_notes = ?, prescription_notes = ?, "
            "followup_date = ?, outcome = ? WHERE id = ?",
            (data.get("case_id"), data.get("visit_type"),
             data.get("visit_notes"), data.get("investigation_notes"),
             data.get("prescription_notes"), data.get("followup_date"),
             data.get("outcome"), visit_id),
        )
        # Re-extract structured items
        conn.execute("DELETE FROM prescription_items WHERE visit_id = ?",
                     (visit_id,))
        for item in extract_prescription_items(data.get("prescription_notes")):
            conn.execute(
                "INSERT INTO prescription_items "
                "(visit_id, medicine_name, potency, dosage, instructions) "
                "VALUES (?, ?, ?, ?, ?)",
                (visit_id, item["medicine_name"], item["potency"],
                 item["dosage"], item["instructions"]),
            )
        conn.commit()
    finally:
        conn.close()
    log_action(user_id, "Visit Updated", "visit", visit_id, "")


def get_visit(visit_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM visits WHERE id = ?", (visit_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def visits_for_patient(patient_id: int) -> List[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT v.*, c.case_title FROM visits v "
            "LEFT JOIN patient_cases c ON c.id = v.case_id "
            "WHERE v.patient_id = ? ORDER BY v.visit_date DESC",
            (patient_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def prescription_items_for_visit(visit_id: int) -> List[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM prescription_items WHERE visit_id = ?", (visit_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def visit_stats() -> dict:
    conn = get_connection()
    try:
        today = conn.execute(
            "SELECT COUNT(*) AS c FROM visits "
            "WHERE DATE(visit_date) = DATE('now', 'localtime')"
        ).fetchone()["c"]
        followups_due = conn.execute(
            "SELECT COUNT(*) AS c FROM visits "
            "WHERE followup_date IS NOT NULL "
            "AND DATE(followup_date) <= DATE('now', 'localtime')"
        ).fetchone()["c"]
        return {"visits_today": today, "followups_due": followups_due}
    finally:
        conn.close()
