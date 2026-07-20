"""Authentication — models."""

from dataclasses import dataclass
from typing import Optional

from app.core.model import RowModel


@dataclass
class User(RowModel):
    """A system user (mirrors the `users` table)."""

    id: Optional[int] = None
    username: Optional[str] = None
    password_hash: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[int] = None
    created_at: Optional[str] = None
