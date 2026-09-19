"""Roles / RBAC — models (mirror the v0003_rbac tables)."""

from dataclasses import dataclass
from typing import Optional

from app.core.model import RowModel


@dataclass
class Role(RowModel):
    """A role (mirrors the `roles` table)."""

    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_system: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class Permission(RowModel):
    """A permission capability key (mirrors the `permissions` table)."""

    id: Optional[int] = None
    key: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class RolePermission(RowModel):
    """A role→permission grant (mirrors the `role_permissions` table)."""

    role_id: Optional[int] = None
    permission_id: Optional[int] = None


@dataclass
class UserRole(RowModel):
    """A user→role binding (mirrors the `user_roles` table)."""

    user_id: Optional[int] = None
    role_id: Optional[int] = None
    created_at: Optional[str] = None
