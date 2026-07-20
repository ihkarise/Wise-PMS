# EPIC-18 — PillFill (Dispensing Automation)

> **Spec:** [`../DISPENSING_SYSTEM.md`](../DISPENSING_SYSTEM.md) · **Backlog:** B4 ·
> **Stage:** D — Insight & Reach · **Depends on:** EPIC-12, EPIC-13 ·
> **Complexity:** L (hardware) · **Risk:** High · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. III §9.

## 1. Objective

Automated dispensing hardware/service as a **provider** behind the existing
Dispensing `fulfil` interface — the manual pharmacy and PillFill are the same
interface with different backends. No caller changes when switching providers.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E18-F1 | PillFill provider | Implements `DispenseProvider.fulfil` for automated fill |
| E18-F2 | Device integration | Communicate with hardware/service at the repository seam |
| E18-F3 | Status/reconciliation | Fill progress, errors, reconcile against order/stock |
| E18-F4 | Fallback to manual | Switch provider back to manual on device failure |

## 3. User stories

- **E18-F1-S1** — As pharmacy, I want orders auto-filled, so that dispensing is
  faster and more accurate.
- **E18-F3-S1** — As pharmacy, I want fill status/errors surfaced, so that I can
  intervene when needed.
- **E18-F4-S1** — As pharmacy, I want to fall back to manual if the device fails,
  so that dispensing is never blocked.

## 4. Engineering tasks

- **E18-T1** — `PillFillProvider` implementing the EPIC-12 `DispenseProvider`
  interface (no new dispensing tables needed beyond status fields).
- **E18-T2** — Device/service integration at the repository seam; secrets via
  Settings/env.
- **E18-T3** — Status/error surfacing + reconciliation with WHIMS (EPIC-13).
- **E18-T4** — Provider switch (config) + manual fallback.
- **E18-T5** — Tests (fake device) + docs (Dispensing/PillFill notes).

## 5. Dependencies

- **Upstream:** EPIC-12 (dispense interface), EPIC-13 (stock).
- **Downstream:** none (terminal automation).

## 6. Acceptance criteria

- **AC1** — *Given* the PillFill provider, *when* an order is fulfilled, *then* it
  dispenses via the device and updates stock/status like the manual path.
- **AC2** — *Given* a device error, *when* it occurs, *then* it is surfaced and the
  order can fall back to manual.
- **AC3** — *Given* provider switch, *when* toggled, *then* callers (Workspace/
  Billing) are unchanged.
- **AC4** — *Given* device secrets, *when* configured, *then* they live in
  Settings/env and are never committed.

## 7. Regression tests

- **Must stay green:** golden, models, router, views; EPIC-12 dispensing tests.
- **New:** PillFill provider test (fake device), fallback test, reconciliation
  test.

## 8. Rollout phases

- **E18-R1** — Provider skeleton against a simulated device.
- **E18-R2** — Real device integration + status/reconciliation.
- **E18-R3** — Fallback + config switch; docs closeout.

## 9. Rollback

Switch provider back to `ManualProvider` (EPIC-12) — instant, no data change.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: callers unchanged by provider swap;
manual fallback always available; device secrets external.
</content>
