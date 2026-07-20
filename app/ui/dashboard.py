"""Wise PMS — Screen 02: Dashboard (Sprint 1 scope)."""

import flet as ft

from app.services.patient_service import patient_stats, recent_patients
from app.services.visit_service import visit_stats
from app.ui import theme as t
from app.ui.shell import shell


def _stat_card(label, value, icon, color):
    return t.card(
        ft.Row(
            [
                ft.Container(
                    width=52, height=52, border_radius=14,
                    bgcolor=color + "1A",  # ~10% tint
                    alignment=ft.alignment.center,
                    content=ft.Icon(icon, color=color, size=26),
                ),
                ft.Column(
                    [
                        ft.Text(str(value), size=28, weight=ft.FontWeight.BOLD,
                                font_family=t.FONT, color=t.TEXT_DARK),
                        t.muted(label),
                    ],
                    spacing=0,
                ),
            ],
            spacing=16,
        ),
        expand=True,
    )


def dashboard_view(page: ft.Page) -> ft.View:
    stats = patient_stats()
    vstats = visit_stats()
    recents = recent_patients(10)

    rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(p["reg_no"], font_family=t.FONT, size=14,
                                    weight=ft.FontWeight.W_600, color=t.PRIMARY)),
                ft.DataCell(ft.Text(p["name"], font_family=t.FONT, size=14)),
                ft.DataCell(ft.Text(p.get("phone") or "—", font_family=t.FONT,
                                    size=14)),
                ft.DataCell(ft.Text(p.get("place") or "—", font_family=t.FONT,
                                    size=14)),
            ],
            on_select_changed=lambda e, pid=p["id"]: page.go(f"/patient/{pid}"),
        )
        for p in recents
    ]

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Reg No", font_family=t.FONT,
                                  weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Name", font_family=t.FONT,
                                  weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Phone", font_family=t.FONT,
                                  weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Place", font_family=t.FONT,
                                  weight=ft.FontWeight.BOLD)),
        ],
        rows=rows,
        heading_row_color=t.LIGHT_GRAY,
        expand=True,
    )

    empty = ft.Container(
        padding=32, alignment=ft.alignment.center,
        content=ft.Column(
            [
                ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=48, color=t.TEXT_MUTED),
                t.muted("No patients registered yet."),
                t.muted("Click  + New Case  to register your first patient."),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
    )

    body = ft.Column(
        [
            t.heading("Dashboard"),
            t.muted("Quick overview of your clinic"),
            ft.Container(height=8),
            ft.Row(
                [
                    _stat_card("Total Patients", stats["total"],
                               ft.Icons.GROUPS, t.PRIMARY),
                    _stat_card("Added Today", stats["today"],
                               ft.Icons.PERSON_ADD_ALT_1, "#2E9E5B"),
                    _stat_card("Visits Today", vstats["visits_today"],
                               ft.Icons.MEDICAL_SERVICES, "#7B3FF2"),
                    _stat_card("Follow-ups Due", vstats["followups_due"],
                               ft.Icons.EVENT_REPEAT, t.ACCENT),
                ],
                spacing=20,
            ),
            ft.Container(height=12),
            t.card(
                ft.Column(
                    [
                        ft.Row(
                            [
                                t.heading("Recent Patients", size=20),
                                ft.Container(expand=True),
                                t.secondary_button(
                                    "View All", icon=ft.Icons.SEARCH,
                                    on_click=lambda e: page.go("/search")),
                            ]
                        ),
                        ft.Divider(color=t.BORDER),
                        table if rows else empty,
                    ],
                    spacing=10,
                ),
            ),
        ],
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    return shell(page, "/dashboard", body)
