"""Wise PMS — Domain constant vocabularies (single source of truth).

These lists back the dropdowns across the UI and the file-type mapping used by
the attachment service. Values are identical to the Sprint 1/2 originals that
were previously duplicated inside individual screens.
"""

GENDERS = ["Female", "Male", "Other"]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# A consultation type and a visit type are the same vocabulary today.
CONSULTATION_TYPES = ["Walk-In", "Online", "Telephonic", "Home Visit"]
VISIT_TYPES = CONSULTATION_TYPES

CASE_STATUSES = ["Open", "Closed", "Resolved", "On Hold"]

VISIT_OUTCOMES = ["Improving", "Same", "Worse", "Cured", "New Complaint", "Other"]

# Consultation Workspace autosave — trailing-edge debounce quiet period (ms).
# Narrative edits persist via ``save_consultation`` this long after the last
# keystroke. UI-only tuning knob; no schema or lifecycle impact.
AUTOSAVE_QUIET_MS = 900

# Attachment extension -> human-readable file type.
FILE_TYPES = {
    ".pdf": "PDF", ".jpg": "Image", ".jpeg": "Image", ".png": "Image",
    ".gif": "Image", ".webp": "Image", ".bmp": "Image",
    ".doc": "Document", ".docx": "Document", ".txt": "Document",
}
