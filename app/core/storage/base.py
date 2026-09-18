"""StorageProvider protocol — the seam between application code and a
file-storage backend (ADR-002 §5.1).

`LocalDiskStorageProvider` is the sole implementation in Sprint 4.
Deliberately cloud-compatible: there is **no** universal `absolute_path()`
or `local_path()` method here, because a cloud object (S3 key, Azure Blob,
GCS object) has no local filesystem path. A provider that needs one
exposes it as its own, concrete, non-Protocol capability (see
`LocalDiskStorageProvider.local_path`) — never on this interface.
"""

from typing import Optional, Protocol


class StorageProvider(Protocol):
    """Universal file-storage interface. Every current and future
    provider implements exactly this — no more."""

    def save(self, key: str, data: bytes) -> str:
        """Write `data` under `key` and return the storage URI."""
        ...

    def open(self, uri: str) -> bytes:
        """Return the bytes stored at `uri`."""
        ...

    def delete(self, uri: str) -> None:
        """Remove the object at `uri`. Best-effort: never raises."""
        ...

    def url_for(self, uri: str, expires_in: Optional[int] = None) -> Optional[str]:
        """Return a browsable/signed URL for `uri`, or `None` when the
        provider has no such concept (e.g. local disk)."""
        ...
