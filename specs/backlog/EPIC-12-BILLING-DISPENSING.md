# EPIC-12 — Billing & Dispensing

> **Spec:** [`../DISPENSING_SYSTEM.md`](../DISPENSING_SYSTEM.md) ·
> **Backlog:** B1, B2 · **Stage:** C — Operations ·
> **Depends on:** EPIC-01, EPIC-03, EPIC-04; full value needs EPIC-13 ·
> **Complexity:** M · **Risk:** Medium · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. III §9.

## 1. Objective

Turn a visit's prescription into a **dispensing record** and an **invoice**:
pick medicines, (with WHIMS) decrement stock and pick batches, print labels, and
bill. Design dispense→fulfil as one interface with manual and (later) PillFill
backends.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E12-F1 | Dispense orders | `dispense_orders`/`dispense_items` seeded from prescription |
| E12-F2 | Fulfil (provider) | ManualProvider default; PillFillProvider later (EPIC-18) |
| E12-F3 | Invoicing | `invoices`/`invoice_items`/`payments` from dispensed order |
| E12-F4 | Pricing | Manual pre-WHIMS; `price_for` with WHIMS (EPIC-13) |
| E12-F5 | Workspace actions | Dispense · Pricing · Invoice inline |
| E12-F6 | Downstream triggers | Labels (EPIC-09), "Medicine Ready" (EPIC-11), Timeline events |

## 3. User stories

- **E12-F1-S1** — As pharmacy, I want an order seeded from the prescription, so
  that I don't retype medicines.
- **E12-F2-S1** — As pharmacy, I want to mark an order fulfilled, so that stock and
  billing update together.
- **E12-F3-S1** — As accounts, I want an invoice from the dispensed order, so that
  billing matches what was given.
- **E12-F4-S1** — As the clinic, I want pricing to work manually before WHIMS, so
  that billing isn't blocked on inventory.
- **E12-F6-S1** — As a patient, I want a "medicine ready" message, so that I know
  when to collect.

## 4. Engineering tasks

- **E12-T1** — Migration: `dispense_orders`, `dispense_items`, `invoices`,
  `invoice_items`, `payments`.
- **E12-T2** — `modules/dispensing/` slice: `create_order` (seed from
  `prescription_items` + narrative), `order_for_visit`, `fulfil(provider)`,
  `cancel`; `DispenseProvider` interface + `ManualProvider`.
- **E12-T3** — `modules/billing/` slice: `create_invoice`, `add_payment`,
  `invoice_for_visit/order`; invoice status lifecycle.
- **E12-T4** — Transactional fulfil + stock decrement (with EPIC-13); manual price
  fallback.
- **E12-T5** — Workspace Dispense/Pricing/Invoice actions; routes
  `^/dispense/(?P<order_id>\d+)$`, `^/invoice/(?P<id>\d+)$`.
- **E12-T6** — Downstream: labels (EPIC-09), `medicine_ready` (EPIC-11), Timeline
  dispense/payment events; RBAC `dispensing.fulfil`, `billing.manage`,
  `payments.record`.
- **E12-T7** — Tests + docs (Dispensing module doc, Billing, CHANGELOG).

## 5. Dependencies

- **Upstream:** EPIC-01, EPIC-03, EPIC-04. Full value: EPIC-13 (stock/pricing).
- **Downstream:** EPIC-09 (labels/invoice print), EPIC-11 (medicine ready),
  EPIC-18 (PillFill), EPIC-14 (revenue/consumption).

## 6. Acceptance criteria

- **AC1** — *Given* a visit prescription, *when* an order is created, *then* items
  are seeded from it.
- **AC2** — *Given* fulfil, *when* invoked with WHIMS, *then* stock decrements
  transactionally (no drift); without WHIMS, manual path works.
- **AC3** — *Given* a fulfilled order, *when* invoiced, *then* invoice lines match
  the dispensed items.
- **AC4** — *Given* RBAC, *when* a non-Pharmacy user dispenses, *then* it is
  refused; non-Accounts cannot record payments.
- **AC5** — *Given* fulfil, *when* completed, *then* `medicine_ready` may fire and a
  Timeline event + audit are written.

## 7. Regression tests

- **Must stay green:** golden, models, router, views.
- **New:** order-seed test, transactional fulfil/decrement test, invoice-from-order
  test, RBAC-refusal tests, manual-path test, model/table parity for 5 tables,
  router contract for `/dispense` + `/invoice`.

## 8. Rollout phases

- **E12-R1** — Dispense orders + manual fulfil + manual pricing.
- **E12-R2** — Billing (invoice/payments) from dispensed order.
- **E12-R3** — WHIMS stock decrement (EPIC-13) + labels/medicine-ready triggers.
- **E12-R4** — RBAC gating + Timeline/analytics events; docs closeout.

## 9. Rollback

Revert routes/nav → data retained; without the module, prescriptions remain on the
visit. No data destroyed.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: fulfil+decrement atomic (no stock drift);
manual path works pre-WHIMS; only Pharmacy/Accounts act under RBAC.
</content>
