"""Wise PMS — Shared composite widgets.

Reusable screen-level building blocks that were previously duplicated inside
individual views. Output is intentionally identical to the originals; call sites
pass the parameters that reproduce each screen's exact look.
"""

import flet as ft

from app.shared import theme as t


def empty_state(icon, primary, secondary=None, *, padding=32, icon_size=48,
                spacing=6, secondary_size=None):
    """Centered icon + muted line(s) inside a padded container.

    Replaces the three near-identical empty-state blocks in the dashboard,
    patient search and patient profile screens.
    """
    lines = [
        ft.Icon(icon, size=icon_size, color=t.TEXT_MUTED),
        t.muted(primary),
    ]
    if secondary:
        lines.append(t.muted(secondary, size=secondary_size) if secondary_size
                     else t.muted(secondary))
    return ft.Container(
        padding=padding,
        alignment=ft.alignment.center,
        content=ft.Column(
            lines,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=spacing,
        ),
    )


def stat_card(label, value, icon, color):
    """Dashboard statistic tile: tinted icon chip + big number + label."""
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


def info_item(label, value):
    """Uppercase label above a value (with an em-dash fallback for blanks)."""
    return ft.Column(
        [
            ft.Text(label.upper(), size=11, font_family=t.FONT,
                    color=t.TEXT_MUTED, weight=ft.FontWeight.W_600),
            ft.Text(str(value) if value not in (None, "") else "—",
                    size=15, font_family=t.FONT, color=t.TEXT_DARK),
        ],
        spacing=2, expand=True,
    )
