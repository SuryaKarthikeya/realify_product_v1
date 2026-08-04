"""T-P2-07: the normal<->internal toggle is ledgered (actor/timestamp/reason) and — because the flag
is evaluated at query time — flipping it retroactively excludes the tenant from a seeded aggregate."""
from realify.agency import internal


def test_toggle_is_ledgered_and_retroactively_excludes(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    ids = []
    for i in range(3):
        cur.execute("INSERT INTO tenants(name,created_at,provisioned,is_internal) "
                    "VALUES(%s,now()::text,1,false) RETURNING id", (f"AGG{i}",))
        ids.append(cur.fetchone()[0])
    owner_conn.commit()

    before = internal.count_billable_tenants(cur)
    r = client.post(f"/api/ops/tenants/{ids[0]}/internal", headers=H,
                    data={"to_internal": "true", "reason": "confirmed tester"})
    assert r.status_code == 200 and r.json()["is_internal"] is True
    owner_conn.commit()
    after = internal.count_billable_tenants(cur)
    assert after == before - 1                              # retroactive, query-time exclusion

    cur.execute("SELECT actor, action, tenant_id, reason, ts FROM agency_audit "
                "WHERE tenant_id=%s AND action='tenant.internal_toggle'", (ids[0],))
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "ops" and row[3] == "confirmed tester" and row[4] is not None   # actor + reason + ts

    # un-toggle restores the count (round-trip)
    client.post(f"/api/ops/tenants/{ids[0]}/internal", headers=H, data={"to_internal": "false"})
    owner_conn.commit()
    assert internal.count_billable_tenants(cur) == before
