"""Wise PMS — Timeline Service (Sprint 2).
The timeline is the heart of Wise PMS: every visit, case and attachment
becomes an event, shown newest first.
"""

from typing import List

from app.database.db import get_connection


def timeline_for_patient(patient_id: int) -> List[dict]:
    conn = get_connection()
    try:
        events = []

        for r in conn.execute(
            "SELECT v.id, v.visit_date AS ts, v.visit_notes, v.outcome, "
            "v.followup_date, c.case_title "
            "FROM visits v LEFT JOIN patient_cases c ON c.id = v.case_id "
            "WHERE v.patient_id = ?", (patient_id,)
        ).fetchall():
            events.append({
                "kind": "visit", "id": r["id"], "ts": r["ts"] or "",
                "title": "Visit" + (f" — {r['case_title']}" if r["case_title"] else ""),
                "summary": (r["visit_notes"] or "").strip().splitlines()[0][:120]
                if (r["visit_notes"] or "").strip() else "No notes",
                "extra": r["outcome"] or "",
                "followup": r["followup_date"],
            })

        for r in conn.execute(
            "SELECT id, created_at AS ts, case_title, status "
            "FROM patient_cases WHERE patient_id = ?", (patient_id,)
        ).fetchall():
            events.append({
                "kind": "case", "id": r["id"], "ts": r["ts"] or "",
                "title": f"Case Opened — {r['case_title'] or 'Untitled'}",
                "summary": f"Status: {r['status']}", "extra": "",
                "followup": None,
            })

        for r in conn.execute(
            "SELECT id, uploaded_at AS ts, file_name, file_type "
            "FROM attachments WHERE patient_id = ?", (patient_id,)
        ).fetchall():
            events.append({
                "kind": "attachment", "id": r["id"], "ts": r["ts"] or "",
                "title": f"Attachment — {r['file_type']}",
                "summary": r["file_name"], "extra": "", "followup": None,
            })

        events.sort(key=lambda e: e["ts"], reverse=True)
        return events
    finally:
        conn.close()
