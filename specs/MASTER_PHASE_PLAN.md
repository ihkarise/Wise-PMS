# Master Phase Plan — Specification

> **Status:** Design only (Phase 2). **Last updated:** 2026-07-20.
> The five-year phased roadmap for WiseOS Health. Near-term detail lives in
> [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md); this document is the
> long-horizon map. Subordinate to
> [`PRODUCT_CONSTITUTION.md`](./PRODUCT_CONSTITUTION.md).

## 1. Purpose

Break the whole product into logical, approval-gated phases from foundation to a
full multi-clinic, patient-facing, AI-assisted operating system. Each phase lists
Objectives · Deliverables · Dependencies · Estimated complexity · Risk · Manual
testing checklist · Rollback strategy · Future integration points. **No phase
starts automatically** (Constitution Art. IX §3).

Complexity: **S** small · **M** medium · **L** large · **XL** very large.

## 2. Horizon overview

```
Stage A — Foundation      : Migrations → Settings → RBAC → User Mgmt
Stage B — Clinical core   : Consultation Workspace → Protocol → Printer →
                            Investigation → OCR
Stage C — Operations      : Appointments + Queue → WhatsApp → Billing +
                            Dispensing → Inventory (WHIMS)
Stage D — Insight & reach : Analytics/Reports → Encryption at rest →
                            Patient Portal → Telemedicine → PillFill → AI/Holoscan
Stage E — Platform        : Cloud Sync → Mobile → Public API → Multi-clinic
```

Foundation (A) and security (D: encryption) gate everything networked. The
Consultation Workspace (B) is the anchor the whole product feeds.

---

## Stage A — Foundation

### Phase 2 — DB Migrations & Schema Versioning (F1)
- **Objectives:** safe, versioned schema evolution; unblock every future table.
- **Deliverables:** `schema_version` table + migration runner in
  `core/database.py`; convert `SCHEMA` → `0001_initial`; migration parity test;
  updated `DATABASE.md`/`KNOWN_LIMITATIONS.md`/`CHANGELOG.md`/`DECISIONS.md`.
- **Dependencies:** none. **Complexity:** S. **Risk:** Low.
- **Manual test:** existing `data/wise_pms.db` opens unchanged and stamps its
  version; fresh DB == migrated DB; `pytest -q` green.
- **Rollback:** revert commit; stamp/tables inert to prior build.
- **Future hooks:** every later phase adds migrations here.

### Phase 3 — Settings UI + Templates (F2)
- **Objectives:** editable clinic identity, branding, and templates.
- **Deliverables:** `modules/settings/` slice; tabbed Settings screen; template
  storage; env-backed secrets; export/import bundle.
- **Dependencies:** F1. **Complexity:** S–M. **Risk:** Low.
- **Manual test:** edits persist + audit; template edits change rendered output;
  secrets never in DB plaintext.
- **Rollback:** revert; new tables inert.
- **Future hooks:** Printer, WhatsApp, Telemedicine, Billing branding, Backup.

### Phase 4 — RBAC (F3) + Phase 4b User Management (F4)
- **Objectives:** enforce roles/permissions; manage users.
- **Deliverables:** `roles`/`permissions`/`role_permissions`/`user_roles`;
  router + repository/service enforcement; user CRUD; force-change default creds.
- **Dependencies:** F1. **Complexity:** M. **Risk:** Medium (retrofit onto
  existing routes — introduce with Admin-all defaults, then tighten).
- **Manual test:** guarded route/service refuses an under-permissioned role;
  audit records authority; regression golden green.
- **Rollback:** revert; default to session-guard-only (current behavior).
- **Future hooks:** gates all networked surfaces; multi-clinic scoping later.

---

## Stage B — Clinical Core

### Phase 5 — Consultation Workspace (skeleton) (C1)
- **Objectives:** one integrated consultation screen (the anchor feature).
- **Deliverables:** Workspace route + view composing Patient Summary + narrative
  sections + follow-up over `visits`; draft autosave; interaction/event test
  harness introduced.
- **Dependencies:** F1–F3. **Complexity:** L. **Risk:** High (touches the most
  modules — build skeleton first, grow via feeders).
- **Manual test:** case → draft visit in Workspace; autosave survives a crash;
  complete writes one visit + timeline + audit; unbuilt panels show honest empty
  states.
- **Rollback:** revert; the built Case/Visit screens remain the fallback path.
- **Future hooks:** every feeder module lights up a panel.

### Phase 6 — Protocol Engine (C2)
- **Objectives:** reusable, advisory per-condition templates.
- **Deliverables:** `protocols`/`protocol_items`; management screen; `apply_protocol`
  advisory suggestions into the Workspace.
- **Dependencies:** F1, P5. **Complexity:** M. **Risk:** Medium (avoid
  form-first drift — keep advisory).
- **Manual test:** author a protocol; suggestions don't auto-commit; editing keeps
  narrative authoritative; past visits unaffected by later edits.
- **Rollback:** revert; Workspace panel hidden.
- **Future hooks:** Analytics (usage vs. outcome), AI (suggest protocol).

### Phase 7 — Wise Printer (D1)
- **Objectives:** print prescriptions/invoices/labels from branded templates.
- **Deliverables:** `printer.service` render/output; PDF + OS-printer targets;
  Timeline print events.
- **Dependencies:** F2, P5. **Complexity:** M. **Risk:** Medium.
- **Manual test:** prescription renders with branding; headless assertion on
  document; PDF + printer output; print failure doesn't break consultation.
- **Rollback:** revert; Print action hidden.
- **Future hooks:** Billing invoices, Dispensing labels, Reports.

### Phase 8 — Investigation Engine (C4)
- **Objectives:** order tests, record results, compare over time.
- **Deliverables:** `investigation_orders`/`investigation_results`; order + result
  + compare services; Workspace panels.
- **Dependencies:** F1, P5. **Complexity:** M. **Risk:** Medium (analyte
  normalization).
- **Manual test:** order/result flow; same analyte trends; abnormal flags from
  ranges; manual entry works before OCR.
- **Rollback:** revert; panels hidden.
- **Future hooks:** OCR (auto values), Analytics (graphs), AI.

### Phase 9 — OCR Engine (D2)
- **Objectives:** document → text → structured values (offline-first).
- **Deliverables:** `ocr_results`; provider interface (LocalTesseract default);
  values feed Investigation; review/confidence + manual override.
- **Dependencies:** F1, P8, Attachments. **Complexity:** L. **Risk:** High
  (accuracy/footprint).
- **Manual test:** OCR augments (never mutates) the document; low-confidence →
  review; upload succeeds when OCR unavailable; manual override wins.
- **Rollback:** revert; documents remain viewable; Investigation manual entry
  intact.
- **Future hooks:** Holoscan vision, AI interpretation, Analytics.

---

## Stage C — Operations

### Phase 10 — Appointments + Waiting Queue
- **Objectives:** booking, schedules, tokens, live queue.
- **Deliverables:** `appointments`/`doctor_schedules`/`queue`; calendar + queue
  board; check-in → token → call-next into the Workspace.
- **Dependencies:** F1, F3, F5 (dates). **Complexity:** M. **Risk:** Medium
  (doctor entity gap L3, real date/time).
- **Manual test:** no double-booking; check-in tokenizes; walk-in tokenizes;
  no-show logic; call-next opens the Workspace.
- **Rollback:** revert; routes/nav hidden; `followup_date` remains the seed.
- **Future hooks:** WhatsApp reminders, Telemedicine Meet, Portal self-book,
  Analytics utilization.

### Phase 11 — WhatsApp Automation (E1)
- **Objectives:** templated patient messaging + retention loop.
- **Deliverables:** `message_templates`/`messages`; provider interface (link
  default); render/send; opt-out logging.
- **Dependencies:** F1, F2, F3. **Complexity:** M. **Risk:** Medium
  (consent/compliance).
- **Manual test:** variables substitute; template edits change output; every
  send/skip logged + audited; opted-out skipped; link provider works at ₹0.
- **Rollback:** revert; no messages sent.
- **Future hooks:** Appointments, Dispensing, Follow-up, Telemedicine, Portal.

### Phase 12 — Billing & Dispensing (B1/B2)
- **Objectives:** invoice a visit; pharmacy handoff.
- **Deliverables:** `invoices`/`invoice_items`/`payments`, `dispense_orders`/
  `dispense_items`; create/fulfil with a provider interface (manual default);
  invoice from dispensed order.
- **Dependencies:** F1, F3, P5; full value needs WHIMS. **Complexity:** M.
  **Risk:** Medium.
- **Manual test:** order seeds from prescription; fulfil is transactional; invoice
  from order; only Pharmacy/Accounts act (RBAC); manual path works pre-WHIMS.
- **Rollback:** revert; routes hidden; data retained.
- **Future hooks:** WHIMS stock decrement, PillFill, WhatsApp "Medicine Ready",
  Printer labels, Analytics revenue.

### Phase 13 — Inventory (WHIMS) (B3)
- **Objectives:** stock, batches, expiry, pricing feeding dispensing/pricing.
- **Deliverables:** `inventory_items`/`inventory_batches`/ledger; `price_for`,
  `receive_stock`, `low_stock`, `expiring_soon`; FEFO batch pick.
- **Dependencies:** F1. **Complexity:** M. **Risk:** Medium.
- **Manual test:** stock decrements on dispense; FEFO picks correct batch; low/
  expiring alerts; pricing flows into the Workspace.
- **Rollback:** revert; dispensing falls back to manual pricing.
- **Future hooks:** PillFill hardware at the repo seam, Analytics consumption.

---

## Stage D — Insight & Reach

### Phase 14 — Analytics & Reports (B5)
- **Objectives:** charts/KPIs (Analytics) + tabular exports (Reports) over
  existing data. **Deliverables:** read models; charting view (design-system
  palette); export to `exports/` (D3). **Dependencies:** structured data from B/C.
  **Complexity:** M. **Risk:** Low. **Rollback:** revert (read-only, no data
  risk). **Future hooks:** AI features as model inputs.

### Phase 15 — Encryption at Rest (F7)
- **Objectives:** protect DB/attachments/backups on disk. **Deliverables:**
  encryption at the storage seam; encryptable backups/exports. **Dependencies:**
  repository seam. **Complexity:** M–L. **Risk:** High (data-migration to
  encrypted store must be reversible/verified). **Rollback:** documented decrypt
  path; verified backup before enabling. **Future hooks:** hard prerequisite for
  Portal/Sync.

### Phase 16 — Patient Portal
- **Objectives:** patient-facing web/mobile over a public API. **Deliverables:**
  API adapter + patient auth (separate principal); read models + safe actions.
  **Dependencies:** F3 + F7 + API + patient auth (+ F8 if hosted off-device).
  **Complexity:** XL. **Risk:** High (security surface). **Rollback:** disable the
  API surface; offline core unaffected. **Future hooks:** Telemedicine join,
  online payments.

### Phase 17 — Telemedicine (Online Consultation)
- **Objectives:** remote consultation with Meet sessions. **Deliverables:**
  `sessions`; Meet provider behind an interface; same visit workflow.
  **Dependencies:** F1, Appointments, Settings (Meet creds), F3, transport
  security. **Complexity:** M. **Risk:** Medium. **Rollback:** revert; in-person
  flow unaffected. **Future hooks:** Portal join, WhatsApp `{meetingLink}`.

### Phase 18 — PillFill (B4)
- **Objectives:** automated dispensing hardware/service. **Deliverables:**
  PillFill provider implementing the Dispensing interface. **Dependencies:**
  Dispensing (P12), WHIMS (P13). **Complexity:** L (hardware). **Risk:** High.
  **Rollback:** switch provider back to manual. **Future hooks:** the dispense
  interface is already provider-agnostic.

### Phase 19 — AI Assistant / Holoscan (A1–A3)
- **Objectives:** advisory clinical intelligence + imaging vision + voice.
  **Deliverables:** `ai.service` seam; provider interface (on-device default);
  advisory suggestions/flags/summaries; audited. **Dependencies:** OCR, Protocols,
  F3/F7. **Complexity:** L. **Risk:** High (trust/privacy). **Rollback:** disable
  provider; consultation unaffected. **Future hooks:** every structured feed.

---

## Stage E — Platform

### Phase 20 — Cloud Sync (F8)
- **Objectives:** multi-device sync via the repository seam. **Deliverables:**
  sync layer swapping/extending repositories; conflict handling for SQLite
  single-writer (L12). **Dependencies:** F3, F7. **Complexity:** XL. **Risk:**
  High. **Rollback:** disable sync; local store authoritative. **Future hooks:**
  Mobile, Portal hosting.

### Phase 21 — Mobile app & Public API
- **Objectives:** reuse the UI-agnostic domain layer on mobile + a formal API.
  **Deliverables:** Flet mobile target and/or REST/GraphQL over existing services.
  **Dependencies:** F3, F7, sync. **Complexity:** XL. **Risk:** High. **Rollback:**
  API/app are additive surfaces; desktop unaffected. **Future hooks:** integrations,
  Portal.

### Phase 22 — Multi-Clinic
- **Objectives:** scope data/users/roles per clinic. **Deliverables:** additive
  `clinic_id` scoping via migration; clinic-scoped RBAC. **Dependencies:** F1, F3.
  **Complexity:** L. **Risk:** Medium. **Rollback:** single-clinic default
  (nullable scope). **Future hooks:** group practices, franchising.

---

## 3. Cross-cutting rules for every phase

- **Docs = implementation:** update `CHANGELOG.md`, affected module docs,
  `KNOWN_LIMITATIONS.md`, `DECISIONS.md`, and the `.ai/` memory in the same commit.
- **Quality gates** (Constitution Art. IX §5) must pass before "done".
- **Approval gate:** deliver the phase-end report; wait for the Product Owner.
- **Never** foreclose a future module or remove functionality without approval.

## 4. Estimated shape (indicative, not a commitment)

| Stage | Phases | Indicative effort | Gate before next stage |
| ----- | ------ | ----------------- | ---------------------- |
| A Foundation | 2–4b | Small–Medium | RBAC proven |
| B Clinical core | 5–9 | Large | Workspace usable end-to-end |
| C Operations | 10–13 | Medium–Large | Billing/stock accurate |
| D Insight & reach | 14–19 | Large–XL | Encryption before Portal |
| E Platform | 20–22 | XL | Sync before Mobile/Multi-clinic |

Sequence and effort are a **compass, not a contract** — each phase is approved
individually.
</content>
