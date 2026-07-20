# WiseOS Health — Lessons Learned

> Durable lessons from building the ecosystem, so mistakes aren't repeated.
> Append at the end of every phase. **Last updated:** 2026-07-20.

## From the architecture refactor (PR #1)

1. **A behavioral golden test makes structural refactors safe.** Because
   `test_regression.py` pinned observable behavior, code could move across
   layers/modules stage by stage while proving the app still did the same thing.
   *Lesson:* pin behavior before you move structure.

2. **Compatibility shims enable incremental migration.** Keeping old import
   paths as re-export shims meant nothing broke mid-flight; shims were deleted
   only in the final cleanup. *Lesson:* migrate behind shims, then remove.

3. **Committed shell mistakes are real.** Literal-brace directories
   (`app/{ui,services,...}`) were committed because a shell didn't expand braces.
   *Lesson:* verify `mkdir` results; `.gitignore` and hygiene commits matter.

4. **Missing `__init__.py` is fine until PyInstaller.** Namespace packages work
   in dev but are fragile for the `.exe` build. *Lesson:* make packages explicit.

## From Sprint 1–2 (as-built)

5. **Fail-safe auditing protects clinical flow.** `log_action` swallows all
   exceptions, so an audit hiccup can never break a consultation. *Lesson:*
   cross-cutting concerns must degrade quietly, never take down the workflow.

6. **Narrative-first beat form-first.** Free-text notes as the source of truth,
   with structure extracted afterward, matched how clinicians actually work.
   *Lesson:* don't force structure at the point of care.

7. **"Auto-upgrade" claims can be false comfort.** Sprint-2 DBs upgraded only
   because Sprint 2 added *new tables*; a column change would have had no path.
   *Lesson:* build migrations before you need them (backlog F1).

## Process lessons (charter-driven)

8. **Phase 0 first, always.** Reading the whole repo before touching it revealed
   the refactor was already implemented — preventing redundant or conflicting
   work. *Lesson:* understand before modifying.

9. **Documentation drifts unless it's part of the diff.** Three good docs
   existed but the wider memory system didn't, and reality had moved on. *Lesson:*
   update every affected doc in the same commit as the code.

10. **Approval gates prevent scope creep.** Asking the Product Owner to pick the
    phase kept work aligned instead of guessing. *Lesson:* gate scope, then execute.
