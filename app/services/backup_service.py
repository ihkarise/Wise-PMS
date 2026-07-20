"""Compatibility shim → app.modules.backup.service."""

from app.modules.backup.service import backup_now  # noqa: F401

__all__ = ["backup_now"]
