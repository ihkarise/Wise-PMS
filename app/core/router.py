"""Wise PMS — Centralized router.

Replaces the hand-rolled ``if/elif`` dispatcher that lived in ``main.py``. The
router is generic infrastructure: it matches ``page.route`` against a registered
route table and calls the matching controller. Modules register their own routes
(see each module's ``controller.py``), so adding a screen never means editing a
growing conditional here.

Behavior:
- Every route except ``/login`` requires a logged-in user (session guard).
- After the session guard, a route that declares a required permission is
  gated by a **permission guard** (Sprint 5 / F3, ADR-003): the current user
  must hold that permission or the request is denied, fail-closed. The guard
  is injected (``has_permission`` / ``denied_handler``) so this core module
  never imports the RBAC service — the permission-resolution logic stays in
  ``app/modules/roles`` and is wired in by ``bootstrap``.
- Unmatched routes fall back to the dashboard.
- Any error during dispatch shows a friendly snackbar, never a traceback.

The authorization sequence is: request → session/authentication check →
permission check → route handler.
"""

import re

from app.shared.theme import snack


class Router:
    def __init__(self, page, routes, *, anonymous_handler, fallback_handler,
                 has_permission, denied_handler):
        """
        routes: iterable of (regex_pattern, handler, required_permission). The
            permission is a permission key (str) or ``None`` for a public /
            session-only route (e.g. ``/login``). Each handler is called as
            handler(page, params: dict, query: str) -> ft.View.
        anonymous_handler: handler used when the session guard fails (login).
        fallback_handler: handler for unmatched routes and recovered errors
            (dashboard).
        has_permission: callable(user, permission_key) -> bool. Injected from
            the RBAC service so the router does not import it directly.
        denied_handler: handler rendered when the permission guard fails
            (fail-closed authorization outcome).
        """
        self.page = page
        # Each route is (compiled_pattern, handler, required_permission|None).
        self.routes = [(re.compile(p), h, perm) for p, h, perm in routes]
        self.anonymous_handler = anonymous_handler
        self.fallback_handler = fallback_handler
        self.has_permission = has_permission
        self.denied_handler = denied_handler

    # -- matching ---------------------------------------------------
    def _resolve(self, route):
        path, _, query = route.partition("?")
        for rx, handler, perm in self.routes:
            m = rx.match(path)
            if m:
                return handler, m.groupdict(), query, perm
        return None, {}, query, None

    def _is_authenticated(self):
        return bool(self.page.session.get("user"))

    def _authorized(self, permission):
        """Fail-closed permission check for the current session user.

        A route with no declared permission (``None``) needs only a session
        (the session guard already ran). Any error while resolving permissions
        denies access rather than granting it.
        """
        if permission is None:
            return True
        user = self.page.session.get("user")
        try:
            return bool(self.has_permission(user, permission))
        except Exception:
            return False

    # -- Flet callbacks ---------------------------------------------
    def dispatch(self, e=None):
        page = self.page
        route = page.route

        # Session guard — everything except /login requires login.
        if route != "/login" and not self._is_authenticated():
            page.views.clear()
            page.views.append(self.anonymous_handler(page, {}, ""))
            page.update()
            return

        page.views.clear()
        try:
            handler, params, query, permission = self._resolve(route)
            if handler is None:
                page.views.append(self.fallback_handler(page, {}, ""))
            elif not self._authorized(permission):
                # Permission guard — fail-closed authorization outcome.
                page.views.append(self.denied_handler(page, params, query))
                snack(page, "You don't have permission to open that.",
                      error=True)
            else:
                page.views.append(handler(page, params, query))
        except Exception:
            # Never show a raw Python error to the user.
            recover = (self.fallback_handler if self._is_authenticated()
                       else self.anonymous_handler)
            page.views.append(recover(page, {}, ""))
            snack(page, "Something went wrong. Please try again.", error=True)

        page.update()

    def on_view_pop(self, e):
        if len(self.page.views) > 1:
            self.page.views.pop()
            self.page.go(self.page.views[-1].route)
