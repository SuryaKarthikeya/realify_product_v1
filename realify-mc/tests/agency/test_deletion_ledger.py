"""T-P3-07 rider: deleting a tenant via the existing delete flow writes a hash-chained deletion_ledger
entry that SURVIVES the deletion, and the chain verifies."""
import os

from realify import config, db
from realify.agency import deletion
from realify.repositories.tenant_repo import TenantRepository

DIRECT = os.environ["AGENCY_DATABASE_URL"]


def test_tenant_delete_writes_surviving_hash_chained_entry(owner_conn, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_URL", DIRECT, raising=False)   # app db layer -> harness PG
    con = db.connect()
    tid = db.create_tenant(con, "delete-me")
    con.close()

    con = db.connect()
    TenantRepository(con).delete(tid)                 # existing delete path (fires the additive hook)
    con.close()

    cur = owner_conn.cursor()
    cur.execute("SELECT count(*) FROM deletion_ledger WHERE tenant_id=%s", (tid,))
    assert cur.fetchone()[0] == 1                      # entry survived the tenant's deletion
    cur.execute("SELECT count(*) FROM tenants WHERE id=%s", (tid,))
    assert cur.fetchone()[0] == 0                      # tenant is actually gone
    assert deletion.verify_chain(cur) is True          # chain intact
