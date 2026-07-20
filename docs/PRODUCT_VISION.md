# WiseOS Health — Product Vision

> **Status:** Living document. Update whenever product direction changes.
> **Last updated:** 2026-07-20 (Phase 1 — Project Memory System).

## 1. One sentence

**WiseOS Health is the operating system for a modern healthcare practice** —
a modular ecosystem where each clinical, pharmacy, and business function is an
independent module mounted on one shared platform.

## 2. What exists today

Today the ecosystem ships one working module: **Wise PMS** — an offline-first,
local, ₹0/month desktop Patient Management System for a homeopathy clinic
(Python + Flet + SQLite). It handles login, registration, patient search,
profiles, cases, visits/consultation, prescription intelligence, timeline,
attachments, audit, and backup. See [`SYSTEM_OVERVIEW.md`](./SYSTEM_OVERVIEW.md).

Wise PMS is **module #1**, not the whole product. Its architecture (see
[`ARCHITECTURE.md`](./ARCHITECTURE.md)) was deliberately built as a registry of
vertical-slice modules so the rest of the ecosystem can be added without
rewrites.

## 3. The ecosystem (target)

| Module | Purpose |
| ------ | ------- |
| **Wise PMS** | Patients, cases, consultation, prescriptions — the clinical core |
| **WHIMS** | Warehouse/Health Inventory Management — stock, batches, expiry |
| **PillFill** | Dispensing automation / pharmacy handoff |
| **Wise Printer** | Prescription, invoice, and label printing engine |
| **Holoscan** | Imaging / AI vision on uploaded reports |
| **Patient Portal** | Patient-facing web access to records & bookings |
| **Online Consultation** | Telemedicine (video/Meet) sessions |
| **AI Assistant** | Clinical decision support over structured data |
| **WhatsApp Automation** | Templated messaging (welcome, reminders, follow-ups) |
| **Analytics** | Practice, clinical, and prescription analytics |
| **OCR Engine** | Structured extraction from uploaded documents |
| **Protocol Engine** | Reusable clinical templates per condition |

## 4. Principles

1. **Modular before featureful.** No feature is implemented in isolation; every
   feature must integrate cleanly with future modules.
2. **Local-first, cost-zero by default.** Offline SQLite desktop is the baseline;
   cloud/sync is additive, never assumed.
3. **Narrative is the source of truth.** Doctors write free text; structure
   (prescription items, OCR values) is a non-authoritative extraction layer.
4. **Think five years ahead.** No decision may hardcode assumptions that block
   Portal, AI, Voice, Inventory, Billing, Analytics, Telemedicine, Cloud Sync,
   Mobile, or a public API.
5. **Every phase leaves the app working.** Independently deployable increments,
   documentation-as-implementation, tests, and explicit approval gates.

## 5. Success looks like

A clinician runs an entire consultation — from registering a patient to
printing a prescription and dispensing medicine — on one integrated screen,
with the same data instantly available to analytics, the patient portal, and
AI assistance, whether the practice is one desktop or many synced devices.

## 6. Non-goals (for now)

- Not a cloud SaaS first (cloud is a later, additive module).
- Not multi-tenant hospital ERP; the initial customer is a homeopathy clinic.
- Not a rewrite target — the ecosystem grows by adding modules, never by
  replacing the working core.
