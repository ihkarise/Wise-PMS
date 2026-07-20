"""Wise PMS — Screen 01: Login."""

import flet as ft

from app.modules.authentication.service import authenticate
from app.shared import theme as t


def login_view(page: ft.Page) -> ft.View:
    username = t.text_field("Username", width=320)
    password = t.text_field("Password", width=320, password=True)
    remember = ft.Checkbox(
        label="Remember Me",
        label_style=ft.TextStyle(font_family=t.FONT, size=14, color=t.TEXT_MUTED),
        active_color=t.PRIMARY,
    )
    error_text = ft.Text("", color=t.ACCENT, size=14, font_family=t.FONT)

    def do_login(e=None):
        error_text.value = ""
        if not username.value.strip() or not password.value:
            error_text.value = "Username and Password are required."
            page.update()
            return
        user = authenticate(username.value, password.value)
        if user is None:
            error_text.value = "Invalid Username or Password"
            page.update()
            return
        page.session.set("user", user)
        if remember.value:
            page.client_storage.set("wisepms.username", username.value.strip())
        page.go("/dashboard")

    def do_exit(e):
        page.window.close()

    password.on_submit = do_login
    saved = page.client_storage.get("wisepms.username")
    if saved:
        username.value = saved
        remember.value = True

    left_panel = ft.Container(
        expand=5,
        bgcolor=t.PRIMARY,
        padding=60,
        content=ft.Column(
            [
                ft.Container(height=40),
                ft.Container(
                    width=88, height=88, border_radius=22, bgcolor=t.WHITE,
                    alignment=ft.alignment.center,
                    content=ft.Stack(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.ADD, color=t.PRIMARY, size=52),
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(width=14, height=14, bgcolor=t.ACCENT,
                                         border_radius=3, right=12, top=12),
                        ],
                        width=88, height=88,
                    ),
                ),
                ft.Container(height=24),
                ft.Text("Wise PMS", size=48, weight=ft.FontWeight.BOLD,
                        font_family=t.FONT, color=t.WHITE),
                ft.Text("Smart Healthcare Management", size=18,
                        font_family=t.FONT, color="#C9D4F0"),
                ft.Container(height=32),
                ft.Text("From Registration to Recovery", size=14,
                        font_family=t.FONT, color="#9FB0DF"),
                ft.Container(height=60),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.WIFI_OFF, color="#9FB0DF", size=18),
                        ft.Text("Works fully offline · Data stays on this computer",
                                size=13, font_family=t.FONT, color="#9FB0DF"),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    form = t.card(
        ft.Column(
            [
                t.heading("Welcome back", size=28),
                t.muted("Sign in to continue to your clinic"),
                ft.Container(height=16),
                username,
                password,
                ft.Row([remember], width=320),
                error_text,
                ft.Container(height=8),
                ft.Row(
                    [
                        t.secondary_button("Exit", on_click=do_exit),
                        ft.Container(expand=True),
                        t.primary_button("Login", on_click=do_login,
                                         icon=ft.Icons.LOGIN),
                    ],
                    width=320,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        padding=40,
    )

    right_panel = ft.Container(
        expand=6,
        bgcolor=t.LIGHT_GRAY,
        alignment=ft.alignment.center,
        content=form,
    )

    return ft.View(
        route="/login",
        padding=0,
        controls=[ft.Row([left_panel, right_panel], expand=True, spacing=0)],
    )
