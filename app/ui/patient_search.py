"""Wise PMS — Screen 04: Patient Search (real-time)."""

import flet as ft

from app.services.patient_service import search_patients
from app.ui import theme as t
from app.ui.shell import shell


def search_view(page: ft.Page) -> ft.View:
    results_holder = ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
    count_text = t.muted("")

    def build_table(patients):
        if not patients:
            return ft.Container(
                padding=40, alignment=ft.alignment.center,
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=t.TEXT_MUTED),
                        t.muted("No patients found."),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(p["reg_no"], font_family=t.FONT, size=14,
                                        weight=ft.FontWeight.W_600,
                                        color=t.PRIMARY)),
                    ft.DataCell(ft.Text(p["name"], font_family=t.FONT, size=14)),
                    ft.DataCell(ft.Text(str(p.get("age") or "—"),
                                        font_family=t.FONT, size=14)),
                    ft.DataCell(ft.Text(p.get("gender") or "—",
                                        font_family=t.FONT, size=14)),
                    ft.DataCell(ft.Text(p.get("phone") or "—",
                                        font_family=t.FONT, size=14)),
                    ft.DataCell(ft.Text(p.get("place") or "—",
                                        font_family=t.FONT, size=14)),
                    ft.DataCell(ft.Text((p.get("created_at") or "")[:10],
                                        font_family=t.FONT, size=14)),
                    ft.DataCell(
                        ft.Row(
                            [
                                ft.IconButton(
                                    ft.Icons.OPEN_IN_NEW, icon_color=t.PRIMARY,
                                    tooltip="Open Profile", icon_size=20,
                                    on_click=lambda e, pid=p["id"]:
                                        page.go(f"/patient/{pid}")),
                                ft.IconButton(
                                    ft.Icons.EDIT, icon_color=t.TEXT_MUTED,
                                    tooltip="Edit Patient", icon_size=20,
                                    on_click=lambda e, pid=p["id"]:
                                        page.go(f"/patient/{pid}/edit")),
                            ],
                            spacing=0, tight=True,
                        )
                    ),
                ],
                on_select_changed=lambda e, pid=p["id"]:
                    page.go(f"/patient/{pid}"),
            )
            for p in patients
        ]
        cols = ["Reg No", "Name", "Age", "Gender", "Phone", "Place",
                "Created", "Actions"]
        return ft.DataTable(
            columns=[ft.DataColumn(ft.Text(c, font_family=t.FONT,
                                           weight=ft.FontWeight.BOLD))
                     for c in cols],
            rows=rows,
            heading_row_color=t.LIGHT_GRAY,
            expand=True,
        )

    def refresh(query=""):
        patients = search_patients(query)
        count_text.value = f"{len(patients)} patient(s)"
        results_holder.controls = [build_table(patients)]
        page.update()

    search_box = ft.TextField(
        hint_text="Search by Name, Phone, Registration Number, or Place…",
        prefix_icon=ft.Icons.SEARCH,
        bgcolor=t.WHITE,
        border_radius=t.RADIUS_INPUT,
        border_color=t.BORDER,
        focused_border_color=t.PRIMARY,
        text_style=ft.TextStyle(font_family=t.FONT, size=15),
        on_change=lambda e: refresh(e.control.value),
        expand=True,
        autofocus=True,
    )

    refresh()  # initial load: most recent patients

    body = ft.Column(
        [
            t.heading("Patient Search"),
            t.muted("Results update instantly while you type"),
            ft.Container(height=8),
            ft.Row([search_box], spacing=12),
            count_text,
            t.card(results_holder, padding=12, expand=True),
        ],
        spacing=8,
        expand=True,
    )

    return shell(page, "/search", body)
