# .ai/NEXT_TASK.md — The single next actionable task

> Keep this to **one** concrete task. When it's done, replace it with the next
> one. **Updated:** 2026-07-20.

## Now
**Sprint 1 (Consultation Workspace Skeleton / C1) is complete and committed —
await Product Owner review.** Do not start the next sprint automatically
(charter: one sprint, then stop).

Delivered this sprint:
- [x] `app/modules/consultation/` vertical slice — service (read-only
      composition), controller + `ROUTES`, workspace skeleton view
- [x] Layout: top header · left section nav · center sections · right
      placeholder panels · bottom disabled action bar
- [x] Shared `disabled_button` + `placeholder_card`; `theme.card(border=…)`
- [x] Navigation wired (`bootstrap.py` + **Start Consultation** in the case view)
- [x] Router-contract + view-build tests extended for the new route/view
- [x] `python3 -m pytest -q` → 16 passing (regression golden byte-identical)
- [x] Docs updated (module doc, CHANGELOG, spec status, `.ai/`); pushed, no PR

## Blocked on
Product Owner approval before starting the next sprint.

## After approval (proposed next sprint)
Grow the Workspace by landing its **first feeder slice** rather than more
skeleton. Two low-risk candidates, pick one:
1. **Real narrative editors + draft autosave** — wire Chief Complaint / History /
   Diagnosis / Prescription / Remarks / Follow-up to `visits.service`
   (create/update a draft visit), with autosave; needs the F1 migration runner
   for any new additive visit columns (chief complaint, examination). Makes the
   Workspace actually usable end-to-end for one consultation.
2. **Settings UI (F2)** — small, visible, unblocks Printer/WhatsApp templates the
   Workspace's Print/WhatsApp actions will eventually need.

Recommendation: **(1)** — it turns the skeleton into a working consultation and
directly serves the anchor feature; (2) can follow to enable the terminal
actions. Either way: one sprint, then stop for approval.
