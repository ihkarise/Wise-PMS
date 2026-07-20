# Dispensing System — Specification

> **Status:** Design only (Phase 2). Not implemented. Backlog **B2** (feeds
> PillFill B4). Planned tables: `dispense_orders`, `dispense_items`.
> **Last updated:** 2026-07-20. Extends
> [`../docs/modules/Dispensing.md`](../docs/modules/Dispensing.md).

## 1. Purpose

Turn a visit's prescription into a **dispensing record**: pick medicines,
decrement inventory (WHIMS), print labels (Wise Printer), feed the invoice
(Billing), and hand off to automated fill (PillFill). This is the pharmacy stage
of the patient flow.

## 2. Core design: one interface, manual or automated

Design the **dispense → fulfil** boundary so a manual pharmacy and an automated
PillFill line are the **same interface with different backends** (Constitution
Art. III §9). The consultation and billing don't care which fulfilled the order.

```
Prescription (visit)
     │  create_order
     ▼
dispense_order (created)
     │  fulfil  ──►  DispenseProvider
     ├─ ManualProvider   (pharmacist picks, marks fulfilled)
     └─ PillFillProvider (automated hardware/service — future)
     ▼
dispense_order (fulfilled)  ──► decrement WHIMS · print labels · feed invoice ·
                                 WhatsApp "Medicine Ready" · Timeline event
```

## 3. Data model (planned — needs F1)

```
dispense_orders
  id · visit_id FK · patient_id FK · status (created|fulfilled|cancelled) ·
  dispensed_by · dispensed_at · notes · created_at

dispense_items
  id · order_id FK · inventory_item_id FK (nullable pre-WHIMS) ·
  medicine_name · potency · qty · batch_id (nullable) · unit_price · line_total
```

- Source of *what* to dispense is the visit's `prescription_items` + narrative
  (narrative authoritative — the pharmacist reconciles against it).
- `inventory_item_id`/`batch_id` link to WHIMS when it exists; before WHIMS,
  items carry name/potency/qty and pricing is manual.

## 4. Service contract (target)

```
dispensing.service
  create_order(visit_id, user_id) -> int         # seeds items from prescription
  order_for_visit(visit_id) -> dict | None
  fulfil(order_id, provider, user_id) -> None     # decrement stock, mark done
  cancel(order_id, user_id) -> None
```

All mutations audited. `fulfil` is transactional with the stock decrement so
inventory never drifts.

## 5. Integrations

| With | For |
| ---- | --- |
| **Visits / Prescription** | source of items (extracted + narrative) |
| **Inventory (WHIMS)** | stock decrement, batch pick (FEFO), pricing |
| **Wise Printer** | medicine labels |
| **Billing** | dispensed order → invoice lines |
| **WhatsApp** | `medicine_ready` on fulfil |
| **PillFill** | automated fulfilment via the provider interface |
| **Timeline** | dispense event |

## 6. Consultation Workspace integration

- **Dispensing** panel: create the order inline from the prescription; shows
  pick list and (with WHIMS) stock availability + batch/expiry.
- **Pricing** panel: `inventory.price_for(item)` totals the order.
- **Invoice** action: turns the dispensed order into invoice lines.

## 7. Inventory & pricing (WHIMS) relationship

- Pricing and stock live behind **WHIMS** (`inventory.service`) so PillFill
  hardware or external suppliers integrate at the repository seam without touching
  dispensing callers.
- **FEFO** (first-expiry-first-out) batch selection is a WHIMS concern; dispensing
  requests a pick and records the chosen `batch_id`.
- Before WHIMS ships, dispensing works with manual medicine names + manual price.

## 8. Dependencies & sequencing

- **Requires:** F1 (tables), visits (built). Full value needs **WHIMS**
  (stock/pricing) and RBAC (F3, so only Pharmacy dispenses).
- **Feeds:** Billing, Printer (labels), WhatsApp, PillFill, Timeline, Analytics
  (consumption).
- **Sequencing:** manual dispensing first; WHIMS decrement next; PillFill last.

## 9. Manual test checklist (implementing phase)

- [ ] Creating an order seeds items from the visit's prescription.
- [ ] Fulfilling decrements WHIMS stock transactionally (no drift).
- [ ] A fulfilled order can feed an invoice and print labels.
- [ ] `medicine_ready` WhatsApp fires on fulfil (if enabled).
- [ ] Manual (no-WHIMS) path works end-to-end.
- [ ] Only Pharmacy/Admin can dispense (once RBAC lands).
- [ ] Model/table parity green.

## 10. Risks

- **Stock accuracy** — fulfil + decrement must be atomic; reconcile against
  narrative (the doctor may have written free-text substitutions).
- **PillFill hardware variance** — keep it behind the provider interface; the
  manual path is always the fallback.
</content>
