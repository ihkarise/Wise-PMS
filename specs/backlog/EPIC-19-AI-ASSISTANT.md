# EPIC-19 — AI Assistant & Holoscan

> **Spec:** [`../AI_ASSISTANT.md`](../AI_ASSISTANT.md) · **Backlog:** A1, A2, A3 ·
> **Stage:** D — Insight & Reach · **Depends on:** EPIC-05, EPIC-06, EPIC-07,
> EPIC-03, EPIC-15 · **Complexity:** L · **Risk:** High ·
> **Status:** Backlog (planning only). Governed by
> [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. II §6, VII §3.

## 1. Objective

Advisory clinical intelligence over the structured, audited data the ecosystem
produces — protocol suggestions, interaction/allergy flags, history summaries,
report interpretation (Holoscan), and voice dictation. **Advisory only, labeled,
auditable, offline-preferred.** Never auto-commits to the record.

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E19-F1 | Service seam | `ai.service`: typed data in, suggestions out |
| E19-F2 | Provider interface | LocalModelProvider default; HostedApiProvider opt-in (env, consented) |
| E19-F3 | Suggestions (A1) | Protocol suggestion, interaction/allergy flags, history summary |
| E19-F4 | Holoscan (A2) | Imaging/vision interpretation feeding OCR/timeline |
| E19-F5 | Voice dictation (A3) | Speech-to-text into narrative fields |
| E19-F6 | Guardrails | Labeled, advisory, audited, privacy-first, degrade gracefully |

## 3. User stories

- **E19-F3-S1** — As a doctor, I want a suggested protocol from the complaint, so
  that I start faster — but I decide.
- **E19-F3-S2** — As a doctor, I want interaction/allergy flags at the
  prescription, so that safety is visible where I prescribe.
- **E19-F3-S3** — As a doctor, I want a "what changed since last visit" summary, so
  that I regain context quickly.
- **E19-F2-S1** — As the clinic, I want AI on-device by default, so that PHI stays
  local and there's no cost.
- **E19-F5-S1** — As a doctor, I want to dictate into notes, so that I type less —
  while I confirm the text.

## 4. Engineering tasks

- **E19-T1** — `modules/ai/` service seam: `suggest_protocol`, `summarize_history`,
  `flag_interactions`, `interpret_report`.
- **E19-T2** — `AiProvider` interface + `LocalModelProvider` (default);
  `HostedApiProvider` opt-in (consent + env secret + encryption).
- **E19-T3** — Workspace integration: labeled, dismissible suggestions; safety
  flags at the prescription; follow-up summary preload.
- **E19-T4** — Audit every AI call (inputs/outputs, `entity_type = ai_event`);
  `kind = ai` timeline events.
- **E19-T5** — Holoscan provider (A2) feeding OCR/timeline; voice dictation (A3)
  into narrative editors.
- **E19-T6** — Tests (advisory-never-commit, audit, offline-degrade) + docs (AI
  module doc).

## 5. Dependencies

- **Upstream:** EPIC-05 (suggestion surface), EPIC-06/07 (structured values),
  EPIC-03/EPIC-15 (PHI + external providers). Typed models + audit already ready.
- **Downstream:** none (advisory layer).

## 6. Acceptance criteria

- **AC1** — *Given* AI outputs, *when* rendered, *then* they are labeled and
  dismissible; none auto-commit to the record.
- **AC2** — *Given* a prescription, *when* interactions/allergies exist, *then*
  flags surface at the prescription.
- **AC3** — *Given* any AI call, *when* made, *then* inputs/outputs are audited.
- **AC4** — *Given* default config, *when* AI runs, *then* it is on-device and no
  PHI leaves without explicit consent.
- **AC5** — *Given* the provider unavailable, *when* consulting, *then* the
  consultation is unaffected.

## 7. Regression tests

- **Must stay green:** golden, models, router, views.
- **New:** advisory-never-commit test, audit-of-AI test, provider-interface test
  (fake provider), offline-degrade test, flag-surfacing test.

## 8. Rollout phases

- **E19-R1** — Service seam + LocalModelProvider + history summary (advisory).
- **E19-R2** — Protocol suggestion + interaction/allergy flags in the Workspace.
- **E19-R3** — Holoscan (A2) + voice dictation (A3).
- **E19-R4** — Hosted provider opt-in (consented/encrypted); docs closeout.

## 9. Rollback

Disable the provider → consultation unaffected; suggestions simply absent. No data
destroyed (AI never wrote authoritative data).

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: nothing auto-commits; default on-device;
every AI action audited; provider outage harmless.
</content>
