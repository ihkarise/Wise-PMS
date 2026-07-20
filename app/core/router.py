"""Wise PMS — Centralized router.

Replaces the hand-rolled ``if/elif`` dispatcher that lived in ``main.py``. The
router is generic infrastructure: it matches ``page.route`` against a registered
route table and calls the matching controller. Modules register their own routes
(see each module's ``controller.py``), so adding a screen never means editing a
growing conditional here.

Behavior preserved from Sprint 2:
- Every route except ``/login`` requires a logged-in user (session guard).
- Unmatched routes fall back to the dashboard.
- Any error during dispatch shows a friendly snackbar, never a traceback.
"""

import re

from app.shared.theme import snack


class Router:
    def __init__(self, page, routes, *, anonymous_handler, fallback_handler):
        """
        routes: iterable of (regex_pattern, handler). Each handler is called as
            handler(page, params: dict, query: str) -> ft.View.
        anonymous_handler: handler used when the session guard fails (login).
        fallback_handler: handler for unmatched routes and recovered errors
            (dashboard).
        """
        self.page = page
        self.routes = [(re.compile(p), h) for p, h in routes]
        self.anonymous_handler = anonymous_handler
        self.fallback_handler = fallback_handler

    # -- matching ---------------------------------------------------
    def _resolve(self, route):
        path, _, query = route.partition("?")
        for rx, handler in self.routes:
            m = rx.match(path)
            if m:
                return handler, m.groupdict(), query
        return None, {}, query

    def _is_authenticated(self):
        return bool(self.page.session.get("user"))

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
            handler, params, query = self._resolve(route)
            if handler is None:
                page.views.append(self.fallback_handler(page, {}, ""))
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
