# Printer System (Wise Printer) — Specification

> **Status:** Design only (Phase 2). Not implemented. Backlog **D1**. Related
> built code: `utils/prescription.py`; templates live in Settings (planned).
> **Last updated:** 2026-07-20. Extends
> [`../docs/modules/Printer.md`](../docs/modules/Printer.md).

## 1. Purpose

Render and print **prescriptions, invoices, and medicine labels** from
clinic-branded, **editable templates**. Printing is a consultation output and the
physical artifact the patient carries away.

## 2. Design principle: render ≠ output

Separate **rendering** (build the document from data + template) from **output**
(send to a printer, save as PDF, or attach). The same rendered document can be
printed, saved, or attached, and a headless test can assert on the rendered
document without a printer (Constitution Art. III + testability).

```
data (visit/invoice/dispense) + template (Settings)
        │  render
        ▼
   Document (structured/HTML/PDF)
        │  output
        ├─► printer (physical)
        ├─► PDF (exports/ or attach)
        └─► preview (Workspace)
```

## 3. What Wise Printer produces

| Output | Source | Template |
| ------ | ------ | -------- |
| **Prescription** | a visit (narrative Rx + extracted items) | prescription template |
| **Invoice** | a billing invoice | invoice template |
| **Medicine label** | a dispense item | label template |
| **Advice sheet** | protocol advice / remarks | advice template |
| **Reports** (later) | Reports module | report template |

## 4. Templates & branding (from Settings)

Templates and clinic branding live in **Settings** (F2): logo, clinic name,
address, phone, email, website, doctor name/registration. Variables mirror
WhatsApp/patient fields for consistency (Constitution Art. VIII §3):
`{regname}`, `{fileno}`, `{doctorName}`, `{clinicName}`, `{appointmentDate}`,
plus prescription-specific tokens (medicine list, potency, dosage, instructions,
date, next review). See [`SETTINGS_SYSTEM.md`](./SETTINGS_SYSTEM.md).

## 5. Service contract (target)

```
printer.service
  render_prescription(visit) -> Document
  render_invoice(invoice) -> Document
  render_label(dispense_item) -> Document
  render_advice(visit | protocol) -> Document
  output(document, target)   # target: printer | pdf | preview
```

- No table of its own (likely) — templates come from Settings; rendered PDFs may
  be saved to `exports/` or attached via Attachments.
- Printing an artifact emits a **Timeline** "print" event and an audit row.

## 6. Consultation Workspace integration

- **Print** action renders the prescription (using the case's protocol print
  template if one applies) and sends to the configured printer or PDF preview.
- **Invoice** action renders and (later) issues the invoice.
- **Wise Printer Integration** panel shows printer status / target selection.
- Labels print from the Dispensing step.

## 7. Output targets & offline posture

- **Default:** the OS's installed printer + PDF export — fully offline, ₹0.
- Wise Printer hardware (if any) integrates behind the same `output(...)` target
  interface (Constitution Art. III §9) — swappable, no assumption baked into
  callers.
- Printing failures degrade gracefully; the consultation still completes and the
  document can be re-printed/saved.

## 8. Dependencies & sequencing

- **Requires:** F2 (Settings for templates + branding). Consumes visits (built),
  Billing/Dispensing (planned) as sources.
- **Feeds:** the Consultation Workspace Print/Invoice actions; Timeline print
  events; `exports/` (D3).
- **Sequencing:** prescription printing first (highest value), then invoices,
  then labels.

## 9. Manual test checklist (implementing phase)

- [ ] A prescription renders to a document with branding + variables filled.
- [ ] The rendered document is assertable headlessly (no printer needed).
- [ ] Output to PDF saves a file; output to printer sends a job.
- [ ] Editing the template in Settings changes the rendered output.
- [ ] A print emits a Timeline event and an audit row.
- [ ] Print failure does not break the consultation.

## 10. Risks

- **Template flexibility vs. simplicity** — give a good default template; make
  editing safe (no code, just fields/layout).
- **Printer environment variance** — rely on the OS print stack + PDF fallback so
  the feature works everywhere offline.
</content>
