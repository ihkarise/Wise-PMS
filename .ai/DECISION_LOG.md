# .ai/DECISION_LOG.md — Running decision log (AI-facing)

> Chronological log of decisions made while working, including small ones not big
> enough for a full ADR. Full ADRs live in
> [`../docs/DECISIONS.md`](../docs/DECISIONS.md). Newest first.
> **Updated:** 2026-07-20.

## 2026-07-20 — Phase 1 scope confirmed with Product Owner
Asked the Owner to choose Phase 1; they selected **Project Memory System**
(docs only, zero runtime risk). Proceeded to author `docs/`, `docs/modules/`,
and `.ai/`.

## 2026-07-20 — Documented planned modules as specs, not stubs
Chose to write "planned" module docs as clearly-labeled design specs rather than
create empty module folders. Rationale: charter rule "no dead scaffolding";
docs must never imply code that doesn't exist. Built modules are documented from
the actual source.

## 2026-07-20 — Kept existing docs, added around them
`ARCHITECTURE.md`, `TARGET_ARCHITECTURE.md`, `DEPENDENCY_MAP.md` already existed
and are accurate; left them intact and cross-linked new docs to them instead of
rewriting.

## 2026-07-20 — Recommended Migrations (F1) as Phase 2
Identified schema versioning as the highest-leverage, lowest-risk next code
phase and the prerequisite for most future modules. Recorded in
[`NEXT_PHASE.md`](./NEXT_PHASE.md); awaiting approval.

## Pre-existing decisions (inherited, see docs/DECISIONS.md)
- ADR-0001 Local-first offline SQLite desktop, ₹0/month.
- ADR-0002 Narrative-first clinical model.
- ADR-0003 Domain-driven vertical slices.
- ADR-0004 Typed models via `RowModel`, dicts at the boundary.
- ADR-0005 Repository layer as the single data-access seam.
- ADR-0006 Centralized regex router + per-module route registration.
- ADR-0007 Documentation is part of implementation.
