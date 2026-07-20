# Module: Dispensing

**Status:** 🔜 Planned — **not implemented** · planned tables: `dispense_*`

## Purpose (target)
Pharmacy handoff: turn a visit's prescription into a dispensing record, decrement
inventory, and hand off to automated fill (PillFill).

## Target design (planned — needs approval)
- `app/modules/dispensing/` vertical slice.
- Tables (migration F1): `dispense_orders` (visit_id, patient_id, status,
  dispensed_by, dispensed_at) and `dispense_items` (order_id, inventory_item_id,
  qty, batch_id, price).
- Service: `create_order(visit)`, `fulfil`, `cancel`, `order_for_visit`.

## Integrations
- **Visits / Prescription** — source of what to dispense (from
  `prescription_items` + narrative).
- **Inventory (WHIMS)** — decrements stock, picks batches (FEFO).
- **PillFill** — automated dispensing hardware/service via the repository seam.
- **Billing** — a dispensed order feeds the invoice.
- **Consultation Workspace → Dispense** action creates the order inline.

## Dependencies
Migrations (F1), Inventory (for stock/pricing), Visits (built). RBAC (F3) so
only Pharmacy dispenses.

## Notes
Design the dispense→fulfil boundary so a manual pharmacy and an automated
PillFill line are the same interface with different backends.
