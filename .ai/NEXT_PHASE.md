# .ai/NEXT_PHASE.md — Proposed next phase (needs approval)

**Updated:** 2026-09-18

## Recommendation: Sprint 5 — RBAC (backlog F3)

### Why this next
Per `docs/planning/SPRINT4_RECOMMENDATION.md` §2: F3 scores nearly as
high as Sprint 4's items and is genuinely urgent (Security.md: "any
logged-in user can do anything" today). It was deliberately **not**
bundled into Sprint 4 to keep that phase's risk scoped to two pure
refactors + one narrow UI module. ADR-002 §11 sequences RBAC *after* the
`DatabaseAdapter`/`StorageProvider` seams (so its future row-level
enforcement is written against the final repository shape) but *before*
encryption at rest (F7) and before any future Administrator/Security
settings surface that would host database/storage/backup-destination/
API-key configuration (ADR-002 §6.6).

### Scope
- Roles/permissions schema (additive migration via the F1 runner).
- Route/action guards in `core/router.py` and per-module controllers.
- `users.role` becomes enforced, not decorative.
- Tests: permission-guard unit tests + a router-contract extension per
  guarded route; regression golden stays green (or changes intentionally
  and documentedly per rule 12/13).
- Docs: update `SECURITY.md` (close the RBAC gap), `KNOWN_LIMITATIONS.md`
  (close L4), `CHANGELOG.md`, `DECISIONS.md` (new ADR), and this file.

### Risk
Medium. Larger surface than Sprint 4 (touches every existing module's
routes), but additive (new tables, new guard checks) and gated per-route.

### Alternatives (if the Owner prefers)
1. **F7 Encryption at rest** — also urgent, but ADR-002 §11 sequences it
   *after* RBAC.
2. **Consultation Workspace feeders (Protocol Engine / Wise Printer /
   OCR)** — higher clinical value, but better built against the
   Sprint 4 seams *and* with RBAC already gating who can use them.
3. **AI Gateway skeleton + `provider_credentials`** — explicitly blocked
   until F3 and F7 both land (ADR-002 §6.5/§11).

### Do not start until
The Product Owner approves. Per the charter, no phase begins automatically.
