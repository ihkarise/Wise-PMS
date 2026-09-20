# .ai/WORK_LOG.md — Chronological work log

> Append an entry per work session. Newest first. **Updated:** 2026-09-20.

## 2026-09-20 — Sprint 5 closure confirmation + post-merge doc synchronization
**Type:** Documentation-only maintenance (no runtime code, tests, schema, or
behavior changed). **Branch:** `claude/eloquent-feynman-aj24sn`.

### Ground truth established
- `git` verified: `HEAD == origin/main == 10e0738` (Merge pull request **#14**
  from `claude/sprint-5-implementation`), working tree clean, no unexpected
  commits. Sprint 5 (F3 RBAC, ADR-003) is **merged and CLOSED**.
- Verified baseline green **after** merge: `python3 -m pytest -q` → **130
  passed** (0 failed/skipped/errors/warnings); `tests/test_layering.py` → 5
  passed; `tests/test_regression.py` (golden) → 1 passed.
- Verified against source: migration `v0003_rbac` creates
  `roles`/`permissions`/`role_permissions`/`user_roles` (5 roles, 16
  permissions, `idx_user_roles_user` UNIQUE); `app/modules/roles/` +
  `permissions.py` registry + `core/router.py` permission guard are present
  and wired. RBAC is genuinely enforced.

### Stale current-state documentation corrected
- `.ai/CURRENT_PHASE.md`, `.ai/NEXT_TASK.md`, `.ai/NEXT_PHASE.md` — had
  described Sprint 5 as an unmerged branch (`claude/sprint-5-implementation`,
  HEAD `ebe58fb`) "awaiting the Sprint 5 PR / release authorization". Updated
  to reflect the merge (PR #14, `10e0738`); next action is a Product Owner
  planning decision only.
- `docs/DATABASE.md` — `users.role` "RBAC not yet enforced" corrected to
  non-authoritative/enforced-via-`user_roles`; the four RBAC tables documented
  in full; removed from the "planned (not yet created)" list; table count and
  date stamp updated.
- `docs/modules/Users.md` — "role stored but not enforced" and "RBAC
  enforcement (F3)" listed as future, corrected (F3 delivered; F4 still open).
- `docs/modules/Settings.md` — "any authenticated user can reach this route"
  corrected; `/settings` is now gated by `settings.edit` (router + action).
- `docs/DEPLOYMENT.md` — F3 removed from the list of unmet multi-user
  preconditions (F7/F8/server-grade adapter still required).

### Intentionally NOT changed (historical / future records — correct as-is)
- ADR-002, ADR-003, ADR-0011 and all `docs/planning/SPRINT*` docs (point-in-time
  records), `docs/CHANGELOG.md` (`[Unreleased]`; no version tagging scheme),
  `specs/*` and planned `docs/modules/*` ("Design only / not implemented"),
  `docs/audits/*`. No implementation history rewritten.

### Result
- Re-ran after edits: **130 passed**, layering 5 passed, golden 1 passed —
  documentation-only changes confirmed to not affect code/tests/schema.
- No next sprint started; no feature implemented; no new migration.

## 2026-09-18 — Sprint 4: Cloud-Ready Architecture Seams + Settings UI (ADR-002)
**Planning branch:** `claude/wiseos-architecture-review-f6gd11` (merged to
`main` as PR #10). **Implementation branch:** `claude/sprint-4-implementation`
(based on the post-merge `main`).

### Phase 0 (re-grounding)
- Read the full architecture review this sprint's planning was based on:
  `docs/{ARCHITECTURE,TARGET_ARCHITECTURE,DATABASE,DECISIONS,DEPENDENCY_MAP,
  ROADMAP,MASTER_BACKLOG,KNOWN_LIMITATIONS,SECURITY,DEPLOYMENT}.md`,
  `specs/PRODUCT_CONSTITUTION.md`, `.ai/{ARCHITECTURE_RULES,PRODUCT_DIRECTION,
  CURRENT_PHASE,NEXT_PHASE}.md`, and the current `app/` tree
  (`core/{database,repository,model}.py`, `config/paths.py`,
  `modules/{attachments,backup,patients,registration}/*`, `shared/{shell,
  theme}.py`, `bootstrap.py`) plus every existing test file.
- Confirmed baseline green: `python3 -m pytest -q` → 31 passing, before
  any change.

### Planning (two review rounds, Product Owner approved)
- ADR-002 (Cloud-Ready Architecture) + 6 `SPRINT4_*` planning docs,
  revised twice per Product Owner feedback: readiness-tier vocabulary
  (Production-supported / Conditionally permitted-temporary /
  Architecture-ready), the SQLite network-deployment rule, the Settings
  security field whitelist, the `StorageProvider` interface correction
  (no universal `absolute_path()`), the Backup boundary, and the
  finalized canonical deployment-tier table (ADR-002 §8.0).
- Committed only the planning docs, pushed, opened PR #10, merged into
  `main` before any implementation branch was created (per the Product
  Owner's required Git sequence — no planning/implementation commit
  mixing).

### Implementation (per the approved 10-item scope)
- `app/core/db_adapters/`: `DatabaseAdapter` Protocol + `Dialect`
  (`base.py`); `SQLiteAdapter` (`sqlite_adapter.py`) — a line-for-line
  move of the pre-existing connection/transaction logic; `get_adapter()`
  singleton (`__init__.py`), single hardcoded `sqlite` branch.
- `app/core/repository.py`: `BaseRepository` delegates to `get_adapter()`
  instead of importing `app.core.database` directly; `_all/_one/_scalar/
  _execute/transaction()` signatures and return shapes unchanged.
- `app/core/database.py`: `get_connection()` is now a shim delegating to
  `SQLiteAdapter`; `sqlite3` import removed from this file.
- `app/core/storage/`: `StorageProvider` Protocol — `save`/`open`/
  `delete`/`url_for` only, **no** universal `absolute_path()` (`base.py`);
  `LocalDiskStorageProvider` (`local_disk_provider.py`) — reproduces the
  pre-existing path conventions verbatim, plus a `local_path()` helper
  kept off the Protocol, plus explicit path-traversal rejection
  (`_resolve()` confines every key under `BASE_DIR`); `get_storage()`
  singleton, single hardcoded `local` branch.
- `app/modules/attachments/service.py`: `add_attachment`/
  `delete_attachment` call `storage.save/delete`; `absolute_path()` calls
  `LocalDiskStorageProvider.local_path()` directly (documented local-only
  dependency). Public signatures unchanged.
- `app/modules/backup/service.py`: rewritten around the Backup boundary —
  `_build_archive()` (local filesystem walk, unchanged) writes to a temp
  file; the bytes are read and handed to `storage.save()` for the
  destination write only; naming/collision convention unchanged.
- `app/modules/settings/`: new vertical slice — `models.Settings`;
  `repository.SettingsRepository` + `SETTINGS_FIELDS` whitelist
  (`clinic_name`, `doctor_name`, `clinic_address`, `phone`, `email`,
  `logo_path` — mirrors the `PATIENT_FIELDS` convention);
  `service.update_clinic_settings` rejects any other key
  (`ValueError`) and audits every update; `service.upload_logo` is the
  first net-new caller of `StorageProvider`; `controller`/`view`
  (`^/settings$`, reachable from a new header gear icon).
- `app/bootstrap.py`, `app/shared/shell.py`: wired `SETTINGS_ROUTES` and
  the Settings nav icon — the only two files touched outside the new
  packages/module and the two migrated services.

### Tests
- New: `test_db_adapter.py` (connection/transaction parity + no-second-
  engine guard), `test_storage_provider.py` (Protocol-conformance split
  from `LocalDiskStorageProvider`-specific tests, including path-
  traversal rejection), `test_settings_domain.py` (CRUD, validation,
  audit, logo upload, field-whitelist rejection, `backup_path` read-only),
  `test_layering.py` (AST-based import/dependency boundary gates: no
  stray `sqlite3` import, no stray `shutil`/raw `os` write, no stray
  `local_path()` call site, no new runtime dependency, no out-of-scope
  driver/ORM/cloud-SDK import).
- Extended: `test_router.py` (`/settings` guard + resolution),
  `test_views_build.py` (`settings_view` build + a field-whitelist
  assertion over the rendered controls), `test_models.py` (`Settings`
  model/table parity).
- `python3 -m pytest -q` → **56 passing** (31 prior + 25 new). Regression
  golden (`test_regression.py`) unmodified and green — no `TABLES:`/
  `INDEXES:` change, confirming the two refactors are truly behavior-
  preserving.

### Docs (same session)
- `DATABASE.md` (DatabaseAdapter seam + settings-table UI note),
  `DEPLOYMENT.md` (SQLite network-deployment rule), `CHANGELOG.md`,
  `DECISIONS.md` (ADR-0010), `modules/Settings.md` (new),
  `modules/Attachments.md`, `modules/Backups.md` (Backup boundary),
  `MASTER_BACKLOG.md` (F2 closed; AR1/AR2 closed), `KNOWN_LIMITATIONS.md`
  (L7 closed; L12 formalized), `TARGET_ARCHITECTURE.md` (folder map +
  Settings status), `.ai/{CURRENT_PHASE,NEXT_TASK,NEXT_PHASE}.md` (this
  entry's companions).

### Result
- Not committed at the time this entry was written — self-review
  (Step 10 of the Sprint 4 Implementation Authorization) runs next, then
  commit + push `claude/sprint-4-implementation` + open the implementation
  PR against `main`. **No PR merge by this session** — Product Owner
  reviews first.

## 2026-07-20 — Sprint 2: Consultation Domain Model (C3, ADR-001 Option C)
**Branch:** `claude/sprint-2-implementation` (based on `origin/main`)

### Implementation (per approved ADR-001 Hybrid + Sprint 2 planning)
- Migration `app/core/migrations/v0002_consultations.py` — `consultations` table
  (1:1 with `visits`, UNIQUE `visit_id`), additive `up` + reversible `down`;
  appended to `registry.MIGRATIONS`. `visits` untouched.
- `consultation` slice: `models.Consultation`; `repository` (sole `consultations`
  writer: `create_draft`, `update`, `set_status`, `get`, `get_by_visit`,
  `open_draft_for_case`, `for_patient`); `service` lifecycle state machine
  (`draft → in_progress → completed`, `amended`/`locked` reserved; `_ALLOWED`
  transition table; `ConsultationLifecycleError`; audit each transition;
  `workspace_context` extended with the active consultation); `controller`
  create/open-draft on workspace open; `view` bottom-bar status read-back.
- Tests: `test_consultation_domain.py` (lifecycle, 1:1 invariant, illegal
  transition, draft isolation, audit); `test_migrations.py` (`v0002` create/
  rollback/unique, fresh==migrated, legacy stamping); `test_models.py`
  (`Consultation` parity); `test_regression.py` golden `TABLES:`/`INDEXES:`
  updated (intentional — ADR-0009). `python3 -m pytest -q` → **26 passing**.
- Docs: DATABASE, DECISIONS (ADR-0009), CHANGELOG, modules/{Consultation,Visits},
  MASTER_BACKLOG (C3), `.ai/{CURRENT_PHASE,NEXT_TASK}`.
- Deferred: Timeline source row (M5, optional); live editors/autosave UI;
  Investigation/OCR/AI (seams only — grep-verified no provider SDK import).
- Not committed — awaiting Product Owner review.

---

## 2026-07-20 — Sprint 1: Consultation Workspace Skeleton (C1)
**Branch:** `claude/consultation-workspace-skeleton-qi1nfx`

### Phase 0 (targeted re-grounding)
- Read the sprint's inputs only: `specs/CONSULTATION_WORKSPACE.md`,
  `.ai/{CURRENT_PHASE,NEXT_TASK,ARCHITECTURE_RULES,NEXT_PHASE}.md`;
  `app/bootstrap.py`, `core/router.py`, `shared/{shell,theme,widgets}.py`; the
  dashboard/visits/cases/patients controllers + views as pattern references; the
  four+ existing tests.
- Confirmed baseline green (`python3 -m pytest -q` → 16 passing) before changes.

### Scope kept (skeleton only — per charter)
No business logic, no persistence, no OCR/AI/Protocol/WhatsApp/Billing/
Dispensing/Investigation. Structure + navigation + honest placeholders. Sprint 0
(migrations/DB infra) untouched.

### Implementation
- New `app/modules/consultation/` vertical slice (composition-only — **no
  `models.py`, no `repository.py`, no SQL**):
  - `service.py` — `workspace_context(pid, cid)`: read-only composition over
    `patients.service.get_patient` + `cases.service.get_case`. No mutation.
  - `controller.py` — `workspace_controller` + `ROUTES`; parses the optional
    draft-visit sentinel and the `?section=` deep-link. Orchestrates only.
  - `view.py` — `workspace_view`: shell header + left section-nav rail + center
    section cards (Patient Summary = real read-only data; Chief Complaint,
    History, Diagnosis, Prescription, Remarks, Follow-up = placeholders) + right
    rail placeholder panels (Timeline, Investigations, OCR, Protocol, AI) +
    bottom status/action bar with **disabled** Print/Invoice/Dispense/WhatsApp/
    Complete Visit. Not-found → friendly state, never a crash.
- `app/shared/widgets.py` — new DRY helpers `disabled_button` and
  `placeholder_card` (10 call sites across the workspace).
- `app/shared/theme.py` — `card()` gains an optional `border` argument (used to
  highlight the active section; reusable).
- Navigation wiring: `bootstrap.py` registers `CONSULTATION_ROUTES`;
  `cases/view.py` gains a **Start Consultation** button that saves the case and
  opens the Workspace (the only cross-module edit — a nav link, no logic change).

### Tests
- `tests/test_router.py` — `_setup` now creates a case; contract extended to
  cover the workspace base route, `/visit/new`, `/visit/<id>`, and `?section=`.
- `tests/test_views_build.py` — builds the workspace (new draft, reopened visit,
  section deep-link, case-not-found path).
- `python3 -m pytest -q` → **16 passing** (regression golden byte-identical —
  no schema/behaviour change).

### Docs (same commit)
- `docs/modules/Consultation.md` (new), `docs/CHANGELOG.md`,
  `specs/CONSULTATION_WORKSPACE.md` (implementation-status note), `.ai/`
  state files (this log, `CURRENT_PHASE`, `NEXT_TASK`).

---

## 2026-07-20 — Sprint 0: Infrastructure Foundation (DB Migrations / F1)
**Branch:** `claude/wiseos-health-sprint-exec-w2jjvh`

### Phase 0 (targeted re-grounding)
- Read only what the sprint needed: `.ai/CURRENT_PHASE.md`, `NEXT_TASK.md`,
  `WORK_LOG.md`, `ARCHITECTURE_RULES.md`, `NEXT_PHASE.md`; `specs/
  IMPLEMENTATION_PLAN.md`; `app/core/{database,model,repository}.py`,
  `bootstrap.py`, `config/paths.py`; the four existing tests; `docs/DATABASE.md`.
- Confirmed baseline green (`python3 -m pytest -q` → 4 passing) before changes.

### Implementation
- New `app/core/migrations/` package (single-responsibility, DI'd connection):
  - `runner.py` — `Migration` dataclass, `MigrationError`, and the engine
    (`ensure_version_table`, `applied_versions`, `current_version`,
    `run_migrations`, `rollback`). Each migration stamped atomically with its DDL.
  - `registry.py` — ordered `MIGRATIONS` tuple, validated sequential-from-1.
  - `v0001_initial.py` — the former inline `SCHEMA` moved verbatim into `up`
    (create-if-not-exists → legacy DBs are no-op-stamped), with a child-first
    reversible `down`.
  - `__init__.py` — public API (`migrate`, `rollback_to`, `current_version`,
    `LATEST_VERSION`, …).
- `app/core/database.py` — removed the inline `SCHEMA`; `init_db()` now calls
  `migrate(conn)` then seeds admin + settings (seed kept in Python: bcrypt salt is
  non-deterministic, can't be static SQL). No duplicate schema logic left behind.
- `tests/test_migrations.py` — 12 tests: ledger basics, apply/stamp, idempotency,
  apply-only-pending, **legacy-DB stamping w/o data loss**, rollback-to-zero +
  re-apply, rollback no-op, partial rollback, irreversible/unknown-version raise,
  **fresh == migrated parity**, and an `init_db` integration/idempotency test.
- Regression golden: `TABLES` line now lists `schema_version` (documented
  intentional addition — ADR-0008; no service-behaviour change).

### Docs (same commit)
- `docs/DATABASE.md` — replaced the ⚠️ migration-gap section with the delivered
  framework + "how to add a migration"; source-of-truth now the migration set.
- `docs/DECISIONS.md` — **ADR-0008** (ordered idempotent migrations + ledger).
- `docs/CHANGELOG.md`, `docs/KNOWN_LIMITATIONS.md` (L1 closed),
  `.ai/KNOWN_ISSUES.md` (F1 closed), `CURRENT_PHASE.md`, `NEXT_TASK.md`.

### Result
- `python3 -m pytest -q` → **16 passing** (4 prior + 12 new).
- Verified `import app.bootstrap` + `init_db()` boot; ledger stamped at v1.
- Committed + pushed to the feature branch. **No PR** (charter). Awaiting Product
  Owner approval before Sprint 1 (proposed: Settings UI / F2).

## 2026-07-20 — Phase 2: Product Architecture & Clinical Workflow Design
**Branch:** `claude/wiseos-phase-2-architecture-6knli6`

### Phase 0 (re-grounding)
- Re-read the whole memory system before writing: `README.md`, all of `docs/`
  (vision, roadmap, backlog, architecture/target/dependency, database, API,
  clinical workflow, patient journey, design system, UI, security, deployment,
  testing, known limitations, decisions, lessons), all of `docs/modules/` (10
  built + 13 planned), all of `.ai/`, and the `app/` tree layout + constants.
- Confirmed: refactor + Phase 1 memory already complete; no runtime code to touch.

### Phase 2 (this session)
- Created `specs/` with **21 required specs + a README index** (22 files):
  - Foundation: `PRODUCT_CONSTITUTION.md` (permanent rulebook — all specs
    subordinate to it), `SCREEN_FLOW.md`, `PATIENT_FLOW.md`.
  - Clinical workflow: `CONSULTATION_WORKSPACE.md` (anchor feature),
    `NEW_CASE_WORKFLOW.md`, `FOLLOWUP_WORKFLOW.md`.
  - Engines: `PROTOCOL_ENGINE.md`, `INVESTIGATION_ENGINE.md`, `OCR_ENGINE.md`,
    `TIMELINE_ENGINE.md`.
  - Systems: `WHATSAPP_SYSTEM.md`, `PRINTER_SYSTEM.md`, `DISPENSING_SYSTEM.md`,
    `APPOINTMENT_SYSTEM.md`, `WAITING_QUEUE.md`.
  - Platform: `USER_ROLES.md`, `SETTINGS_SYSTEM.md`, `PATIENT_PORTAL.md`,
    `AI_ASSISTANT.md`.
  - Planning: `IMPLEMENTATION_PLAN.md`, `MASTER_PHASE_PLAN.md` (Stages A–E,
    Phases 2–22 with objectives/deliverables/deps/complexity/risk/manual-test/
    rollback/future hooks).
- Grounded every spec in the existing architecture (vertical slices, repository
  seam, narrative-first, offline-first, ₹0), backlog IDs (F1/F2/F3/F5/F7/F8, C1–
  C4, D1–D3, E1, B1–B5, A1–A3), and the future-product list.
- **No runtime code touched.** Docs-only change.

### Consistency review
- All relative links across `specs/` resolve (script-checked).
- All 21 required filenames present; local cross-refs use `./NAME.md`, doc refs
  use `../docs/...`.
- Backlog-ID usage consistent with the memory system (F1 dominant unlock).

### Result
- `python3 -m pytest -q` → **4 passing** (the PATH `pytest` uses a uv-isolated
  interpreter missing runtime deps; use `python3 -m pytest`).
- Updated `.ai/CURRENT_PHASE.md`, `.ai/NEXT_TASK.md`, and this log.
- Phase-end report delivered; awaiting Product Owner approval for Phase 3
  (proposed: Migrations / F1). No PR opened, per instruction.

## 2026-07-20 — Phase 1: Project Memory System
**Branch:** `claude/wiseos-health-architecture-1yumsy`

### Phase 0 (understand before modifying)
- Read git history, README, `main.py`, and the full `app/` tree (~3.1k LOC).
- Read existing docs: `ARCHITECTURE.md`, `TARGET_ARCHITECTURE.md`,
  `DEPENDENCY_MAP.md`. Confirmed the domain-driven refactor is **already
  implemented** (merged PR #1).
- Read core (`database.py`, `router.py`, `repository.py`, `model.py`),
  config (`paths.py`, `constants.py`), shared (`theme.py`, `shell.py`), utils
  (`prescription.py`), and every module service + controller route.
- Ran `pytest -q` → **4 passing**. Confirmed `.ai/` and `docs/modules/` did not
  exist.

### Phase 1 (this session)
- Created `docs/`: PRODUCT_VISION, ROADMAP, MASTER_BACKLOG, CHANGELOG,
  SYSTEM_OVERVIEW, DATABASE, API, CLINICAL_WORKFLOW, PATIENT_JOURNEY,
  DESIGN_SYSTEM, UI_GUIDELINES, SECURITY, DEPLOYMENT, TESTING,
  KNOWN_LIMITATIONS, DECISIONS, LESSONS_LEARNED. (ARCHITECTURE/DEPENDENCY_MAP/
  TARGET_ARCHITECTURE kept as-is.)
- Created `docs/modules/`: built modules (Patients, Cases, Visits, Timeline,
  Users, Backups, Attachments, Dashboard, Audit, Settings[schema-only]) from
  source; planned modules (Appointments, Protocols, OCR, Inventory, Dispensing,
  Printer, WhatsApp, Roles, Reports, Analytics, PatientPortal, Telemedicine, AI)
  as labeled design specs.
- Created `.ai/`: MEMORY, PROJECT_CONTEXT, CURRENT_PHASE, NEXT_PHASE, NEXT_TASK,
  ARCHITECTURE_RULES, PRODUCT_DIRECTION, KNOWN_ISSUES, IMPLEMENTATION_NOTES,
  DECISION_LOG, WORK_LOG, CLAUDE_NOTES.
- **No runtime code touched.** Docs-only change.

### Result
- Verified `pytest -q` still green.
- Phase-end report delivered; awaiting Product Owner approval for Phase 2
  (proposed: DB Migrations / F1).

### Interruption note
Worker process restarted mid-phase; resumed by checking which files existed and
continuing from the module/`.ai` docs. No duplication or data loss.
