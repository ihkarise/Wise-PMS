"""Wise PMS — Clinical Consultation Workspace (Sprint 3: Narrative Editors + Autosave).

The central screen of WiseOS Health. Sprint 1 delivered the structure; Sprint 3
makes the narrative the living record of care:

    ┌ shell header ─────────────────────────────────────────────────┐
    ├ LEFT RAIL ─┬ CENTER (editors) ─────────────┬ RIGHT RAIL ───────┤
    │ section nav│ Summary · Complaint · History │ Timeline          │
    │            │ Examination · Diagnosis ·     │ Investigations    │
    │            │ Remarks · (Rx/Follow-up soon) │ OCR · Protocol·AI │
    ├ STATUS BAR ┴───────────────────────────────┴───────────────────┤
    │ ● dirty · Saving/Saved HH:MM:SS · … · Complete Visit            │
    └────────────────────────────────────────────────────────────────┘

Narrative fields (Chief Complaint / History / Examination / Diagnosis / Remarks)
are editable multiline fields that **autosave** on a debounce through the Sprint 2
lifecycle service (``controller.autosave`` -> ``save_consultation``). No new
persistence, no schema change, no status logic here: the view owns only ephemeral
UI state (dirty flags, save-status label, last-saved timestamp, debounce timer),
and the service stays the single authority over ``status``.

Prescription and Follow-up remain honest placeholders (still ``visits``-owned,
deferred). Right-rail context panels and Print/Invoice/Dispense/WhatsApp stay
placeholders/disabled until their feeder modules land. Controls come from
``shared/theme.py`` + ``shared/widgets.py`` (no raw widgets, no hex literals).
"""

import threading
import time

import flet as ft

from app.config.constants import AUTOSAVE_QUIET_MS
from app.modules.consultation import controller as cc
from app.modules.consultation.service import workspace_context
from app.shared import theme as t
from app.shared.shell import shell
from app.shared.widgets import disabled_button, info_item, placeholder_card

# Center sections, in clinical order. key · label · icon · narrative-field.
# ``field`` None => not a narrative editor (Summary is read-only; Prescription /
# Follow-up stay placeholders — still visits-owned, deferred).
_SECTIONS = [
    ("summary", "Patient Summary", ft.Icons.PERSON, None),
    ("complaint", "Chief Complaint", ft.Icons.RECORD_VOICE_OVER, "chief_complaint"),
    ("history", "History", ft.Icons.HISTORY, "history"),
    ("examination", "Examination", ft.Icons.MONITOR_HEART, "examination"),
    ("diagnosis", "Diagnosis", ft.Icons.MEDICAL_INFORMATION, "diagnosis"),
    ("remarks", "Remarks", ft.Icons.STICKY_NOTE_2, "remarks"),
    ("prescription", "Prescription", ft.Icons.MEDICATION, None),
    ("followup", "Follow-up", ft.Icons.EVENT_REPEAT, None),
]

# Placeholder note shown for the not-yet-editable narrative-adjacent sections.
_DEFERRED_NOTE = ("This section stays on the visit record for now and gets its "
                  "own editor in a later sprint.")

# Right-rail context panels — placeholders until their feeder modules land.
_CONTEXT_PANELS = [
    ("Timeline", "Visit history will appear here.", ft.Icons.TIMELINE),
    ("Investigations", "Ordered tests and results will appear here.",
     ft.Icons.SCIENCE),
    ("OCR", "Extracted report values will appear here.",
     ft.Icons.DOCUMENT_SCANNER),
    ("Protocol Suggestions", "Advisory protocol picks will appear here.",
     ft.Icons.RULE),
    ("AI Assistant", "Clinical assistance will appear here.",
     ft.Icons.SMART_TOY),
]

# Bottom action bar — terminal actions still disabled placeholders (their feeder
# modules land later). Complete Visit is wired separately (enabled when editable).
_ACTIONS = [
    ("Print", ft.Icons.PRINT),
    ("Invoice", ft.Icons.RECEIPT_LONG),
    ("Dispense", ft.Icons.LOCAL_PHARMACY),
    ("WhatsApp", ft.Icons.CHAT),
]

_EDITABLE_STATUSES = ("draft", "in_progress")

_STATUS_TEXT = {
    "draft": "Draft consultation",
    "in_progress": "Consultation in progress",
    "completed": "Consultation completed",
    "amended": "Consultation amended",
    "locked": "Consultation locked",
}


def _not_found(page) -> ft.View:
    body = ft.Column(
        [
            t.heading("Patient or case not found"),
            t.muted("This consultation could not be opened."),
            ft.Container(height=12),
            t.primary_button("Back to Search",
                             on_click=lambda e: page.go("/search")),
        ]
    )
    return shell(page, "/search", body)


def workspace_view(page: ft.Page, patient_id: int, case_id: int,
                   visit_id=None, section="") -> ft.View:
    ctx = workspace_context(patient_id, case_id, visit_id)
    patient = ctx["patient"]
    case = ctx["case"]
    consultation = ctx["consultation"]
    if not patient or not case:
        return _not_found(page)

    base = f"/patient/{patient_id}/case/{case_id}/workspace"
    valid_keys = {key for key, *_ in _SECTIONS}
    active = section if section in valid_keys else "summary"

    user = page.session.get("user") or {}
    user_id = user.get("id")
    status = consultation["status"] if consultation else None
    editable = status in _EDITABLE_STATUSES
    consultation_id = consultation["id"] if consultation else None

    # ------- Autosave / dirty / save-status state (ephemeral, view-only) -----
    field_refs: dict = {}   # narrative col -> TextField
    saved_values = {
        col: (consultation.get(col) or "" if consultation else "")
        for _, _, _, col in _SECTIONS if col
    }
    timer_holder: dict = {"t": None}

    dirty_dot = ft.Container(width=9, height=9, border_radius=5,
                             bgcolor=t.ACCENT, visible=False,
                             tooltip="Unsaved changes")
    save_status = t.muted("All changes saved" if editable else
                          _STATUS_TEXT.get(status, "No active consultation"))
    saved_ts = t.muted("", size=12)

    def _collect():
        return {col: ref.value for col, ref in field_refs.items()}

    def _is_dirty():
        return any((v or "") != (saved_values.get(c) or "")
                   for c, v in _collect().items())

    def _safe_update(*controls):
        for ctrl in controls:
            try:
                ctrl.update()
            except Exception:
                pass  # no live runtime (build-time / headless) — nothing to paint

    def _refresh_dirty():
        dirty = _is_dirty()
        dirty_dot.visible = dirty
        if dirty:
            save_status.value = "Unsaved changes…"
        _safe_update(dirty_dot, save_status)

    def _do_save():
        """Persist current editor values via the controller (no-op guarded)."""
        if consultation_id is None or not editable:
            return
        fields = _collect()
        save_status.value = "Saving…"
        _safe_update(save_status)
        try:
            updated = cc.autosave(consultation_id, fields, user_id)
            for col in field_refs:
                saved_values[col] = fields.get(col) or ""
            dirty_dot.visible = False
            save_status.value = "Saved"
            stamp = (updated or {}).get("updated_at")
            saved_ts.value = f"Last saved {_short_time(stamp)}"
        except Exception:
            save_status.value = "Error — changes not saved"
        _safe_update(dirty_dot, save_status, saved_ts)

    def _schedule_autosave():
        old = timer_holder.get("t")
        if old is not None:
            old.cancel()
        timer = threading.Timer(AUTOSAVE_QUIET_MS / 1000.0, _do_save)
        timer.daemon = True
        timer_holder["t"] = timer
        timer.start()

    def _flush():
        """Cancel any pending debounce and force-save now (Ctrl/Cmd+S, nav)."""
        old = timer_holder.get("t")
        if old is not None:
            old.cancel()
            timer_holder["t"] = None
        _do_save()

    def _on_field_change(e):
        _refresh_dirty()
        _schedule_autosave()

    def _on_keyboard(e):
        # Ctrl/Cmd+S force-flushes the pending autosave (same save path).
        if getattr(e, "key", "").lower() == "s" and (
                getattr(e, "ctrl", False) or getattr(e, "meta", False)):
            _flush()

    def _navigate(target):
        # Unsaved-changes safety: flush before leaving so no keystroke is lost.
        if editable and _is_dirty():
            _flush()
        page.go(target)

    if editable:
        page.on_keyboard_event = _on_keyboard

    # ---------- Left rail: section navigation -------------------------
    def nav_item(key, label, icon):
        is_active = key == active
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=18,
                            color=t.WHITE if is_active else t.PRIMARY),
                    ft.Text(label, size=13, font_family=t.FONT,
                            weight=ft.FontWeight.W_600,
                            color=t.WHITE if is_active else t.TEXT_DARK),
                ],
                spacing=10,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=11),
            border_radius=t.RADIUS_BUTTON,
            bgcolor=t.PRIMARY if is_active else t.WHITE,
            on_click=lambda e, k=key: _navigate(f"{base}?section={k}"),
            ink=True,
        )

    left_rail = t.card(
        ft.Column(
            [
                ft.Text("CONSULTATION", size=11, font_family=t.FONT,
                        weight=ft.FontWeight.W_600, color=t.TEXT_MUTED),
                ft.Container(height=2),
                *[nav_item(k, lbl, ic) for k, lbl, ic, _ in _SECTIONS],
            ],
            spacing=6,
        ),
        padding=14,
        width=220,
    )

    # ---------- Center: section cards --------------------------------
    def summary_body():
        return ft.Column(
            [
                ft.Row(
                    [
                        info_item("Reg No", patient.get("reg_no")),
                        info_item("Age", patient.get("age")),
                        info_item("Gender", patient.get("gender")),
                        info_item("Blood Group", patient.get("blood_group")),
                    ],
                    spacing=16,
                ),
                ft.Row(
                    [
                        info_item("Phone", patient.get("phone")),
                        info_item("Place", patient.get("place")),
                        info_item("Consultation", patient.get("consultation_type")),
                        info_item("Case", case.get("case_title")),
                    ],
                    spacing=16,
                ),
                ft.Divider(color=t.BORDER),
                t.muted("Allergy & chronic-condition flags will appear here in "
                        "a later sprint."),
            ],
            spacing=14,
        )

    def editor_body(col, label):
        value = consultation.get(col) if consultation else ""
        field = t.text_field(
            label,
            value=value,
            expand=True,
            multiline=True,
            min_lines=6,
            read_only=not editable,
            hint=(f"Type the {label.lower()}…" if editable else None),
            on_change=(_on_field_change if editable else None),
        )
        field_refs[col] = field
        note = (t.muted("Autosaves as you type.", size=12) if editable else
                t.muted("Read-only — this consultation is "
                        f"{status}.", size=12))
        return ft.Column([field, note], spacing=8)

    def section_card(key, label, icon, col):
        is_active = key == active
        if key == "summary":
            body = summary_body()
        elif col:
            body = editor_body(col, label)
        else:
            body = t.muted(_DEFERRED_NOTE)
        return ft.Container(
            key=key,
            content=t.card(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(icon, size=20, color=t.PRIMARY),
                                ft.Text(label, size=18,
                                        weight=ft.FontWeight.BOLD,
                                        font_family=t.FONT, color=t.TEXT_DARK),
                            ],
                            spacing=10,
                        ),
                        ft.Divider(color=t.BORDER),
                        body,
                    ],
                    spacing=12,
                ),
                border=(ft.border.all(2, t.PRIMARY) if is_active else None),
            ),
        )

    center = ft.Column(
        [section_card(k, lbl, ic, col) for k, lbl, ic, col in _SECTIONS],
        spacing=16,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    # ---------- Right rail: context panels (placeholders) ------------
    right_rail = ft.Column(
        [
            ft.Text("CONTEXT", size=11, font_family=t.FONT,
                    weight=ft.FontWeight.W_600, color=t.TEXT_MUTED),
            *[placeholder_card(title, msg, icon)
              for title, msg, icon in _CONTEXT_PANELS],
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        width=300,
    )

    # ---------- Bottom status / action bar ---------------------------
    def _do_complete(e):
        if consultation_id is None:
            return
        try:
            cc.complete(consultation_id, user_id, _collect())
            t.snack(page, "Consultation completed.")
            page.go(f"{base}/visit/{visit_id}")   # reopen read-only
        except Exception:
            t.snack(page, "Could not complete the consultation.", error=True)

    if editable:
        complete_action = t.primary_button(
            "Complete Visit", on_click=_do_complete,
            icon=ft.Icons.CHECK_CIRCLE)
    else:
        complete_action = disabled_button("Complete Visit",
                                          icon=ft.Icons.CHECK_CIRCLE)

    status_label = _STATUS_TEXT.get(status, "No active consultation")
    bottom_bar = ft.Container(
        bgcolor=t.WHITE,
        border_radius=t.RADIUS_CARD,
        padding=ft.padding.symmetric(horizontal=20, vertical=12),
        shadow=t.CARD_SHADOW,
        content=ft.Row(
            [
                ft.Row(
                    [
                        dirty_dot,
                        ft.Icon(ft.Icons.EDIT_NOTE, size=18,
                                color=t.TEXT_MUTED),
                        ft.Column(
                            [
                                ft.Row([save_status], spacing=6, tight=True),
                                ft.Row(
                                    [t.muted(f"{status_label} · "
                                             f"{patient['name']}", size=12),
                                     saved_ts],
                                    spacing=8, tight=True),
                            ],
                            spacing=1,
                        ),
                    ],
                    spacing=8,
                    tight=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(expand=True),
                *[disabled_button(label, icon=icon) for label, icon in _ACTIONS],
                complete_action,
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    # ---------- Assemble ---------------------------------------------
    body = ft.Column(
        [
            ft.Row(
                [left_rail, center, right_rail],
                spacing=16,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            bottom_bar,
        ],
        spacing=16,
        expand=True,
    )

    return shell(page, base, body)


def _short_time(stamp) -> str:
    """Best-effort HH:MM:SS from a DB ``updated_at`` string (falls back to now)."""
    if isinstance(stamp, str):
        # SQLite CURRENT_TIMESTAMP => 'YYYY-MM-DD HH:MM:SS'
        tail = stamp.strip().split(" ")
        if len(tail) == 2 and len(tail[1]) >= 5:
            return tail[1]
    return time.strftime("%H:%M:%S")
