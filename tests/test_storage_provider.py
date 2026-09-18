"""StorageProvider tests (Sprint 4, ADR-002 §5.1).

Split into two sections per SPRINT4_TESTING_PLAN.md §2:

(a) Protocol-conformance tests -- exercise only save/open/delete/url_for,
    the universal contract. Must never reference absolute_path()/
    local_path(), which would silently reintroduce a local-disk
    assumption into provider-agnostic coverage.
(b) LocalDiskStorageProvider-specific tests -- explicitly scoped to the
    concrete class: path conventions, local_path(), path-traversal
    rejection.
"""

import os
import tempfile

os.environ.setdefault("WISE_PMS_HOME", tempfile.mkdtemp(prefix="wisepms_storage_"))


# -- (a) StorageProvider Protocol-conformance ---------------------------

def test_protocol_save_open_roundtrip():
    from app.core.storage import get_storage

    storage = get_storage()
    uri = storage.save("exports/roundtrip_test.txt", b"hello wise pms")
    assert isinstance(uri, str)
    assert storage.open(uri) == b"hello wise pms"


def test_protocol_delete_then_missing_is_noop():
    from app.core.storage import get_storage

    storage = get_storage()
    uri = storage.save("exports/to_delete.txt", b"bye")
    storage.delete(uri)
    # Deleting again must be a no-op, not raise.
    storage.delete(uri)


def test_protocol_url_for_never_raises():
    from app.core.storage import get_storage

    storage = get_storage()
    uri = storage.save("exports/url_for_test.txt", b"data")
    result = storage.url_for(uri)
    assert result is None or isinstance(result, str)


# -- (b) LocalDiskStorageProvider-specific -------------------------------

def test_local_disk_matches_attachment_path_convention():
    from app.config import paths
    from app.core.storage import get_storage

    storage = get_storage()
    key = os.path.join("attachments", "patient_P000123", "lab_20260101_120000.pdf")
    storage.save(key, b"%PDF-fake")
    full = os.path.join(paths.BASE_DIR, key)
    assert os.path.exists(full)
    assert full == os.path.join(paths.ATTACHMENTS_DIR, "patient_P000123",
                                "lab_20260101_120000.pdf")


def test_local_disk_matches_backup_path_convention():
    from app.config import paths
    from app.core.storage import get_storage

    storage = get_storage()
    key = os.path.join("backups", "backup_2026_01_01.zip")
    storage.save(key, b"PK\x03\x04fake-zip")
    full = os.path.join(paths.BASE_DIR, key)
    assert os.path.exists(full)
    assert full == os.path.join(paths.BACKUPS_DIR, "backup_2026_01_01.zip")


def test_local_path_resolves_absolute_path():
    from app.config import paths
    from app.core.storage import get_storage

    storage = get_storage()
    key = "attachments/patient_P000999/report.pdf"
    storage.save(key, b"data")
    assert storage.local_path(key) == os.path.join(paths.BASE_DIR, key)


def test_storage_provider_protocol_has_no_absolute_path_or_local_path():
    """Regression guard for Product Owner Revision 4: the universal
    Protocol must never grow a filesystem-path method."""
    from app.core.storage.base import StorageProvider

    protocol_methods = {
        name for name in vars(StorageProvider) if not name.startswith("_")
    }
    assert "absolute_path" not in protocol_methods
    assert "local_path" not in protocol_methods
    assert protocol_methods == {"save", "open", "delete", "url_for"}


def test_save_rejects_path_traversal():
    from app.config import paths
    from app.core.storage import get_storage

    storage = get_storage()
    malicious_keys = [
        "../../etc/passwd",
        "attachments/../../etc/passwd",
        "attachments/patient_1/evil\x00.txt",
    ]
    for key in malicious_keys:
        try:
            uri = storage.save(key, b"malicious")
        except (ValueError, OSError):
            continue  # rejecting outright is also acceptable
        # If it didn't reject, it must not have escaped BASE_DIR.
        full = os.path.abspath(os.path.join(paths.BASE_DIR, uri))
        assert full.startswith(os.path.abspath(paths.BASE_DIR)), (
            f"path traversal escaped BASE_DIR for key={key!r} -> {full!r}"
        )


if __name__ == "__main__":
    test_protocol_save_open_roundtrip()
    test_protocol_delete_then_missing_is_noop()
    test_protocol_url_for_never_raises()
    test_local_disk_matches_attachment_path_convention()
    test_local_disk_matches_backup_path_convention()
    test_local_path_resolves_absolute_path()
    test_storage_provider_protocol_has_no_absolute_path_or_local_path()
    test_save_rejects_path_traversal()
    print("[PASS] storage provider")
