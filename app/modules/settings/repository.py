"""Settings — repository (all SQL for `settings`).

There is exactly one settings row, seeded by `core.database.init_db()`.
"""

from typing import Optional

from app.core.repository import BaseRepository
from app.modules.settings.models import Settings

# Clinic-profile columns writable through this module (Sprint 4 Settings
# security boundary -- ADR-002 §6.6 / SPRINT4_TECHNICAL_PLAN.md §2.3).
# Deliberately excludes `backup_path` and any database/storage/credential/
# RBAC column (none of which exist on this table). Mirrors the
# `PATIENT_FIELDS` convention in `patients/repository.py`.
SETTINGS_FIELDS = [
    "clinic_name", "doctor_name", "clinic_address", "phone", "email",
    "logo_path",
]


class SettingsRepository(BaseRepository):
    def get(self) -> Optional[dict]:
        row = self._one("SELECT * FROM settings ORDER BY id LIMIT 1")
        model = Settings.from_row(row)
        return model.to_dict() if model else None

    def update(self, data: dict) -> None:
        """Update the single settings row's clinic-profile columns.

        Always writes exactly `SETTINGS_FIELDS`, regardless of any other
        keys `data` may contain -- callers must already be restricted to
        this whitelist by the service layer
        (`settings.service.update_clinic_settings`).
        """
        current = self.get()
        settings_id = current["id"] if current else 1
        sets = ", ".join(f"{f} = ?" for f in SETTINGS_FIELDS)
        self._execute(
            f"UPDATE settings SET {sets} WHERE id = ?",
            [data.get(f) for f in SETTINGS_FIELDS] + [settings_id],
        )
