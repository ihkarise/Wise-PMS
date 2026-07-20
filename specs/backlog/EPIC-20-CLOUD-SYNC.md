# EPIC-20 — Cloud Sync

> **Spec:** [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) (repository
> seam) · **Backlog:** F8 · **Stage:** E — Platform ·
> **Depends on:** EPIC-03, EPIC-15 · **Complexity:** XL · **Risk:** High ·
> **Status:** Backlog (planning only). Governed by
> [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. VII.

## 1. Objective

Optional multi-device synchronization via the **repository seam** — the whole point
of the repository layer. Cloud stays additive and opt-in; the local store remains
authoritative. Must account for SQLite single-writer (L12).

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E20-F1 | Sync layer at the repo seam | Push/pull without touching services or UI |
| E20-F2 | Conflict handling | Deterministic resolution for concurrent edits |
| E20-F3 | Encrypted transport + at rest | Builds on EPIC-15; nothing plaintext off-device |
| E20-F4 | Opt-in + offline-first | Off by default; full offline operation preserved |

## 3. User stories

- **E20-F1-S1** — As a multi-device clinic, I want records synced across devices,
  so that any terminal has the latest data.
- **E20-F4-S1** — As the clinic, I want sync optional, so that we can keep running
  fully offline if we choose.
- **E20-F2-S1** — As the clinic, I want predictable conflict resolution, so that
  concurrent edits don't corrupt data.

## 4. Engineering tasks

- **E20-T1** — Sync adapter extending/wrapping repositories (no service/UI change).
- **E20-T2** — Change tracking + conflict resolution strategy (single-writer aware).
- **E20-T3** — Encrypted transport; reuse EPIC-15 at rest.
- **E20-T4** — Opt-in config; local-authoritative fallback.
- **E20-T5** — Tests (sync round-trip, conflict, offline fallback) + docs
  (ARCHITECTURE sync section, SECURITY, DECISIONS ADR).

## 5. Dependencies

- **Upstream (hard):** EPIC-03 (RBAC), EPIC-15 (encryption). Repository seam
  (built).
- **Downstream:** EPIC-16 (hosted portal), EPIC-21 (mobile).

## 6. Acceptance criteria

- **AC1** — *Given* two devices, *when* one edits, *then* the change propagates via
  the repository seam without service/UI changes.
- **AC2** — *Given* concurrent edits, *when* they conflict, *then* resolution is
  deterministic and audited.
- **AC3** — *Given* sync off, *when* the app runs, *then* it operates fully offline.
- **AC4** — *Given* data in transit/at rest, *when* synced, *then* it is encrypted.

## 7. Regression tests

- **Must stay green:** golden, models, router, views (offline path unchanged).
- **New:** sync round-trip, conflict resolution, offline-fallback, encrypted
  transport tests.

## 8. Rollout phases

- **E20-R1** — Sync adapter + change tracking (single device → remote).
- **E20-R2** — Multi-device + conflict resolution.
- **E20-R3** — Encryption end-to-end + opt-in config; docs closeout.

## 9. Rollback

Disable sync → local store authoritative; app fully offline. No data destroyed.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: services/UI untouched by sync; offline
operation preserved; nothing plaintext off-device.
</content>
