# EPIC-05 — Protocol Engine

> **Spec:** [`../PROTOCOL_ENGINE.md`](../PROTOCOL_ENGINE.md) · **Backlog:** C2 ·
> **Stage:** B — Clinical Core · **Depends on:** EPIC-01, EPIC-04 (surface),
> benefits from EPIC-02 (print templates) · **Complexity:** M · **Risk:** Medium ·
> **Status:** Backlog (planning only). Governed by
> [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. II §2, §6.

## 1. Objective

Reusable, **advisory** per-condition templates that pre-fill a consultation
(investigations, medicines+dosage, advice, review schedule, print template). A
protocol proposes; the doctor accepts/edits/ignores. Structure never gates the
narrative.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E05-F1 | Protocol data model | `protocols` + `protocol_items` (kind = investigation/medicine/advice) |
| E05-F2 | Protocol authoring screen | Create/edit protocols + items; enable/disable |
| E05-F3 | Seed library | Migraine, GERD, IBS, Allergic Rhinitis, Asthma, PCOS, Infertility, Skin, Anxiety, Depression |
| E05-F4 | Apply (advisory) | `apply_protocol` → editable suggestions into the Workspace |
| E05-F5 | Follow-up rule resolution | Relative rule (`+14d`) → concrete review date |
| E05-F6 | Usage link | Record applied protocol per visit for Analytics (non-authoritative) |

## 3. User stories

- **E05-F2-S1** — As a doctor, I want to author a protocol for a condition, so that
  common cases are fast and consistent.
- **E05-F4-S1** — As a doctor, I want to pull a protocol's suggestions into the
  consultation, so that I start from a template but edit freely.
- **E05-F4-S2** — As a doctor, I want suggestions to never auto-commit, so that I
  stay in control of the record.
- **E05-F5-S1** — As a doctor, I want the review date pre-filled from the protocol,
  so that follow-up scheduling is one step.
- **E05-F6-S1** — As a practice owner, I want to know which protocol a visit used,
  so that Analytics can relate protocol to outcome.

## 4. Engineering tasks

- **E05-T1** — Migration: `protocols`, `protocol_items`; optional
  `visits.applied_protocol_id` (additive).
- **E05-T2** — `modules/protocols/` slice: models, repository, service
  (`list/get/create/update`, `apply_protocol` returning a suggestion bundle),
  controller (`^/protocols(?:/(?P<id>new|\d+))?$`), authoring view.
- **E05-T3** — Seed the initial library (editable, not hardcoded strings).
- **E05-T4** — Follow-up rule grammar + resolver (`+Nd/+Nm`).
- **E05-T5** — Workspace integration: Protocol Suggestions panel (accept/edit/
  dismiss chips → narrative Rx / Investigation panel / Remarks / follow-up date).
- **E05-T6** — Reuse `utils.prescription` shapes for medicine items.
- **E05-T7** — Tests + docs (Protocols module doc, CHANGELOG).

## 5. Dependencies

- **Upstream:** EPIC-01, EPIC-04 (its only meaningful surface), EPIC-02 (print
  template reference).
- **Downstream:** EPIC-06 (recommended investigations), EPIC-09 (print template),
  EPIC-14 (usage vs. outcome), EPIC-19 (AI suggest/refine).

## 6. Acceptance criteria

- **AC1** — *Given* a protocol with items, *when* authored/saved, *then* it lists
  investigations, medicines (potency/dosage), advice, review rule, print template.
- **AC2** — *Given* `apply_protocol`, *when* invoked, *then* suggestions are
  returned **without** writing to the visit.
- **AC3** — *Given* accepted suggestions, *when* pulled in, *then* they populate the
  narrative/panels and remain fully editable.
- **AC4** — *Given* a dismissed suggestion, *when* dismissed, *then* nothing is
  written.
- **AC5** — *Given* a protocol edited later, *when* saved, *then* past visits are
  unchanged.

## 7. Regression tests

- **Must stay green:** golden, models, router, views.
- **New:** protocol service tests (CRUD, apply returns-without-write, rule
  resolution), authoring view-build, model/table parity, router contract for
  `/protocols`, Workspace panel interaction test (accept/dismiss).

## 8. Rollout phases

- **E05-R1** — Tables + model + authoring screen + seed library.
- **E05-R2** — `apply_protocol` advisory bundle + follow-up rule resolver.
- **E05-R3** — Workspace Protocol Suggestions panel wiring.
- **E05-R4** — Usage link + Analytics hook; docs closeout.

## 9. Rollback

Revert module + hide panel/route; `applied_protocol_id` inert. No data destroyed;
consultations still work without protocols.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: no suggestion auto-commits; past visits
provably unaffected by later protocol edits.
</content>
