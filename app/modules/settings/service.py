"""Settings — service (clinic-profile business rules + audit).

Security boundary (ADR-002 §6.6, §5.2 Configuration boundary): this
module exposes ONLY the six clinic-profile fields in `SETTINGS_FIELDS`
(clinic_name, doctor_name, clinic_address, phone, email, logo_path).
Database configuration, storage-provider configuration, backup-
destination configuration, API keys, and RBAC/security settings are
never accepted here -- `update_clinic_settings` rejects any other key.
Those require a future, RBAC-gated Administrator/Security surface, once
F3 (RBAC) and F7 (encryption at rest) exist -- never this module.
"""

import os
from typing import Optional

from app.core.storage import get_storage
from app.modules.audit.service import log_action
from app.modules.settings.repository import SETTINGS_FIELDS, SettingsRepository

_repo = SettingsRepository()

__all__ = [
    "SETTINGS_FIELDS", "get_clinic_settings", "update_clinic_settings",
    "upload_logo",
]


def get_clinic_settings() -> Optional[dict]:
    return _repo.get()


def update_clinic_settings(data: dict, user_id: int) -> dict:
    """Update the clinic-profile fields. Rejects any key outside
    `SETTINGS_FIELDS` -- the Configuration-boundary enforcement point
    (ADR-002 §5.2/§6.6; see tests/test_settings_domain.py)."""
    disallowed = set(data) - set(SETTINGS_FIELDS)
    if disallowed:
        raise ValueError(
            "Unsupported setting(s): " + ", ".join(sorted(disallowed)) +
            ". Only clinic-profile fields may be set through this module "
            "(clinic_name, doctor_name, clinic_address, phone, email, "
            "logo_path) -- see ADR-002 §6.6."
        )
    if not (data.get("clinic_name") or "").strip():
        raise ValueError("Clinic Name is required.")

    _repo.update(data)
    updated = _repo.get()
    log_action(user_id, "Settings Updated", "settings",
               updated["id"] if updated else None,
               f"Updated {data.get('clinic_name', '')}")
    return updated


def upload_logo(source_path: str, user_id: int) -> dict:
    """Store a new clinic logo via the StorageProvider (ADR-002 §5.1) and
    persist its path through the same whitelist/audit path as every other
    clinic-profile field. Returns the updated settings row."""
    current = get_clinic_settings() or {}
    ext = os.path.splitext(source_path)[1].lower() or ".png"
    key = os.path.join("data", f"clinic_logo{ext}")

    with open(source_path, "rb") as fh:
        data = fh.read()
    get_storage().save(key, data)

    fields = {f: current.get(f) for f in SETTINGS_FIELDS}
    fields["logo_path"] = key
    return update_clinic_settings(fields, user_id)
