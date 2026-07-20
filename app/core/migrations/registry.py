"""Ordered registry of all schema migrations.

Every migration the application knows about is listed here in ascending version
order. A new table or column change ships as a new ``vNNNN_*`` module whose
``MIGRATION`` is appended to :data:`MIGRATIONS`. The tuple is validated at import
so a duplicate or non-sequential version fails fast rather than corrupting a
clinic database at launch.
"""

from app.core.migrations.runner import Migration, MigrationError
from app.core.migrations.v0001_initial import MIGRATION as _V0001

MIGRATIONS: "tuple[Migration, ...]" = (
    _V0001,
)


def _validate(migrations: "tuple[Migration, ...]") -> "tuple[Migration, ...]":
    """Guard that versions are positive, unique, and gap-free from 1."""
    versions = [m.version for m in migrations]
    if versions != sorted(versions):
        raise MigrationError("Migrations must be listed in ascending version order.")
    if len(set(versions)) != len(versions):
        raise MigrationError(f"Duplicate migration version in registry: {versions}")
    expected = list(range(1, len(migrations) + 1))
    if versions != expected:
        raise MigrationError(
            f"Migration versions must be sequential from 1; got {versions}, "
            f"expected {expected}."
        )
    return migrations


_validate(MIGRATIONS)
