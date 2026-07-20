# WiseOS Health — Testing

> Current test suite, philosophy, and the standard every phase must meet.
> **Last updated:** 2026-07-20.

## Running

```bash
pip install -r requirements-dev.txt
pytest -q                              # all suites
python tests/test_regression.py        # regression runnable standalone
```

All suites set `WISE_PMS_HOME` to a throwaway temp dir **before importing the
app**, so runtime paths resolve into isolation and **real clinic data is never
touched**. Current status: **4 passing**.

## Suites

| File | Guards | What it does |
| ---- | ------ | ------------ |
| `test_regression.py` | Behavior | Golden snapshot of the whole service layer: auth → patients → search → cases → visits → prescription extraction → timeline → attachments → backup → audit. The snapshot must stay **byte-identical** across refactors. |
| `test_models.py` | Schema/model parity | Each `RowModel` dataclass must define exactly its table's columns; fails on drift. |
| `test_router.py` | Routing contract | Session guard, static + dynamic route matching, `new` sentinel, `?case=` query, unmatched-route fallback — against a fake page. |
| `test_views_build.py` | UI build | Every view constructs into an `ft.View` without raising, against a seeded DB and a fake page. Event handlers are **not** exercised (need a live Flet runtime). |

## Philosophy

1. **Behavior is pinned, structure is free.** The regression golden lets code
   move between layers/modules while proving the app still does the same thing.
2. **No display required.** Views are built against a mock page so tests run
   headless in CI.
3. **Parity, not mocks, for the DB.** Tests use a real SQLite temp DB, so schema
   and SQL are exercised for real.

## The bar for every phase

Before a phase is "done" (per the charter's Quality Gates):

- [ ] `pytest -q` green (including the regression golden — update it only with a
      documented, intentional behavior change).
- [ ] New module ships its own `test_*` (service behavior + view-build at
      minimum).
- [ ] Model/table parity holds for any new table.
- [ ] Router contract holds for any new route.
- [ ] Imports clean; app starts; DB initializes.

## Gaps / future

- No **event-handler** (interaction) tests — needs a live Flet or Playwright
  harness; candidate once the Consultation Workspace lands.
- No CI yet — add a GitHub Action / SessionStart hook to run `pytest` on push
  (see [`DEPLOYMENT.md`](./DEPLOYMENT.md)).
- No coverage measurement configured.
