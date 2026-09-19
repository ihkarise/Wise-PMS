"""Roles / RBAC module (backlog F3, Sprint 5, ADR-003).

Milestone 1 provides the database/domain foundation only: the role/permission
models, the data-access repository, and the domain service that enforces the
approved invariants (one active role per user; at least one active
Administrator). Route-level and action-level authorization enforcement and the
RBAC administration UI are later, separately authorized milestones and are NOT
part of this module yet.
"""
