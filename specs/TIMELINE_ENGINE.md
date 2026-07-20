# Timeline Engine — Specification

> **Status:** Core built (visits + cases + attachments); this spec designs the
> **target unified timeline** across all modules. Backlog extends
> [`../docs/modules/Timeline.md`](../docs/modules/Timeline.md).
> **Last updated:** 2026-07-20.

## 1. Purpose

Every patient has **one continuous medical timeline** — a single newest-first feed
of everything that happened to them, across every module. It is the longitudinal
record made visible (Constitution Art. II §4) and the fastest way for a doctor to
regain context before a consultation.

## 2. What the timeline includes (target)

Per the charter, the timeline includes:

| Event kind | Source module | Status |
| ---------- | ------------- | ------ |
| Appointments | Appointments | 🔜 |
| Visits | visits | ✅ |
| Investigations (orders + results) | Investigation Engine | 🔜 |
| OCR (report processed, values) | OCR Engine | 🔜 |
| Medicines (prescribed / dispensed) | visits / Dispensing | ✅ (Rx) / 🔜 (dispense) |
| Protocol Changes (applied/updated) | Protocol Engine | 🔜 |
| Follow-ups (scheduled / due / missed) | visits / Appointments | ✅ (seed) / 🔜 |
| Payments / Invoices | Billing | 🔜 |
| Printing (script/invoice printed) | Wise Printer | 🔜 |
| Cases (opened / resolved) | cases | ✅ |
| Attachments (uploaded) | attachments | ✅ |
| Future AI Events (summaries, flags) | AI Assistant | 🔜 |

Today's timeline already merges **visits, cases, attachments**.

## 3. Architecture — a read model, not a table

The Timeline owns **no base table**. It is a **read model** (`timeline.service`)
that composes one SELECT per source via `TimelineRepository`, merges, shapes, and
sorts newest-first (existing design). New modules join the timeline by **adding a
repository query**, not by changing the timeline's contract (Constitution
Art. IV §5).

### Event shape (stable contract)

```
TimelineEvent
  kind     # visit | case | attachment | appointment | investigation |
           #   ocr | dispense | protocol | followup | payment | print | ai
  id       # id within its source
  ts       # timestamp used for ordering (descending)
  title    # e.g. "Visit — Migraine" / "Report — CBC"
  summary  # first line / key detail
  extra    # kind-specific dict (outcome, values, amount, status…)
  followup # optional follow-up marker
  ref      # route to open the underlying record
```

Adding a new `kind` must not break existing consumers — consumers switch on
`kind` and fall back gracefully for unknown kinds.

## 4. Service contract (target)

```
timeline.service
  timeline_for_patient(patient_id, kinds=None, since=None) -> list[dict]
  # kinds/since let callers filter (e.g. Workspace "reports only", "last 6 months")
```

Pure read; writes nothing, audits nothing (existing behavior). Filtering is added
additively; the default call keeps its current contract for the regression golden.

## 5. Consultation Workspace integration

- **Timeline peek** (right rail) shows the recent feed while consulting.
- **Investigation Timeline** panel is a filtered view (`kinds=[investigation,
  ocr]`).
- Clicking any event opens the underlying record (route via `ref`).

## 6. Performance

- Timeline reads scale with a patient's history; each source query is indexed by
  `patient_id`. As modules grow, prefer per-source LIMIT + a merged top-N rather
  than loading a whole life history at once (relevant to L11).
- The read model is rebuilt on navigation (current model); a future paginated /
  "load more" mode is a candidate once histories get long.

## 7. Future events & AI

- **AI events** (summaries, risk flags) appear as `kind = ai`, always labeled
  advisory and audited (Constitution Art. II §6).
- A future **AI timeline summary** ("what changed since last visit") is generated
  on demand from the same feed — advisory, never stored as fact.

## 8. Dependencies & sequencing

- **Built on:** the existing timeline read model.
- **Grows with:** each module that emits events (Appointments, Investigation,
  OCR, Dispensing, Billing, Printer, Protocol, AI). Each contributes a repository
  query when it ships — no big-bang timeline rewrite.
- **No new base table**; no F1 dependency for the core (new source tables arrive
  with their own modules).

## 9. Manual test checklist (per contributing module)

- [ ] The new module's events appear in the feed with correct `kind`, `ts`,
      `title`, and open the right record.
- [ ] Existing consumers still render (unknown-kind fallback holds).
- [ ] `timeline_for_patient` default contract unchanged (regression golden green).
- [ ] Filtering by `kinds`/`since` returns the expected subset.

## 10. Risks

- **Contract drift** — every module adding events must respect the event shape;
  centralize the shape and the merge in `timeline.service`.
- **Volume** — long histories need pagination before they feel slow (F6).
</content>
