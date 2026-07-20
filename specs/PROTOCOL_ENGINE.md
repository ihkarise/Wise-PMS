# Protocol Engine — Specification

> **Status:** Design only (Phase 2). Not implemented. Backlog **C2**. Planned
> tables: `protocols`, `protocol_items`. **Last updated:** 2026-07-20.
> Extends [`../docs/modules/Protocols.md`](../docs/modules/Protocols.md).

## 1. Purpose

A reusable clinical **template per condition** that pre-fills a consultation so
common presentations are fast and consistent — while staying **advisory**. A
protocol proposes; the doctor accepts, edits, or ignores. Structure never gates
the narrative (Constitution Art. II §2, §6).

## 2. Example protocols (initial library)

Migraine · GERD · IBS · Allergic Rhinitis · Asthma · PCOS · Infertility · Skin
Diseases · Anxiety · Depression.

These are seeded as editable templates (in Settings / a management screen), not
hardcoded — a clinician can author their own.

## 3. What a protocol defines

Per the charter, each protocol defines:

| Element | Meaning | Feeds |
| ------- | ------- | ----- |
| **Recommended investigations** | Baseline/monitoring tests to order | Investigation Engine |
| **Medicine templates** | Suggested remedies (name) | Prescription panel |
| **Dosage templates** | Potency + dosage + instructions per medicine | Prescription panel |
| **Advice templates** | Standard advice/remarks text | Remarks panel |
| **Printing instructions** | Which print template + advice sheet to use | Wise Printer |
| **Review schedule** | When to follow up (e.g. +2 weeks) | Follow-up / Appointments |
| **Doctor notes** | Private clinical notes / rationale for the protocol | Workspace |
| **Future AI hooks** | Placeholder for AI-assisted suggestion/refinement | AI Assistant |

## 4. Data model (planned — needs F1)

```
protocols
  id · name · condition · description · print_template_key ·
  followup_rule (e.g. "+14d") · doctor_notes · enabled · created_at · updated_at
  (multi-clinic: optional clinic_id later)

protocol_items
  id · protocol_id FK · kind (investigation | medicine | advice) ·
  name · potency · dosage · instructions · display_order
```

- `kind` discriminates the item type; medicine items reuse the *shape* of
  `utils.prescription` output (medicine/potency/dosage/instructions) so pulling a
  suggestion into the prescription is a straight mapping.
- `followup_rule` is a small relative-date grammar (e.g. `+14d`, `+1m`) resolved
  at apply time — no hardcoded schedules.
- `print_template_key` references a template defined in Settings (F2).

## 5. Service contract (target)

```
protocols.service
  list_protocols(enabled_only=True) -> list[dict]
  get_protocol(protocol_id) -> dict | None        # incl. items
  create_protocol(data, user_id) -> int
  update_protocol(protocol_id, data, user_id) -> None
  apply_protocol(protocol_id, patient, case) -> ProtocolSuggestion   # advisory
```

`apply_protocol` returns a **suggestion object** — a bundle of proposed
investigations, medicine items, advice, a follow-up date (from `followup_rule`),
and the print template — that the Workspace renders as editable chips. **Nothing
is written to the visit until the doctor accepts.** No auto-commit.

All create/update calls write an audit row.

## 6. Consultation Workspace integration

- The **Protocol Suggestions** panel offers a searchable list (by condition).
- Selecting a protocol calls `apply_protocol`; the panel shows the proposed
  investigations, medicines (with dosage), and advice as **accept/edit/dismiss**
  chips.
- Accepted medicines flow into the **narrative** prescription (the doctor can
  edit freely); accepted investigations flow into the **Investigation Panel**;
  the advice flows into **Remarks**; the follow-up date pre-fills **Follow-up**.
- The protocol's print template is used by **Wise Printer** when printing.

## 7. Authoring & governance

- A management screen (Administrator/Doctor under RBAC) authors protocols.
- Protocols are **versioned conceptually** via `updated_at`; changing a protocol
  never rewrites past visits (those captured the narrative that was actually
  written).
- Protocols are exportable/importable (Settings → Import/Export) so a clinician
  can share or back up their library.

## 8. Analytics hook (future)

`protocol_id` applied per visit lets Analytics correlate **protocol usage vs.
outcomes** (`visits.outcome`). This requires recording which protocol was applied
— a lightweight, non-authoritative link (e.g. `visits.applied_protocol_id`,
additive via F1) that never constrains the narrative.

## 9. AI hooks (future)

- **Suggest a protocol** from the chief complaint/history (AI Assistant, advisory).
- **Refine dosages** based on outcome history (advisory, audited).
- Any AI involvement is labeled, advisory, offline-preferred, and auditable
  (Constitution Art. VII §3).

## 10. Dependencies & sequencing

- **Requires:** F1 (tables), best paired with the **Consultation Workspace**
  phase (its only meaningful surface), and F2 (Settings) for print templates.
- **Feeds:** Investigation Engine, Prescription, Printer, Follow-up, Analytics,
  AI.

## 11. Manual test checklist (implementing phase)

- [ ] A protocol can be authored with investigations, medicines, advice, review
      rule, print template.
- [ ] `apply_protocol` returns suggestions without writing to the visit.
- [ ] Accepting suggestions edits the narrative/panels; dismissing changes
      nothing.
- [ ] Editing a medicine after accepting keeps the narrative authoritative.
- [ ] Changing a protocol does not alter past visits.
- [ ] Model/table parity + router contract green for new tables/routes.

## 12. Risks

- **Over-templating** could nudge toward form-first care — mitigate by keeping
  everything advisory and editable (Constitution Art. II §2).
- **Stale library** — provide easy authoring/import so protocols reflect current
  practice.
</content>
