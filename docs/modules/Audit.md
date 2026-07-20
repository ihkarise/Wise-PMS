# Module: Audit

**Status:** ✅ Built · **Path:** `app/modules/audit/` · **Table:** `audit_logs`

## Purpose
Append-only trail of important actions (logins, and every create/update/delete
across modules) for traceability.

## Layers
`repository.py` (`AuditRepository.insert`) · `service.py`. No model/controller/
view — it is a cross-cutting concern used by every write service.

## Public service API
- `log_action(user_id, action_type, entity_type, entity_id, details="") -> None`

## Key behavior — never raises
`log_action` wraps the insert in `try/except: pass`. **Auditing must never break
a clinical workflow** — a failed audit write is swallowed. This is deliberate
(see [`../LESSONS_LEARNED.md`](../LESSONS_LEARNED.md) #5).

## Who writes audit rows
authentication (login/logout), patients, cases, visits, attachments. Backup does
not yet audit (candidate improvement).

## Fields
`user_id`, `action_type`, `entity_type`, `entity_id`, `action_details`,
`created_at`.

## Dependencies
`audit.repository → core`. Imported by every write service.

## Future
Feeds Analytics (staff activity) and any compliance reporting. When RBAC lands,
the audit trail becomes the record of who-did-what under which permission. AI
actions must also be audited (see [`AI.md`](./AI.md)).
