"""StorageProvider selection point (ADR-002 §5.1 and the Configuration
boundary, ADR-002 §5.2).

Exactly one provider exists in Sprint 4: `LocalDiskStorageProvider`.
There is no environment variable and no Settings UI control for this
selection — adding a second provider (S3/Azure Blob/GCS/MinIO/NAS) is a
future, separately approved phase, not built here.
"""

from app.core.storage.base import StorageProvider
from app.core.storage.local_disk_provider import LocalDiskStorageProvider

_provider = LocalDiskStorageProvider()


def get_storage() -> StorageProvider:
    """Return the active StorageProvider. Single hardcoded ``local``
    branch today (Sprint 4 Configuration boundary)."""
    return _provider


__all__ = ["StorageProvider", "LocalDiskStorageProvider", "get_storage"]
