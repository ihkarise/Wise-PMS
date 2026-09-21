# .ai/NEXT_PHASE.md — Next phase (design approved; implementation not authorized)

**Updated:** 2026-09-21

> **Status:** Sprint 5 — **F3 RBAC is DELIVERED and CLOSED** (merged via
> PR #14 `10e0738` and PR #15 `cf0f1e5`). **Sprint 6 — F7 Encryption at
> Rest** has been selected by the Product Owner and its **architecture/design
> is approved**; the formal design documents (ADR-004 + Sprint 6 technical
> plan) are authored in this planning phase. **F7 implementation is NOT
> authorized** — it remains separately gated (milestones M1–M7). No crypto
> code, key store, dependency, migration, or schema change is authorized by
> the design approval.

## Sprint 6 — F7 Encryption at Rest (design approved)
See [`../docs/architecture-decisions/ADR-004-F7-Encryption-at-Rest.md`](../docs/architecture-decisions/ADR-004-F7-Encryption-at-Rest.md)
and [`../docs/planning/SPRINT6_TECHNICAL_PLAN.md`](../docs/planning/SPRINT6_TECHNICAL_PLAN.md).
Approved direction: SQLCipher (database) · envelope key model · mandatory
offline recovery key · `EncryptedStorageProvider` for attachments ·
independently recoverable encrypted backups + restore · explicit/resumable
migration · DB+attachments+backups together · a crypto dependency approved
**in principle** (not installed/chosen) · mandatory security review. Every
cryptographic detail is marked **[SECURITY DESIGN DECISION REQUIRED]** /
**[SECURITY REVIEW REQUIRED]** (the M0 gate).

## Later candidate phases (from the backlog — not yet authorized)
1. **F4 — User management screen** (create/deactivate users, credential
   reset). Depends on F3 (delivered).
2. **Consultation Workspace feeders** (Protocol Engine / Wise Printer / OCR).
3. **AI Gateway / `provider_credentials`** — blocked until F7 ships
   (ADR-002 §6.3/§11).

## Sequencing note (unchanged)
ADR-002 §11 orders foundation work: the Sprint 4 seams → **F3 RBAC (done)**
→ **F7 encryption (design approved; implementation gated)** → AI Gateway /
`provider_credentials` → Cloud Sync (only once a server-grade
`DatabaseAdapter` is Production-supported). Networked/multi-user surfaces
still require F3 **and** F7 first (SECURITY.md rule 1).

## Do not start until
The Product Owner authorizes F7 **implementation** (a separate approval from
this design approval). Per the charter, no implementation phase begins
automatically.
