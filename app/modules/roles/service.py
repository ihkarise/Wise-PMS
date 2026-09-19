"""Roles / RBAC — service (domain rules for role assignment).

Milestone 1 scope: the role-assignment domain model and its invariants only —
one active role per user, and the system must always retain at least one active
Administrator. This is data-integrity domain logic, NOT authorization
enforcement (no route guard, no permission check that gates a feature — those
are later milestones).
"""

from typing import List

from app.modules.audit.service import log_action
from app.modules.roles.repository import RoleRepository

_repo = RoleRepository()


class RoleError(Exception):
    """Raised when a role assignment would violate an RBAC invariant."""


def permission_keys_for_user(user_id: int) -> List[str]:
    """The permission keys a user holds via their assigned role."""
    return _repo.permission_keys_for_user(user_id)


def roles_for_user(user_id: int) -> List[dict]:
    return _repo.roles_for_user(user_id)


def assign_role(user_id: int, role_name: str, actor_id: int = None) -> None:
    """Assign ``role_name`` as the user's single active role.

    Enforces the approved invariants:
    - one active role per user (the assignment replaces any existing binding);
    - the system must retain at least one active Administrator — demoting the
      last active Administrator is refused.

    Never touches credentials or other user data. Audited.
    """
    role = _repo.get_role_by_name(role_name)
    if role is None:
        raise RoleError(f"Unknown role: {role_name!r}")

    # At-least-one-active-Administrator invariant: block demoting the last one.
    if role_name != "Administrator" and _repo.is_user_active(user_id):
        currently_admin = any(
            r["name"] == "Administrator" for r in _repo.roles_for_user(user_id)
        )
        if currently_admin and _repo.count_active_administrators() <= 1:
            raise RoleError(
                "Cannot remove the last active Administrator; assign another "
                "Administrator first."
            )

    _repo.set_user_role(user_id, role["id"])
    log_action(actor_id, "Role Assigned", "user", user_id, f"role={role_name}")
