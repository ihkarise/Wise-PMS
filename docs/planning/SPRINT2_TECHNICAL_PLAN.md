# Sprint 2 — Technical Plan (v2): Consultation Domain Model (Hybrid / ADR-001)

**Architecture:** Option C (Hybrid) — frozen by
[`../architecture-decisions/ADR-001-Consultation-Domain.md`](../architecture-decisions/ADR-001-Consultation-Domain.md).
**Supersedes:** Sprint 2 planning v1 (Option A — extend `visits`). Obsolete.
**Depends on:** F1 migration runner (Sprint 0), C1 workspace skeleton (Sprint 1, `v0.5.0`).
**Status:** PLAN ONLY — no code. Await Product Owner approval.
**Date:** 2026-07-20

---

## 1. Objectives

1. Give the Consultation Workspace a real persistence spine as a **dedicated
   `consultations` aggregate** (the clinical document), separate from the
   `visits` event.
2. Enforce **one consultation per visit** (1:1, `visit_id FK`).
3. Deliver the **draft → completed** lifecycle with audit on every mutation.
4. Keep everything **additive and reversible**; `visits` and its slice are
   untouched.
5. Wire **extension seams** (not implementations) for AI Gateway, Investigation,
   OCR, Timeline — so later phases plug in without reworking the domain.

Non-goals: live editors/autosave UI, AI/OCR/Investigation logic, RBAC, Settings.
Sprint 2 = domain aggregate + service API + tests + seams.

## 2. Bounded contexts (from ADR-001)

```
Visit          = ENCOUNTER event      (visits)          unchanged
Consultation   = CLINICAL DOCUMENT    (consultations)   NEW — this sprint
Investigation  = independent module   (investigation_*) later; seam only now
OCR            = independent module   (ocr_results)     later; seam only now
AI             = one Gateway          (ai_gateway)       later; seam only now
Protocols      = independent module   (protocols/*)      later; seam only now
Attachments    = independent module   (attachments)      built
Timeline       = READ MODEL (no table)                   add 1 source query
```

Rule: **only `consultations/repository.py` writes `consultations`.** Workspace
composes services. No module talks to an AI provider directly — all AI egress via
the future `ai_gateway` (Sprint 2 defines the call site, not the gateway).

## 3. Data model — `consultations` (new table)

```
consultations
  id            INTEGER PK
  visit_id      INTEGER NOT NULL UNIQUE  FK -> visits(id)   # 1:1 invariant
  patient_id    INTEGER NOT NULL         FK -> patients(id) # denormalized for query/scope
  case_id       INTEGER                  FK -> patient_cases(id)
  chief_complaint  TEXT
  history          TEXT
  examination      TEXT
  diagnosis        TEXT
  remarks          TEXT
  status        TEXT NOT NULL DEFAULT 'draft'   # draft|in_progress|completed|amended|locked
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
  updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
```

- Narrative-first: all clinical fields **nullable/optional**; nothing forced.
- History/Prescription/Follow-up still live on `visits` until a later, deliberate
  phase — no duplication now.
- `visit_id UNIQUE` enforces one-consultation-per-visit at the DB level.
- `patient_id`/`case_id` denormalized → cheap timeline/report queries + future
  multi-clinic scoping (add `clinic_id` additively later).
- `created_at`/`updated_at` → future Cloud Sync conflict handling.
- **New table → regression golden `TABLES:` line changes once, intentionally**
  (ADR + CHANGELOG + DECISIONS in the same commit; not silent).

## 4. Consultation lifecycle

Five states on `consultations.status`. `amended` and `locked` are optional
(land fully in later phases) but the state machine + audit are designed now so
nothing blocks them.

```
 draft ──► in_progress ──► completed ──► amended ──► locked
   │            │              │            │
   └── the only editable states ┘      (re-completes back
        (writes allowed)                to completed each
                                        amend cycle)
```

### 4a. States
| State | Meaning | Editable? |
| ----- | ------- | --------- |
| `draft` | Created on workspace open; nothing authored yet | yes |
| `in_progress` | Doctor has authored ≥1 field (first save flips draft→in_progress) | yes |
| `completed` | Doctor finalized the document for this visit | no (read-back) |
| `amended` (opt.) | A completed doc was reopened + changed; each amend writes an audit trail entry, then returns to `completed` | transient/audited |
| `locked` (opt.) | Sealed for medico-legal retention; immutable | no, ever |

### 4b. Allowed transitions (all others rejected by the service)
```
draft        -> in_progress            (first field saved)
draft        -> completed              (finalize an empty-but-intentional doc — allowed)
in_progress  -> completed              (finalize)
in_progress  -> draft                  NOT allowed (no silent regression)
completed    -> amended               (reopen + edit; audited)   [later phase]
amended      -> completed              (re-finalize the amendment) [later phase]
completed    -> locked                (seal)                      [later phase]
amended      -> locked                (seal)                      [later phase]
locked       -> *                      NEVER (terminal, immutable)
```
Sprint 2 implements `draft → in_progress → completed`; `amended`/`locked` are
recognized-but-guarded (transition table present, enforcement wired when their
phase is approved).

### 4c. Flow
```
Workspace opens on a case
   → consultation.service.open_or_create_draft(visit_id, patient_id, case_id)
        · existing open doc for visit? return it
        · else INSERT status='draft'  (+ audit "Consultation Started")
   → save_consultation(id, fields, user)
        · guard status in (draft, in_progress); draft→in_progress on first write
        · UPDATE fields + updated_at   (+ audit "Consultation Updated")
   → complete_consultation(id, user)
        · guard status in (in_progress, draft) -> 'completed'
          (+ audit "Consultation Completed"); idempotent if already completed
   → [later] amend_consultation(id, user)   completed -> amended -> completed (audited)
   → [later] lock_consultation(id, user)     -> 'locked' (terminal, immutable)
```
One open document per visit (guaranteed by `visit_id UNIQUE` +
`open_draft_for_visit`).

### 4d. State ownership
- **`consultation.service` owns the state machine** — the single authority that
  validates transitions and stamps status. Repository does dumb persistence
  (`set_status`); view/controller never mutate status directly.
- No other module writes `consultations.status`. Workspace *reads* it (bottom-bar
  label) but transitions only through the service API.

### 4e. Future compatibility
- **Autosave:** the `draft`/`in_progress` editable window is the autosave target —
  a future UI sprint calls `save_consultation` on a debounce; `updated_at` already
  present; no schema change needed. Autosave never crosses into `completed`.
- **Audit history:** every transition already emits `audit.service.log_action`
  (actor + entity + action). A future append-only `consultation_revisions` table
  (its own additive migration) can snapshot field values per amend — the lifecycle
  hooks (amend cycle) are the insertion points; nothing here blocks it.
- **Digital signatures:** `completed`/`locked` are the signable states. Signature
  data (`signed_by`, `signed_at`, hash) arrives as **additive columns/table in a
  later migration**, gated behind RBAC (F3) + encryption; the lifecycle reserves
  `locked` as the post-signature terminal state.
- **Medico-legal records:** `locked` = immutable retention; combined with
  never-physical-delete (Constitution) + audit history + signature, yields a
  tamper-evident legal record. `locked_at`/retention fields are future additive
  columns; the terminal, no-exit `locked` state is defined now so later work only
  adds data, never reworks the machine.

## 5. Module layout — new `consultation` slice gains model + repository

ADR-001 makes `consultation` a **real domain** (not composition-only). Full
vertical slice:

- `consultation/models.py` — `Consultation(RowModel)` dataclass mirroring the table.
- `consultation/repository.py` — **all** `consultations` SQL on `BaseRepository`:
  `create_draft`, `update`, `set_status`, `get`, `get_by_visit`,
  `open_draft_for_visit`, `for_patient` (read model helper).
- `consultation/service.py` — lifecycle API (§4); audits each mutation; composes
  `visits.service`/`cases.service` for context; **no SQL**.
- `consultation/controller.py` — resolve/create draft on workspace open; wire
  save/complete entry points (buttons stay disabled this sprint).
- `consultation/view.py` — read-back only (show draft status in bottom bar); no
  new editable widgets.

`visits/*` = 🔒 unchanged. No two writers on any table.

## 6. Migration strategy

- `app/core/migrations/v0002_consultations.py`: `up` = `CREATE TABLE IF NOT
  EXISTS consultations (...)` + indexes (`idx_consultation_visit` UNIQUE,
  `idx_consultation_patient`); `down` = `DROP TABLE IF EXISTS consultations` +
  drop indexes (fully reversible — new table, no data migration).
- Append `MIGRATION` to `registry.MIGRATIONS`; `_validate` enforces sequential-from-1.
- `init_db()` already runs `migrate(conn)` → no bootstrap change.
- Idempotent (`IF NOT EXISTS`), forward-only, reversible → clean `rollback_to(1)`.

## 7. Extension seams (defined, not built)

- **AI Gateway:** `consultation.service` exposes context object
  `to_ai_context(consultation_id)` (plain dict) that a future
  `ai_gateway.request(capability, context)` consumes. No provider import anywhere
  in this sprint. Documented seam only.
- **Investigation:** `consultation` references orders/results by `visit_id`/
  `consultation_id`; no embedding. Seam = FK contract documented; table lands in
  its own phase.
- **OCR:** untouched; `ocr_results` augments `attachments`; values reach
  consultation via Investigation, never inline.
- **Timeline:** add one `TimelineRepository` SELECT over `consultations`
  (kind='consultation') — read model, no write coupling. Optional this sprint or
  deferred; low risk either way.

## 8. Testing strategy

See [`SPRINT2_TESTING_PLAN.md`](./SPRINT2_TESTING_PLAN.md). Headline: migration
create/rollback/parity; aggregate CRUD + lifecycle + 1:1 invariant + audit;
workspace still builds; **regression golden changes exactly once** (new `TABLES:`
line) and that diff is reviewed + documented, not rubber-stamped.

## 9. Risks

See [`SPRINT2_RISK_ASSESSMENT.md`](./SPRINT2_RISK_ASSESSMENT.md). Top: intended
golden change mistaken for regression; visit↔consultation drift; draft leakage
into timeline/stats; AI-seam scope creep.

## 10. Rollback plan

- Code: revert Sprint 2 commit → skeleton + Case/Visit screens remain.
- Schema: `rollback_to(1)` drops `consultations` (reversible `down`); `visits`,
  cases, patients, attachments untouched → zero data loss on the event record.

## 11. Acceptance criteria

1. `python3 -m pytest -q` green; regression golden diff = **only** the intended
   new `consultations` table line, documented (ADR + CHANGELOG + DECISIONS).
2. `v0002` applies on fresh + legacy DB (no data loss); `rollback_to(1)` clean;
   fresh == migrated parity.
3. `consultation` slice = models + repository + service + controller + view;
   only `consultations/repository.py` writes the table.
4. Lifecycle round-trips `draft → in_progress → completed`; illegal transitions
   rejected by `consultation.service`; `amended`/`locked` present in the guarded
   transition table (enforced in a later phase); `visit_id UNIQUE` enforced;
   every transition audited — proven headlessly.
5. AI/Investigation/OCR/Timeline seams documented; **none implemented**; no
   provider SDK imported.
6. Workspace builds/opens; bottom-bar actions stay disabled.
7. Docs + `.ai/` memory updated same commit; `MASTER_BACKLOG` C3 advanced.
