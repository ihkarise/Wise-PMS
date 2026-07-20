"""Wise PMS — Screen 06: Case Record.
Narrative first: a large free-writing area. No mandatory structure.
"""

import flet as ft

from app.config.constants import CASE_STATUSES
from app.modules.cases.service import create_case, get_case, update_case
from app.modules.patients.service import get_patient
from app.shared import theme as t
from app.shared.shell import shell


def case_view(page: ft.Page, patient_id: int, case_id=None) -> ft.View:
    user = page.session.get("user") or {}
    patient = get_patient(patient_id)
    if not patient:
        return shell(page, "/search",
                     ft.Column([t.heading("Patient not found")]))

    case = get_case(case_id) if case_id else None
    is_new = case is None

    case_title = t.text_field("Case Title (e.g. Migraine)",
                              value=(case or {}).get("case_title"), expand=True)
    diagnosis = t.text_field("Diagnosis (optional)",
                             value=(case or {}).get("diagnosis"), expand=True)
    status = t.dropdown("Status", CASE_STATUSES,
                        value=(case or {}).get("status") or "Open", width=180)

    case_notes = ft.TextField(
        value=(case or {}).get("case_notes") or "",
        multiline=True,
        min_lines=18,
        max_lines=40,
        hint_text=("Write the case naturally — chief complaints, history, "
                   "mentals, physicals, constitution… no structure required."),
        bgcolor=t.WHITE,
        border_radius=t.RADIUS_INPUT,
        border_color=t.BORDER,
        focused_border_color=t.PRIMARY,
        text_style=ft.TextStyle(font_family=t.FONT, size=15, color=t.TEXT_DARK),
        expand=True,
    )
    error_text = ft.Text("", color=t.ACCENT, size=14, font_family=t.FONT)

    def collect():
        return {
            "case_title": (case_title.value or "").strip() or None,
            "diagnosis": (diagnosis.value or "").strip() or None,
            "case_notes": case_notes.value or None,
            "status": status.value,
        }

    def save(then_visit=False):
        nonlocal case_id
        if not (case_title.value or "").strip() and not (case_notes.value or "").strip():
            error_text.value = "Write a case title or some case notes before saving."
            page.update()
            return
        try:
            if is_new and case_id is None:
                case_id = create_case(patient_id, collect(), user.get("id"))
            else:
                update_case(case_id, collect(), user.get("id"))
        except Exception:
            t.snack(page, "Unable to save record. Please try again.", error=True)
            return
        t.snack(page, "Case saved.")
        if then_visit:
            page.go(f"/patient/{patient_id}/visit/new?case={case_id}")
        else:
            page.go(f"/patient/{patient_id}")

    header_card = t.card(
        ft.Row(
            [
                ft.Column(
                    [
                        t.heading(("New Case" if is_new else "Case Record")
                                  + f" — {patient['name']}", size=22),
                        t.muted(f"{patient['reg_no']}  ·  "
                                f"{patient.get('age') or '—'} yrs  ·  "
                                f"{patient.get('gender') or '—'}"),
                    ],
                    spacing=2,
                ),
                ft.Container(expand=True),
                t.secondary_button("Back to Profile", icon=ft.Icons.ARROW_BACK,
                                   on_click=lambda e:
                                       page.go(f"/patient/{patient_id}")),
            ],
        ),
        padding=20,
    )

    form = t.card(
        ft.Column(
            [
                ft.Row([case_title, diagnosis, status], spacing=16),
                ft.Text("Case Notes", size=16, weight=ft.FontWeight.BOLD,
                        font_family=t.FONT, color=t.PRIMARY),
                case_notes,
                error_text,
                ft.Divider(color=t.BORDER),
                ft.Row(
                    [
                        t.secondary_button(
                            "Cancel", icon=ft.Icons.CLOSE,
                            on_click=lambda e:
                                page.go(f"/patient/{patient_id}")),
                        ft.Container(expand=True),
                        t.secondary_button(
                            "Save + Start Visit", icon=ft.Icons.MEDICAL_SERVICES,
                            on_click=lambda e: save(then_visit=True)),
                        t.primary_button("Save Case", icon=ft.Icons.SAVE,
                                         on_click=lambda e: save()),
                    ],
                    spacing=12,
                ),
            ],
            spacing=14,
            expand=True,
        ),
        expand=True,
    )

    body = ft.Column([header_card, form], spacing=16, expand=True,
                     scroll=ft.ScrollMode.AUTO)
    return shell(page, f"/patient/{patient_id}/case", body)
