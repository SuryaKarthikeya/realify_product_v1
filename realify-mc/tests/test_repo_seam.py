"""Repository-seam guard (agency-plan §1c-3): legacy tables keep app-layer tenant filtering, so no
repository BULK READ may return brand rows without a tenant filter. This enumerates the repository
classes and asserts every bulk-read method (all*/list*/for_*/by_*) takes a tenant scoping parameter —
except a reviewed allowlist of intentionally global/admin reads. A new agency-reachable repo that
exposed an unscoped cross-tenant read would fail here.
"""
import importlib
import inspect
import os
import pkgutil
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import realify.repositories as repos_pkg                 # noqa: E402
from realify.repositories.base import BaseRepository     # noqa: E402

_TENANT_PARAMS = {"tenant_id", "tid", "tenant"}
_BULK_READ = re.compile(r"^(all|list|for_|by_)")

# Reviewed, intentionally NOT tenant-scoped bulk reads: global config or cross-tenant admin/ops.
_ALLOWLIST = {
    "RulesRepository.all_rules",              # rules are global config, not brand data
    "TenantRepository.list_all",              # admin: enumerate tenants
    "TenantRepository.list_provisioned_ids",  # scheduler: all provisioned tenants
    "DeletedAccountAuditRepository.list_all",  # deletion audit is cross-tenant by design (ops trail)
}


def _repo_classes():
    found = []
    for m in pkgutil.iter_modules(repos_pkg.__path__):
        mod = importlib.import_module(f"realify.repositories.{m.name}")
        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, BaseRepository) and obj is not BaseRepository and obj.__module__ == mod.__name__:
                found.append(obj)
    return found


def test_every_bulk_brand_read_is_tenant_scoped():
    offenders = []
    for cls in _repo_classes():
        for name, fn in inspect.getmembers(cls, inspect.isfunction):
            if name.startswith("_") or not _BULK_READ.match(name):
                continue
            if f"{cls.__name__}.{name}" in _ALLOWLIST:
                continue
            params = set(inspect.signature(fn).parameters)
            if not (params & _TENANT_PARAMS):
                offenders.append(f"{cls.__name__}.{name}({', '.join(inspect.signature(fn).parameters)})")
    assert not offenders, "unscoped bulk brand reads (add a tenant param or review into _ALLOWLIST):\n" + "\n".join(offenders)


def test_seam_actually_enumerated_repos():
    assert len(_repo_classes()) >= 5
