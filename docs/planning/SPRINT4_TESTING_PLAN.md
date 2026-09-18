# Sprint 4 — Testing Plan: Settings UI + Database/Storage Abstraction Seams

**Status:** PLAN ONLY — no code. Await Product Owner approval.
**Date:** 2026-08-07 · **Revision 1:** 2026-09-18 — split `StorageProvider`
Protocol-conformance tests from `LocalDiskStorageProvider`-specific tests
(no more `absolute_path()` on the Protocol); added a Settings field-
whitelist test; added a manual-checklist item verifying the Settings UI
shows only the 6 safe fields; added the SQLite network-deployment rule as
a documentation-only check. Runs on `pytest` per `docs/TESTING.md`
conventions (isolated `WISE_PMS_HOME` temp data dir; never touches real
clinic data).

## 1. Test strategy

Sprint 4 is two behavior-preserving refactors (`DatabaseAdapter`,
`StorageProvider`), one explicit Configuration boundary, and one small,
narrowly-scoped additive module (Settings). The test plan therefore has
three distinct jobs:

1. **Prove the refactors changed nothing** — parity tests comparing new
   adapter/provider output to the pre-refactor implementation, plus the
   existing full regression suite staying green untouched.
2. **Prove the Configuration/Settings boundary holds** — a field-
   whitelist test that fails CI if a future change tries to expose
   security-sensitive configuration through the F2 Settings UI.
3. **Cover the new Settings module** normally, the same way
   `test_consultation_domain.py` covered Sprint 2/3.

No behavior change is expected anywhere else in the app; the acceptance
bar is that `python3 -m pytest -q` produces the **same pass count plus
the new tests**, and the regression golden diff contains only the new
`^/settings$` route/view lines.

## 2. New test files

### `tests/test_db_adapter.py`
- `SQLiteAdapter.connect()` returns a connection with `row_factory =
  sqlite3.Row` and `PRAGMA foreign_keys = ON` (identical to today's
  `get_connection()`).
- `SQLiteAdapter.transaction()` commits on success, rolls back on
  exception, always closes — same contract `BaseRepository.transaction()`
  documents today; assert via a forced exception mid-transaction leaves
  no partial write.
- `BaseRepository._all/_one/_scalar/_execute` produce identical output
  (same dict shapes, same `lastrowid` behavior) before/after the adapter
  is wired in — run against a representative repository (e.g.
  `PatientRepository`) with fixed fixture data.
- `core.database.get_connection()` (the shim) is behaviorally identical
  to calling `SQLiteAdapter().connect()` directly.
- **No test in this file exercises a second engine** — there is only one
  adapter this sprint; asserting otherwise would misrepresent scope.

### `tests/test_storage_provider.py` (revised — Revision 1/4)

Split into two clearly separated sections:

**(a) `StorageProvider` Protocol-conformance tests** — run against
whatever the current implementation is, asserting only the universal
contract:
- `save()`/`open()`/`delete()` round-trip correctly for arbitrary bytes.
- `delete()` on a missing URI is a no-op.
- `url_for()` returns `None` or a string; never raises for a valid URI.
- **These tests must not reference `absolute_path()` or `local_path()`**
  — that would silently reintroduce a local-disk assumption into what is
  meant to be provider-agnostic test coverage.

**(b) `LocalDiskStorageProvider`-specific tests** — explicitly scoped to
the concrete class, not the Protocol:
- `save()` reproduces the exact path convention of
  `attachments.service.add_attachment` (`attachments/patient_<reg_no>/
  <stem>_<timestamp><ext>`) for the same inputs.
- `save()` reproduces the exact path convention of
  `backup.service.backup_now`'s destination write
  (`backups/backup_YYYY_MM_DD[_HHMMSS].zip`).
- `local_path()` returns a correct absolute filesystem path for a given
  URI — tested only here, never assumed elsewhere.
- **Security case (R6):** `save()` rejects/sanitizes a path-traversal
  filename (`../../etc/passwd`, embedded null byte, absolute path) —
  never writes outside its configured root.

### `tests/test_settings_domain.py` (extended — Revision 1/3)
- `get_clinic_settings()` returns the single seeded row.
- `update_clinic_settings(data, user_id)` persists changes and writes an
  audit row (`"Settings Updated"`), for each of the 6 whitelisted fields
  (`clinic_name`, `doctor_name`, `clinic_address`, `phone`, `email`,
  `logo_path`).
- Validation: empty `clinic_name` is rejected with the same style of
  error the patient/case services use today.
- Logo upload: a `settings_view` upload call results in a file written
  via `StorageProvider.save()` and `settings.logo_path` updated to the
  returned URI — proves the provider end-to-end on a fresh code path
  before `attachments`/`backup` are migrated onto it.
- **New — field-whitelist rejection test (Configuration boundary, Part
  D):** calling `update_clinic_settings` with any key outside the
  whitelist (e.g. `backup_path`, `database_url`, `storage_provider`,
  `api_key`, `role`) raises/rejects rather than silently persisting it.
  This is the CI-enforced guarantee behind Revision 3/7's Settings
  security boundary.
- **New — `backup_path` is read-only:** confirm `update_clinic_settings`
  cannot change the existing `backup_path` column even though it is
  already present in the `settings` table schema.

## 3. Extended existing tests

- `tests/test_regression.py` — golden gains exactly the new
  `^/settings$` route entry and `settings_view` in the view-build list;
  no `TABLES:`/`INDEXES:` line changes (Sprint 4 adds zero tables/columns).
  Any other diff fails the gate.
- `tests/test_router.py` — router-contract coverage extended to
  `^/settings$` (session guard applies; not-found/guard behavior matches
  every other authenticated route).
- `tests/test_views_build.py` — `settings_view` added to the view-build
  smoke test (builds without a live `page`, per the existing pattern);
  the built view is asserted to contain no field/control bound to a
  non-whitelisted setting.
- **Full existing suite (regression, model/table parity, consultation
  domain, migration runner, router, views) must stay green, unmodified in
  assertions** — this is the primary signal that the two refactors are
  truly behavior-preserving.

## 4. Manual test checklist (per Article IX §3 "standard report")

- [ ] Fresh `data/wise_pms.db` (delete or point `WISE_PMS_HOME` at an
      empty dir) → app boots, admin/admin123 login works, `settings` row
      seeded as before.
- [ ] Existing (pre-Sprint-4) `data/wise_pms.db` + `attachments/` +
      `backups/` fixture → app boots, all existing patient records,
      attachments, and backups remain readable with no path errors.
- [ ] Navigate to Settings from the header nav; **confirm the form shows
      exactly 6 fields — clinic name, doctor name, address, phone, email,
      logo — and nothing else** (no database, storage, backup-destination,
      API-key, or permissions control anywhere on the page).
- [ ] Edit clinic name/address/phone/email; Save; reload the app; changes
      persisted.
- [ ] Upload a clinic logo in Settings; file appears under the expected
      path; `settings.logo_path` updated; logo renders in the header
      block (if wired) or profile view.
- [ ] Create a patient, add an attachment, take a backup (header Backup
      button) — all three exercise the migrated `StorageProvider` path;
      confirm files land in the same folders as before the migration.
- [ ] Confirm `audit_logs` gains a `"Settings Updated"` row after a save.
- [ ] Confirm no traceback is ever shown to the user (router error
      containment still holds for the new route).
- [ ] **Documentation check (not a runtime test):** confirm
      `docs/DEPLOYMENT.md`/`docs/DATABASE.md` (once updated per
      `SPRINT4_MILESTONE_CHECKLIST.md` M8) do not suggest running the
      shipped SQLite database from a network/shared drive — this is a
      review-time check against ADR-002 §8.1, not an automated test.

## 5. Layering & convention gates (static checks, no runtime)

- `app/modules/settings/*` imports only `app.core.*`, `app.shared.*`,
  `app.config.*` — no cross-module imports beyond `audit.service`
  (matches every other write-module's pattern).
- No file outside `app/core/db_adapters/` imports `sqlite3` directly
  (grep gate) — proves the adapter seam is actually enforced, not just
  added alongside the old import.
- No file outside `app/core/storage/` imports `shutil`/raw `os.remove`/
  `os.makedirs` against attachment/backup paths (grep gate) — same
  enforcement for the storage seam. (`os.path.join`/`os.path.exists` for
  read-only path composition remain fine anywhere, per existing
  convention.)
- **New:** no file outside `app/core/storage/local_disk_provider.py`
  calls `.local_path(` or references `LocalDiskStorageProvider` by name
  where a `StorageProvider`-typed reference would do (grep gate) — proves
  the Protocol/local-only-helper split (Revision 4) is actually observed.
- No new entry in `requirements.txt`/`requirements-dev.txt` (Sprint 4
  adds zero dependencies — a diff there fails review).

## 6. Definition of done (testing)

- [ ] `python3 -m pytest -q` green; pass count = previous count + new
      Sprint 4 tests; zero unexpected golden diff.
- [ ] Parity tests (`test_db_adapter.py`, `test_storage_provider.py`
      Protocol section) pass, proving byte-identical behavior to the
      pre-Sprint-4 implementation.
- [ ] `LocalDiskStorageProvider`-specific tests pass, including the
      path-traversal rejection case.
- [ ] Field-whitelist rejection test passes (Configuration boundary
      enforced in code, not just documentation).
- [ ] Manual test checklist (§4) executed against both a fresh DB and an
      existing pre-Sprint-4 fixture DB.
- [ ] Layering/import grep gates (§5) clean.
