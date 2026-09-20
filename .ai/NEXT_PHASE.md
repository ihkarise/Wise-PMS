# .ai/NEXT_PHASE.md — Proposed next phase (needs approval)

**Updated:** 2026-09-20

> **Status:** Sprint 5 — **F3 RBAC is DELIVERED and CLOSED** (implemented
> M1–M6, security-audited, documentation closed, and **merged to `main` via
> PR #14**, merge commit `10e0738`). It is no longer a planned/proposed
> phase. The **next phase after Sprint 5 has not been scoped or authorized**
> — it requires Product Owner planning/authorization. No future feature is
> committed here.

## Candidate next phases (from the existing backlog — not yet authorized)

The repository roadmap and `MASTER_BACKLOG.md` establish these as the
natural follow-ons once RBAC (F3) is in place. They are candidates only;
the Product Owner selects and authorizes the next sprint.

1. **F4 — User management screen** (create/deactivate users, credential
   reset). Depends on F3 (now delivered). Sprint 5 deliberately shipped only
   the *minimum* RBAC administration (existing-user → role assignment); full
   user lifecycle management is F4 and remains out of scope until authorized.
2. **F7 — Encryption at rest** for PHI. Sequenced *after* RBAC (ADR-002 §11);
   required before any `provider_credentials`/BYO-key (AI Gateway) work.
3. **Consultation Workspace feeders** (Protocol Engine / Wise Printer / OCR)
   — higher clinical value, now able to be built with RBAC gating who may
   use them.

## Sequencing note (unchanged)
ADR-002 §11 orders foundation work: the Sprint 4 seams → **F3 RBAC (done)**
→ F7 encryption → AI Gateway / `provider_credentials` → Cloud Sync (only
once a server-grade `DatabaseAdapter` is Production-supported). Networked/
multi-user surfaces still require F3 **and** F7 first (SECURITY.md rule 1).

## Do not start until
The Product Owner scopes and approves the next phase. Per the charter, no
phase begins automatically.
