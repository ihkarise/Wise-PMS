# Implementation Plan — Specification

> **Status:** Design only (Phase 2). **Last updated:** 2026-07-20.
> The near-term, ordered build plan with approval gates. Companion to
> [`MASTER_PHASE_PLAN.md`](./MASTER_PHASE_PLAN.md) (the long-term roadmap).
> Every phase is subordinate to
> [`PRODUCT_CONSTITUTION.md`](./PRODUCT_CONSTITUTION.md).

## 1. Purpose

Translate these specifications into an executable sequence of **small,
independently-deployable, approval-gated phases**. This plan does not authorize
any implementation — it proposes the order. No phase begins until the Product
Owner approves it (Constitution Art. IX §3).

## 2. Sequencing principles

1. **Foundation before features.** Migrations (F1) → Settings (F2) → RBAC (F3)
   precede the large feature modules, because features depend on all three
   (roadmap Sequencing rule 1).
2. **The Consultation Workspace is the anchor.** Protocol, Investigation, OCR,
   Printer, Dispensing are built to feed it — but the Workspace ships as a
   **skeleton first** and grows as feeders land (Constitution Art. IX §3).
3. **Cloud/Portal/AI last.** Networked and patient-facing surfaces come only after
   the security foundation (F3 + F7) is proven (Constitution Art. VI §3, VII).
4. **Every phase leaves the app working**, ships its own tests, and updates every
   affected doc in the same commit (Constitution Art. IX §2).

## 3. Near-term ordered plan

Each row is one approval-gated phase. "Backlog" cross-references
[`../docs/MASTER_BACKLOG.md`](../docs/MASTER_BACKLOG.md); "Spec" links the design.

| # | Phase | Backlog | Spec | Depends on | Complexity | Risk |
| - | ----- | ------- | ---- | ---------- | ---------- | ---- |
| P2 | **DB Migrations & schema versioning** | F1 | [`../docs/DATABASE.md`](../docs/DATABASE.md) | — | S | Low |
| P3 | **Settings UI + templates** | F2 | [`SETTINGS_SYSTEM.md`](./SETTINGS_SYSTEM.md) | F1 | S–M | Low |
| P4 | **RBAC (roles, permissions, enforcement)** | F3 | [`USER_ROLES.md`](./USER_ROLES.md) | F1 | M | Medium |
| P4b | **User management screen** | F4 | [`USER_ROLES.md`](./USER_ROLES.md) | F3 | S | Low |
| P5 | **Consultation Workspace (skeleton)** | C1 | [`CONSULTATION_WORKSPACE.md`](./CONSULTATION_WORKSPACE.md) | F1–F3 | L | High |
| P6 | **Protocol Engine** | C2 | [`PROTOCOL_ENGINE.md`](./PROTOCOL_ENGINE.md) | F1, P5 | M | Medium |
| P7 | **Wise Printer** | D1 | [`PRINTER_SYSTEM.md`](./PRINTER_SYSTEM.md) | F2, P5 | M | Medium |
| P8 | **Investigation Engine** | C4 | [`INVESTIGATION_ENGINE.md`](./INVESTIGATION_ENGINE.md) | F1, P5 | M | Medium |
| P9 | **OCR Engine** | D2 | [`OCR_ENGINE.md`](./OCR_ENGINE.md) | F1, P8 | L | High |
| P10 | **Appointments + Waiting Queue** | — | [`APPOINTMENT_SYSTEM.md`](./APPOINTMENT_SYSTEM.md), [`WAITING_QUEUE.md`](./WAITING_QUEUE.md) | F1, F3, F5 | M | Medium |
| P11 | **WhatsApp Automation** | E1 | [`WHATSAPP_SYSTEM.md`](./WHATSAPP_SYSTEM.md) | F1, F2, F3 | M | Medium |
| P12 | **Billing & Dispensing** | B1/B2 | [`DISPENSING_SYSTEM.md`](./DISPENSING_SYSTEM.md) | F1, F3, P5 | M | Medium |
| P13 | **Inventory (WHIMS)** | B3 | [`../docs/modules/Inventory.md`](../docs/modules/Inventory.md) | F1 | M | Medium |

Later horizons (Analytics, Reports, Portal, Telemedicine, PillFill, AI, Cloud
Sync, Mobile, API) are sequenced in [`MASTER_PHASE_PLAN.md`](./MASTER_PHASE_PLAN.md).

## 4. The critical path

```
F1 (migrations) ─► F2 (settings) ─► F3 (RBAC) ─► Consultation Workspace (skeleton)
                                                        │
        ┌───────────────────────────────────────────────┤
        ▼            ▼             ▼            ▼          ▼
     Protocol    Printer     Investigation   Appts     Dispensing
        │            │             │           │          │
        └── all feed back into the Workspace panels ──────┘
                                                        │
                                                        ▼
                                    Analytics · Portal · Telemedicine · AI
                                       (only after F3 + F7)
```

F1 is the unlock for everything (no table can safely change without it). The
Workspace is the convergence point; feeders can be built in parallel once it
exists as a skeleton.

## 5. Per-phase definition of done (Quality Gates)

Applies to **every** phase (Constitution Art. IX §5):

- [ ] `pytest -q` green; regression golden byte-identical (or an intentional,
      documented behavior change with golden + CHANGELOG + DECISIONS updated).
- [ ] New module ships its own tests (service behavior + view-build min).
- [ ] Model/table parity for any new table; router contract for any new route.
- [ ] Imports clean; app starts; DB initializes; migrations idempotent.
- [ ] Every affected doc updated in the **same commit** (docs = implementation).
- [ ] Phase-end report delivered; **await Product Owner approval** before the next.
- [ ] Rollback strategy documented (see §6).

## 6. Rollback strategy (per phase)

- **Docs/spec phases:** revert the commit; no runtime impact.
- **Migration phases (F1+):** migrations are forward-only and idempotent; each
  new migration is additive (`CREATE TABLE IF NOT EXISTS` / additive columns).
  Rollback = revert the app commit; the stamped `schema_version` and new empty
  tables are inert and harmless to the prior version. **Never** write a migration
  that drops/renames a column an older build reads (Constitution Art. IV §2).
- **Feature phases:** each module is a vertical slice; disabling its route/nav
  removes it from the UI without touching other modules. Data written remains
  (nothing destroyed).
- **Provider-backed phases (WhatsApp/OCR/AI/Meet):** the offline core is
  unaffected if the provider is removed; the feature degrades to unavailable.

## 7. Testing approach across phases

- Pin behavior first (regression golden), then build structure (Lessons #1).
- Add a **migration parity test** ("fresh DB == migrated DB") at F1.
- Add **interaction/event tests** (Flet/Playwright harness) when the Workspace
  lands — the current suite builds views but doesn't exercise handlers (L15).
- Add **CI** (pytest on push) early — currently none (L15,
  [`../docs/TESTING.md`](../docs/TESTING.md)).

## 8. Future integration points (kept open by this plan)

Wise PMS · WHIMS · Holoscan · PillFill · Wise Printer · Patient Portal ·
Telemedicine · AI Assistant · Analytics · Cloud Sync — each is a mountable module
on `core/router` + `shared/shell`; the repository layer is the sync/RBAC seam; no
phase in this plan forecloses any of them (Constitution Art. VIII §1).

## 9. What this plan explicitly does NOT do

- It does not start any phase (approval-gated).
- It does not modify the database, refactor modules, or write feature code.
- It does not commit empty scaffolding for planned modules (Constitution
  Art. IV §3).
</content>
