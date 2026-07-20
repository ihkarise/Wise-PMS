"""Audit — repository (data access for `audit_logs`)."""

from app.core.repository import BaseRepository


class AuditRepository(BaseRepository):
    def insert(self, user_id, action_type, entity_type, entity_id, details):
        self._execute(
            "INSERT INTO audit_logs "
            "(user_id, action_type, entity_type, entity_id, action_details) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, action_type, entity_type, entity_id, details),
        )
