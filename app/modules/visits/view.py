"""Wise PMS — Screen 07: Visit Entry.
Daily consultation screen. Narrative editors are primary; the detected
medicines panel is optional assistance and never restricts the doctor.
"""

from datetime import date

import flet as ft

from app.config.constants import VISIT_OUTCOMES as OUTCOMES
from app.config.constants import VISIT_TYPES
from app.modules.cases.service import cases_for_patient
from app.modules.patients.service import get_patient
from app.modules.visits.service import (create_visit,
                                        extract_prescription_items,
                                        get_visit, update_visit)
from app.shared import theme as t
from app.shared.shell import shell


def _notes_field(value, hint, min_lines=4):
    return ft.TextField(
        value=value or "",
        multiline=True,
        min_lines=min_lines,
        max_lines=30,
        hint_text=hint,
        bgcolor=t.WHITE,
        border_radius=t.RADIUS_INPUT,
        border_color=t.BORDER,
        focused_border_color=t.PRIMARY,
        text_style=ft.TextStyle(font_family=t.FONT, size=15, color=t.TEXT_DARK),
    )


def visit_view(page: ft.Page, patient_id: int, visit_id=None,
               preselected_case=None) -> ft.View:
    user = page.session.get("user") or {}
    patient = get_patient(patient_id)
    if not patient:
        return shell(page, "/search",
                     ft.Column([t.heading("Patient not found")]))

    visit = get_visit(visit_id) if visit_id else None
    is_new = visit is None

    cases = cases_for_patient(patient_id)
    case_options = ["No Case"] + [
        f"#{c['id']} — {c['case_title'] or 'Untitled'}" for c in cases
    ]
    selected_case_id = (visit or {}).get("case_id") or preselected_case
    case_dd = t.dropdown(
        "Linked Case", case_options,
        value=next((f"#{c['id']} — {c['case_title'] or 'Untitled'}"
                    for c in cases if c["id"] == selected_case_id), "No Case"),
        width=320,
    )

    visit_type = t.dropdown("Consultation Type", VISIT_TYPES,
                            value=(visit or {}).get("visit_type")
                            or patient.get("consultation_type") or "Walk-In",
                            width=200)
    outcome = t.dropdown("Visit Outcome", OUTCOMES,
                         value=(visit or {}).get("outcome"), width=200)
    followup = t.text_field("Follow-up Date (YYYY-MM-DD)",
                            value=(visit or {}).get("followup_date"), width=240)

    visit_notes = _notes_field(
        (visit or {}).get("visit_notes"),
        "Patient reports 60% improvement. Headache reduced. Sleep improved…",
        min_lines=8,
    )
    investigation_notes = _notes_field(
        (visit or {}).get("investigation_notes"),
        "Investigation findings, reports advised…",
    )
    prescription_notes = _notes_field(
        (visit or {}).get("prescription_notes"),
        "Bell 200\nBry 30 TDS\nReview after 15 days",
    )

    detected_panel = ft.Row(wrap=True, spacing=8)
    error_text = ft.Text("", color=t.ACCENT, size=14, font_family=t.FONT)

    def refresh_detected(e=None):
        items = extract_prescription_items(prescription_notes.value)
        detected_panel.controls = [
            ft.Container(
                content=ft.Text(
                    f"{i['medicine_name']} {i['potency']}"
                    + (f" · {i['dosage']}" if i["dosage"] else ""),
                    size=13, font_family=t.FONT, color=t.PRIMARY,
                    weight=ft.FontWeight.W_600),
                bgcolor=t.PRIMARY + "14",
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=20,
            )
            for i in items
        ] or [t.muted("No medicines detected yet — that's fine, "
                      "your narrative is the record.", size=12)]
        page.update()

    prescription_notes.on_change = refresh_detected
    refresh_detected()

    def collect():
        cid = None
        if case_dd.value and case_dd.value != "No Case":
            cid = int(case_dd.value.split("—")[0].strip().lstrip("#"))
        return {
            "case_id": cid,
            "visit_type": visit_type.value,
            "visit_notes": visit_notes.value or None,
            "investigation_notes": investigation_notes.value or None,
            "prescription_notes": prescription_notes.value or None,
            "followup_date": (followup.value or "").strip() or None,
            "outcome": outcome.value,
        }

    def save(e=None):
        if not (visit_notes.value or "").strip() and \
           not (prescription_notes.value or "").strip():
            error_text.value = ("Write visit notes or a prescription "
                                "before saving.")
            page.update()
            return
        try:
            if is_new:
                create_visit(patient_id, collect(), user.get("id"))
            else:
                update_visit(visit_id, collect(), user.get("id"))
        except Exception:
            t.snack(page, "Unable to save record. Please try again.", error=True)
            return
        t.snack(page, "Visit saved.")
        page.go(f"/patient/{patient_id}")

    def section(title):
        return ft.Text(title, size=16, weight=ft.FontWeight.BOLD,
                       font_family=t.FONT, color=t.PRIMARY)

    header_card = t.card(
        ft.Row(
            [
                ft.Column(
                    [
                        t.heading(("New Visit" if is_new else "Edit Visit")
                                  + f" — {patient['name']}", size=22),
                        t.muted(f"{patient['reg_no']}  ·  {date.today()}  ·  "
                                f"Dr: {user.get('full_name') or '—'}"),
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
                ft.Row([case_dd, visit_type], spacing=16),
                section("Visit Notes"),
                visit_notes,
                section("Investigation Notes"),
                investigation_notes,
                section("Prescription Notes"),
                prescription_notes,
                ft.Row(
                    [ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=t.PRIMARY),
                     ft.Text("Detected medicines (optional, editable later)",
                             size=13, font_family=t.FONT, color=t.TEXT_MUTED)],
                    spacing=6,
                ),
                detected_panel,
                ft.Divider(color=t.BORDER),
                section("Follow-Up"),
                ft.Row([followup, outcome], spacing=16),
                error_text,
                ft.Divider(color=t.BORDER),
                ft.Row(
                    [
                        t.secondary_button(
                            "Cancel", icon=ft.Icons.CLOSE,
                            on_click=lambda e:
                                page.go(f"/patient/{patient_id}")),
                        ft.Container(expand=True),
                        t.primary_button("Save Visit", icon=ft.Icons.SAVE,
                                         on_click=save),
                    ],
                    spacing=12,
                ),
            ],
            spacing=12,
        ),
    )

    body = ft.Column([header_card, form], spacing=16, expand=True,
                     scroll=ft.ScrollMode.AUTO)
    return shell(page, f"/patient/{patient_id}/visit", body)
