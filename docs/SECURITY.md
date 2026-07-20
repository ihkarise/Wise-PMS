# WiseOS Health — Security

> Current posture and the roadmap to a PHI-grade posture. Be honest about what
> is and isn't protected today. **Last updated:** 2026-07-20.

## Threat context

Wise PMS stores **Protected Health Information** (names, contacts, clinical
notes, prescriptions, documents). Today it runs as a **single-user, offline
desktop app on the clinic's own machine** — the trust boundary is physical
access to that machine.

## What exists today

| Control | Status | Detail |
| ------- | ------ | ------ |
| Password hashing | ✅ | bcrypt (`gensalt` + `checkpw`) for the `users` table |
| Session guard | ✅ | Router forces `/login` for any route without a session user |
| Audit trail | ✅ | `audit_logs` records login/logout and every mutation; writes never raise |
| Soft delete | ✅ | Patients never physically removed (`is_active`) |
| Error containment | ✅ | Router hides tracebacks behind a friendly snackbar |
| Local-only data | ✅ | No network calls; DB is a local file |

## What is NOT protected today — ⚠️

| Gap | Impact | Backlog |
| --- | ------ | ------- |
| **No RBAC** | Any logged-in user can do anything; `role` is decorative | F3 |
| **No encryption at rest** | `data/wise_pms.db` and `attachments/` are plaintext on disk | F7 |
| **Default credentials** | Ships `admin`/`admin123`; must be changed on first use | — |
| **No account lockout / rate limiting** | Brute force possible if machine is accessed | — |
| **Backups unencrypted** | `backups/backup_*.zip` contains the full DB + attachments in the clear | — |
| **No transport security** | N/A today (offline); becomes critical for Portal/API/Sync | F8 |

## Rules for future work

1. **RBAC (F3) and encryption at rest (F7) must land before** any networked or
   multi-user surface (Patient Portal, Online Consultation, Cloud Sync, API).
2. Every new mutation must write an audit row via `audit.service.log_action`.
3. Secrets (future API keys for WhatsApp/Meet/AI) must never be committed —
   route them through Settings/env, and add them to `.gitignore` paths.
4. The **repository layer is the enforcement seam** for row-level access control
   when RBAC arrives.
5. Backups and exports must be encryptable before any off-device transfer.

## Compliance note

No formal HIPAA/GDPR/Indian DPDP compliance work has been done. Treat the
current build as **suitable for a single trusted clinician on a controlled
machine**, not for multi-user or cloud deployment, until F3/F7/F8 are complete.
