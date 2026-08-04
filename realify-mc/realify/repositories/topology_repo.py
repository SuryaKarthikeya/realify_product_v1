"""Persistence for cross-channel onboarding (spec §5): the resolved TenantTopology (one JSON blob per
tenant) and the SKU crosswalk (external identity -> canonical_sku_id). Tenant-scoped; sqlite-style
`INSERT OR REPLACE` that dbengine rewrites to Postgres ON CONFLICT via the registered keys."""
import datetime
import json

from .base import BaseRepository
from ..topology_model import TenantTopology

MAPPED, UNMAPPED, PARKED = "MAPPED", "UNMAPPED", "PARKED"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


class TopologyRepository(BaseRepository):
    def get(self, tenant_id):
        row = self.con.execute(
            "SELECT entry_path, schema_version, topology FROM tenant_topology WHERE tenant_id=?",
            (tenant_id,)).fetchone()
        if not row:
            return None
        d = json.loads(row["topology"] or "{}")
        d.setdefault("tenant_id", tenant_id)
        d.setdefault("entry_path", row["entry_path"])
        return TenantTopology.from_dict(d)

    def save(self, tenant_id, topo: TenantTopology):
        """Upsert the tenant's resolved topology. The JSON blob is the source of truth for the nested,
        volatile structure (channels/flags/completeness); entry_path + schema_version are surfaced as
        columns for cheap filtering."""
        now = _now()
        existing = self.con.execute(
            "SELECT created_at FROM tenant_topology WHERE tenant_id=?", (tenant_id,)).fetchone()
        created = (existing["created_at"] if existing else None) or now
        self.con.execute(
            "INSERT OR REPLACE INTO tenant_topology"
            "(tenant_id, schema_version, entry_path, topology, created_at, updated_at) VALUES(?,?,?,?,?,?)",
            (tenant_id, topo.schema_version, topo.entry_path,
             json.dumps(topo.to_dict()), created, now))
        return topo


class SkuCrosswalkRepository(BaseRepository):
    @staticmethod
    def _key(store_id, external_variant_id):
        return (store_id or ""), (external_variant_id or "")

    def upsert(self, tenant_id, channel, external_sku, canonical_sku_id, status=MAPPED,
               store_id="", external_variant_id=""):
        store_id, external_variant_id = self._key(store_id, external_variant_id)
        self.con.execute(
            "INSERT OR REPLACE INTO sku_crosswalk"
            "(tenant_id, channel, store_id, external_sku, external_variant_id, canonical_sku_id, status,"
            " created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (tenant_id, channel, store_id, str(external_sku or ""), external_variant_id,
             canonical_sku_id, status, _now(), _now()))

    def resolve(self, tenant_id, channel, external_sku, store_id="", external_variant_id=""):
        store_id, external_variant_id = self._key(store_id, external_variant_id)
        row = self.con.execute(
            "SELECT canonical_sku_id FROM sku_crosswalk WHERE tenant_id=? AND channel=? AND store_id=? "
            "AND external_sku=? AND external_variant_id=?",
            (tenant_id, channel, store_id, str(external_sku or ""), external_variant_id)).fetchone()
        return row["canonical_sku_id"] if row else None

    def unmapped(self, tenant_id):
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM sku_crosswalk WHERE tenant_id=? AND status IN (?, ?)",
            (tenant_id, UNMAPPED, PARKED)).fetchall()]

    def count(self, tenant_id):
        return self.con.execute(
            "SELECT COUNT(*) c FROM sku_crosswalk WHERE tenant_id=?", (tenant_id,)).fetchone()["c"]
