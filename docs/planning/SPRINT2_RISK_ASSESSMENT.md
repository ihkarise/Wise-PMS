# Sprint 2 — Risk Assessment (v2): Consultation Domain Model (Hybrid / ADR-001)

Severity: 🔴 Critical · 🟠 High · 🟡 Medium · 🟢 Low
Supersedes v1 (Option A). Per ADR-001.

| ID | Risk | Sev | Likelihood | Impact | Mitigation |
| -- | ---- | --- | ---------- | ------ | ---------- |
| **R1** | Intended regression-golden `TABLES:` change (new `consultations`) mistaken for a regression, or rubber-stamped. | 🟡 Medium | Medium | Hidden drift slips in, or reviewers distrust the golden. | Land the golden edit **with** ADR + CHANGELOG + DECISIONS in the same commit; review the golden diff line-by-line; only `consultations` line + its indexes may change. |
| **R2** | visit ↔ consultation 1:1 drift — orphan or duplicate consultation per visit. | 🟠 High | Low | Two clinical documents per encounter → data integrity loss. | `visit_id UNIQUE` at DB level + service invariant via `open_draft_for_visit`; test that a second `create_draft` for the same visit returns the existing row, not a new one. |
| **R3** | Draft leakage — abandoned `status='draft'` consultations pollute timeline/reports/stats. | 🟡 Medium | Medium | Dashboards/timeline show unfinished documents. | Timeline/report/`for_patient` queries filter or mark `status='draft'`; one reusable draft per visit; test drafts don't inflate completed counts. |
| **R4** | Rollback faulty → `consultations` not cleanly dropped. | 🟢 Low | Low | Rollback leaves orphan table/index. | `down` = `DROP TABLE IF EXISTS` + drop indexes; new table, no data migration → trivially reversible; rollback round-trip + parity test. |
| **R5** | AI Gateway bypass — a module imports a provider SDK directly. | 🟠 High | Low (this sprint) | Violates ADR-001 single-egress rule; secrets/coupling spread. | Sprint 2 defines **only** `to_ai_context` seam; no provider import. Add layering grep gate: no `openai`/`google.generativeai`/`anthropic`/`ollama`/etc. imports outside a future `ai_gateway` module. |
| **R6** | Secret exposure once BYO keys arrive (not this sprint, but seam invites it). | 🟡 Medium | Low | Clinic API keys leak. | Seam passes context only, never keys; keys deferred to Settings + encryption phase; secret-scan gate; document "no keys in consultation layer". |
| **R7** | Scope creep — building AI/OCR/Investigation logic or live editors under a "domain model" sprint. | 🟡 Medium | Medium | Sprint balloons; regression surface grows. | Seams are documented contracts only; editors/autosave + feeders are separate approved phases; buttons stay disabled. |
| **R8** | Over-structuring narrative into required fields. | 🟢 Low | Medium | Rigid forms → violates narrative-first. | All `consultations` clinical fields nullable/optional; History/Rx/Follow-up stay on `visits` for now. |
| **R9** | Two writers on `consultations` if another module writes it. | 🟢 Low | Low | Duplicated SQL, sync bugs. | Only `consultation/repository.py` writes; enforced by review + layering grep. |
| **R10** | Audit gaps on new mutations (start/save/complete). | 🟢 Low | Low | Compliance gap. | Each lifecycle fn calls `audit.service.log_action`; assert audit rows in domain test. |

## Residual risk
With R1 (documented golden), R2 (UNIQUE + invariant test), R5 (grep gate) covered,
residual = Low. No Critical. Change is additive, reversible, seam-only for AI/OCR.

## Avoided by design (ADR-001)
- No `visits` widening → no god-table.
- No live data migration → clean reversible new table.
- No provider egress this sprint → no AI secret surface.
- Timeline stays read model → no write coupling.
