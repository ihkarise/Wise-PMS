"""Wise PMS — Audit Log Service (Sprint 1)."""

from app.database.db import get_connection


def log_action(user_id, action_type, entity_type, entity_id, details=""):
    """Record an important action. Never raises — auditing must not break the app."""
    try:
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO audit_logs "
                "(user_id, action_type, entity_type, entity_id, action_details) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, action_type, entity_type, entity_id, details),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass
