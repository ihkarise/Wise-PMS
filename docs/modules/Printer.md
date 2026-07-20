# Module: Printer (Wise Printer)

**Status:** 🔜 Planned — **not implemented** · related: `utils/prescription.py`
(built), `settings` (templates, planned)

## Purpose (target)
Render and print prescriptions, invoices, and medicine labels from clinic-branded
templates.

## Target design (planned — needs approval)
- `app/modules/printer/` — a **rendering + output** module (templates in, printed
  document/PDF out). Likely no table of its own; templates live in Settings.
- Service: `render_prescription(visit)`, `render_invoice(invoice)`,
  `render_label(dispense_item)` → produces a document (PDF/print job); `print(doc)`.
- Templates (from Settings): prescription template, invoice template, label
  template — with clinic branding (logo, name, address, doctor).

## Integrations
- **Consultation Workspace → Print** action.
- **Settings** supplies branding + template layouts.
- **Billing** invoices, **Dispensing** labels.
- Variables mirror WhatsApp/patient fields (`{regname}`, `{fileno}`,
  `{doctorName}`, `{clinicName}`) for consistency.

## Dependencies
Settings (F2) for templates/branding; Visits/Billing/Dispensing as sources.

## Notes
Keep rendering (build the document) separate from output (send to printer/PDF)
so the same document can be printed, saved, or attached, and so headless tests
can assert on the rendered document without a printer.
