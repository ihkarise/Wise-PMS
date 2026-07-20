# EPIC-15 — Encryption at Rest

> **Spec:** [`../../docs/SECURITY.md`](../../docs/SECURITY.md) · **Backlog:** F7 ·
> **Stage:** D — Insight & Reach · **Depends on:** EPIC-01, repository seam ·
> **Complexity:** M–L · **Risk:** High · **Status:** Backlog (planning only).
> Governed by [`../PRODUCT_CONSTITUTION.md`](../PRODUCT_CONSTITUTION.md) Art. VI §3.

## 1. Objective

Protect PHI on disk — the DB, attachments, and backups are plaintext today (L5).
Encryption at rest, together with RBAC (EPIC-03), is a hard prerequisite for any
networked/patient-facing surface (Portal, Telemedicine, Sync).

## 2. Features

| ID | Feature | Description |
| -- | ------- | ----------- |
| E15-F1 | Encrypted DB | Encrypt `data/wise_pms.db` at rest (e.g. SQLCipher-style) |
| E15-F2 | Encrypted attachments | Encrypt files under `attachments/` |
| E15-F3 | Encrypted backups/exports | Encryptable `backups/*.zip` and exports |
| E15-F4 | Key management | Key derived/stored securely (OS keystore/passphrase), never committed |
| E15-F5 | Safe migration | Reversible, verified plaintext→encrypted conversion with backup |

## 3. User stories

- **E15-F1-S1** — As the clinic, I want the database encrypted at rest, so that
  file access alone doesn't expose PHI.
- **E15-F2-S1** — As the clinic, I want attachments encrypted, so that lab reports
  aren't readable off-device.
- **E15-F3-S1** — As the clinic, I want encrypted backups, so that a copied zip
  isn't a breach.
- **E15-F4-S1** — As an Administrator, I want the key managed securely, so that it
  isn't committed or trivially recoverable.

## 4. Engineering tasks

- **E15-T1** — Choose the encryption mechanism at the storage/repository seam;
  keep it swappable.
- **E15-T2** — Key management (OS keystore or passphrase-derived); never in DB/git.
- **E15-T3** — Encrypt DB connection layer; encrypt attachment read/write.
- **E15-T4** — Encryptable backups/exports (EPIC-02 config toggle).
- **E15-T5** — One-time conversion: verified backup → encrypt → verify → keep a
  documented decrypt/rollback path.
- **E15-T6** — Tests (encrypted round-trip; wrong-key fails closed) + docs
  (SECURITY closes L5/F7, DEPLOYMENT, DECISIONS ADR).

## 5. Dependencies

- **Upstream:** EPIC-01; repository/storage seam. Pairs with EPIC-03.
- **Downstream:** hard prerequisite for EPIC-16 (Portal), EPIC-20 (Sync), EPIC-21
  (API) and any off-device transfer.

## 6. Acceptance criteria

- **AC1** — *Given* encryption enabled, *when* the DB file is opened without the
  key, *then* it is unreadable.
- **AC2** — *Given* encryption enabled, *when* attachments are stored, *then* they
  are encrypted at rest.
- **AC3** — *Given* a backup, *when* created with encryption on, *then* the zip is
  encrypted.
- **AC4** — *Given* the key, *when* the app runs, *then* data reads/writes work
  normally.
- **AC5** — *Given* the wrong key, *when* opening, *then* it fails closed (no
  partial/plaintext leak).
- **AC6** — *Given* conversion, *when* run, *then* a verified backup exists and a
  documented rollback restores plaintext.

## 7. Regression tests

- **Must stay green:** golden, models, router, views (run against an encrypted
  temp store).
- **New:** encrypted round-trip test, wrong-key fail-closed test, backup-encryption
  test, conversion verification test.

## 8. Rollout phases

- **E15-R1** — DB encryption at the connection seam + key management.
- **E15-R2** — Attachment encryption.
- **E15-R3** — Encryptable backups/exports.
- **E15-R4** — Verified conversion + docs closeout (L5/F7).

## 9. Rollback

Documented decrypt path; a verified plaintext backup is taken before conversion.
The local store remains authoritative; conversion is reversible.

## 10. Definition of done

Per [`README.md`](./README.md) DoD; plus: key never committed; wrong-key fails
closed; conversion reversible and verified; L5/F7 closed.
</content>
