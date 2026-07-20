"""Wise PMS — Design System (from Wise_PMS_Design_System.pdf)

Primary Blue : #1F3F8C   (navigation, headers, buttons, icons)
Primary Red  : #D6284D   (highlights, alerts, danger)
White        : #FFFFFF   (backgrounds, cards)
Light Gray   : #F5F7FA   (panels, forms, tables)
Dark BG      : #0B0D12   (dark theme — future)

Cards 16px · Buttons 12px · Inputs 10px · Font Poppins (fallback Inter)
Minimum button height 44px · Minimum readable font 14px
"""

import flet as ft

PRIMARY = "#1F3F8C"
PRIMARY_DARK = "#162E68"
ACCENT = "#D6284D"
WHITE = "#FFFFFF"
LIGHT_GRAY = "#F5F7FA"
DARK_BG = "#0B0D12"
TEXT_DARK = "#1A2238"
TEXT_MUTED = "#6B7280"
BORDER = "#E3E8F2"

FONT = "Poppins"

RADIUS_CARD = 16
RADIUS_BUTTON = 12
RADIUS_INPUT = 10

CARD_SHADOW = ft.BoxShadow(
    blur_radius=20,
    spread_radius=0,
    offset=ft.Offset(0, 4),
    color="#14000000",  # rgba(0,0,0,0.08)
)


def apply_theme(page: ft.Page) -> None:
    page.title = "Wise PMS — Smart Healthcare Management"
    page.bgcolor = LIGHT_GRAY
    page.padding = 0
    page.fonts = {}
    page.theme = ft.Theme(
        font_family=FONT,
        color_scheme=ft.ColorScheme(primary=PRIMARY, error=ACCENT),
    )
    page.window.min_width = 1366
    page.window.min_height = 768
    page.window.width = 1366
    page.window.height = 768


# ------------------------------------------------------------------
# Shared components
# ------------------------------------------------------------------
def primary_button(text, on_click=None, icon=None, expand=False):
    return ft.ElevatedButton(
        text,
        icon=icon,
        on_click=on_click,
        expand=expand,
        height=44,
        style=ft.ButtonStyle(
            bgcolor=PRIMARY,
            color=WHITE,
            overlay_color=PRIMARY_DARK,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_BUTTON),
            text_style=ft.TextStyle(font_family=FONT, weight=ft.FontWeight.W_600),
        ),
    )


def secondary_button(text, on_click=None, icon=None):
    return ft.OutlinedButton(
        text,
        icon=icon,
        on_click=on_click,
        height=44,
        style=ft.ButtonStyle(
            color=PRIMARY,
            side=ft.BorderSide(1.5, PRIMARY),
            shape=ft.RoundedRectangleBorder(radius=RADIUS_BUTTON),
            text_style=ft.TextStyle(font_family=FONT, weight=ft.FontWeight.W_600),
        ),
    )


def danger_button(text, on_click=None, icon=None):
    return ft.ElevatedButton(
        text,
        icon=icon,
        on_click=on_click,
        height=44,
        style=ft.ButtonStyle(
            bgcolor=ACCENT,
            color=WHITE,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_BUTTON),
            text_style=ft.TextStyle(font_family=FONT, weight=ft.FontWeight.W_600),
        ),
    )


def text_field(label, value="", width=None, expand=False, password=False,
               keyboard=None, on_change=None, multiline=False, hint=None):
    return ft.TextField(
        label=label,
        value=value or "",
        width=width,
        expand=expand,
        password=password,
        can_reveal_password=password,
        keyboard_type=keyboard,
        on_change=on_change,
        multiline=multiline,
        min_lines=3 if multiline else 1,
        hint_text=hint,
        bgcolor=WHITE,
        border_radius=RADIUS_INPUT,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        text_style=ft.TextStyle(font_family=FONT, size=14, color=TEXT_DARK),
        label_style=ft.TextStyle(font_family=FONT, size=14, color=TEXT_MUTED),
    )


def dropdown(label, options, value=None, width=None, expand=False):
    return ft.Dropdown(
        label=label,
        value=value,
        width=width,
        expand=expand,
        options=[ft.dropdown.Option(o) for o in options],
        bgcolor=WHITE,
        border_radius=RADIUS_INPUT,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        label_style=ft.TextStyle(font_family=FONT, size=14, color=TEXT_MUTED),
    )


def card(content, padding=24, expand=False, width=None):
    return ft.Container(
        content=content,
        bgcolor=WHITE,
        border_radius=RADIUS_CARD,
        padding=padding,
        shadow=CARD_SHADOW,
        expand=expand,
        width=width,
    )


def heading(text, size=28, color=TEXT_DARK):
    return ft.Text(text, size=size, weight=ft.FontWeight.BOLD,
                   font_family=FONT, color=color)


def muted(text, size=14):
    return ft.Text(text, size=size, font_family=FONT, color=TEXT_MUTED)


def snack(page: ft.Page, message: str, error: bool = False):
    page.open(
        ft.SnackBar(
            ft.Text(message, font_family=FONT, color=WHITE),
            bgcolor=ACCENT if error else PRIMARY,
        )
    )


def logo_block(size=40):
    """Wise PMS logo mark: blue rounded square, white cross, red pixel accent."""
    return ft.Row(
        [
            ft.Container(
                width=size,
                height=size,
                border_radius=size * 0.25,
                bgcolor=PRIMARY,
                alignment=ft.alignment.center,
                content=ft.Stack(
                    [
                        ft.Container(
                            content=ft.Icon(ft.Icons.ADD, color=WHITE,
                                            size=size * 0.6),
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(
                            width=size * 0.18,
                            height=size * 0.18,
                            bgcolor=ACCENT,
                            border_radius=2,
                            right=size * 0.12,
                            top=size * 0.12,
                        ),
                    ],
                    width=size,
                    height=size,
                ),
            ),
            ft.Column(
                [
                    ft.Text("Wise PMS", size=size * 0.45,
                            weight=ft.FontWeight.BOLD, font_family=FONT,
                            color=PRIMARY),
                    ft.Text("Smart Healthcare Management", size=size * 0.22,
                            font_family=FONT, color=TEXT_MUTED),
                ],
                spacing=0,
            ),
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
    )
