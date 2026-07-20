# .ai/PRODUCT_DIRECTION.md — Where the product is heading

> The product-side compass. Complements [`ARCHITECTURE_RULES.md`](./ARCHITECTURE_RULES.md)
> (the engineering-side compass). **Updated:** 2026-07-20.

## The vision in one line
WiseOS Health = the operating system for a modern healthcare practice, built as
independent modules on one platform. Full statement:
[`../docs/PRODUCT_VISION.md`](../docs/PRODUCT_VISION.md).

## The anchor feature
The **Consultation Workspace**: after creating a case, the doctor enters one
integrated screen — Patient Summary, Chief Complaint, History, Examination,
Diagnosis, Investigation, OCR Results, Timeline, Protocol Suggestions,
Prescription, Medicine Pricing, Remarks, Print/Dispense/Invoice, Follow-up.
Everything below is built to feed it.

## Build order (compass, not contract — each phase needs approval)
1. **Foundation:** Migrations (F1) → Settings UI (F2) → RBAC (F3).
2. **Clinical core:** Consultation Workspace → Protocol Engine → Printer → OCR.
3. **Engagement/business:** WhatsApp → Billing/Dispensing → Inventory (WHIMS) →
   PillFill.
4. **Insight & reach:** Analytics/Reports → Patient Portal → Telemedicine →
   AI Assistant/Holoscan.
5. **Platform:** Cloud Sync → Mobile → public API.

## Product principles
- **One integrated screen** for the consultation — reduce clicks and context
  switches for the doctor.
- **Templates everywhere** (protocols, prescriptions, invoices, WhatsApp) —
  editable in Settings, consistent across modules.
- **Reminders and follow-up are retention** — surface them, automate them.
- **Structure serves insight, narrative serves care** — never trade one for the
  other.
- **The clinic owns its data** — offline-first, exportable, backup-able.

## What we will not do
- Ship a cloud/multi-user surface before RBAC + encryption at rest.
- Force clinicians into rigid forms.
- Build a monolith — every capability is a mountable module.
- Remove functionality without explicit Product Owner approval.
