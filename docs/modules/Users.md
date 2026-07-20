# Module: Users (Authentication)

**Status:** ✅ Built (auth) · 🟡 user management UI not built ·
**Path:** `app/modules/authentication/` · **Table:** `users`

## Purpose
Authenticate staff and record login/logout. Account **management** (create,
deactivate, assign roles) has no UI yet.

## Layers
`models.py` (`User`) · `repository.py` (`UserRepository.find_active_by_username`)
· `service.py` · `controller.py` · `view.py` (login screen).

## Public service API
- `authenticate(username, password) -> dict | None` — bcrypt `checkpw`; audits
  "User Login" on success; returns `None` for bad/blank credentials
- `logout(user) -> None` — audits "User Logout"

## Route
`^/login$` — the only screen not wrapped by the shared shell.

## Seeded account
`init_db()` seeds `admin` / `admin123` (role `Admin`, full name "Administrator")
only if absent. **Must be changed on first use** (see [`../SECURITY.md`](../SECURITY.md)).

## Session
On success the user dict is stored in `page.session["user"]`; the router's
session guard requires it for every non-`/login` route. The shell reads it for
the user chip and logout.

## Known limitations
No user-management screen (F4), no password-change UI, default creds, no lockout
(L6). `role` is stored but **not enforced** — see [`Roles.md`](./Roles.md).

## Future
User CRUD screen + RBAC enforcement (F3/F4). Passwords change flow, optional
2FA, and account lockout before any networked deployment.
