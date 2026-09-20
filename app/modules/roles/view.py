"""Roles / RBAC — Administrator-only administration screen (Sprint 5, M5).

Minimum `rbac.manage` surface: view the five predefined roles and the 16
approved permissions, edit a role's permission grants, and assign an existing
user to one predefined role. All reads and mutations go through
`app.modules.roles.service` (which enforces `rbac.manage` and preserves the
single-role and last-Administrator invariants); this view never touches the
RBAC tables directly. It is not user management (no create/delete/credentials).
"""

import flet as ft

from app.modules.roles import service as svc
from app.shared import theme as t
from app.shared.shell import shell

_ROUTE = "/admin/roles"


def rbac_admin_view(page: ft.Page) -> ft.View:
    user = page.session.get("user") or {}

    # Defense in depth: the route guard already requires rbac.manage, but if a
    # non-authorized caller reaches here the service raises and we render a
    # denial body rather than leaking the surface.
    try:
        roles = svc.list_roles_with_permissions(user)
        catalogue = svc.list_permission_catalogue(user)
        users = svc.list_users_with_roles(user)
    except svc.AuthorizationError:
        return shell(page, _ROUTE, t.card(
            ft.Column([
                t.heading("RBAC Administration", size=20),
                t.muted("You don't have permission to administer roles."),
            ], spacing=8)))

    role_names = [r["name"] for r in roles]
    all_keys = [p["key"] for p in catalogue]

    # -- role -> permission editing -------------------------------------
    def make_toggle(role_name, key):
        def handler(e):
            try:
                if e.control.value:
                    svc.grant_permission(user, role_name, key)
                    t.snack(page, f"Granted {key} to {role_name}.")
                else:
                    svc.revoke_permission(user, role_name, key)
                    t.snack(page, f"Revoked {key} from {role_name}.")
            except svc.AuthorizationError:
                t.snack(page, "You don't have permission to change roles.",
                        error=True)
            except svc.RoleError as exc:
                t.snack(page, str(exc), error=True)
            page.go(_ROUTE)  # rebuild from persisted state
        return handler

    role_cards = []
    for role in roles:
        granted = set(role["permissions"])
        checks = [
            ft.Checkbox(label=key, value=(key in granted),
                        on_change=make_toggle(role["name"], key))
            for key in all_keys
        ]
        role_cards.append(t.card(
            ft.Column(
                [
                    t.heading(role["name"], size=18),
                    t.muted(role.get("description") or ""),
                    ft.Row(checks, wrap=True, spacing=12, run_spacing=4),
                ],
                spacing=8,
            )
        ))

    # -- existing user -> role assignment -------------------------------
    def make_assign(uid, dd):
        def handler(e):
            try:
                svc.admin_assign_user_role(user, uid, dd.value)
                t.snack(page, "Role assigned.")
            except svc.AuthorizationError:
                t.snack(page, "You don't have permission to assign roles.",
                        error=True)
            except svc.RoleError as exc:
                t.snack(page, str(exc), error=True)
            page.go(_ROUTE)
        return handler

    user_rows = []
    for u in users:
        dd = t.dropdown("Role", role_names, value=u.get("role_name"), width=200)
        user_rows.append(ft.Row(
            [
                ft.Text(u["username"], size=14, font_family=t.FONT,
                        weight=ft.FontWeight.W_600, color=t.TEXT_DARK, width=160),
                t.muted(u.get("full_name") or ""),
                ft.Container(expand=True),
                dd,
                t.primary_button("Assign", icon=ft.Icons.CHECK,
                                 on_click=make_assign(u["id"], dd)),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ))

    body = ft.Column(
        [
            t.heading("RBAC Administration"),
            t.muted("Manage role permissions and assign existing users to a "
                    "role. Administrator-only."),
            ft.Container(height=8),
            t.heading("Roles & Permissions", size=20),
            ft.Column(role_cards, spacing=14),
            ft.Container(height=8),
            t.heading("User Role Assignment", size=20),
            t.card(ft.Column(user_rows or [t.muted("No users.")], spacing=10)),
        ],
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
    return shell(page, _ROUTE, body)
