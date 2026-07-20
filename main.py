"""
Wise PMS — Smart Healthcare Management
Sprint 1: Login · Registration · Search · Patient Profile · Edit · Backup
Local-first. Offline. SQLite. ₹0/month.

Run:    python main.py
Login:  admin / admin123
"""

import flet as ft

from app.database.db import init_db
from app.ui import theme as t
from app.ui.case_record import case_view
from app.ui.dashboard import dashboard_view
from app.ui.login import login_view
from app.ui.patient_profile import edit_view, profile_view
from app.ui.patient_search import search_view
from app.ui.registration import registration_view
from app.ui.visit_entry import visit_view


def main(page: ft.Page):
    t.apply_theme(page)

    def route_change(e):
        route = page.route
        user = page.session.get("user")

        # Session guard — everything except /login requires login
        if route != "/login" and not user:
            page.views.clear()
            page.views.append(login_view(page))
            page.update()
            return

        page.views.clear()
        try:
            if route == "/login":
                page.views.append(login_view(page))
            elif route == "/dashboard":
                page.views.append(dashboard_view(page))
            elif route == "/register":
                page.views.append(registration_view(page))
            elif route == "/search":
                page.views.append(search_view(page))
            elif route.startswith("/patient/"):
                clean, _, query = route.partition("?")
                parts = clean.strip("/").split("/")
                pid = int(parts[1])
                sub = parts[2] if len(parts) > 2 else None
                arg = parts[3] if len(parts) > 3 else None

                if sub == "edit":
                    page.views.append(edit_view(page, pid))
                elif sub == "case":
                    cid = int(arg) if arg and arg != "new" else None
                    page.views.append(case_view(page, pid, cid))
                elif sub == "visit":
                    pre_case = None
                    if query.startswith("case="):
                        try:
                            pre_case = int(query.split("=", 1)[1])
                        except ValueError:
                            pre_case = None
                    vid = int(arg) if arg and arg != "new" else None
                    page.views.append(
                        visit_view(page, pid, vid, preselected_case=pre_case))
                else:
                    page.views.append(profile_view(page, pid))
            else:
                page.views.append(dashboard_view(page))
        except Exception:
            # Never show raw Python errors to the user
            page.views.append(dashboard_view(page) if user else login_view(page))
            t.snack(page, "Something went wrong. Please try again.", error=True)

        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")


if __name__ == "__main__":
    init_db()
    ft.app(target=main)
