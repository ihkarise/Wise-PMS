"""Wise PMS — Authentication Service (Sprint 1)."""

from typing import Optional

import bcrypt

from app.database.db import get_connection
from app.services.audit_service import log_action


def authenticate(username: str, password: str) -> Optional[dict]:
    """Return the user as a dict if credentials are valid, else None."""
    username = (username or "").strip()
    if not username or not password:
        return None

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (username,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    try:
        ok = bcrypt.checkpw(
            password.encode("utf-8"), row["password_hash"].encode("utf-8")
        )
    except (ValueError, TypeError):
        return None

    if not ok:
        return None

    user = dict(row)
    log_action(user["id"], "User Login", "user", user["id"], f"{username} logged in")
    return user


def logout(user: dict) -> None:
    if user:
        log_action(
            user["id"], "User Logout", "user", user["id"],
            f"{user.get('username', '')} logged out",
        )
