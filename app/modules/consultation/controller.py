"""Consultation Workspace — controller (router dispatch target).

Parses the workspace route, resolves the optional draft-visit sentinel and the
``?section=`` deep-link, and hands off to the view. No business logic lives here
— it orchestrates only (arch rule 4).
"""

from app.modules.consultation.service import (
    complete_consultation,
    get_consultation,
    open_or_create_draft,
    save_consultation,
)
from app.modules.consultation.view import workspace_view

# Editable narrative fields the workspace autosaves. Kept here so the no-op guard
# compares only what the editors can change (status/ids are never mass-updated).
_NARRATIVE_FIELDS = ("chief_complaint", "history", "examination", "diagnosis",
                     "remarks")


def _changed_fields(consultation_id, fields):
    """Return only the fields whose value differs from what is already persisted.

    This is the autosave **no-op guard**: an identical save (debounce firing on
    an untouched document, or a re-flush of already-saved text) yields an empty
    delta, so the service is never called and no duplicate audit row is written.
    """
    current = get_consultation(consultation_id) or {}
    delta = {}
    for col in _NARRATIVE_FIELDS:
        if col in fields and str(fields[col] or "") != str(current.get(col) or ""):
            delta[col] = fields[col]
    return delta


def autosave(consultation_id, fields, user_id):
    """Persist changed narrative fields via the lifecycle service.

    Debounce target for the editors. Delegates all persistence + the
    ``draft -> in_progress`` flip + audit to ``save_consultation``; writes
    nothing when the no-op guard finds no real change. Returns the current
    consultation dict either way.
    """
    delta = _changed_fields(consultation_id, fields)
    if not delta:
        return get_consultation(consultation_id)
    return save_consultation(consultation_id, delta, user_id)


def flush(consultation_id, user_id, fields=None):
    """Force-save pending edits *now* — Ctrl/Cmd+S, section nav, route-away.

    Same persistence path as ``autosave`` (no separate save mechanism); the
    no-op guard still applies, so a flush with nothing pending is free.
    """
    return autosave(consultation_id, fields or {}, user_id)


def complete(consultation_id, user_id, fields=None):
    """Flush any pending edits, then finalize the document (-> completed).

    Guarantees the last keystroke is persisted before the document seals — no
    edit is lost to a still-pending debounce.
    """
    if fields:
        autosave(consultation_id, fields, user_id)
    return complete_consultation(consultation_id, user_id)


def workspace_controller(page, params, query=""):
    pid = int(params["pid"])
    cid = int(params["cid"])

    vid_raw = params.get("vid")
    visit_id = int(vid_raw) if vid_raw and vid_raw not in (None, "new") else None

    # Ensure an open draft consultation exists for this case (create-on-open,
    # reused on reopen). A concrete /visit/<vid> in the route takes precedence.
    if visit_id is None:
        user = page.session.get("user") or {}
        draft = open_or_create_draft(pid, cid, user.get("id"))
        visit_id = draft["visit_id"]

    section = ""
    for part in query.split("&"):
        if part.startswith("section="):
            section = part.split("=", 1)[1]
            break

    return workspace_view(page, pid, cid, visit_id, section=section)


ROUTES = [
    # /patient/<pid>/case/<cid>/workspace
    #   · …/workspace/visit/new   (open on a new draft visit)
    #   · …/workspace/visit/<vid> (reopen an existing visit)
    (r"^/patient/(?P<pid>\d+)/case/(?P<cid>\d+)/workspace"
     r"(?:/visit/(?P<vid>new|\d+))?$", workspace_controller),
]
