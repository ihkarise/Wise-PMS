"""RBAC permission registry (Sprint 5 / F3 — ADR-003, Milestone 2).

The canonical **code-side** catalogue of the 16 approved permission keys
(``module.action``). It mirrors the keys seeded into the ``permissions`` table
by migration ``v0003_rbac`` — it is a declaration for callers (and, in a later
milestone, the route→permission map), **not** a second source of truth. Grants
are always resolved against the database (``user_roles`` → ``role_permissions``
→ ``permissions``); this registry only names the keys. Its identity with the
seeded table is asserted by ``tests/test_permission_infrastructure.py`` so the
two can never silently diverge.

No key here may be added or removed without a corresponding change to the
approved matrix (``docs/planning/SPRINT5_TECHNICAL_PLAN.md`` §5.2) and the
seed migration.
"""

# Individual permission keys, grouped by area (module.action).
DASHBOARD_VIEW = "dashboard.view"

PATIENTS_VIEW = "patients.view"
PATIENTS_EDIT = "patients.edit"
PATIENTS_DEACTIVATE = "patients.deactivate"
REGISTRATION_CREATE = "registration.create"

ATTACHMENTS_UPLOAD = "attachments.upload"
ATTACHMENTS_DELETE = "attachments.delete"

CASES_VIEW = "cases.view"
CASES_MANAGE = "cases.manage"

VISITS_VIEW = "visits.view"
VISITS_MANAGE = "visits.manage"

CONSULTATION_VIEW = "consultation.view"
CONSULTATION_EDIT = "consultation.edit"

SETTINGS_EDIT = "settings.edit"
BACKUP_RUN = "backup.run"
RBAC_MANAGE = "rbac.manage"

# The complete, immutable set of approved permission keys (exactly 16).
ALL_PERMISSIONS = frozenset({
    DASHBOARD_VIEW,
    PATIENTS_VIEW,
    PATIENTS_EDIT,
    PATIENTS_DEACTIVATE,
    REGISTRATION_CREATE,
    ATTACHMENTS_UPLOAD,
    ATTACHMENTS_DELETE,
    CASES_VIEW,
    CASES_MANAGE,
    VISITS_VIEW,
    VISITS_MANAGE,
    CONSULTATION_VIEW,
    CONSULTATION_EDIT,
    SETTINGS_EDIT,
    BACKUP_RUN,
    RBAC_MANAGE,
})


def is_known_permission(key: str) -> bool:
    """True if ``key`` is one of the approved permission keys."""
    return key in ALL_PERMISSIONS
