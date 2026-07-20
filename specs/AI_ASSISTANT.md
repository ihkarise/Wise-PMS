# AI Assistant — Specification

> **Status:** Design only (Phase 2). Not implemented. Backlog **A1–A3**.
> Primarily a **service seam**. **Last updated:** 2026-07-20.
> Extends [`../docs/modules/AI.md`](../docs/modules/AI.md).

## 1. Purpose

Clinical decision **support** and document interpretation over the structured,
audited data the ecosystem already produces. The AI Assistant is **advisory
only** — it proposes; the doctor decides. Outputs are labeled, never auto-committed
to the record (Constitution Art. II §6).

## 2. Scope

| Capability | What it does |
| ---------- | ------------ |
| **AI Assistant** | Suggestions from typed models + prescription extraction + timeline + OCR values: protocol suggestions, drug-interaction flags, history summarization, "what changed since last visit" |
| **Holoscan** | Imaging/vision interpretation of uploaded reports/images, feeding structured findings back into OCR/timeline |
| **Voice dictation** | Speech-to-text into the narrative fields (never replaces the doctor's authorship) |

## 3. Why the current architecture is ready

- **Typed models** (`RowModel`) give clean, structured entities to feed models.
- **`utils/prescription`** already produces structured medicine items.
- **Audit trail** provides traceability for any AI-influenced decision.
- **Repository seam** lets AI read data without new coupling.

## 4. Design: one provider interface, offline-preferred

Per Constitution Art. III §9 and VII §3:

```
AiProvider (interface)
  suggest(context) -> Suggestion[]        # advisory, labeled, with rationale
  summarize(timeline) -> Summary
  flag_interactions(prescription) -> Flag[]

Implementations (planned):
  • LocalModelProvider   (on-device / local model — default, privacy-preserving)
  • HostedApiProvider    (cloud LLM — opt-in, consented, encrypted, key in env)
```

- **Default to privacy-preserving / on-device** options to protect the offline,
  ₹0 posture. Any cloud AI is an **explicit, consented, encrypted opt-in** with
  secrets in Settings/env, never committed.
- The backend is swappable behind the interface; callers never assume a provider.

## 5. Service contract (target)

```
ai.service
  suggest_protocol(case, history) -> list[Suggestion]     # advisory
  summarize_history(patient_id) -> Summary                # advisory
  flag_interactions(prescription_items) -> list[Flag]     # safety, advisory
  interpret_report(ocr_result) -> Interpretation          # advisory (Holoscan)
```

- Every call and its **inputs/outputs are auditable** (`entity_type = ai_event`).
- Outputs surface as **labeled, dismissible suggestions** in the Consultation
  Workspace and as `kind = ai` timeline events — never as facts written to the
  record.

## 6. Consultation Workspace integration

- **Protocol Suggestions** panel may be AI-assisted (suggest a protocol from
  complaint/history) — still routed through the Protocol Engine as advisory picks.
- **Safety flags** (interactions, allergy conflicts) surface where the
  prescription is written.
- **History summary** ("what changed since last visit") appears in the follow-up
  preload — advisory context, not stored as fact.
- Voice dictation feeds the narrative editors; the doctor edits/confirms.

## 7. Guardrails (hard rules)

1. **Advisory, never automatic** — no AI output auto-commits to the clinical
   record (Constitution Art. II §6).
2. **Labeled** — AI-originated content is always visibly marked as such.
3. **Auditable** — inputs and outputs are logged.
4. **Privacy-first** — default on-device; cloud is opt-in + consented + encrypted;
   PHI never leaves the machine without explicit consent.
5. **Degrade gracefully** — if the provider is unavailable, the consultation is
   unaffected (offline core intact).

## 8. Dependencies & sequencing

- **Best after:** OCR (structured values), Protocols (suggestion surface), and
  RBAC/security (F3/F7) — since AI may involve external providers and PHI.
- **One of the later modules**; the seam can exist early (typed models + audit are
  ready) but meaningful features need the feeders in place.

## 9. Manual test checklist (implementing phase)

- [ ] Suggestions render labeled and dismissible; none auto-commit.
- [ ] Interaction/allergy flags surface at the prescription.
- [ ] Every AI call logs inputs/outputs to audit.
- [ ] Default provider is on-device; no PHI leaves the machine without consent.
- [ ] Provider outage does not affect the consultation.

## 10. Risks

- **Trust & liability** — advisory framing and audit are essential; never present
  AI output as authoritative.
- **Privacy** — cloud providers touch PHI; keep them opt-in, consented, encrypted,
  and off by default (Constitution Art. VII §3).
- **Footprint** — a local model must not bloat the offline `.exe`; keep it behind
  the provider interface and optional.
</content>
