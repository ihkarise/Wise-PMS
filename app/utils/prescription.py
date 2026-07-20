"""Wise PMS — Prescription intelligence (pure helper).

Best-effort extraction of medicine/potency/dosage from a doctor's free-text
prescription (e.g. "Bell 200", "Bry 30 TDS"). This assists analytics; it never
restricts the doctor — the narrative prescription remains the source of truth.

This is a pure function with no database or UI dependency, so it is trivially
unit-testable and reusable by any future module (analytics, AI workflows).
"""

import re
from typing import List

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
    """Extract structured medicine items from free-text prescription notes.

    The doctor's narrative remains the source of truth; this is a non-
    authoritative extraction layer for future analytics.
    """
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
            name = m.group(1).strip()
            potency = m.group(2).strip()
            rest = m.group(3).strip()
            if name.lower() in _SKIP_WORDS:
                continue
            items.append({
                "medicine_name": name,
                "potency": potency.upper().replace(" ", ""),
                "dosage": rest or None,
                "instructions": None,
            })
    return items
