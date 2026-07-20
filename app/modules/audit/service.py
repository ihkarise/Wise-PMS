"""Audit — service.

Records important actions. Never raises: auditing must not break a clinical
workflow (a failing audit write is swallowed, exactly as in Sprint 1).
"""

from app.modules.audit.repository import AuditRepository

_repo = AuditRepository()


def log_action(user_id, action_type, entity_type, entity_id, details=""):
    """Record an important action. Never raises."""
    try:
        _repo.insert(user_id, action_type, entity_type, entity_id, details)
    except Exception:
        pass
