"""Wise PMS — Screen 03: New Case Registration."""

import flet as ft

from app.config.constants import BLOOD_GROUPS, CONSULTATION_TYPES, GENDERS
from app.services.patient_service import create_patient
from app.ui import theme as t
from app.ui.shell import shell


def registration_view(page: ft.Page) -> ft.View:
    user = page.session.get("user") or {}

    # Required (per build spec: Name, Age, Gender required; rest optional)
    name = t.text_field("Patient Name *", expand=True)
    age = t.text_field("Age *", width=120,
                       keyboard=ft.KeyboardType.NUMBER)
    gender = t.dropdown("Gender *", GENDERS, width=160)
    phone = t.text_field("Phone", expand=True,
                         keyboard=ft.KeyboardType.PHONE)
    place = t.text_field("Place", expand=True)
    doctor = t.text_field("Doctor", expand=True)
    consultation = t.dropdown("Consultation Type", CONSULTATION_TYPES,
                              value="Walk-In", width=220)

    # Optional
    dob = t.text_field("DOB (YYYY-MM-DD)", width=200)
    whatsapp = t.text_field("WhatsApp", expand=True,
                            keyboard=ft.KeyboardType.PHONE)
    email = t.text_field("Email", expand=True)
    address = t.text_field("Address", expand=True, multiline=True)
    occupation = t.text_field("Occupation", expand=True)
    blood_group = t.dropdown("Blood Group", BLOOD_GROUPS, width=160)
    notes = t.text_field("Notes", expand=True, multiline=True)

    error_text = ft.Text("", color=t.ACCENT, size=14, font_family=t.FONT)

    def collect():
        return {
            "name": name.value.strip(),
            "age": int(age.value) if (age.value or "").strip().isdigit() else None,
            "gender": gender.value,
            "dob": (dob.value or "").strip() or None,
            "phone": (phone.value or "").strip() or None,
            "whatsapp": (whatsapp.value or "").strip() or None,
            "email": (email.value or "").strip() or None,
            "address": (address.value or "").strip() or None,
            "place": (place.value or "").strip() or None,
            "occupation": (occupation.value or "").strip() or None,
            "blood_group": blood_group.value,
            "photo_path": None,
            "doctor": (doctor.value or "").strip() or None,
            "consultation_type": consultation.value,
            "notes": (notes.value or "").strip() or None,
        }

    def validate() -> bool:
        error_text.value = ""
        for field, label in ((name, "Patient Name"), (age, "Age")):
            field.border_color = t.BORDER
        gender.border_color = t.BORDER

        if not name.value.strip():
            name.border_color = t.ACCENT
            error_text.value = "Patient Name is required."
            name.focus()
            page.update()
            return False
        if not (age.value or "").strip():
            age.border_color = t.ACCENT
            error_text.value = "Age is required."
            age.focus()
            page.update()
            return False
        if not (age.value or "").strip().isdigit():
            age.border_color = t.ACCENT
            error_text.value = "Age must be a number."
            age.focus()
            page.update()
            return False
        if not gender.value:
            gender.border_color = t.ACCENT
            error_text.value = "Gender is required."
            page.update()
            return False
        return True

    def save(open_profile: bool):
        if not validate():
            return
        try:
            patient = create_patient(collect(), user.get("id"))
        except Exception:
            t.snack(page, "Unable to save patient. Please try again.", error=True)
            return
        t.snack(page, f"Patient saved — Registration No: {patient['reg_no']}")
        if open_profile:
            page.go(f"/patient/{patient['id']}")
        else:
            page.go("/register")  # fresh form for next registration

    def section(title):
        return ft.Text(title, size=16, weight=ft.FontWeight.BOLD,
                       font_family=t.FONT, color=t.PRIMARY)

    form = t.card(
        ft.Column(
            [
                section("Patient Information"),
                ft.Row([name, age, gender], spacing=16),
                ft.Row([phone, whatsapp], spacing=16),
                ft.Row([place, doctor, consultation], spacing=16),
                ft.Container(height=8),
                section("Additional Details (Optional)"),
                ft.Row([dob, blood_group, occupation], spacing=16),
                ft.Row([email], spacing=16),
                ft.Row([address], spacing=16),
                ft.Row([notes], spacing=16),
                error_text,
                ft.Divider(color=t.BORDER),
                ft.Row(
                    [
                        t.secondary_button(
                            "Cancel", icon=ft.Icons.CLOSE,
                            on_click=lambda e: page.go("/dashboard")),
                        ft.Container(expand=True),
                        t.secondary_button(
                            "Save + Open Profile", icon=ft.Icons.OPEN_IN_NEW,
                            on_click=lambda e: save(True)),
                        t.primary_button(
                            "Save Patient", icon=ft.Icons.SAVE,
                            on_click=lambda e: save(False)),
                    ],
                    spacing=12,
                ),
            ],
            spacing=14,
        ),
    )

    body = ft.Column(
        [
            t.heading("New Case Registration"),
            t.muted("Registration number is generated automatically (P000001…)"),
            ft.Container(height=8),
            form,
        ],
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    return shell(page, "/register", body)
