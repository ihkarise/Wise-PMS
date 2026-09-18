"""LocalDiskStorageProvider — the sole `StorageProvider` implementation in
Sprint 4. Wraps the existing filesystem conventions verbatim: URIs are the
same relative-path strings already stored today in
`attachments.file_path` and returned by `backup.service.backup_now`, all
rooted at `app.config.paths.BASE_DIR`.

See ADR-002 §5.1 and `SPRINT4_TECHNICAL_PLAN.md` §4.
"""

import os
from typing import Optional

from app.config import paths


class LocalDiskStorageProvider:
    """StorageProvider backed by the local filesystem, rooted at BASE_DIR."""

    def _resolve(self, key: str) -> str:
        """Resolve `key` to an absolute path guaranteed to stay under
        BASE_DIR. Raises ValueError for any path-traversal attempt
        (SPRINT4_RISK_ASSESSMENT.md R6)."""
        base = os.path.abspath(paths.BASE_DIR)
        full = os.path.abspath(os.path.join(base, key))
        if os.path.commonpath([base, full]) != base:
            raise ValueError(f"storage key escapes the storage root: {key!r}")
        return full

    def save(self, key: str, data: bytes) -> str:
        full = self._resolve(key)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as fh:
            fh.write(data)
        return key

    def open(self, uri: str) -> bytes:
        with open(self._resolve(uri), "rb") as fh:
            return fh.read()

    def delete(self, uri: str) -> None:
        # Best-effort, matching the pre-existing attachment-delete semantics
        # (a missing file or permission error must never break a caller).
        try:
            full = self._resolve(uri)
            if os.path.exists(full):
                os.remove(full)
        except Exception:
            pass

    def url_for(self, uri: str, expires_in: Optional[int] = None) -> Optional[str]:
        # Local disk has no browsable/signed URL.
        return None

    # -- Local-only capability — NOT part of the StorageProvider Protocol --
    def local_path(self, uri: str) -> str:
        """Resolve a stored URI to a real filesystem path.

        This exists only on this concrete class (ADR-002 §5.1). Call sites
        that genuinely need a raw path (e.g.
        `attachments.service.absolute_path`, used for OS "open file" /
        print-preview actions) call this method directly against the
        `LocalDiskStorageProvider` instance — never through the
        `StorageProvider` Protocol type. A non-local provider has no
        equivalent method; those call sites are documented as a known
        local-only dependency to redesign whenever a non-local provider is
        introduced (out of scope for Sprint 4).
        """
        return self._resolve(uri)
