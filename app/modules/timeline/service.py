"""Timeline — service.

The timeline is the heart of Wise PMS: every visit, case and attachment becomes
an event, shown newest first. The shaping/merge/sort logic lives here; the SQL
lives in the repository.
"""

from typing import List

from app.modules.timeline.repository import TimelineRepository

_repo = TimelineRepository()


def timeline_for_patient(patient_id: int) -> List[dict]:
    events = []

    for r in _repo.visits(patient_id):
        events.append({
            "kind": "visit", "id": r["id"], "ts": r["ts"] or "",
            "title": "Visit" + (f" — {r['case_title']}" if r["case_title"] else ""),
            "summary": (r["visit_notes"] or "").strip().splitlines()[0][:120]
            if (r["visit_notes"] or "").strip() else "No notes",
            "extra": r["outcome"] or "",
            "followup": r["followup_date"],
        })

    for r in _repo.cases(patient_id):
        events.append({
            "kind": "case", "id": r["id"], "ts": r["ts"] or "",
            "title": f"Case Opened — {r['case_title'] or 'Untitled'}",
            "summary": f"Status: {r['status']}", "extra": "",
            "followup": None,
        })

    for r in _repo.attachments(patient_id):
        events.append({
            "kind": "attachment", "id": r["id"], "ts": r["ts"] or "",
            "title": f"Attachment — {r['file_type']}",
            "summary": r["file_name"], "extra": "", "followup": None,
        })

    events.sort(key=lambda e: e["ts"], reverse=True)
    return events
