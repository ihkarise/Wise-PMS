"""DatabaseAdapter protocol — the seam between `BaseRepository` and the
underlying database engine driver (ADR-002 §3, Option C).

`SQLiteAdapter` is the sole implementation in Sprint 4. Business logic
(services, controllers, views) never imports this module or any engine
driver directly — only `app.core.repository.BaseRepository` and
`app.core.database` depend on it.
"""

from dataclasses import dataclass
from typing import Any, Iterator, Protocol


@dataclass(frozen=True)
class Dialect:
    """Engine-specific SQL conventions.

    Only the ``sqlite`` dialect exists today. No repository currently
    branches on this — it exists so a second adapter (added only when a
    real deployment needs one, per ADR-002 §11) has a documented place to
    describe its differences, rather than repositories special-casing
    engines inline.
    """

    name: str
    placeholder: str = "?"


class DatabaseAdapter(Protocol):
    """Connection lifecycle + statement execution, independent of engine."""

    dialect: Dialect

    def connect(self) -> Any:
        """Return a new connection to the database."""
        ...

    def execute(self, conn: Any, sql: str, params: tuple = ()) -> Any:
        """Run one statement on `conn` and return its cursor."""
        ...

    def transaction(self) -> Iterator[Any]:
        """Context manager yielding a connection wrapped in one transaction:
        commits on success, rolls back on error, always closes."""
        ...
