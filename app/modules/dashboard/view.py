"""Wise PMS — Screen 02: Dashboard."""

import flet as ft

from app.modules.patients.service import patient_stats, recent_patients
from app.modules.visits.service import visit_stats
from app.shared import theme as t
from app.shared.shell import shell
from app.shared.widgets import empty_state, stat_card


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

    empty = empty_state(
        ft.Icons.PEOPLE_OUTLINE,
        "No patients registered yet.",
        "Click  + New Case  to register your first patient.",
    )

    body = ft.Column(
        [
            t.heading("Dashboard"),
            t.muted("Quick overview of your clinic"),
            ft.Container(height=8),
            ft.Row(
                [
                    stat_card("Total Patients", stats["total"],
                              ft.Icons.GROUPS, t.PRIMARY),
                    stat_card("Added Today", stats["today"],
                              ft.Icons.PERSON_ADD_ALT_1, "#2E9E5B"),
                    stat_card("Visits Today", vstats["visits_today"],
                              ft.Icons.MEDICAL_SERVICES, "#7B3FF2"),
                    stat_card("Follow-ups Due", vstats["followups_due"],
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
