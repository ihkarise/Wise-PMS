"""Layering / import boundary gates (Sprint 4, SPRINT4_TESTING_PLAN.md §5).

Static source checks -- no runtime behavior asserted here. These
operationalize the Sprint 4 architecture boundaries so a future edit that
quietly reintroduces a direct engine/filesystem dependency, or an
out-of-scope runtime dependency, fails CI rather than passing review by
accident.
"""

import ast
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(REPO_ROOT, "app")

# Files allowed to import sqlite3 directly: the DatabaseAdapter seam
# itself, and the pre-existing, unchanged migration-runner package (out
# of scope for Sprint 4 -- ADR-002 §13 / SPRINT4_TECHNICAL_PLAN.md §3.4).
_SQLITE_IMPORT_ALLOWED = {
    os.path.join(APP_DIR, "core", "db_adapters", "sqlite_adapter.py"),
    os.path.join(APP_DIR, "core", "migrations", "runner.py"),
    os.path.join(APP_DIR, "core", "migrations", "__init__.py"),
}

# Files allowed to write/delete raw filesystem paths for attachments or
# backups outside the StorageProvider seam: none, other than the
# LocalDiskStorageProvider itself and the backup archive *builder* (which
# is explicitly, and only, allowed to keep local filesystem calls for
# archive CONSTRUCTION -- ADR-002 §5.3 / SPRINT4_TECHNICAL_PLAN.md §4.4).
_STORAGE_WRITE_ALLOWED = {
    os.path.join(APP_DIR, "core", "storage", "local_disk_provider.py"),
    os.path.join(APP_DIR, "modules", "backup", "service.py"),
}

_LOCAL_ONLY_HELPER_ALLOWED = {
    os.path.join(APP_DIR, "core", "storage", "local_disk_provider.py"),
    os.path.join(APP_DIR, "modules", "attachments", "service.py"),
}


def _python_files(root):
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)


def _imports(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_sqlite3_imported_only_by_the_adapter_and_migration_runner():
    offenders = []
    for path in _python_files(APP_DIR):
        if path in _SQLITE_IMPORT_ALLOWED:
            continue
        with open(path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
        if "sqlite3" in _imports(tree):
            offenders.append(path)
    assert not offenders, f"unexpected direct sqlite3 import(s): {offenders}"


def _uses_shutil_or_raw_os_write(tree):
    """AST-based (not substring) check, so prose mentioning "shutil" in a
    docstring/comment never produces a false positive."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "shutil":
                return True
            if node.value.id == "os" and node.attr in ("remove", "makedirs"):
                return True
    return False


# app/config/paths.py's ensure_folders() creates the top-level runtime
# folders (data/, attachments/, backups/, exports/, logs/) at startup --
# infra bootstrap that predates and is independent of the Sprint 4
# attachments/backup StorageProvider migration; explicitly out of scope.
_INFRA_BOOTSTRAP_ALLOWED = {os.path.join(APP_DIR, "config", "paths.py")}


def test_shutil_and_raw_os_writes_confined_to_storage_seam():
    """`shutil`, `os.remove`, and `os.makedirs` must not appear outside the
    storage seam / the documented backup-archive-construction exception."""
    offenders = []
    for path in _python_files(APP_DIR):
        if path in _STORAGE_WRITE_ALLOWED or path in _INFRA_BOOTSTRAP_ALLOWED:
            continue
        with open(path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
        if _uses_shutil_or_raw_os_write(tree):
            offenders.append(path)
    assert not offenders, f"unexpected direct filesystem write(s): {offenders}"


def test_local_only_helper_confined_to_documented_call_sites():
    """`.local_path(` must appear only where ADR-002 §5.1 documents it as
    a known local-only dependency."""
    offenders = []
    for path in _python_files(APP_DIR):
        if path in _LOCAL_ONLY_HELPER_ALLOWED:
            continue
        with open(path, "r", encoding="utf-8") as fh:
            source = fh.read()
        if ".local_path(" in source:
            offenders.append(path)
    assert not offenders, f"unexpected local_path() call site(s): {offenders}"


def test_no_new_runtime_dependency_added():
    """Sprint 4 adds zero dependencies (Product Owner Revision 6/7)."""
    req_path = os.path.join(REPO_ROOT, "requirements.txt")
    with open(req_path, "r", encoding="utf-8") as fh:
        lines = [l.strip() for l in fh if l.strip() and not l.startswith("#")]
    packages = {l.split("==")[0].split(">=")[0].strip().lower() for l in lines}
    assert packages == {"flet", "bcrypt"}, (
        f"requirements.txt changed unexpectedly: {sorted(packages)}"
    )


def test_out_of_scope_technologies_absent():
    """No PostgreSQL/MySQL/SQL Server driver, ORM, or cloud SDK import
    anywhere in the app (Product Owner Revision 6/7)."""
    banned_modules = {
        "psycopg2", "psycopg", "pymysql", "mysqlclient", "pyodbc",
        "sqlalchemy", "alembic", "boto3", "azure", "google.cloud",
    }
    offenders = []
    for path in _python_files(APP_DIR):
        with open(path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
        found = _imports(tree) & banned_modules
        if found:
            offenders.append((path, found))
    assert not offenders, f"out-of-scope dependency import(s): {offenders}"


if __name__ == "__main__":
    test_sqlite3_imported_only_by_the_adapter_and_migration_runner()
    test_shutil_and_raw_os_writes_confined_to_storage_seam()
    test_local_only_helper_confined_to_documented_call_sites()
    test_no_new_runtime_dependency_added()
    test_out_of_scope_technologies_absent()
    print("[PASS] layering gates")
