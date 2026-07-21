# Sprint 3 — Recommendation: Narrative Editors + Autosave (Consultation Workspace, live)

**Status:** PLAN ONLY — no code. Await Product Owner approval.
**Date:** 2026-07-21
**Roles:** Lead Product Architect · Clinical Software Architect · Technical Lead
**Depends on:** Sprint 2 consultation aggregate + lifecycle service (shipped, PR #7),
ADR-001 (frozen). Builds on `v0.5.0` workspace skeleton (Sprint 1).

---

## TL;DR

**Recommendation: build Narrative Editors + Autosave.** Turn the Consultation
Workspace from a read-only skeleton into a live, editable clinical document that
persists through the lifecycle service already shipped in Sprint 2.

Everything needed underneath is already built: the `consultations` table, the
`draft → in_progress → completed` state machine, `save_consultation` /
`complete_consultation`, audit on every mutation. Sprint 2 explicitly named the
editable window as **the autosave target** (Technical Plan §4e). Sprint 3 wires
the UI to that spine — **no schema change, no new domain, no AI/OCR risk.**

This is the payoff milestone: the anchor feature ("the heart of the software")
becomes usable for the first time.

---

## The candidates, ranked

Scored 1–5 (5 = best/lowest-risk). Ranking columns: Clinical value · Technical
dependency (5 = dependencies already met) · Risk (5 = lowest risk) · User impact
· Future scalability.

| Candidate | Clinical | Tech-dep | Risk | User | Scale | Total | Verdict |
| --------- | :------: | :------: | :--: | :--: | :---: | :---: | ------- |
| **Narrative Editors + Autosave** | 5 | 5 | 5 | 5 | 4 | **24** | ✅ **Sprint 3** |
| Follow-up in workspace (C6) | 4 | 5 | 5 | 4 | 4 | 22 | fast-follow (fits Sprint 3 tail) |
| Protocol Engine (C2) | 4 | 3 | 3 | 4 | 5 | 19 | Sprint 4 candidate |
| Attachments-in-workspace (surface) | 3 | 4 | 4 | 4 | 3 | 18 | fast-follow |
| Investigation Workspace (C4) | 4 | 2 | 2 | 3 | 5 | 16 | after editors + protocol |
| AI Gateway (A1) | 4 | 2 | 2 | 3 | 5 | 16 | after editors give it context |
| OCR Engine (D2) | 3 | 1 | 1 | 3 | 4 | 12 | latest — depends on Investigation |

### Why the order

- **Narrative Editors + Autosave wins on every axis except raw scalability.**
  The domain spine is done, so technical dependency and risk are near-zero, and
  clinical/user impact is maximal: it's the first sprint where a doctor can
  actually *write a consultation*.
- **Autosave has no meaning without editors** — they are one milestone, not two.
  Sprint 2 reserved `updated_at` and the editable-state window precisely for
  this; splitting them would ship a debounce with nothing to save.
- **AI Gateway, Investigation, OCR all consume the consultation document.**
  `to_ai_context` (the Sprint 2 seam) returns the narrative fields — which stay
  empty until editors exist. Building AI/OCR first means building on an empty
  record. **Editors are the enabling dependency for the entire right rail.**
- **OCR ranks last**: it depends on Investigation (structured values flow OCR →
  Investigation → consultation, never inline — ADR-001), which itself depends on
  the editable workspace. Highest risk, longest dependency chain.
- **Protocol Engine** is high-value and the natural Sprint 4, but it *writes into*
  the narrative fields (templates prefill Complaint/History/Diagnosis). It needs
  the editors as its insertion surface — so editors come first.

## Scope (Sprint 3)

**In:** editable Complaint / History / Examination* / Diagnosis / Remarks fields
in the center column; debounced autosave → `save_consultation`; live status
reflecting `draft → in_progress`; enable **Complete Visit** →
`complete_consultation`; save-state indicator ("Saving… / Saved HH:MM"); draft
auto-created on workspace open via `open_or_create_draft`.

> *Examination has a column in `consultations` but no section in the current
> skeleton nav — Sprint 3 adds the nav entry. No schema change.

**Out (non-goals):** AI, OCR, Investigation, Protocol logic (seams stay
placeholders); Prescription editor (still `visits`-owned — deferred, ADR-001);
Print/Invoice/Dispense/WhatsApp actions (stay disabled); RBAC; amend/lock
surfaces (guarded in service, no UI this sprint); rich-text/markdown.

## Success = one sentence

A doctor opens a case, types into Chief Complaint, and the words are still there
— audited, status flipped to `in_progress` — after a refresh, without ever
pressing Save; pressing Complete Visit seals the document to `completed`.

## Deliverables in this planning set

- `SPRINT3_TECHNICAL_PLAN.md` — architecture, autosave design, state ownership
- `SPRINT3_FILE_MAP.md` — new/modify/frozen files
- `SPRINT3_RISK_ASSESSMENT.md` — risks + mitigations
- `SPRINT3_TESTING_PLAN.md` — test matrix + acceptance
- `SPRINT3_MILESTONE_CHECKLIST.md` — ordered execution checklist

**Await Product Owner approval before any implementation.**
