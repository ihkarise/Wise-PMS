"""Migration 0003 — RBAC foundation (Sprint 5 / F3, ADR-003).

Adds the role-based access-control schema — ``roles``, ``permissions``,
``role_permissions``, ``user_roles`` — and seeds the approved five roles, the
16-permission catalogue, and the default role→permission grants
(``SPRINT5_TECHNICAL_PLAN.md`` §5.2). The pre-existing ``users.role`` column is
left untouched (non-authoritative legacy hint, ADR-003 §5); ``user_roles`` is
the authoritative binding.

Scope: this migration is the **database/domain foundation only** (Milestone 1).
It adds no route guard, no service authorization check, and no UI — those are
later, separately authorized milestones.

The ``up`` is additive and idempotent: ``CREATE TABLE IF NOT EXISTS`` /
``CREATE ... INDEX IF NOT EXISTS`` and ``INSERT OR IGNORE`` (guarded by UNIQUE
constraints), so applying it to any database — fresh or an existing Sprint 4
clinic — is safe and repeatable. The UNIQUE index ``idx_user_roles_user``
enforces the approved **one active role per user** invariant at the database
level. The legacy-user mapping binds any existing ``users.role`` of ``'Admin'``
or ``'Administrator'`` to the seeded Administrator role, so an upgraded clinic's
existing administrator is never locked out (ADR-003 §6). On a *fresh* database
the default admin is seeded by ``init_db`` after migrations run, so its
Administrator binding is ensured there as well (idempotently) — the two paths
together cover both upgrade and first-run.

The ``down`` fully reverses the migration (new tables + seed data, no schema
change to existing tables), so ``rollback_to(2)`` restores the exact Sprint 4
schema. Credentials and account data are never read or written by this
migration except to bind existing admins to the Administrator role.
"""

from app.core.migrations.runner import Migration

_UP = """
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    is_system INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY(role_id) REFERENCES roles(id),
    FOREIGN KEY(permission_id) REFERENCES permissions(id)
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(role_id) REFERENCES roles(id)
);

-- Enforces the approved one-active-role-per-user invariant at the DB level.
-- A future, separately approved multi-role phase would drop this index.
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);

-- Seed the five approved roles (Administrator is a protected system role).
INSERT OR IGNORE INTO roles (name, description, is_system) VALUES
    ('Administrator', 'Full system access; administers RBAC, clinic settings, and backups.', 1),
    ('Doctor', 'Runs consultations; full clinical access to patients, cases, visits, and attachments.', 0),
    ('Reception', 'Front desk: registers and maintains patients and uploads documents.', 0),
    ('Pharmacy', 'Dispensing role; dashboard only until the dispensing module is built.', 0),
    ('Accounts', 'Billing role; dashboard only until the billing module is built.', 0);

-- Seed the 16 approved permission keys (module.action).
INSERT OR IGNORE INTO permissions (key, description) VALUES
    ('dashboard.view', 'Open the dashboard.'),
    ('patients.view', 'View patient search and profiles.'),
    ('registration.create', 'Register a new patient.'),
    ('patients.edit', 'Edit an existing patient.'),
    ('patients.deactivate', 'Soft-delete (deactivate) a patient.'),
    ('attachments.upload', 'Upload a patient attachment.'),
    ('attachments.delete', 'Delete a patient attachment.'),
    ('cases.view', 'Open a case record.'),
    ('cases.manage', 'Create or edit a case.'),
    ('visits.view', 'Open a visit entry.'),
    ('visits.manage', 'Create or edit a visit.'),
    ('consultation.view', 'Open the consultation workspace.'),
    ('consultation.edit', 'Author or change a consultation.'),
    ('settings.edit', 'View and edit clinic settings.'),
    ('backup.run', 'Run a backup.'),
    ('rbac.manage', 'Administer roles and permissions.');

-- Administrator: all 16 permissions.
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r CROSS JOIN permissions p
WHERE r.name = 'Administrator';

-- Doctor: full clinical access (13 permissions), no admin/config keys.
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'Doctor' AND p.key IN (
    'dashboard.view', 'patients.view', 'registration.create', 'patients.edit',
    'patients.deactivate', 'attachments.upload', 'attachments.delete',
    'cases.view', 'cases.manage', 'visits.view', 'visits.manage',
    'consultation.view', 'consultation.edit'
);

-- Reception: front-desk permissions (5).
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'Reception' AND p.key IN (
    'dashboard.view', 'patients.view', 'registration.create',
    'patients.edit', 'attachments.upload'
);

-- Pharmacy: dashboard only (dispensing module not built).
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'Pharmacy' AND p.key = 'dashboard.view';

-- Accounts: dashboard only (billing module not built).
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'Accounts' AND p.key = 'dashboard.view';

-- Legacy-user migration: bind any existing 'Admin'/'Administrator' user to the
-- Administrator role (no-op on a fresh DB where users is still empty; the
-- fresh-DB admin is bound by init_db after seeding). Credentials untouched.
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON r.name = 'Administrator'
WHERE u.role IN ('Admin', 'Administrator');
"""

_DOWN = """
DROP INDEX IF EXISTS idx_user_roles_user;
DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS role_permissions;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS roles;
"""

MIGRATION = Migration(version=3, name="rbac", up=_UP, down=_DOWN)
