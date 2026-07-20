"""Compatibility shim → app.modules.authentication.service.

Kept so existing imports (`from app.services.auth_service import authenticate`)
keep working after the domain-module refactor. New code should import from
``app.modules.authentication.service``.
"""

from app.modules.authentication.service import authenticate, logout  # noqa: F401

__all__ = ["authenticate", "logout"]
