"""Authentication — service (credential verification + audit)."""

from typing import Optional

import bcrypt

from app.modules.audit.service import log_action
from app.modules.authentication.repository import UserRepository

_repo = UserRepository()


def authenticate(username: str, password: str) -> Optional[dict]:
    """Return the user as a dict if credentials are valid, else None."""
    username = (username or "").strip()
    if not username or not password:
        return None

    user = _repo.find_active_by_username(username)
    if user is None:
        return None

    try:
        ok = bcrypt.checkpw(
            password.encode("utf-8"), (user.password_hash or "").encode("utf-8")
        )
    except (ValueError, TypeError):
        return None

    if not ok:
        return None

    log_action(user.id, "User Login", "user", user.id, f"{username} logged in")
    return user.to_dict()


def logout(user: dict) -> None:
    if user:
        log_action(
            user["id"], "User Logout", "user", user["id"],
            f"{user.get('username', '')} logged out",
        )
