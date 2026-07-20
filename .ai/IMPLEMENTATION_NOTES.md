# .ai/IMPLEMENTATION_NOTES.md — Practical how-to for this codebase

> Concrete patterns and gotchas when writing code here. **Updated:** 2026-07-20.

## Add a new module (the standard recipe)
1. Create `app/modules/<domain>/` with:
   - `models.py` — `@dataclass` on `core.model.RowModel`, fields == table columns.
   - `repository.py` — `class XRepository(BaseRepository)`, SQL only. Use
     `self._one/_all/_scalar/_execute` and `self.transaction()` for multi-statement
     atomic writes.
   - `service.py` — module-level functions: rules + validation + `log_action`.
   - `controller.py` — handlers `handler(page, params, query) -> ft.View`; export
     `ROUTES = [(r"^/…$", handler), …]`.
   - `view.py` (or `views/`) — Flet controls only; wrap body in `shell(page,
     route, body)`.
2. Add the module's `ROUTES` to the tuple in `app/bootstrap.py`.
3. Add a nav button in `app/shared/shell.py` if needed.
4. Add the table via a migration (once F1 lands) — until then, extend `SCHEMA`
   with `CREATE TABLE IF NOT EXISTS` (new tables only; never alter existing ones).
5. Add tests: service behavior + `test_views_build` coverage; model/table parity
   for the new table; router contract for new routes.

## Repository patterns
- One connection per operation (`get_connection()`), row_factory = Row.
- Reads return `dict`/`list[dict]`; the service may wrap in a model if useful.
- Atomic multi-write: `with self.transaction() as conn: conn.execute(...)`.

## Router
- Routes are regex with named groups (`(?P<pid>\d+)`), matched against the path
  (query is split off and passed separately).
- Session guard is automatic: everything but `^/login$` needs a logged-in user.
- Return an `ft.View`; never raise to the user.

## Paths & config
- Import paths from `app.config.paths` (never hardcode); they honor
  `WISE_PMS_HOME`. `get_connection` resolves `DB_PATH` dynamically.
- Vocabularies from `app.config.constants`.

## Design
- Build UI with `theme.*` factories and `shared/widgets.py`. No hex, no raw
  buttons/fields.

## Testing gotchas
- Set `WISE_PMS_HOME` to a temp dir **before importing the app** (see existing
  tests) so real data is never touched.
- Views build against a mock page; event handlers are not exercised headless.
- If you intentionally change behavior, regenerate the regression golden and
  document it (CHANGELOG + DECISIONS).

## Prescription extraction
- Pure helper `app.utils.prescription.extract_prescription_items` — reuse it,
  don't reimplement. It's re-run (delete+insert) on every visit write.
