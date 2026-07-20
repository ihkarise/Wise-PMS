# EPIC-09 — Wise Printer

> **Spec:** [`../PRINTER_SYSTEM.md`](../PRINTER_SYSTEM.md) · **Backlog:** D1 ·
> **Stage:** B — Clinical Core · **Depends on:** EPIC-02 (templates), EPIC-04
> (surface) · **Complexity:** M · **Risk:** Medium · **Status:** Backlog (planning).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. III, V, VIII §3.

## 1. Objective

Render and output prescriptions, invoices, and labels from clinic-branded,
editable templates. Separate **render** (build document from data + template) from
**output** (printer / PDF / preview) so the same document can be printed, saved, or
attached, and rendering is headlessly testable.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E09-F1 | Render engine | `render_prescription/invoice/label/advice` → Document |
| E09-F2 | Output targets | `output(doc, target)`: printer · PDF · preview (OS stack + PDF, offline ₹0) |
| E09-F3 | Branding & templates | From Settings (EPIC-02); default templates shipped |
| E09-F4 | Variable substitution | Shared tokens (`{regname}`, `{fileno}`, `{doctorName}`, `{clinicName}`, Rx list…) |
| E09-F5 | Workspace actions | Print / Invoice / Wise Printer status panel |
| E09-F6 | Timeline + audit | Print emits a Timeline event + audit row |

## 3. User stories

- **E09-F1-S1** — As a doctor, I want to print a prescription from the Workspace,
  so that the patient leaves with a script.
- **E09-F3-S1** — As the clinic, I want my branding on printed output, so that
  documents look professional and consistent.
- **E09-F2-S1** — As a doctor, I want to save a script as PDF when no printer is
  handy, so that I can print later or share it.
- **E09-F1-S2** — As a reviewer, I want rendering asserted without a printer, so
  that print output is testable in CI.

## 4. Engineering tasks

- **E09-T1** — `modules/printer/` slice: `render_*` (Document model) + `output`
  target interface (printer/PDF/preview). Likely no table (templates in Settings).
- **E09-T2** — Default templates (prescription/invoice/label/advice) shipped so the
  feature works before custom templates.
- **E09-T3** — Variable substitution into a fixed layout (no code injection).
- **E09-T4** — Workspace Print/Invoice actions + Wise Printer status panel.
- **E09-T5** — Timeline print event + audit.
- **E09-T6** — Optional PDF save to `exports/` or attach via Attachments.
- **E09-T7** — Tests (headless render assertions) + docs (Printer module doc,
  CHANGELOG).

## 5. Dependencies

- **Upstream:** EPIC-02 (branding/templates), EPIC-04 (actions). Sources: visits
  (built), EPIC-12 (invoices/labels), EPIC-05 (protocol print template).
- **Downstream:** EPIC-14 (printed reports), `exports/` (D3).

## 6. Acceptance criteria

- **AC1** — *Given* a visit, *when* the prescription is rendered, *then* the
  document contains branding + substituted variables.
- **AC2** — *Given* a rendered document, *when* asserted in a test, *then* no
  printer is required.
- **AC3** — *Given* an edited template (EPIC-02), *when* rendering, *then* output
  reflects the change.
- **AC4** — *Given* output to PDF, *when* invoked, *then* a file is produced; to
  printer, *then* a job is sent.
- **AC5** — *Given* a print, *when* it completes, *then* a Timeline event + audit
  row are recorded.
- **AC6** — *Given* a print failure, *when* it occurs, *then* the consultation is
  unaffected and the document can be re-printed/saved.

## 7. Regression tests

- **Must stay green:** golden, models, router, views.
- **New:** render tests (branding/variables/headless), output-target tests (fake
  target), template-change reflection, Timeline print-event test.

## 8. Rollout phases

- **E09-R1** — Render engine + default templates + PDF/preview output (offline).
- **E09-R2** — Printer output target + Workspace Print action.
- **E09-R3** — Invoice/label rendering (with EPIC-12) + Timeline/audit events.
- **E09-R4** — Custom templates from Settings; docs closeout.

## 9. Rollback

Revert module + hide Print action; consultations complete on narrative. No data
destroyed.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: works offline with default templates;
render asserted headlessly; template editing cannot inject code into output.
</content>
