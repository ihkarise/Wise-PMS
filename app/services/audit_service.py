"""Compatibility shim → app.modules.audit.service."""

from app.modules.audit.service import log_action  # noqa: F401

__all__ = ["log_action"]
