"""Wise PMS — Shared application shell (header + workflow bar)."""

import flet as ft

from app.services.auth_service import logout
from app.services.backup_service import backup_now
from app.ui import theme as t


def shell(page: ft.Page, route: str, body: ft.Control) -> ft.View:
    """Wrap a screen body with the Wise PMS header and workflow bar."""
    user = page.session.get("user") or {}

    def nav(target):
        return lambda e: page.go(target)

    def do_logout(e):
        logout(user)
        page.session.remove("user")
        page.go("/login")

    def do_backup(e):
        try:
            path = backup_now()
            t.snack(page, f"Backup created: {path}")
        except Exception:
            t.snack(page, "Backup failed. Please try again.", error=True)

    def workflow_btn(label, icon, target, primary=False):
        active = route == target
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=18,
                            color=t.WHITE if (primary or active) else t.PRIMARY),
                    ft.Text(label, size=14, font_family=t.FONT,
                            weight=ft.FontWeight.W_600,
                            color=t.WHITE if (primary or active) else t.PRIMARY),
                ],
                spacing=6,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=t.RADIUS_BUTTON,
            bgcolor=(t.ACCENT if primary else (t.PRIMARY if active else t.WHITE)),
            border=None if (primary or active) else ft.border.all(1.2, t.PRIMARY),
            on_click=nav(target),
            ink=True,
        )

    header = ft.Container(
        bgcolor=t.WHITE,
        padding=ft.padding.symmetric(horizontal=24, vertical=14),
        shadow=ft.BoxShadow(blur_radius=12, offset=ft.Offset(0, 2),
                            color="#0F000000"),
        content=ft.Row(
            [
                ft.GestureDetector(content=t.logo_block(size=42),
                                   on_tap=nav("/dashboard")),
                ft.Container(width=24),
                workflow_btn("+ New Case", ft.Icons.PERSON_ADD, "/register",
                             primary=True),
                workflow_btn("Follow Up", ft.Icons.EVENT_REPEAT, "/search"),
                workflow_btn("Search Patient", ft.Icons.SEARCH, "/search"),
                workflow_btn("Dashboard", ft.Icons.DASHBOARD, "/dashboard"),
                ft.Container(expand=True),
                ft.IconButton(ft.Icons.BACKUP, icon_color=t.PRIMARY,
                              tooltip="Backup Now", on_click=do_backup),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.CircleAvatar(
                                content=ft.Text(
                                    (user.get("full_name") or "U")[0].upper(),
                                    color=t.WHITE, font_family=t.FONT,
                                    weight=ft.FontWeight.BOLD),
                                bgcolor=t.PRIMARY, radius=16,
                            ),
                            ft.Column(
                                [
                                    ft.Text(user.get("full_name") or "User",
                                            size=13, font_family=t.FONT,
                                            weight=ft.FontWeight.W_600,
                                            color=t.TEXT_DARK),
                                    ft.Text(user.get("role") or "", size=11,
                                            font_family=t.FONT,
                                            color=t.TEXT_MUTED),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=8,
                        tight=True,
                    ),
                ),
                ft.IconButton(ft.Icons.LOGOUT, icon_color=t.ACCENT,
                              tooltip="Logout", on_click=do_logout),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    return ft.View(
        route=route,
        padding=0,
        bgcolor=t.LIGHT_GRAY,
        controls=[
            ft.Column(
                [
                    header,
                    ft.Container(content=body, padding=24, expand=True),
                ],
                expand=True,
                spacing=0,
            )
        ],
    )
