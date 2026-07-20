# Module: Patient Portal

**Status:** 🔜 Planned — **not implemented** · separate front-end + API

## Purpose (target)
Patient-facing access to their own records: bookings, prescriptions, reports,
and messages.

## Target design (planned — needs approval)
- A **separate front-end** (web/mobile) talking to WiseOS through a **public API**
  layer (not yet built). The API reuses existing services/repositories — which
  are UI-agnostic — without modifying them.
- Patient identity ties to the existing `patients` record (reg-no / verified
  phone). No duplicate patient store.

## Capabilities (target)
- View profile, visit history/timeline, prescriptions, uploaded reports (+OCR
  values), and invoices.
- Self-book appointments; receive WhatsApp confirmations.
- Join Online Consultation sessions.

## Hard prerequisites
- **RBAC (F3)** — patient is a distinct principal with least-privilege access.
- **Encryption at rest (F7)** and **transport security** — PHI leaves the single
  trusted machine for the first time.
- **Public API** layer + authentication (patient login, not the staff `users`
  table).
- **Cloud sync (F8)** if the portal is hosted off the clinic device.

## Dependencies
Everything above. This is a **late** module by design — it must not ship before
the security foundation is proven.

## Notes
Treat the portal as an untrusted client: all authorization decisions happen
server-side at the service/repository seam, never in the portal UI.
