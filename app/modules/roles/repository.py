"""Roles / RBAC — repository (all SQL for the RBAC tables).

Reads and the single role-assignment write. No authorization decision is made
here (that is a later milestone); this layer only stores and retrieves the
role/permission data.
"""

from typing import List, Optional

from app.core.repository import BaseRepository
from app.modules.roles.models import Role


class RoleRepository(BaseRepository):
    # -- roles / permissions ---------------------------------------
    def list_roles(self) -> List[dict]:
        return self._all("SELECT * FROM roles ORDER BY id")

    def get_role_by_name(self, name: str) -> Optional[dict]:
        row = self._one("SELECT * FROM roles WHERE name = ?", (name,))
        model = Role.from_row(row)
        return model.to_dict() if model else None

    def list_permissions(self) -> List[dict]:
        return self._all("SELECT * FROM permissions ORDER BY key")

    def permission_keys_for_role(self, role_name: str) -> List[str]:
        """The permission keys granted to a role, ascending by key."""
        return [
            r["key"]
            for r in self._all(
                "SELECT p.key FROM permissions p "
                "JOIN role_permissions rp ON rp.permission_id = p.id "
                "JOIN roles r ON r.id = rp.role_id "
                "WHERE r.name = ? ORDER BY p.key",
                (role_name,),
            )
        ]

    # -- user bindings ---------------------------------------------
    def roles_for_user(self, user_id: int) -> List[dict]:
        return self._all(
            "SELECT r.* FROM roles r "
            "JOIN user_roles ur ON ur.role_id = r.id "
            "WHERE ur.user_id = ? ORDER BY r.id",
            (user_id,),
        )

    def permission_keys_for_user(self, user_id: int) -> List[str]:
        """The distinct permission keys a user has, via their role binding.

        A pure read used by tests today and by the (later) authorization guard;
        it makes no access decision itself.
        """
        return [
            r["key"]
            for r in self._all(
                "SELECT DISTINCT p.key FROM permissions p "
                "JOIN role_permissions rp ON rp.permission_id = p.id "
                "JOIN user_roles ur ON ur.role_id = rp.role_id "
                "WHERE ur.user_id = ? ORDER BY p.key",
                (user_id,),
            )
        ]

    def is_user_active(self, user_id: int) -> bool:
        return bool(self._scalar(
            "SELECT is_active FROM users WHERE id = ?", (user_id,)
        ))

    def count_active_administrators(self) -> int:
        """Active users currently bound to the Administrator role."""
        return self._scalar(
            "SELECT COUNT(*) FROM user_roles ur "
            "JOIN roles r ON r.id = ur.role_id "
            "JOIN users u ON u.id = ur.user_id "
            "WHERE r.name = 'Administrator' AND u.is_active = 1"
        ) or 0

    def set_user_role(self, user_id: int, role_id: int) -> None:
        """Bind a user to exactly one role (replaces any existing binding).

        Enforces the one-active-role model together with the UNIQUE index
        ``idx_user_roles_user``.
        """
        with self.transaction() as conn:
            conn.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
            conn.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, role_id),
            )
