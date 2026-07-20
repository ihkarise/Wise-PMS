"""Wise PMS — Base row-mapped model.

`RowModel` is a mixin for dataclasses that mirror a database table. It provides
row <-> object mapping and dict serialization, giving the domain layer a single
typed definition of each entity while the UI continues to consume plain dicts.

Models are intentionally thin today (typed field definitions). They are the
natural home for future domain behavior and computed properties.
"""

from dataclasses import asdict, fields


class RowModel:
    """Mixin providing (de)serialization for table-backed dataclasses."""

    @classmethod
    def field_names(cls):
        """Return the model's field names (== its table columns)."""
        return [f.name for f in fields(cls)]

    @classmethod
    def from_row(cls, row):
        """Build a model from a sqlite3.Row / dict, ignoring unknown columns.

        Returns ``None`` when ``row`` is ``None`` so callers can pass through a
        missing record unchanged.
        """
        if row is None:
            return None
        allowed = set(cls.field_names())
        keys = row.keys() if hasattr(row, "keys") else row
        data = {k: row[k] for k in keys if k in allowed}
        return cls(**data)

    def to_dict(self):
        """Serialize to a plain dict with the same keys as the table row."""
        return asdict(self)
