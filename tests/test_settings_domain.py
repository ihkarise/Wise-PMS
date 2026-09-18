"""Settings domain tests (Sprint 4).

Covers CRUD on the six clinic-profile fields, validation, audit, logo
upload via StorageProvider, the field-whitelist rejection (the
Configuration-boundary enforcement point, ADR-002 §5.2/§6.6), and that
`backup_path` stays read-only through this module.
"""

import os
import tempfile

os.environ.setdefault("WISE_PMS_HOME", tempfile.mkdtemp(prefix="wisepms_settings_"))


def _fresh_db():
    from app.config import paths
    from app.core.database import init_db
    if os.path.exists(paths.DB_PATH):
        os.remove(paths.DB_PATH)
    init_db()


def test_get_clinic_settings_returns_seeded_row():
    from app.modules.settings.service import get_clinic_settings

    _fresh_db()
    settings = get_clinic_settings()
    assert settings is not None
    assert settings["id"] == 1


def test_update_clinic_settings_persists_all_six_fields_and_audits():
    from app.core.database import get_connection
    from app.modules.settings.service import (get_clinic_settings,
                                               update_clinic_settings)

    _fresh_db()
    data = {
        "clinic_name": "Wise Homeopathy",
        "doctor_name": "Dr. Wise",
        "clinic_address": "1 Clinic Road",
        "phone": "9000000000",
        "email": "clinic@example.com",
        "logo_path": None,
    }
    updated = update_clinic_settings(data, user_id=1)
    for field, value in data.items():
        assert updated[field] == value

    reloaded = get_clinic_settings()
    for field, value in data.items():
        assert reloaded[field] == value

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) c FROM audit_logs WHERE action_type = 'Settings Updated'"
        ).fetchone()
        assert row["c"] == 1
    finally:
        conn.close()


def test_update_clinic_settings_requires_clinic_name():
    from app.modules.settings.service import update_clinic_settings

    _fresh_db()
    try:
        update_clinic_settings({
            "clinic_name": "", "doctor_name": None, "clinic_address": None,
            "phone": None, "email": None, "logo_path": None,
        }, user_id=1)
        assert False, "expected ValueError for empty clinic_name"
    except ValueError as exc:
        assert "Clinic Name" in str(exc)


def test_update_clinic_settings_rejects_unsupported_fields():
    """The Configuration-boundary enforcement test (Product Owner
    Revision 3/7, SPRINT4_RISK_ASSESSMENT.md R13). This must fail loudly
    if a future edit tries to reintroduce a security-sensitive field."""
    from app.modules.settings.service import update_clinic_settings

    _fresh_db()
    forbidden_payloads = [
        {"clinic_name": "X", "backup_path": "/tmp/evil"},
        {"clinic_name": "X", "database_url": "postgres://evil"},
        {"clinic_name": "X", "storage_provider": "s3"},
        {"clinic_name": "X", "api_key": "sk-xxx"},
        {"clinic_name": "X", "role": "Admin"},
    ]
    for payload in forbidden_payloads:
        try:
            update_clinic_settings(payload, user_id=1)
            assert False, f"expected rejection for payload {payload!r}"
        except ValueError:
            pass


def test_backup_path_is_read_only_through_settings_module():
    """`backup_path` already exists on the `settings` table (Sprint 1) but
    must never be reachable through this module's whitelist."""
    from app.modules.settings.repository import SETTINGS_FIELDS

    assert "backup_path" not in SETTINGS_FIELDS
    assert set(SETTINGS_FIELDS) == {
        "clinic_name", "doctor_name", "clinic_address", "phone", "email",
        "logo_path",
    }


def test_upload_logo_writes_through_storage_provider_and_updates_path():
    from app.config import paths
    from app.modules.settings.service import (get_clinic_settings,
                                               update_clinic_settings,
                                               upload_logo)

    _fresh_db()
    update_clinic_settings({
        "clinic_name": "Wise Homeopathy", "doctor_name": None,
        "clinic_address": None, "phone": None, "email": None,
        "logo_path": None,
    }, user_id=1)

    src = os.path.join(os.environ["WISE_PMS_HOME"], "logo.png")
    with open(src, "wb") as fh:
        fh.write(b"\x89PNG fake logo bytes")

    updated = upload_logo(src, user_id=1)
    assert updated["logo_path"] is not None
    stored_full = os.path.join(paths.BASE_DIR, updated["logo_path"])
    assert os.path.exists(stored_full)
    with open(stored_full, "rb") as fh:
        assert fh.read() == b"\x89PNG fake logo bytes"

    # Clinic name must be unaffected by the logo-only upload.
    assert get_clinic_settings()["clinic_name"] == "Wise Homeopathy"


if __name__ == "__main__":
    test_get_clinic_settings_returns_seeded_row()
    test_update_clinic_settings_persists_all_six_fields_and_audits()
    test_update_clinic_settings_requires_clinic_name()
    test_update_clinic_settings_rejects_unsupported_fields()
    test_backup_path_is_read_only_through_settings_module()
    test_upload_logo_writes_through_storage_provider_and_updates_path()
    print("[PASS] settings domain")
