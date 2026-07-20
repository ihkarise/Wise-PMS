# Module: Protocols (Protocol Engine)

**Status:** 🔜 Planned — **not implemented** · planned tables: `protocols`,
`protocol_items`

## Purpose (target)
Reusable clinical templates per condition that pre-fill a consultation, so
common presentations are fast and consistent.

## Example protocols
Migraine · GERD · Allergic Rhinitis · Asthma · Skin Disease · PCOS · Infertility
· IBS · Anxiety · Depression.

## A protocol may contain
- Investigation recommendations
- Medicine suggestions (name, potency, dosage, instructions)
- Remarks
- Printing template reference
- Follow-up schedule

## Target design (planned — needs approval)
- `app/modules/protocols/` vertical slice.
- Tables (migration F1): `protocols` (name, condition, description, print
  template, followup rule) and `protocol_items` (protocol_id, kind =
  investigation/medicine, name, potency, dosage, instructions, order).
- Management screen (Administrator/Doctor) to author protocols; a **read seam**
  the Consultation Workspace calls to surface suggestions.
- Service: `list_protocols`, `get_protocol`, `apply_protocol(case/visit)` →
  returns suggested items the doctor can accept/edit (never auto-committed).

## Integrations
- **Consultation Workspace** shows "Protocol Suggestions" and lets the doctor
  pull items into the prescription (narrative stays authoritative).
- **Printer** uses the protocol's print template.
- **Analytics** correlates protocol usage with outcomes.
- Reuses `app.utils.prescription` shapes for medicine items.

## Dependencies
Migrations (F1); best paired with the Consultation Workspace phase.

## Notes
Suggestions must be **advisory**, mirroring the narrative-first principle —
never constrain what the doctor writes.
