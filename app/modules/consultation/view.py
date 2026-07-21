"""Wise PMS — Consultation Workspace (Sprint 1 skeleton).

The central screen of WiseOS Health. This sprint delivers the *structure only*:

    ┌ shell header ─────────────────────────────────────────────────┐
    ├ LEFT RAIL ─┬ CENTER (sections) ────────────┬ RIGHT RAIL ───────┤
    │ section nav│ Summary · Complaint · History │ Timeline          │
    │            │ Diagnosis · Prescription ·    │ Investigations    │
    │            │ Remarks · Follow-up           │ OCR · Protocol·AI │
    ├ STATUS BAR ┴───────────────────────────────┴───────────────────┤
    │ Print · Invoice · Dispense · WhatsApp · Complete Visit (disabled)│
    └────────────────────────────────────────────────────────────────┘

No business logic, no persistence, no feeder-module calls. Patient Summary shows
read-only patient data (composition over ``patients.service``); every other
panel is an honest placeholder. Terminal actions are disabled placeholders. All
controls come from ``shared/theme.py`` + ``shared/widgets.py`` (no raw
buttons/fields, no hex literals) per arch rule 11.
"""

import flet as ft

from app.modules.consultation.service import workspace_context
from app.shared import theme as t
from app.shared.shell import shell
from app.shared.widgets import disabled_button, info_item, placeholder_card

# Center sections, in clinical order (subset of the full spec — the panels this
# skeleton exposes). key · label · icon.
_SECTIONS = [
    ("summary", "Patient Summary", ft.Icons.PERSON),
    ("complaint", "Chief Complaint", ft.Icons.RECORD_VOICE_OVER),
    ("history", "History", ft.Icons.HISTORY),
    ("diagnosis", "Diagnosis", ft.Icons.MEDICAL_INFORMATION),
    ("prescription", "Prescription", ft.Icons.MEDICATION),
    ("remarks", "Remarks", ft.Icons.STICKY_NOTE_2),
    ("followup", "Follow-up", ft.Icons.EVENT_REPEAT),
]

# Right-rail context panels — all placeholders until their feeder modules land.
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

# Bottom action bar — disabled terminal actions (placeholders this sprint).
_ACTIONS = [
    ("Print", ft.Icons.PRINT),
    ("Invoice", ft.Icons.RECEIPT_LONG),
    ("Dispense", ft.Icons.LOCAL_PHARMACY),
    ("WhatsApp", ft.Icons.CHAT),
    ("Complete Visit", ft.Icons.CHECK_CIRCLE),
]


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
    valid_keys = {key for key, _, _ in _SECTIONS}
    active = section if section in valid_keys else "summary"

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
            on_click=lambda e, k=key: page.go(f"{base}?section={k}"),
            ink=True,
        )

    left_rail = t.card(
        ft.Column(
            [
                ft.Text("CONSULTATION", size=11, font_family=t.FONT,
                        weight=ft.FontWeight.W_600, color=t.TEXT_MUTED),
                ft.Container(height=2),
                *[nav_item(k, lbl, ic) for k, lbl, ic in _SECTIONS],
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

    def section_card(key, label, icon):
        is_active = key == active
        body = (summary_body() if key == "summary" else
                t.muted(f"The {label} editor will be enabled in a later "
                        f"sprint. Narrative stays the record of care."))
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
        [section_card(k, lbl, ic) for k, lbl, ic in _SECTIONS],
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
    _STATUS_TEXT = {
        "draft": "Draft consultation",
        "in_progress": "Consultation in progress",
        "completed": "Consultation completed",
        "amended": "Consultation amended",
        "locked": "Consultation locked",
    }
    if consultation:
        status_label = _STATUS_TEXT.get(consultation["status"],
                                        "Draft consultation")
    else:
        status_label = "No active consultation"
    bottom_bar = ft.Container(
        bgcolor=t.WHITE,
        border_radius=t.RADIUS_CARD,
        padding=ft.padding.symmetric(horizontal=20, vertical=12),
        shadow=t.CARD_SHADOW,
        content=ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.EDIT_NOTE, size=18, color=t.TEXT_MUTED),
                        t.muted(f"{status_label} · {patient['name']} · not yet "
                                f"wired (skeleton)"),
                    ],
                    spacing=8,
                    tight=True,
                ),
                ft.Container(expand=True),
                *[disabled_button(label, icon=icon) for label, icon in _ACTIONS],
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
