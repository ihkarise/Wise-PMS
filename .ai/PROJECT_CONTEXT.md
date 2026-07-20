# .ai/PROJECT_CONTEXT.md — Deep context

> The "why" and "how" behind the project. Read after
> [`MEMORY.md`](./MEMORY.md). **Updated:** 2026-07-20.

## The product
WiseOS Health is a **modular ecosystem** for a homeopathy practice. Wise PMS is
module #1; future modules (WHIMS, PillFill, Wise Printer, Holoscan, Patient
Portal, Online Consultation, AI Assistant, WhatsApp, Analytics, OCR, Protocol
Engine) mount on the same platform. The customer is a working clinic; the tool
must be reliable, offline, and free to run.

## The stack
- **Python 3.10+**, **Flet 0.28.3** (Flutter renderer) for a desktop UI.
- **SQLite** single file `data/wise_pms.db`; one connection per operation.
- **bcrypt** for password hashing.
- Packaged to `WisePMS.exe` via PyInstaller.
- Runtime data under `BASE_DIR` (relocatable via `WISE_PMS_HOME`).

## The architecture (mental model)
Domain-driven vertical slices under `app/modules/<domain>/`, each with
`models → repository → service → controller → view`, depending only downward.
Shared infra in `app/core` (database, router, base repository/model), `app/config`
(paths, constants), `app/shared` (theme, shell, widgets), `app/utils`.

Dependency rule: `views → controllers → services → repositories → core`. Nothing
lower imports higher. The graph is acyclic.

## The seams that matter for the future
- **Repository layer** = the cloud-sync seam and the RBAC enforcement point.
- **Typed models (`RowModel`)** = clean inputs for AI/analytics.
- **Router registry** = each module registers its own `ROUTES`; the platform
  mounts many modules on one shell.
- **`utils/prescription`** = pure, reusable structured extraction.

## Non-negotiable principles
- Narrative is authoritative; structure is derived, advisory, never a gate.
- Nothing is destroyed (soft delete, retained history, full audit).
- No feature in isolation; no assumption that blocks a future module.
- Phased, approval-gated delivery; documentation updated with every change.

## Current honest state
Solid, small, working core. Missing: DB migrations, Settings UI, RBAC,
encryption at rest, and all future modules. See
[`KNOWN_ISSUES.md`](./KNOWN_ISSUES.md) and
[`../docs/KNOWN_LIMITATIONS.md`](../docs/KNOWN_LIMITATIONS.md).

## Who reviews
The **Product Owner** approves each phase before the next begins. This session
develops on branch `claude/wiseos-health-architecture-1yumsy`.
