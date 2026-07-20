# WiseOS Health — Product Constitution

> **Status:** Permanent. This is the highest-authority document in the product.
> Every specification, phase plan, design decision, and line of future code must
> conform to it. When any other document conflicts with this one, **this one
> wins**. Amendments require an explicit Product Owner decision recorded as an
> ADR in [`../docs/DECISIONS.md`](../docs/DECISIONS.md).
> **Ratified (draft):** 2026-07-20 (Phase 2). **Awaiting Product Owner approval.**

This document exists so that a clinic-grade product built over five years, in
many gated phases, by many hands (human and AI), stays coherent. It is the
rulebook a future contributor reads before proposing anything.

---

## Article I — Product Vision

1. **WiseOS Health is the operating system for a modern healthcare practice.**
   It is a modular ecosystem where each clinical, pharmacy, and business function
   is an independent module mounted on one shared platform. Wise PMS is module #1,
   not the whole product.

2. **The first customer is a homeopathy clinic** run by a practising doctor. The
   product must feel built *by* a doctor *for* a doctor — it adapts to the
   clinician's workflow, never the reverse.

3. **The five-year target** is a single clinician, or a small multi-clinic group,
   running an entire practice — registration, consultation, investigation,
   prescription, dispensing, billing, follow-up, and analytics — on WiseOS, with
   the same data instantly available to the patient portal, telemedicine, and AI,
   whether on one desktop or many synced devices.

4. **The ecosystem** (target): Wise PMS · WHIMS (inventory) · PillFill
   (dispensing automation) · Wise Printer · Holoscan (imaging/AI vision) ·
   Patient Portal · Online Consultation (telemedicine) · AI Assistant · WhatsApp
   Automation · Analytics · OCR Engine · Protocol Engine.

---

## Article II — Clinical Principles

1. **The software adapts to the doctor.** Think like a clinician who treats
   patients every day, not like a programmer. Reduce clicks, context switches,
   and cognitive load at the point of care.

2. **Narrative is the source of truth.** Doctors write free text. Structured data
   (prescription items, OCR values, diagnoses, AI suggestions) is a *derived,
   non-authoritative* layer. Structure must **never gate** what a clinician may
   write or block a workflow if extraction fails.

3. **One integrated consultation.** After a case is created, the doctor works in
   **one** screen — the Consultation Workspace — not a maze of tabs. See
   [`CONSULTATION_WORKSPACE.md`](./CONSULTATION_WORKSPACE.md).

4. **Longitudinal record is sacred.** One patient → many cases → many visits,
   with one continuous timeline. New modules *reference* these IDs; they never
   replace or fork the record.

5. **Follow-up is first-class.** Every consultation can schedule the next touch;
   the system surfaces and (later) automates reminders. Retention is care.

6. **Advisory, never automatic, for clinical judgment.** Protocol suggestions,
   AI outputs, and drug-interaction flags are proposals the doctor accepts,
   edits, or ignores. Nothing clinical is auto-committed to the record.

7. **Safety visible, not buried.** Red-flag / allergy / interaction information,
   when present, must be surfaced where the decision is made, not hidden a click
   away.

---

## Article III — Engineering Principles

1. **Modular before featureful.** No feature is built in isolation. Every feature
   must integrate cleanly with current and future modules.

2. **Vertical slices.** A new business capability is a new folder under
   `app/modules/<domain>/` containing `models → repository → service →
   controller → view`, depending only downward. No other module is edited except
   to register routes/nav and add tables via a migration.

3. **Layering is law.** Dependency direction is
   `views → controllers → services → repositories → core`. Nothing lower imports
   anything higher. The dependency graph stays acyclic.

4. **SQL lives only in repositories.** Services hold rules and validation; views
   are Flet-only and collect a plain dict. No SQL in services or views.

5. **The repository layer is the seam** for cloud sync and for RBAC enforcement.
   Protect it: do not scatter data access elsewhere.

6. **Typed models at the core, dicts at the boundary.** Each entity has one
   dataclass definition (`core.model.RowModel`) mirroring its table; the UI may
   consume plain dicts.

7. **Behavior is pinned; structure is free.** The regression golden test must
   stay byte-identical unless a behavior change is intentional and documented
   (golden + CHANGELOG + DECISIONS updated in the same commit).

8. **Small, reviewable, runnable commits.** Every commit leaves the app working.

9. **External providers behind an interface.** WhatsApp, Google Meet, OCR
   engines, AI models, cloud sync — each hides behind one swappable interface.
   Secrets live in Settings/env and are **never committed**.

---

## Article IV — Architecture Principles

1. **One platform, many modules.** `core/router` + per-module `ROUTES` +
   `shared/shell` mean each product surface is a set of modules mounted on one
   shell. The platform is the registry, not a monolith.

2. **Migrations gate schema change.** Once the migration runner (F1) lands, every
   table change is an ordered, idempotent, forward-only migration. Until then,
   only *new* `CREATE TABLE IF NOT EXISTS` tables are safe; existing tables are
   never altered.

3. **No dead scaffolding.** Do not commit empty module folders or docs that claim
   code which does not exist. A module gets a folder when it gets real code.

4. **IDs are the contract between modules.** Modules integrate by referencing
   `patient_id`, `case_id`, `visit_id`, `attachment_id`, etc. — not by reaching
   into each other's tables or logic.

5. **Read models for cross-cutting views.** Timeline, Analytics, Reports are
   read models composed over other modules' repositories; they own no base
   tables.

6. **UI-agnostic domain layer.** Services and repositories never import UI. A
   future API, mobile target, or portal reuses them unchanged.

---

## Article V — UI / UX Principles

1. **One design system.** Colors, fonts, radii, and components come only from
   `app/shared/theme.py` and `app/shared/widgets.py`. No hex literals, no raw
   buttons/fields, no new fonts in views. Palette: `PRIMARY #1F3F8C`,
   `ACCENT #D6284D`, Poppins, 16/12/10 radii. See
   [`../docs/DESIGN_SYSTEM.md`](../docs/DESIGN_SYSTEM.md).

2. **Consistency across 20+ modules.** As modules grow, the product must still
   read as one system. New composites go into `shared/widgets.py`, never
   copy-pasted between views.

3. **Reduce clicks at the point of care.** The consultation is the hottest path;
   optimize it above all others.

4. **Feedback, never tracebacks.** All user feedback uses `theme.snack`; the
   router hides exceptions behind a friendly message and a safe fallback.

5. **Design for 1366×768 without horizontal scroll.** Wide content scrolls inside
   its own container.

6. **Accessibility floor:** minimum 14px text, 44px touch targets (enforced by
   the factories).

7. **Dark theme is reserved, not partial.** The `DARK_BG` token exists; do not
   ship half-styled dark mode.

---

## Article VI — Data Safety Principles

1. **Nothing clinical is ever physically destroyed.** Patients are soft-deleted;
   cases, visits, attachments, and messages are retained. History is immutable in
   spirit.

2. **Every mutation is audited.** All writes go through `audit.service.log_action`
   (which never raises — a failed audit must never break a clinical flow).

3. **PHI is protected before it travels.** The current build is safe only for a
   single trusted clinician on a controlled machine. **RBAC (F3) and encryption
   at rest (F7) must land before any networked or multi-user surface** (Portal,
   Telemedicine, Cloud Sync, API).

4. **The clinic owns its data.** Always exportable, always backup-able, always
   restorable — locally, without a vendor.

5. **Consent and least privilege.** Patient-facing channels (WhatsApp, Portal)
   respect opt-out; every principal (staff role, patient) gets least-privilege
   access enforced server-side at the repository/service seam.

6. **Secrets never committed.** API keys and credentials live in Settings/env and
   in `.gitignore`d paths.

---

## Article VII — Offline-First Principles

1. **Local-first, cost-zero by default.** Offline SQLite desktop is the baseline.
   The product must be fully usable with no internet and no recurring cost.

2. **Cloud is additive, never assumed.** Sync, hosted AI/OCR, and remote backup
   are opt-in modules layered on top — never a dependency of the core.

3. **Prefer on-device options.** For OCR, AI, and dictation, default to local /
   offline engines to preserve the ₹0/offline posture; any cloud provider is an
   explicit, consented, encrypted opt-in.

4. **Degrade gracefully.** A network- or provider-dependent feature that is
   offline must fail quietly and leave the offline core fully working.

---

## Article VIII — Future Expansion Rules

1. **No assumption may block** Wise PMS, WHIMS, Holoscan, PillFill, Wise Printer,
   Patient Portal, Telemedicine, AI Assistant, Analytics, or Cloud Sync. Every
   design leaves room for all of them.

2. **Think five years ahead.** Prefer the decision that keeps the most doors
   open, even at some short-term cost.

3. **Templates everywhere, editable in Settings.** Protocols, prescriptions,
   invoices, labels, and WhatsApp messages are data-driven templates a
   non-programmer clinician can edit — not hardcoded strings.

4. **Permissions and vocabularies are data, not code.** New modules add their own
   permission keys and dropdown vocabularies without editing the RBAC core or
   other modules.

5. **Multi-clinic is a dimension, not a rewrite.** Where reasonable, design so a
   future `clinic_id` scoping can be added by migration without reshaping the
   domain.

---

## Article IX — Delivery & Governance

1. **Phase 0 first, always.** Read and understand the whole repo and memory
   system before modifying anything.

2. **Documentation is part of implementation.** Update every affected doc in the
   same commit as the code. Docs must never claim code that doesn't exist.

3. **Phased, approval-gated delivery.** No phase begins or merges automatically.
   Each phase is independently deployable, leaves the app working, and ends with
   the standard report (Summary · Files · Architecture Changes · DB Changes ·
   Risk · Manual Test Checklist · Rollback · Known Issues · Recommended Next
   Phase).

4. **Never remove functionality without explicit Product Owner approval.**

5. **Quality gates per phase:** `pytest -q` green (regression golden intact
   unless intentionally changed), new module ships its own tests, model/table
   parity for new tables, router contract for new routes, imports clean, app
   starts, DB initializes.

---

## Article X — Amendment

This constitution changes only by an explicit Product Owner decision, recorded as
a new ADR in [`../docs/DECISIONS.md`](../docs/DECISIONS.md) and reflected here in
the same commit. No phase may quietly override an article; a conflict is resolved
by amending the constitution first, then proceeding.
</content>
