"""Wise PMS — Settings: Clinic Profile (Sprint 4).

Exposes ONLY the six clinic-profile fields approved for this module:
clinic name, doctor name, address, phone, email, logo. Database,
storage-provider, backup-destination, API-key, and RBAC/security
configuration are explicitly out of scope for this UI -- see ADR-002 §6.6
and SPRINT4_TECHNICAL_PLAN.md §2.3/Part D. There is no control on this
page for any of those; `update_clinic_settings` also rejects them at the
service layer if anything ever tried to submit one.
"""

import flet as ft

from app.modules.settings.service import (get_clinic_settings,
                                          update_clinic_settings,
                                          upload_logo)
from app.shared import theme as t
from app.shared.shell import shell


def settings_view(page: ft.Page) -> ft.View:
    user = page.session.get("user") or {}
    settings = get_clinic_settings() or {}

    clinic_name = t.text_field("Clinic Name *",
                               value=settings.get("clinic_name") or "",
                               expand=True)
    doctor_name = t.text_field("Doctor Name",
                               value=settings.get("doctor_name") or "",
                               expand=True)
    clinic_address = t.text_field("Clinic Address",
                                  value=settings.get("clinic_address") or "",
                                  expand=True, multiline=True)
    phone = t.text_field("Phone", value=settings.get("phone") or "",
                         expand=True, keyboard=ft.KeyboardType.PHONE)
    email = t.text_field("Email", value=settings.get("email") or "",
                         expand=True)

    error_text = ft.Text("", color=t.ACCENT, size=14, font_family=t.FONT)
    logo_text = t.muted(settings.get("logo_path") or "No logo uploaded yet.")

    logo_picker = ft.FilePicker()
    page.overlay.append(logo_picker)

    def on_logo_picked(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        try:
            upload_logo(e.files[0].path, user.get("id"))
            t.snack(page, "Logo updated.")
            page.go("/settings")  # rebuild view, showing the new logo path
        except Exception:
            t.snack(page, "Logo upload failed. Please try again.", error=True)

    logo_picker.on_result = on_logo_picked

    def collect():
        return {
            "clinic_name": (clinic_name.value or "").strip(),
            "doctor_name": (doctor_name.value or "").strip() or None,
            "clinic_address": (clinic_address.value or "").strip() or None,
            "phone": (phone.value or "").strip() or None,
            "email": (email.value or "").strip() or None,
            "logo_path": settings.get("logo_path"),
        }

    def save(e):
        error_text.value = ""
        clinic_name.border_color = t.BORDER
        if not (clinic_name.value or "").strip():
            clinic_name.border_color = t.ACCENT
            error_text.value = "Clinic Name is required."
            clinic_name.focus()
            page.update()
            return
        try:
            update_clinic_settings(collect(), user.get("id"))
        except ValueError as exc:
            error_text.value = str(exc)
            page.update()
            return
        except Exception:
            t.snack(page, "Unable to save settings. Please try again.",
                   error=True)
            return
        t.snack(page, "Settings saved.")
        page.go("/settings")

    form = t.card(
        ft.Column(
            [
                t.heading("Clinic Profile", size=18),
                t.muted("Shown on printed documents and the app header. "
                       "Database, storage, backup, and security settings "
                       "are managed separately by an administrator."),
                ft.Container(height=8),
                ft.Row([clinic_name, doctor_name], spacing=16),
                ft.Row([phone, email], spacing=16),
                ft.Row([clinic_address], spacing=16),
                ft.Divider(color=t.BORDER),
                ft.Row(
                    [
                        logo_text,
                        ft.Container(expand=True),
                        t.secondary_button(
                            "Upload Logo", icon=ft.Icons.IMAGE,
                            on_click=lambda e: logo_picker.pick_files(
                                allow_multiple=False,
                                allowed_extensions=["png", "jpg", "jpeg"])),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                error_text,
                ft.Divider(color=t.BORDER),
                ft.Row(
                    [
                        ft.Container(expand=True),
                        t.primary_button("Save Settings", icon=ft.Icons.SAVE,
                                        on_click=save),
                    ],
                ),
            ],
            spacing=14,
        ),
    )

    body = ft.Column(
        [
            t.heading("Settings"),
            t.muted("Clinic profile only."),
            ft.Container(height=8),
            form,
        ],
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    return shell(page, "/settings", body)
