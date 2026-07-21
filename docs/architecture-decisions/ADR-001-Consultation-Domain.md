# ADR-001 — Consultation Domain Architecture

**Status:** Proposed (Product Owner review) · **Date:** 2026-07-20
**Supersedes:** the "extend `visits`" recommendation in
`docs/planning/SPRINT2_TECHNICAL_PLAN.md` §3 (Option A).
**Context:** WiseOS Health is an integrated **Clinical Operating System**, not a
Patient Management System. The Consultation Workspace is the product's center and
must support Timeline, OCR, AI, Investigation comparison, Voice, Protocols,
Patient Portal, WHIMS, PillFill, Printing, Analytics, Telemedicine, Mobile,
Multi-clinic, and Cloud Sync.

---

## 1. Problem statement

Sprint 1 shipped the Consultation Workspace **skeleton** (composition-only, no
persistence). Sprint 2 must define the **persistence spine** ("Consultation
Domain Model"). The current planning assumes that spine is *the existing `visits`
table, widened with narrative columns*. That decision is **premature**: it fixes
the clinical data model before the OS-wide architecture (AI Gateway, Investigation
Intelligence, independent Timeline/OCR/AI modules) is settled. Widening `visits`
now risks a "god table" that later blocks the very modules the product is built
around.

**Decision needed:** what is the correct home for consultation clinical data, and
how do Investigations, OCR, AI, Timeline, Protocols, and Attachments relate to it?

## 2. Requirements

### Functional
- One integrated consultation surface; narrative is authoritative.
- Draft → completed lifecycle; nothing lost mid-consult.
- Investigation Intelligence per uploaded report: OCR → structured extraction →
  AI interpretation → previous-report comparison → trend → timeline → doctor
  review.
- AI everywhere, but through **one central AI Gateway** — no module talks to a
  provider directly. Two modes: (A) clinic's own API key (encrypted;
  OpenAI/Gemini/Claude/OpenRouter/NVIDIA NIM/Azure/Ollama), (B) WiseOS-managed
  (plans Basic/Professional/Enterprise; usage limits, token accounting, cost,
  billing).

### Non-functional (evaluation axes)
Scalability · AI integration · OCR · Timeline · Future expansion · Reporting ·
Multi-clinic · Cloud Sync · Offline mode · Performance · Migration complexity.

### Constraints (from Product Constitution / architecture rules)
- Narrative authoritative; derived data (OCR/AI/extraction) never gates the record.
- Never physically delete clinical data; every mutation audited.
- SQL only in repositories; vertical-slice modules; providers behind an interface;
  secrets never committed; offline/₹0 default, cloud additive.

---

## 3. Architecture options

### Option A — Large `visits` table
Add `chief_complaint`, `examination`, `diagnosis`, `remarks`, `status`, and (over
time) every consultation facet as columns on `visits`.

- **+** Smallest immediate diff; single writer; reuses the visits slice; keeps the
  regression golden byte-identical (columns-only).
- **−** `visits` becomes the dumping ground for the whole clinical document.
  Consultation, investigation summaries, AI outputs, protocol state all gravitate
  here → wide, sparse table. Reporting and multi-clinic scoping get harder.
  Conflates the **visit event** (an appointment/encounter) with the **clinical
  document** (what was recorded). Poor fit for Cloud Sync (large row churn) and
  AI (no clean aggregate to feed).

### Option B — Dedicated Consultation aggregate
New `consultations` (+ child tables) owns all clinical-document data; `visits`
shrinks or is absorbed.

- **+** Clean clinical-document model; good AI/reporting surface.
- **−** Duplicates/deprecates the working `visits` slice and its
  `prescription_items`, timeline, dashboard, and regression coverage. Forces a
  migration of live data and a golden rewrite now — high churn before the OS
  architecture is proven. Two concepts (event vs document) still need separating.

### Option C — Hybrid (separation of concerns) — **recommended**
Distinct bounded contexts, each an independent vertical slice, composed by the
Workspace:

```
Visit          = the ENCOUNTER/event   (visits)            — when/where/who, status
Consultation   = the CLINICAL DOCUMENT (consultations)     — complaint/history/exam/
                                                              diagnosis/remarks, draft→final
Investigations = independent module     (investigation_*)   — orders + results
OCR            = independent module      (ocr_results)       — derived extraction
AI             = independent module      (ai_gateway + logs) — one gateway, all providers
Protocols      = independent module      (protocols/*)       — advisory templates
Attachments    = independent module      (attachments)       — original files (built)
Timeline       = independent READ MODEL  (no table)          — merges all of the above
```

- **+** Each concern evolves without touching the others; matches the built
  design (Timeline is already a read model; OCR/Investigation specs already
  define their own tables). Best fit for AI (a `Consultation` aggregate is the
  natural context object), reporting, multi-clinic scoping, and Cloud Sync
  (small, well-bounded rows). Keeps `visits` intact → no golden churn now.
- **−** More modules/tables over time; the Workspace must compose several
  services (already its job); one new join (visit ↔ consultation).

---

## 4. Trade-off analysis

| Axis | A: Large Visits | B: Consultation Aggregate | C: Hybrid (rec.) |
| ---- | --------------- | ------------------------- | ---------------- |
| Scalability | ✗ wide sparse table | ✓ | ✓✓ bounded contexts |
| AI integration | ✗ no clean aggregate | ✓ | ✓✓ Consultation = context object for Gateway |
| OCR | ✗ unrelated to visit | ~ | ✓✓ own `ocr_results` over attachments |
| Timeline | ~ | ~ | ✓✓ read model already composes per-source |
| Future expansion | ✗ god table | ~ deprecates visits | ✓✓ add module = add slice |
| Reporting | ✗ sparse columns | ✓ | ✓✓ query the right context |
| Multi-clinic | ✗ | ~ | ✓ clinic_id per context, additive |
| Cloud Sync | ✗ large-row churn | ~ | ✓✓ small bounded rows sync independently |
| Offline mode | ✓ | ✓ | ✓ all local-first; AI/OCR degrade gracefully |
| Performance | ~ | ~ | ✓ lazy per-panel loads; no whole-row rewrites |
| Migration complexity | ✓✓ smallest now | ✗ migrate live data now | ✓ additive new table, `visits` untouched |
| Golden impact | ✓ byte-identical | ✗ rewrite now | ~ new `TABLES:` line — **intended, documented** |

Net: A wins only on *immediate* diff size; it loses every axis the product is
actually built for. B pays migration cost too early. **C** is the OS-aligned
choice and defers cost to the point of need.

---

## 5. Recommended architecture — Option C (Hybrid)

- **`visits`** stays the **visit/encounter event** (unchanged): patient, case,
  doctor, type, date, follow-up, outcome, prescription linkage. No new clinical
  columns.
- **`consultations`** (new, F-gated) is the **clinical document**, 1:1 with a
  visit (`visit_id FK`), narrative-first:
  `chief_complaint · history · examination · diagnosis · remarks · status
  (draft|completed) · created_at · updated_at`. History/Prescription/Follow-up
  keep flowing through their existing homes until deliberately migrated; new
  columns stay **optional** (no forced structure).
- **Investigations, OCR, AI, Protocols** are **independent modules** with their
  own tables/seams, referenced by id — never embedded in the consultation row.
- **Timeline** stays a **read model** (no table), gaining one SELECT per new
  source.
- **Workspace** = coordinator composing `consultation + visit + investigations +
  ocr + ai + protocols + timeline` services. No module owns another's SQL.

## 6. Database strategy

- Additive, forward-only, reversible migrations via the F1 runner. Each new
  context ships its **own** `CREATE TABLE IF NOT EXISTS` migration; `visits` is
  left alone.
- `consultations` lands as one migration when Sprint 2 is (re)approved — a **new
  table**, so the regression golden `TABLES:`/`INDEXES:` lines change **once,
  intentionally**, recorded in an ADR + CHANGELOG + DECISIONS (per rule 12), not
  silently.
- Multi-clinic: add nullable `clinic_id` to context tables when Stage E lands —
  additive, no rework.
- Every context row carries `created_at`/`updated_at` for Cloud Sync conflict
  handling later.

## 7. AI strategy

- **One `ai_gateway` service is the only egress to any provider.** Modules call
  `ai_gateway.request(capability, context)`; they never import a provider SDK.
- Provider interface (`AiProvider`) with adapters: OpenAI, Gemini, Claude,
  OpenRouter, NVIDIA NIM, Azure, Ollama, plus a local/offline default.
- **Mode A (BYO key):** keys stored **encrypted** (Settings/secret store, never in
  plaintext DB, never committed).
- **Mode B (managed):** plan tier (Basic/Professional/Enterprise), usage limits,
  token accounting, cost monitoring, billing — all behind the same Gateway API so
  callers are mode-agnostic.
- Every AI call is **advisory, labeled, audited**, never auto-committed to the
  record. Gateway logs requests for cost + traceability.

## 8. OCR strategy

- `ocr_results` (1 row augments 1 `attachments` row) holds `raw_text`,
  `structured` (JSON: test/value/unit/range/flag), `confidence`, `engine`,
  `status`, `doctor_notes`. Original document never mutated (Attachments owns it).
- OCR is **derived/non-authoritative**; structured values flow into
  `investigation_results` (`source=ocr`) and are always doctor-reviewable.
- Engine behind a swappable interface; AI interpretation is a **separate** Gateway
  call over OCR output, not baked into OCR.

## 9. Timeline strategy

- Remains a **read model** with no base table; `timeline.service` composes one
  SELECT per source (visits, cases, attachments today; consultations,
  investigations, ocr, protocols, ai events later) and merges newest-first.
- A new module joins the timeline by adding a source query — no schema coupling,
  no writes.

## 10. Investigation strategy

- `investigation_orders` (what was requested, during consult) +
  `investigation_results` (what came back, linked to an attachment + optional OCR
  values). Comparison/trend is a **service** over results by analyte, surfaced in
  the Workspace and Timeline.
- Manual result entry works before OCR/AI exist → graceful degradation.

## 11. Future compatibility

Option C keeps every listed future module unblocked: each is an independent slice
that references consultation/visit by id and joins the Timeline read model. AI and
Cloud Sync get clean, bounded aggregates. Multi-clinic scoping is an additive
`clinic_id`. Nothing in this ADR hardens against Voice, Portal, WHIMS, PillFill,
Printing, Analytics, Telemedicine, Mobile, or Public API.

## 12. Risks

| ID | Risk | Mitigation |
| -- | ---- | ---------- |
| AR1 | More tables/modules → more composition surface | Workspace is already a composer; add slices incrementally, one panel at a time |
| AR2 | visit ↔ consultation 1:1 drift (orphan/duplicate) | FK + service invariant "one open consultation per visit"; test it |
| AR3 | Intended golden change mistaken for regression | Land `consultations` with ADR + CHANGELOG + DECISIONS note; review diff of golden explicitly |
| AR4 | AI Gateway bypass (a module calls a provider directly) | Enforce with layering grep in CI + code review; providers only imported by the gateway module |
| AR5 | Secret leakage (BYO keys) | Encrypt at rest; env/secret store; never in DB plaintext or git; add a secret-scan gate |
| AR6 | Over-structuring narrative | New consultation fields optional; narrative stays authoritative |
| AR7 | Premature build of AI/OCR before foundation (F2 Settings/F3 RBAC/encryption) | Sequence: foundation → consultation document → feeders; AI/OCR gated behind Settings + encryption |

## 13. Migration guidelines

- **Do not widen `visits`** for clinical-document data. `visits` = event only.
- Each bounded context = its **own additive migration**, reversible `down`,
  idempotent `up` (`CREATE TABLE IF NOT EXISTS`; guard `ADD COLUMN` with
  `PRAGMA table_info`).
- Introduce `consultations` first (Sprint 2, once re-approved); OCR/Investigation/
  AI/Protocol tables land with their own phases.
- Any golden-changing migration ships with ADR + CHANGELOG + DECISIONS in the same
  commit. Keep foundation order: **F1 (done) → F2 Settings → F3 RBAC + encryption
  → Consultation document → feeders (Protocol/Investigation/OCR/AI)**.

---

## Decision
**Adopt Option C (Hybrid).** `visits` = visit event; a new `consultations`
aggregate = clinical document; Investigations/OCR/AI/Protocols/Attachments are
independent modules; Timeline is a read model; all AI egress via one Gateway.
Revisit Sprint 2 planning to match (see session report). Await Product Owner
approval before any implementation.
