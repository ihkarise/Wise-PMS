# WiseOS Health — Architecture Decision Records

> Significant, hard-to-reverse decisions and their rationale. Newest first.
> Add an ADR whenever a phase makes a structural choice.
> **Last updated:** 2026-07-20. See also [`.ai/DECISION_LOG.md`](../.ai/DECISION_LOG.md).

## ADR-0009 — Consultation as a dedicated aggregate, 1:1 with a visit
**Status:** Accepted (Sprint 2 / C3). Implements
[`architecture-decisions/ADR-001-Consultation-Domain.md`](./architecture-decisions/ADR-001-Consultation-Domain.md)
Option C (Hybrid). The **visit** stays the encounter *event* (`visits`,
unchanged); a new **`consultations`** table is the clinical *document* — 1:1 with
a visit (`visit_id` UNIQUE index), narrative-first optional fields
(`chief_complaint`, `history`, `examination`, `diagnosis`, `remarks`) and a
`status` lifecycle (`draft → in_progress → completed`, with `amended`/`locked`
reserved). All `consultations` SQL lives only in `consultation/repository.py`;
the state machine + audit live in `consultation/service.py`.
**Why:** widening `visits` would create a god-table conflating event and document
and hurt AI/reporting/Cloud-Sync. A bounded aggregate keeps contexts independent
and additive. Migration `v0002_consultations` is additive + reversible; the
regression golden `TABLES:`/`INDEXES:` lines gain `consultations` +
`idx_consultation_visit`/`idx_consultation_patient` — an **intentional**,
documented change (rule 12).

## ADR-0008 — Ordered, idempotent schema migrations with a version ledger
**Status:** Accepted (Sprint 0 / F1). Schema DDL is owned by
`app/core/migrations/`: a `schema_version` ledger table plus a forward-only
runner that applies numbered `vNNNN_*` migrations in order, exactly once, and
supports rollback via each migration's `down` script. `init_db()` migrates then
seeds. The former inline `SCHEMA` became migration `0001_initial`.
**Why:** Create-if-not-exists could add *tables* but had **no path to change an
existing table**, blocking Settings, RBAC, Appointments, Protocols, OCR,
Billing, and Inventory. Migrations must be additive/idempotent
(`... IF NOT EXISTS`, `ADD COLUMN`) so applying them onto a live clinic database
is a safe no-op that only stamps its version — never dropping or renaming a
column an older build reads (Constitution Art. IV §2).
**Consequence:** The regression golden's `TABLES` list gains the internal
`schema_version` table (documented, no service-behaviour change).

## ADR-0007 — Documentation is part of implementation (Project Memory System)
**Status:** Accepted (Phase 1). Establish `docs/`, `docs/modules/`, and `.ai/`
as living memory, updated in the same commit as any behavior change.
**Why:** A 20+ module ecosystem built in gated phases needs durable, machine- and
human-readable context so no phase re-derives the world or drifts from reality.

## ADR-0006 — Centralized regex router + per-module route registration
**Status:** Accepted. `core/router.Router` matches `page.route` against a route
table; each module exports `ROUTES`, assembled in `bootstrap.py`.
**Why:** The old `if/elif` dispatcher in `main.py` wouldn't scale to 50+ routes.
Modules now register their own routes without editing shared conditionals.

## ADR-0005 — Repository layer as the single data-access seam
**Status:** Accepted. All SQL lives in `modules/*/repository.py` on
`core/repository.BaseRepository`; services never touch SQL.
**Why:** Testability, one place per aggregate for SQL, and — critically — the
**seam a future cloud-sync layer plugs into** without touching services or UI.

## ADR-0004 — Typed models via `RowModel`, dicts at the boundary
**Status:** Accepted. Dataclass models mirror tables (`from_row`/`to_dict`); the
UI still consumes plain dicts.
**Why:** A single typed definition per entity (feeds AI/analytics later) without
forcing a big-bang change to every view.

## ADR-0003 — Domain-driven vertical slices over screen-oriented layout
**Status:** Accepted (Architecture Refactor, PR #1). Code organized as
`modules/<domain>/{models,repository,service,controller,view}`.
**Why:** Screen-oriented `ui/` + `services/` wouldn't scale to 20+ domains with
clear ownership; vertical slices let a module be added without touching others.

## ADR-0002 — Narrative-first clinical model
**Status:** Accepted (Sprint 2). Free-text notes are authoritative; structured
`prescription_items` are a non-authoritative regex extraction.
**Why:** Doctors must never be constrained by a form; structure is derived for
analytics, not imposed on care.

## ADR-0001 — Local-first, offline SQLite desktop, ₹0/month
**Status:** Accepted (Sprint 1). Single SQLite file, Flet desktop, bcrypt, no
cloud.
**Why:** The target clinic needs a reliable, zero-cost, offline tool; cloud is an
additive future module, not a dependency.

## Standing meta-decisions (from the charter)

- **Phased, approval-gated delivery.** No phase starts or merges automatically;
  each is independently deployable and leaves the app working.
- **Modular-before-featureful.** No feature in isolation; every design leaves
  room for Portal, AI, Voice, Inventory, Billing, Analytics, Telemedicine, Cloud
  Sync, Mobile, API.
