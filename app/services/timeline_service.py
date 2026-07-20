"""Compatibility shim → app.modules.timeline.service."""

from app.modules.timeline.service import timeline_for_patient  # noqa: F401

__all__ = ["timeline_for_patient"]
