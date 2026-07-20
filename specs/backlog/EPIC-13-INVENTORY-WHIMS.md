# EPIC-13 — Inventory (WHIMS)

> **Spec:** [`../../docs/modules/Inventory.md`](../../docs/modules/Inventory.md) ·
> **Backlog:** B3 · **Stage:** C — Operations · **Depends on:** EPIC-01 ·
> **Complexity:** M · **Risk:** Medium · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. III §9.

## 1. Objective

Warehouse/Health Inventory Management: stock, batches, expiry, and pricing that
feed prescription pricing (Workspace) and dispensing (EPIC-12). A drop-in module
with its own tables — independent of the clinical core except via IDs.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E13-F1 | Item catalog | `inventory_items` (name, form, potency, unit, price) |
| E13-F2 | Batches & expiry | `inventory_batches` (batch_no, expiry, qty_on_hand, cost) |
| E13-F3 | Stock ledger | Movement entries (receive/adjust/dispense) |
| E13-F4 | Pricing | `price_for(item)` for Workspace + Billing |
| E13-F5 | FEFO picking | First-expiry-first-out batch selection on dispense |
| E13-F6 | Alerts | `low_stock`, `expiring_soon` |

## 3. User stories

- **E13-F1-S1** — As pharmacy, I want a medicine catalog with prices, so that
  pricing and dispensing use consistent data.
- **E13-F2-S1** — As pharmacy, I want batches with expiry, so that I dispense the
  right stock and avoid expired medicine.
- **E13-F5-S1** — As pharmacy, I want FEFO picking, so that near-expiry stock goes
  first.
- **E13-F6-S1** — As pharmacy, I want low-stock/expiry alerts, so that I reorder in
  time.
- **E13-F4-S1** — As a doctor, I want prescription pricing in the Workspace, so
  that the patient knows the cost.

## 4. Engineering tasks

- **E13-T1** — Migration: `inventory_items`, `inventory_batches`, stock ledger.
- **E13-T2** — `modules/inventory/` slice: `stock_level`, `receive_stock`,
  `adjust`, `low_stock`, `expiring_soon`, `price_for`, FEFO `pick(item, qty)`.
- **E13-T3** — Management view (catalog + batches + receive/adjust); alerts on
  Dashboard.
- **E13-T4** — Integrate: Workspace pricing panel; Dispensing decrement + batch
  pick (EPIC-12).
- **E13-T5** — Name alignment with `prescription_items` so extraction maps to stock.
- **E13-T6** — RBAC keys; tests + docs (Inventory module doc, CHANGELOG).

## 5. Dependencies

- **Upstream:** EPIC-01.
- **Downstream:** EPIC-12 (decrement/pricing), EPIC-18 (PillFill at repo seam),
  EPIC-14 (consumption/wastage/expiry).

## 6. Acceptance criteria

- **AC1** — *Given* a catalog item, *when* priced, *then* `price_for` returns its
  price for the Workspace/Billing.
- **AC2** — *Given* batches with expiry, *when* a pick is requested, *then* FEFO
  selects the earliest-expiry batch with stock.
- **AC3** — *Given* a dispense (EPIC-12), *when* fulfilled, *then* the chosen
  batch's `qty_on_hand` decrements transactionally.
- **AC4** — *Given* thresholds, *when* stock is low or expiring, *then* alerts
  surface.
- **AC5** — *Given* no WHIMS data, *when* dispensing runs, *then* it falls back to
  manual pricing (EPIC-12 remains functional).

## 7. Regression tests

- **Must stay green:** golden, models, router, views.
- **New:** pricing test, FEFO pick test, transactional decrement test, low/expiry
  alert tests, model/table parity for inventory tables, router contract.

## 8. Rollout phases

- **E13-R1** — Catalog + pricing (`price_for`) → Workspace pricing.
- **E13-R2** — Batches/expiry + ledger + receive/adjust.
- **E13-R3** — FEFO pick + Dispensing decrement (EPIC-12).
- **E13-R4** — Alerts + Analytics feed; docs closeout.

## 9. Rollback

Revert module → Dispensing/Billing fall back to manual pricing; tables inert. No
data destroyed.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: decrement atomic (no drift); FEFO
correct; dispensing still works without WHIMS.
</content>
