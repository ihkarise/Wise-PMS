# .ai/CURRENT_PHASE.md

**Phase:** Sprint 6 — F7 Encryption at Rest (ADR-004) — **PLANNING/DESIGN ONLY**
**Status:** 🟡 PLANNING. The Product Owner has approved the F7 architecture
**direction** and authorized converting the F7 planning analysis into formal
design documents — **not** implementation. This planning phase adds
`docs/architecture-decisions/ADR-004-F7-Encryption-at-Rest.md` and
`docs/planning/SPRINT6_TECHNICAL_PLAN.md` (plus these `.ai/*` pointers) and
**nothing else** — no runtime code, no crypto utility, no key store, no
dependency, no `requirements.txt` change, no migration, no schema change, no
test/golden change. Implementation (milestones M1–M7) remains **separately
gated** and unauthorized.
**Prior phase:** Sprint 5 — F3 RBAC (ADR-003) is ✅ CLOSED, merged to `main`
via **PR #14** (`10e0738`) and **PR #15** (`cf0f1e5`, docs sync).
`main == origin/main == cf0f1e5`; `python3 -m pytest -q` → **130 passing**;
layering PASS (5); regression golden PASS (1).
**Updated:** 2026-09-21 (Sprint 6 F7 planning: ADR-004 + Sprint 6 technical
plan authored; design only, implementation not authorized)

## F7 architecture direction — APPROVED (Product Owner, 2026-09-21)
- **Database:** SQLCipher / transparent full-database encryption at the
  `SQLiteAdapter` seam (direction only — not installed/implemented).
- **Key management:** envelope model (DEK wrapped by ≥1 KEK).
- **Recovery:** mandatory **offline recovery key** — "encryption without a
  viable recovery path is not acceptable for Wise PMS."
- **Attachments:** `EncryptedStorageProvider` decorator at the
  `StorageProvider` seam; viewer/`local_path` redesigned to decrypt-to-temp.
- **Backups:** independently recoverable encrypted artifact + a designed
  restore workflow; pre-F7 plaintext backups still restorable.
- **Migration:** explicit, administrator-controlled, atomic, resumable,
  verified, idempotent; never silent at startup.
- **Scope:** database + attachments + backups together.
- **Dependency:** a crypto runtime dependency approved **in principle** —
  **not installed, not chosen** here (stdlib has no AEAD cipher).
- **Security review:** mandatory before F7 is production-ready.

## Still requiring specialist review (the M0 gate)
Exact cipher · AEAD mode · KDF · KDF parameters · nonce/IV · key wrapping ·
Windows keystore usage · recovery-key encoding/storage · key rotation ·
secure-deletion limits · temporary plaintext exposure · exact SQLCipher
binding · exact crypto library. Marked **[SECURITY DESIGN DECISION
REQUIRED]** / **[SECURITY REVIEW REQUIRED]** in ADR-004.

---

## (Archived) Sprint 5 — F3 RBAC (ADR-003) — CLOSED

## Goal
Make `users.role` **enforced** instead of decorative (close L4 / the
SECURITY.md RBAC gap): a data-driven role/permission model with a
consistent, testable authorization boundary, so each staff type does only
what its role permits — without changing the database engine, storage
backend, deployment tier, or adding a runtime dependency.

## Delivered (M1–M5)
- **M1 — Foundation (ADR-0011).** Migration `v0003_rbac` (additive,
  reversible) adds `roles`, `permissions`, `role_permissions`, `user_roles`
  and seeds the five predefined roles (Administrator/Doctor/Reception/
  Pharmacy/Accounts), the 16-permission catalogue, and the default
  role→permission grants. `idx_user_roles_user` UNIQUE index enforces one
  active role per user. Legacy `admin` mapped to Administrator (no lockout);
  `users.role` kept as a non-authoritative legacy hint. New
  `app/modules/roles/` (models, repository, service) with the
  at-least-one-active-Administrator invariant.
- **M2 — Permission infrastructure.** `app/modules/roles/permissions.py`
  registry (16 keys, mirrors the DB) + `user_has_permission` /
  `require_permission` read API resolving via
  `user_roles → role_permissions → permissions`; fail-closed for missing/
  unknown/inactive user, unknown permission, no binding; no `users.role`
  read; no Administrator bypass.
- **M3 — Router enforcement.** `core/router.py` gains a permission guard
  after the session guard (auth → permission → handler). Each route
  declares its required permission via registry constants; fail-closed
  denial. `/login` public; `/settings` = `settings.edit`; clinical routes
  gated per the matrix.
- **M4 — Action-level enforcement.** `require_permission` at the service/
  controller action boundary for `create_patient`(registration.create),
  `update_patient`(patients.edit), `deactivate_patient`(patients.deactivate),
  case/visit mutations(cases.manage/visits.manage), consultation edits
  (consultation.edit), attachment upload/delete, `settings.edit`, and the
  shell backup action(backup.run). Guards precede every mutation/side effect.
- **M5 — Administration surface.** Administrator-only `^/admin/roles$`
  (`app/modules/roles/controller.py` + `view.py`), gated by `rbac.manage`
  at the router and again at every service op: view roles, view the 16
  permissions, edit role→permission grants, and assign an existing user to
  a predefined role (via `assign_role`). `rbac.manage` cannot be revoked
  from Administrator; the last Administrator cannot be demoted.

## Enforcement architecture
`authentication → router permission guard → service/controller action
guard → business operation`. Authorization resolves through `user_roles →
role_permissions → permissions`; `users.role` is never the source of truth.

## NOT in scope (deferred — unchanged from the approved plan)
Custom (runtime-created) roles; multi-role users; full F4 user management
(user creation/deletion/credential/profile administration); repository/
row-level authorization; F7 encryption at rest; any new permission or role.
These are not implemented and are not described as implemented anywhere.

## Prior phase
Sprint 4 (Cloud-Ready Architecture Seams + Settings UI, ADR-002) is CLOSED —
merged to `main` via PR #10 (planning) and PR #11 (implementation).

## Verification
```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q     # expect 130 passing
```
