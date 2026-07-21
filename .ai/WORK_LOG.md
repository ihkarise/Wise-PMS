# .ai/WORK_LOG.md — Chronological work log

> Append an entry per work session. Newest first. **Updated:** 2026-07-20.

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
