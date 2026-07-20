# .ai/CLAUDE_NOTES.md — Notes to my future self

> Freeform, honest notes for whoever (human or AI) picks this up next.
> **Updated:** 2026-07-20.

## Read order at session start
1. [`MEMORY.md`](./MEMORY.md) — orientation.
2. [`CURRENT_PHASE.md`](./CURRENT_PHASE.md) + [`NEXT_TASK.md`](./NEXT_TASK.md) —
   what's happening now.
3. [`ARCHITECTURE_RULES.md`](./ARCHITECTURE_RULES.md) before writing any code.
4. Skim [`WORK_LOG.md`](./WORK_LOG.md) and [`DECISION_LOG.md`](./DECISION_LOG.md)
   for recent context.

## The single most important thing
This repo LOOKS like an early prototype but the **architecture is deliberate and
already mature**. Don't "clean it up" by flattening modules or inlining SQL into
services — that undoes the whole growth design. Respect the layering.

## Traps I hit / avoided
- The domain-driven refactor was **already done** — I nearly could have redone
  it. Always Phase 0 first; check `docs/TARGET_ARCHITECTURE.md` "Status:
  IMPLEMENTED".
- `docs/ARCHITECTURE.md` is an **as-built audit of the pre-refactor state** kept
  as a record; it describes `app/ui`/`app/services` which no longer exist. Read
  its header note — the *current* structure is in TARGET_ARCHITECTURE + README.
- Tests set `WISE_PMS_HOME` before importing the app. Follow that pattern or you
  will clobber real data paths.

## Judgment calls I made
- Wrote planned modules as design specs, not empty folders (charter: no dead
  scaffolding). If the Owner wants stubs later, that's a separate decision.
- Recommended Migrations (F1) as Phase 2 because everything else needs it. If the
  Owner wants a visible feature first, Settings UI (F2) is the safe small win.

## Working style for this project (charter)
- Never start a phase without approval. Always end a phase with the report
  format (Summary, Files Changed, Architecture Changes, DB Changes, Risk,
  Manual Testing Checklist, Known Issues, Recommended Next Phase).
- Update every affected doc in the same commit as the code. If you change
  behavior, regenerate the regression golden and note it.
- Keep commits small and the app runnable at every step.

## Open questions for the Product Owner
- Confirm Phase 2 = Migrations (F1), or pick Settings/RBAC/Consultation instead.
- Any compliance target (HIPAA / India DPDP) that should shape the security
  roadmap ordering?
- Preferred approach for future external providers (self-hosted vs. cloud) for
  OCR / AI / WhatsApp — affects the offline-first posture.
