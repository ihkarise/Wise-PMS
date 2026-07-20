# Module: Inventory (WHIMS)

**Status:** 🔜 Planned — **not implemented** · planned tables: `inventory_*`

## Purpose (target)
Warehouse/Health Inventory Management: track medicine stock, batches, expiry,
and pricing that feeds prescription pricing and dispensing.

## Target design (planned — needs approval)
- `app/modules/inventory/` vertical slice (its own repo + tables + migration —
  a drop-in module per the architecture's extension model).
- Tables (migration F1): `inventory_items` (name, form, potency, unit, price),
  `inventory_batches` (item_id, batch_no, expiry, qty_on_hand, cost), and stock
  movement/ledger entries.
- Service: `stock_level`, `receive_stock`, `adjust`, `low_stock`,
  `expiring_soon`, `price_for(item)`.

## Integrations
- **Consultation Workspace → Medicine Pricing** looks up `price_for` per item.
- **Dispensing / PillFill** decrements stock on dispense.
- **Analytics** reports consumption, wastage, expiry.
- Medicine names align with `prescription_items` so extraction can map to stock.

## Dependencies
Migrations (F1). Independent of the clinical core except via IDs — can be built
as a standalone module and mounted on the shell.

## Notes
Keep pricing and stock behind the service so PillFill hardware or external
suppliers can be integrated at the repository seam without touching callers.
