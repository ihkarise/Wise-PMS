"""Roles / RBAC — service (role-assignment rules + permission read API).

Milestone 1 scope: the role-assignment domain model and its invariants (one
active role per user; the system must always retain at least one active
Administrator).

Milestone 2 scope (added here): the read-side permission infrastructure —
``user_has_permission`` and the ``require_permission`` guard primitive. These
are **infrastructure primitives only**: they answer "does this user hold this
permission?" and raise on denial. They do **not** wire any route or
controller/service to enforce authorization — that is a later, separately
authorized milestone. Grants are resolved through the authoritative RBAC model
(``user → active role → role_permissions → permissions``); the legacy
``users.role`` column is never consulted.
"""

from typing import List, Optional, Union

from app.modules.audit.service import log_action
from app.modules.roles import permissions as perms
from app.modules.roles.repository import RoleRepository

_repo = RoleRepository()

# A caller may pass the session user dict, a bare user id, or a model/object
# exposing an ``id``.
UserRef = Union[dict, int, object]


class RoleError(Exception):
    """Raised when a role assignment would violate an RBAC invariant."""


class AuthorizationError(Exception):
    """Raised by ``require_permission`` when a user lacks the permission.

    A fail-closed denial primitive (approved denial model,
    ``docs/planning/SPRINT5_TECHNICAL_PLAN.md`` §8). Milestone 2 defines it;
    a later milestone decides where it is caught and rendered.
    """


def _resolve_user_id(user: UserRef) -> Optional[int]:
    """Extract a user id from a session dict, a bare id, or an object."""
    if user is None:
        return None
    if isinstance(user, bool):  # guard: bool is an int subclass
        return None
    if isinstance(user, int):
        return user
    if isinstance(user, dict):
        return user.get("id")
    return getattr(user, "id", None)


def user_has_permission(user: UserRef, permission_key: str) -> bool:
    """True iff ``user`` holds ``permission_key`` via their active role.

    Fail-closed for every edge case (approved denial model §8): a missing,
    unknown, or inactive user, an unknown permission key, or a user with no
    role binding all resolve to ``False``. Resolution goes through
    ``user_roles`` → ``role_permissions`` → ``permissions`` only; the legacy
    ``users.role`` column is never read.
    """
    user_id = _resolve_user_id(user)
    if user_id is None:
        return False
    if not _repo.is_user_active(user_id):
        return False
    return permission_key in set(_repo.permission_keys_for_user(user_id))


def require_permission(user: UserRef, permission_key: str) -> None:
    """Raise :class:`AuthorizationError` unless ``user`` holds the permission.

    The guard primitive for later enforcement; it makes no routing or UI
    decision itself.
    """
    if not user_has_permission(user, permission_key):
        raise AuthorizationError(f"Permission denied: {permission_key!r}")


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


# -- RBAC administration (Milestone 5) --------------------------------------
# Every function here is gated by `rbac.manage` via require_permission, before
# any read or mutation. Grants resolve through the RBAC service/repository only
# (the UI never touches role_permissions/user_roles directly), and role
# mutations still go through assign_role so the single-role and
# at-least-one-active-Administrator invariants hold. `actor` is the acting
# session user (dict/id); authorization is never derived from users.role.

def list_roles_with_permissions(actor: UserRef) -> List[dict]:
    """The predefined roles, each with its granted permission keys."""
    require_permission(actor, perms.RBAC_MANAGE)
    roles = _repo.list_roles()
    for role in roles:
        role["permissions"] = _repo.permission_keys_for_role(role["name"])
    return roles


def list_permission_catalogue(actor: UserRef) -> List[dict]:
    """The approved permission catalogue (the seeded permissions table)."""
    require_permission(actor, perms.RBAC_MANAGE)
    return _repo.list_permissions()


def list_users_with_roles(actor: UserRef) -> List[dict]:
    """Active users and their current active role (read-only, for selection)."""
    require_permission(actor, perms.RBAC_MANAGE)
    return _repo.list_active_users_with_role()


def _validated_role_and_permission(role_name: str, permission_key: str):
    role = _repo.get_role_by_name(role_name)
    if role is None:
        raise RoleError(f"Unknown role: {role_name!r}")
    if not perms.is_known_permission(permission_key):
        raise RoleError(f"Unknown permission: {permission_key!r}")
    permission = _repo.get_permission_by_key(permission_key)
    if permission is None:
        raise RoleError(f"Unknown permission: {permission_key!r}")
    return role, permission


def grant_permission(actor: UserRef, role_name: str, permission_key: str) -> None:
    """Add an approved permission to a predefined role (idempotent)."""
    require_permission(actor, perms.RBAC_MANAGE)
    role, permission = _validated_role_and_permission(role_name, permission_key)
    _repo.add_role_permission(role["id"], permission["id"])
    log_action(_resolve_user_id(actor), "Role Permission Granted", "role",
               role["id"], f"{role_name} + {permission_key}")


def revoke_permission(actor: UserRef, role_name: str, permission_key: str) -> None:
    """Remove a permission from a predefined role.

    Protects the "usable Administrator" invariant (ADR-003 §4.2): `rbac.manage`
    cannot be revoked from the Administrator role, or no one could administer
    RBAC afterwards.
    """
    require_permission(actor, perms.RBAC_MANAGE)
    role, permission = _validated_role_and_permission(role_name, permission_key)
    if role_name == "Administrator" and permission_key == perms.RBAC_MANAGE:
        raise RoleError(
            "Cannot revoke rbac.manage from the Administrator role — it would "
            "leave no one able to administer RBAC.")
    _repo.remove_role_permission(role["id"], permission["id"])
    log_action(_resolve_user_id(actor), "Role Permission Revoked", "role",
               role["id"], f"{role_name} - {permission_key}")


def admin_assign_user_role(actor: UserRef, user_id: int, role_name: str) -> None:
    """Assign an existing user to one predefined role, gated by rbac.manage.

    Delegates to assign_role so the single-active-role and
    at-least-one-active-Administrator invariants are preserved (never calls the
    repository's set_user_role directly)."""
    require_permission(actor, perms.RBAC_MANAGE)
    if not _repo.user_exists(user_id):
        raise RoleError(f"Unknown user: {user_id!r}")
    assign_role(user_id, role_name, actor_id=_resolve_user_id(actor))
