"""Wise PMS — Screen 05: Patient Profile (Sprint 2: tabs + timeline +
attachments + quick actions) and Edit Patient."""

import flet as ft

from app.services.attachment_service import (absolute_path, add_attachment,
                                             attachments_for_patient,
                                             delete_attachment)
from app.services.case_service import cases_for_patient
from app.services.patient_service import get_patient, update_patient
from app.services.timeline_service import timeline_for_patient
from app.services.visit_service import visits_for_patient
from app.ui import theme as t
from app.ui.shell import shell

CONSULTATION_TYPES = ["Walk-In", "Online", "Telephonic", "Home Visit"]
GENDERS = ["Female", "Male", "Other"]
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

_EVENT_STYLE = {
    "visit": (ft.Icons.MEDICAL_SERVICES, t.PRIMARY),
    "case": (ft.Icons.FOLDER_OPEN, "#2E9E5B"),
    "attachment": (ft.Icons.ATTACH_FILE, t.ACCENT),
}


def _info_item(label, value):
    return ft.Column(
        [
            ft.Text(label.upper(), size=11, font_family=t.FONT,
                    color=t.TEXT_MUTED, weight=ft.FontWeight.W_600),
            ft.Text(str(value) if value not in (None, "") else "—",
                    size=15, font_family=t.FONT, color=t.TEXT_DARK),
        ],
        spacing=2, expand=True,
    )


def _empty(icon, line1, line2=""):
    return ft.Container(
        padding=32, alignment=ft.alignment.center,
        content=ft.Column(
            [ft.Icon(icon, size=44, color=t.TEXT_MUTED), t.muted(line1)]
            + ([t.muted(line2, size=12)] if line2 else []),
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4,
        ),
    )


def _not_found(page) -> ft.View:
    body = ft.Column(
        [
            t.heading("Patient not found"),
            t.muted("This patient record does not exist or was removed."),
            ft.Container(height=12),
            t.primary_button("Back to Search",
                             on_click=lambda e: page.go("/search")),
        ]
    )
    return shell(page, "/search", body)


# ------------------------------------------------------------------
# Profile with tabs
# ------------------------------------------------------------------
def profile_view(page: ft.Page, patient_id: int) -> ft.View:
    p = get_patient(patient_id)
    if not p:
        return _not_found(page)

    user = page.session.get("user") or {}

    # ---------- Header + quick actions ----------
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def on_files_picked(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        saved = 0
        for f in e.files:
            try:
                add_attachment(patient_id, p["reg_no"], f.path, user.get("id"))
                saved += 1
            except Exception:
                pass
        if saved:
            t.snack(page, f"{saved} file(s) uploaded.")
            page.go(f"/patient/{patient_id}")  # rebuild view
        else:
            t.snack(page, "File upload failed.", error=True)

    file_picker.on_result = on_files_picked

    header = t.card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.CircleAvatar(
                            content=ft.Text((p["name"] or "?")[0].upper(),
                                            size=26, color=t.WHITE,
                                            font_family=t.FONT,
                                            weight=ft.FontWeight.BOLD),
                            bgcolor=t.PRIMARY, radius=34,
                        ),
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        t.heading(p["name"], size=24),
                                        ft.Container(
                                            content=ft.Text(
                                                p["reg_no"], size=13,
                                                color=t.WHITE,
                                                font_family=t.FONT,
                                                weight=ft.FontWeight.W_600),
                                            bgcolor=t.PRIMARY,
                                            padding=ft.padding.symmetric(
                                                horizontal=12, vertical=4),
                                            border_radius=20,
                                        ),
                                    ],
                                    spacing=12,
                                ),
                                t.muted(
                                    "  ·  ".join(
                                        str(x) for x in [
                                            f"{p.get('age')} yrs"
                                            if p.get("age") else None,
                                            p.get("gender"), p.get("phone"),
                                            p.get("place"),
                                        ] if x
                                    ) or "—"
                                ),
                            ],
                            spacing=4,
                        ),
                        ft.Container(expand=True),
                        t.secondary_button(
                            "Back", icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: page.go("/search")),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                ),
                ft.Divider(color=t.BORDER),
                ft.Row(
                    [
                        t.primary_button(
                            "New Visit", icon=ft.Icons.MEDICAL_SERVICES,
                            on_click=lambda e:
                                page.go(f"/patient/{patient_id}/visit/new")),
                        t.secondary_button(
                            "New Case", icon=ft.Icons.CREATE_NEW_FOLDER,
                            on_click=lambda e:
                                page.go(f"/patient/{patient_id}/case/new")),
                        t.secondary_button(
                            "Upload File", icon=ft.Icons.UPLOAD_FILE,
                            on_click=lambda e: file_picker.pick_files(
                                allow_multiple=True)),
                        ft.Container(expand=True),
                        t.secondary_button(
                            "Edit Patient", icon=ft.Icons.EDIT,
                            on_click=lambda e:
                                page.go(f"/patient/{patient_id}/edit")),
                    ],
                    spacing=12,
                ),
            ],
            spacing=12,
        ),
    )

    # ---------- Tab 1: Profile ----------
    profile_tab = ft.Column(
        [
            ft.Row([_info_item("Registration No", p["reg_no"]),
                    _info_item("Name", p["name"]),
                    _info_item("Age", p.get("age")),
                    _info_item("Gender", p.get("gender"))]),
            ft.Row([_info_item("Phone", p.get("phone")),
                    _info_item("WhatsApp", p.get("whatsapp")),
                    _info_item("Email", p.get("email")),
                    _info_item("Blood Group", p.get("blood_group"))]),
            ft.Row([_info_item("Place", p.get("place")),
                    _info_item("Occupation", p.get("occupation")),
                    _info_item("Doctor", p.get("doctor")),
                    _info_item("Consultation Type",
                               p.get("consultation_type"))]),
            ft.Row([_info_item("DOB", p.get("dob")),
                    _info_item("Registered On", (p.get("created_at") or "")[:10]),
                    _info_item("Address", p.get("address")),
                    _info_item("Notes", p.get("notes"))]),
        ],
        spacing=18,
    )

    # ---------- Tab 2: Cases ----------
    cases = cases_for_patient(patient_id)
    case_rows = [
        ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.FOLDER_OPEN, color=t.PRIMARY),
                    ft.Column(
                        [
                            ft.Text(c["case_title"] or "Untitled Case",
                                    size=15, font_family=t.FONT,
                                    weight=ft.FontWeight.W_600,
                                    color=t.TEXT_DARK),
                            t.muted(f"{c.get('diagnosis') or 'No diagnosis'}"
                                    f"  ·  {c['visit_count']} visit(s)"
                                    f"  ·  Opened {(c['created_at'] or '')[:10]}",
                                    size=12),
                        ],
                        spacing=2, expand=True,
                    ),
                    ft.Container(
                        content=ft.Text(c["status"] or "Open", size=12,
                                        color=t.WHITE, font_family=t.FONT),
                        bgcolor=t.PRIMARY if (c["status"] or "Open") == "Open"
                        else t.TEXT_MUTED,
                        padding=ft.padding.symmetric(horizontal=10, vertical=3),
                        border_radius=12,
                    ),
                    ft.IconButton(
                        ft.Icons.MEDICAL_SERVICES, icon_color=t.ACCENT,
                        tooltip="Start Visit for this case",
                        on_click=lambda e, cid=c["id"]: page.go(
                            f"/patient/{patient_id}/visit/new?case={cid}")),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=14,
            border=ft.border.only(bottom=ft.BorderSide(1, t.BORDER)),
            on_click=lambda e, cid=c["id"]:
                page.go(f"/patient/{patient_id}/case/{cid}"),
            ink=True,
        )
        for c in cases
    ]
    cases_tab = ft.Column(
        case_rows or [_empty(ft.Icons.FOLDER_OPEN, "No cases yet.",
                             "Click  New Case  to open one.")],
        spacing=0,
    )

    # ---------- Tab 3: Timeline ----------
    events = timeline_for_patient(patient_id)

    def open_event(ev):
        if ev["kind"] == "visit":
            page.go(f"/patient/{patient_id}/visit/{ev['id']}")
        elif ev["kind"] == "case":
            page.go(f"/patient/{patient_id}/case/{ev['id']}")

    timeline_items = []
    for ev in events:
        icon, color = _EVENT_STYLE[ev["kind"]]
        timeline_items.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            width=40, height=40, border_radius=12,
                            bgcolor=color + "1A",
                            alignment=ft.alignment.center,
                            content=ft.Icon(icon, color=color, size=20),
                        ),
                        ft.Column(
                            [
                                ft.Text(ev["title"], size=14,
                                        font_family=t.FONT,
                                        weight=ft.FontWeight.W_600,
                                        color=t.TEXT_DARK),
                                t.muted(ev["summary"], size=12),
                            ],
                            spacing=2, expand=True,
                        ),
                        ft.Column(
                            [
                                t.muted((ev["ts"] or "")[:16], size=12),
                                ft.Text(ev["extra"], size=12,
                                        font_family=t.FONT, color=color)
                                if ev["extra"] else ft.Container(),
                            ],
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=12,
                border=ft.border.only(bottom=ft.BorderSide(1, t.BORDER)),
                on_click=(lambda e, ev=ev: open_event(ev))
                if ev["kind"] != "attachment" else None,
                ink=ev["kind"] != "attachment",
            )
        )
    timeline_tab = ft.Column(
        timeline_items or [_empty(ft.Icons.TIMELINE, "No Visits Available",
                                  "Visits, cases and files appear here, "
                                  "newest first.")],
        spacing=0,
    )

    # ---------- Tab 4: Attachments ----------
    attachments = attachments_for_patient(patient_id)

    def open_file(a):
        try:
            path = absolute_path(a).replace("\\", "/")
            page.launch_url(f"file:///{path}")
        except Exception:
            t.snack(page, "Unable to open file.", error=True)

    def confirm_delete(a):
        def do_delete(e):
            delete_attachment(a["id"], user.get("id"))
            page.close(dlg)
            t.snack(page, "Attachment deleted.")
            page.go(f"/patient/{patient_id}")

        dlg = ft.AlertDialog(
            title=ft.Text("Delete attachment?", font_family=t.FONT),
            content=ft.Text(f"{a['file_name']} will be removed permanently.",
                            font_family=t.FONT),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.close(dlg)),
                t.danger_button("Delete", on_click=do_delete),
            ],
        )
        page.open(dlg)

    attach_rows = [
        ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PICTURE_AS_PDF if a["file_type"] == "PDF"
                            else ft.Icons.IMAGE if a["file_type"] == "Image"
                            else ft.Icons.INSERT_DRIVE_FILE,
                            color=t.PRIMARY),
                    ft.Column(
                        [
                            ft.Text(a["file_name"], size=14,
                                    font_family=t.FONT,
                                    weight=ft.FontWeight.W_600,
                                    color=t.TEXT_DARK),
                            t.muted(f"{a['file_type']}  ·  "
                                    f"{(a['uploaded_at'] or '')[:16]}", size=12),
                        ],
                        spacing=2, expand=True,
                    ),
                    ft.IconButton(ft.Icons.OPEN_IN_NEW, icon_color=t.PRIMARY,
                                  tooltip="Open",
                                  on_click=lambda e, a=a: open_file(a)),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=t.ACCENT,
                                  tooltip="Delete",
                                  on_click=lambda e, a=a: confirm_delete(a)),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=12,
            border=ft.border.only(bottom=ft.BorderSide(1, t.BORDER)),
        )
        for a in attachments
    ]
    attachments_tab = ft.Column(
        attach_rows or [_empty(ft.Icons.ATTACH_FILE, "No attachments yet.",
                               "Upload lab reports, ECGs, scans or documents.")],
        spacing=0,
    )

    tabs = t.card(
        ft.Tabs(
            selected_index=2 if events else 0,
            label_color=t.PRIMARY,
            unselected_label_color=t.TEXT_MUTED,
            indicator_color=t.ACCENT,
            tabs=[
                ft.Tab(text="Profile", content=ft.Container(
                    profile_tab, padding=16)),
                ft.Tab(text=f"Cases ({len(cases)})", content=ft.Container(
                    cases_tab, padding=8)),
                ft.Tab(text=f"Timeline ({len(events)})", content=ft.Container(
                    timeline_tab, padding=8)),
                ft.Tab(text=f"Attachments ({len(attachments)})",
                       content=ft.Container(attachments_tab, padding=8)),
            ],
            expand=True,
        ),
        padding=8,
        expand=True,
    )

    body = ft.Column([header, tabs], spacing=16, expand=True,
                     scroll=ft.ScrollMode.AUTO)
    return shell(page, f"/patient/{patient_id}", body)


# ------------------------------------------------------------------
# Edit patient (unchanged behaviour from Sprint 1)
# ------------------------------------------------------------------
def edit_view(page: ft.Page, patient_id: int) -> ft.View:
    p = get_patient(patient_id)
    if not p:
        return _not_found(page)

    user = page.session.get("user") or {}

    name = t.text_field("Patient Name *", value=p["name"], expand=True)
    age = t.text_field("Age *", value=str(p.get("age") or ""), width=120,
                       keyboard=ft.KeyboardType.NUMBER)
    gender = t.dropdown("Gender *", GENDERS, value=p.get("gender"), width=160)
    phone = t.text_field("Phone", value=p.get("phone"), expand=True)
    whatsapp = t.text_field("WhatsApp", value=p.get("whatsapp"), expand=True)
    email = t.text_field("Email", value=p.get("email"), expand=True)
    place = t.text_field("Place", value=p.get("place"), expand=True)
    doctor = t.text_field("Doctor", value=p.get("doctor"), expand=True)
    consultation = t.dropdown("Consultation Type", CONSULTATION_TYPES,
                              value=p.get("consultation_type"), width=220)
    dob = t.text_field("DOB (YYYY-MM-DD)", value=p.get("dob"), width=200)
    occupation = t.text_field("Occupation", value=p.get("occupation"),
                              expand=True)
    blood_group = t.dropdown("Blood Group", BLOOD_GROUPS,
                             value=p.get("blood_group"), width=160)
    address = t.text_field("Address", value=p.get("address"), expand=True,
                           multiline=True)
    notes = t.text_field("Notes", value=p.get("notes"), expand=True,
                         multiline=True)
    error_text = ft.Text("", color=t.ACCENT, size=14, font_family=t.FONT)

    def save(e):
        error_text.value = ""
        if not name.value.strip():
            error_text.value = "Patient Name is required."
            name.focus()
            page.update()
            return
        if not (age.value or "").strip().isdigit():
            error_text.value = "Age is required and must be a number."
            age.focus()
            page.update()
            return
        data = {
            "name": name.value.strip(),
            "age": int(age.value),
            "gender": gender.value,
            "dob": (dob.value or "").strip() or None,
            "phone": (phone.value or "").strip() or None,
            "whatsapp": (whatsapp.value or "").strip() or None,
            "email": (email.value or "").strip() or None,
            "address": (address.value or "").strip() or None,
            "place": (place.value or "").strip() or None,
            "occupation": (occupation.value or "").strip() or None,
            "blood_group": blood_group.value,
            "photo_path": p.get("photo_path"),
            "doctor": (doctor.value or "").strip() or None,
            "consultation_type": consultation.value,
            "notes": (notes.value or "").strip() or None,
        }
        try:
            update_patient(patient_id, data, user.get("id"))
        except Exception:
            t.snack(page, "Unable to save record. Please try again.",
                    error=True)
            return
        t.snack(page, "Patient updated successfully.")
        page.go(f"/patient/{patient_id}")

    form = t.card(
        ft.Column(
            [
                ft.Row([name, age, gender], spacing=16),
                ft.Row([phone, whatsapp, email], spacing=16),
                ft.Row([place, doctor, consultation], spacing=16),
                ft.Row([dob, blood_group, occupation], spacing=16),
                ft.Row([address], spacing=16),
                ft.Row([notes], spacing=16),
                error_text,
                ft.Divider(color=t.BORDER),
                ft.Row(
                    [
                        t.secondary_button(
                            "Cancel", icon=ft.Icons.CLOSE,
                            on_click=lambda e:
                                page.go(f"/patient/{patient_id}")),
                        ft.Container(expand=True),
                        t.primary_button("Save Changes", icon=ft.Icons.SAVE,
                                         on_click=save),
                    ]
                ),
            ],
            spacing=14,
        ),
    )

    body = ft.Column(
        [
            t.heading(f"Edit Patient — {p['reg_no']}"),
            t.muted("Registration number is never editable."),
            ft.Container(height=8),
            form,
        ],
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
    return shell(page, f"/patient/{patient_id}/edit", body)
