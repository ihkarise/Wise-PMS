# Sprint 4 — Recommendation

**Status:** APPROVED — implementation authorized (Sprint 4 Implementation
Authorization). Planning documents are being committed to a planning PR
per that authorization's required Git sequence; implementation begins
only after the planning PR merges into `main`.
**Date:** 2026-08-07 · **Revision 1:** 2026-09-18 — scope finalized per
Product Owner's 7 revisions (see ADR-002 Revision 1 and
`SPRINT4_MILESTONE_CHECKLIST.md` for the full change list).
**Revision 2:** 2026-09-18 — deployment-tier language finalized to match
ADR-002 §8.0's canonical table exactly (single-machine Clinic Server =
Conditionally permitted / temporary, not Production-supported and not
merely "Architecture-ready").
**Depends on:** ADR-002 (Cloud-Ready Architecture, Revision 2),
approved F1 migration runner (Sprint 0), Sprint 2/3 Consultation domain.

---

## 1. Candidate re-ranking

Every remaining backlog item (`MASTER_BACKLOG.md`) plus the new
architecture items ADR-002 introduces, scored 0–5 on each axis. Weights
reflect this review's mandate: architecture dependency and cloud
compatibility are weighted higher than usual because Sprint 4 is
explicitly the "prepare for 10 years of growth" phase; clinical value and
doctor productivity stay first-order because the product exists to serve
the clinic, not the architecture. "Cloud compatibility" below means
**Architecture-ready** (ADR-002 §0) — it is a design-fit score, not a
claim that any engine/target beyond SQLite + Local Disk is built or
supported.

| Axis | Weight |
| ---- | ------ |
| Clinical value | 20% |
| Doctor productivity | 15% |
| Architecture dependency (how many future modules block on this) | 20% |
| Technical debt reduction | 15% |
| Future cloud compatibility (Architecture-ready fit, not production support) | 15% |
| Implementation risk (inverted: 5 = low risk) | 10% |
| Testing effort (inverted: 5 = low effort) | 5% |

| Candidate | Clinical | Productivity | Arch. dep. | Debt | Cloud fit | Risk⁻ | Test⁻ | **Weighted** |
| --------- | :------: | :-----------: | :--------: | :--: | :---: | :---: | :---: | :----------: |
| **F2 Settings UI (clinic profile only)** | 3 | 4 | 4 | 3 | 4 | 5 | 4 | **3.75** |
| **DatabaseAdapter + StorageProvider seams (ADR-002 §3/§5)** | 1 | 1 | 5 | 4 | 5 | 4 | 3 | **3.30** |
| F3 RBAC | 2 | 3 | 5 | 4 | 5 | 2 | 2 | 3.35 |
| C2 Protocol Engine | 4 | 4 | 2 | 1 | 1 | 3 | 3 | 2.85 |
| D1 Wise Printer | 3 | 4 | 2 | 1 | 1 | 4 | 4 | 2.75 |
| D2 OCR Engine | 4 | 3 | 3 | 2 | 2 | 1 | 1 | 2.65 |
| E1 WhatsApp Automation | 3 | 3 | 2 | 1 | 2 | 3 | 3 | 2.55 |
| F7 Encryption at rest | 1 | 1 | 4 | 3 | 5 | 2 | 3 | 2.65 |
| B1/B2 Billing/Dispensing | 3 | 3 | 2 | 1 | 2 | 2 | 2 | 2.30 |
| B3 WHIMS Inventory | 3 | 2 | 2 | 1 | 2 | 2 | 2 | 2.15 |
| AI Gateway skeleton + `provider_credentials` | 1 | 1 | 3 | 1 | 4 | 1 | 2 | 1.95 |

*(F3 RBAC scores well but is intentionally **not** recommended for Sprint 4
— see §3. F7 and the AI Gateway skeleton score lower because ADR-002 §11
sequences them explicitly behind RBAC; building them earlier would violate
that dependency, so their risk score is penalized for being out of order.)*

## 2. Recommendation: Sprint 4 = **Settings UI (F2, clinic profile only) + Database/Storage Abstraction Seams (ADR-002 §3, §5)**

Two workstreams, scoped together because they are low-risk, mutually
reinforcing, and both directly required before anything else on the
board:

1. **Settings UI (F2) — clinic profile fields only** (clinic name, doctor
   name, address, phone, email, logo). The `settings` table has existed
   since Sprint 1 with no editor. Small, visible, doctor-facing value
   now; zero schema risk (table already exists). **Per Revision 3, this
   surface does not and must not host database, storage-provider,
   backup-destination, API-key, RBAC, or other security configuration —
   those require a distinct, future, RBAC-gated Administrator/Security
   surface (ADR-002 §5.2, §6.6).**
2. **`DatabaseAdapter` + `StorageProvider` seams (ADR-002 §3, §5)** —
   introduced as pure, behavior-preserving wrappers: `SQLiteAdapter` wraps
   today's `sqlite3` calls verbatim; `LocalDiskStorageProvider` wraps
   today's `os`/`shutil` calls verbatim. No engine change, no storage
   backend change, no new dependency, no visible behavior change — this
   is architecture debt repayment, not a feature, and it directly answers
   this review's mandate: "the application must become database-
   independent" and "all uploaded files must use a storage abstraction,"
   **at the Architecture-ready tier (ADR-002 §0) — not a claim that any
   engine beyond SQLite or any backend beyond Local Disk becomes usable
   this sprint.**

Both fit in one phase because each is additive-only and independently
testable (see `SPRINT4_MILESTONE_CHECKLIST.md`), and together they clear
the two concrete architecture gaps this review found (§3 of ADR-002)
before Sprint 5 (RBAC) needs them.

### Why not RBAC (F3) despite its high score
F3 scores nearly as high as F2 and is genuinely urgent (Security.md:
"any logged-in user can do anything"). It is **not** recommended for
Sprint 4 because:
- It is a larger, higher-risk phase on its own (roles/permissions schema
  + route/action guards across every existing module) and combining it
  with the abstraction seams would violate the "small, reviewable,
  runnable commits" principle (Constitution Art. III §8) and this
  review's own risk-budget discipline.
- ADR-002 §11 sequences RBAC *after* the abstraction seams (so RBAC's
  future row-level enforcement is written against the final repository
  shape, not against code that gets touched twice) but *before*
  encryption at rest, any AI/BYO-key work, and before the future
  Administrator/Security settings surface that will eventually host
  database/storage/backup/credential configuration (ADR-002 §5.2/§6.6).
- **Recommendation: F3 RBAC is Sprint 5**, immediately following this
  phase, not deferred indefinitely.

### Why not the Consultation Workspace feeders (Protocol/Printer/OCR)
They score respectably on clinical value but poorly on architecture
dependency and cloud compatibility — building them now means building
them again once the storage/database seams land underneath them (OCR
writes files; Printer reads settings; both are exactly the code this
Sprint hardens). Building the seams first means these modules, whenever
approved, are written once against the final interfaces.

## 3. Scope (finalized per Product Owner Revision 7)

**In scope (Sprint 4) — the 10 items of the finalized scope:**
1. `DatabaseAdapter` protocol
2. `SQLiteAdapter` (sole implementation; behavior-preserving wrapper)
3. `StorageProvider` protocol (revised — no `absolute_path()`; see
   ADR-002 §5.1)
4. `LocalDiskStorageProvider` (sole implementation; behavior-preserving
   wrapper; local-only `local_path()` helper kept off the Protocol)
5. Configuration boundary (ADR-002 §5.2 — adapter/provider selection is
   a hardcoded code branch, not an environment variable and not a
   Settings UI control, in Sprint 4)
6. Safe Settings UI — clinic profile fields only (name, doctor name,
   address, phone, email, logo); no security-sensitive configuration
   (ADR-002 §6.6)
7. `attachments.service` migration onto `StorageProvider`
8. Backup **destination-write** migration onto `StorageProvider`
   (archive construction stays a local filesystem walk — ADR-002 §5.3)
9. Tests (parity, domain, field-whitelist, layering/import gates)
10. Documentation (this document set + `docs/modules/Settings.md`,
    `docs/DATABASE.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md`, etc.)

**Explicitly out of scope (Product Owner Revision 7 — restated for
emphasis, not a partial list):**
PostgreSQL, MySQL, SQL Server, AWS, Azure, GCP, S3 (or any object
storage), cloud deployment, Docker deployment, Kubernetes, Cloud Sync,
AI, OCR, RBAC, Encryption at rest, API-key storage, Payment integration.
Also out of scope: any ORM, Alembic, or declarative migration-rendering
mechanism (ADR-002 §13); any change to the migration runner; any schema
change; any new database engine; any new storage backend; any change to
`attachments`'/`backups`' on-disk file layout — the
`LocalDiskStorageProvider` must be byte-for-byte compatible with existing
clinic data; any new runtime dependency unless explicitly justified and
approved.

## 4. Alternatives considered

1. **F2 Settings UI alone** — smallest possible next phase, lowest risk.
   Rejected as *too* narrow: it does not address this review's central
   finding (no DB/storage abstraction), and the two items are small
   enough to ship together without inflating risk (see
   `SPRINT4_RISK_ASSESSMENT.md`).
2. **F3 RBAC first** — addresses the most urgent security gap. Rejected
   for Sprint 4 (see §2) — recommended as Sprint 5 instead.
3. **Consultation Workspace feeder (Protocol Engine)** — highest clinical
   value on the board. Rejected for Sprint 4 because it would be built
   against the pre-abstraction repository/storage code and require
   rework once the seams land; better sequenced after Sprint 4/5.
4. **AI Gateway skeleton + `provider_credentials` now** — explicitly
   rejected: ADR-002 §11 requires F3 (RBAC) and F7 (encryption) before any
   API-key storage exists, and this task's own STOP conditions forbid AI/
   OCR implementation in this cycle.

## 5. Do not start until
The Product Owner approves this recommendation (Revision 1), ADR-002
(Revision 1), and the accompanying Sprint 4 technical/risk/testing/
milestone documents. Per the Constitution (Article IX §3), no phase
begins automatically.
