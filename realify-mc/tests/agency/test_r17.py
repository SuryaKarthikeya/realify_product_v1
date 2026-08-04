"""R17 (Postgres/agency) — the ops close-out queue + composite deletes, asserted on the ENDPOINTS the
console posts to and the DB after the destructive step (never a helper). The billing gate, the operator
override, agency-delete-without-orphans, and user delete (member vs sole owner) are the invariants.
"""
from realify.agency import sandbox


def _seller(cur, name, **cols):
    keys = "name,created_at,provisioned,tenant_kind" + ("," + ",".join(cols) if cols else "")
    vals = ["%s", "now()::text", "1", "'seller'"] + ["%s"] * len(cols)
    cur.execute(f"INSERT INTO tenants({keys}) VALUES({','.join(vals)}) RETURNING id",
                tuple([name] + list(cols.values())))
    return cur.fetchone()[0]


def test_brand_closeout_gate_settle_execute(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    tid = _seller(cur, "CustCo R17", account_type="customer", subscription_status="active")
    owner_conn.commit()
    # request → an open balance parks in HOLD
    r = client.post("/api/ops/deletions/request", headers=H, json={"entity_type": "brand", "entity_ref": str(tid)})
    assert r.status_code == 200 and r.json()["status"] == "hold"
    rid = r.json()["id"]
    # the queue renders the pending row (rendered-HTML assertion)
    page = client.get("/ops/agency/admin", headers=H).text
    assert "Accounts pending close-out" in page and "CustCo R17" in page
    # Execute is BLOCKED while unsettled with no override
    assert client.post(f"/api/ops/deletions/{rid}/execute", headers=H, json={}).status_code == 409
    # Mark paid up → ready, then Execute → hard wipe
    assert client.post(f"/api/ops/deletions/{rid}/settle", headers=H, json={}).json()["status"] == "ready"
    assert client.post(f"/api/ops/deletions/{rid}/execute", headers=H, json={}).json()["ok"]
    owner_conn.rollback()
    cur.execute("SELECT count(*) FROM tenants WHERE id=%s", (tid,))
    assert cur.fetchone()[0] == 0                                   # hard-wiped


def test_execute_override_bypasses_gate(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    tid = _seller(cur, "OverrideCo", account_type="customer", subscription_status="active")
    owner_conn.commit()
    rid = client.post("/api/ops/deletions/request", headers=H,
                      json={"entity_type": "brand", "entity_ref": str(tid)}).json()["id"]
    # unsettled + override reason ⇒ allowed (R17 dec.3)
    r = client.post(f"/api/ops/deletions/{rid}/execute", headers=H, json={"override_reason": "founder waived final month"})
    assert r.status_code == 200 and r.json()["ok"]
    owner_conn.rollback()
    cur.execute("SELECT count(*) FROM tenants WHERE id=%s", (tid,))
    assert cur.fetchone()[0] == 0


def test_cancel_restores_and_admin_gated(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    tid = _seller(cur, "CancelCo", account_type="customer", subscription_status="active")
    owner_conn.commit()
    rid = client.post("/api/ops/deletions/request", headers=H,
                      json={"entity_type": "brand", "entity_ref": str(tid)}).json()["id"]
    assert client.post(f"/api/ops/deletions/{rid}/cancel", headers=H, json={}).json()["status"] == "canceled"
    owner_conn.rollback()
    cur.execute("SELECT count(*) FROM tenants WHERE id=%s", (tid,))
    assert cur.fetchone()[0] == 1                                   # NOT wiped — restored
    # every action is require_admin-gated (no admin header ⇒ 403)
    assert client.post("/api/ops/deletions/request", json={"entity_type": "brand", "entity_ref": str(tid)}).status_code == 403
    assert client.post(f"/api/ops/deletions/{rid}/execute", json={}).status_code == 403


def test_agency_delete_wipes_brands_no_orphans(agency_client, owner_conn):
    client, H = agency_client
    from realify.agency import synth
    spec = synth.spec_from_params({"country": "US", "seed": "r17-agdel", "brands_per_agency": 2,
                                   "direct_brands": 0, "agency_name": "DelAgencyCo"})
    st = sandbox.load_world(owner_conn.cursor(), spec, synth.world_key("r17-agdel")); owner_conn.commit()
    aid = st["agency_id"]; brand_ids = [b["tenant_id"] for b in st["brands"]]
    assert brand_ids
    r = client.post("/api/ops/deletions/request", headers=H, json={"entity_type": "agency", "entity_ref": str(aid)})
    assert r.status_code == 200                                     # no open invoices ⇒ ready
    rid = r.json()["id"]
    assert client.post(f"/api/ops/deletions/{rid}/execute", headers=H, json={}).json()["ok"]
    cur = owner_conn.cursor(); owner_conn.rollback()
    cur.execute("SELECT count(*) FROM agencies WHERE id=%s", (aid,)); assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM engagements WHERE agency_id=%s", (aid,)); assert cur.fetchone()[0] == 0
    for t in brand_ids:
        cur.execute("SELECT count(*) FROM tenants WHERE id=%s", (t,))
        assert cur.fetchone()[0] == 0                              # brands wiped too — no orphans


def test_agency_workspace_tenant_delete_composites(agency_client, owner_conn):
    """R18.2 — deleting an agency's WORKSPACE tenant from the ops page (/api/admin/tenants/{id}/delete)
    must wipe its managed brands FIRST (cascading their hash-chained ledger) so removing the agency owner
    doesn't 500 on ledger_actor_user_fkey. Exact shape that failed in prod: the workspace owner is the
    actor_user on a ledger row in a managed brand."""
    client, H = agency_client
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('WS Del Agency') RETURNING id"); aid = cur.fetchone()[0]
    cur.execute("INSERT INTO tenants(name,created_at,provisioned,tenant_kind) "
                "VALUES('WS Del Agency',now()::text,0,'agency_workspace') RETURNING id"); ws = cur.fetchone()[0]
    cur.execute("INSERT INTO users(email,tenant_id,role,pw_hash,pw_salt,name) "
                "VALUES('wsowner@x.co',%s,'owner','h','s','WS Owner') RETURNING id", (ws,)); owner_uid = cur.fetchone()[0]
    cur.execute("INSERT INTO agency_members(agency_id,user_id,role) VALUES(%s,%s,'agency_admin')", (aid, owner_uid))
    # the inbound application record points at the agency (no-cascade FK) — must not block the wipe
    cur.execute("INSERT INTO agency_requests(ref,agency_name,contact_email,hq_country,status,agency_id) "
                "VALUES('wsdel-ref','WS Del Agency','wsowner@x.co','US','live',%s)", (aid,))
    brand = _seller(cur, "WS Managed Brand")
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status) VALUES(%s,%s,'active')", (aid, brand))
    cur.execute("INSERT INTO ledger(ts,actor_user,tenant_id,action,hash) "
                "VALUES(now(),%s,%s,'test.entry','deadbeef')", (owner_uid, brand))   # the FK-500 trigger
    owner_conn.commit()
    r = client.post(f"/api/admin/tenants/{ws}/delete", headers=H, json={"confirm": "WS Del Agency"})
    assert r.status_code == 200 and r.json()["ok"], r.text            # was 500 (ledger_actor_user_fkey)
    owner_conn.rollback()
    cur.execute("SELECT count(*) FROM tenants WHERE id IN (%s,%s)", (ws, brand)); assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM users WHERE id=%s", (owner_uid,)); assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM agencies WHERE id=%s", (aid,)); assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM engagements WHERE agency_id=%s", (aid,)); assert cur.fetchone()[0] == 0


def test_ops_delete_clears_users_cross_tenant_ledger_footprint(agency_client, owner_conn):
    """R18.4 — deleting a tenant whose user authored ledger rows in ANOTHER (surviving) tenant must not
    500 on ledger_actor_user_fkey. execute_brand now clears that user's ledger footprint everywhere first;
    the surviving tenant stays, minus the deleted user's entries."""
    client, H = agency_client
    cur = owner_conn.cursor()
    survivor = _seller(cur, "Survivor Brand")                        # stays
    cur.execute("INSERT INTO tenants(name,created_at,provisioned,tenant_kind) "
                "VALUES('Victim Onboarding',now()::text,0,'seller') RETURNING id"); victim = cur.fetchone()[0]
    cur.execute("INSERT INTO users(email,tenant_id,role,pw_hash,pw_salt,name) "
                "VALUES('victim@x.co',%s,'owner','h','s','Victim') RETURNING id", (victim,)); vuid = cur.fetchone()[0]
    # the victim's user authored a ledger entry IN the survivor tenant (the exact FK-500 shape)
    cur.execute("INSERT INTO ledger(ts,actor_user,tenant_id,action,hash) "
                "VALUES(now(),%s,%s,'test.entry','beef01')", (vuid, survivor))
    owner_conn.commit()
    r = client.post(f"/api/admin/tenants/{victim}/delete", headers=H, json={"confirm": "Victim Onboarding"})
    assert r.status_code == 200 and r.json()["ok"], r.text            # was 500
    owner_conn.rollback()
    cur.execute("SELECT count(*) FROM tenants WHERE id=%s", (victim,)); assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM users WHERE id=%s", (vuid,)); assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM tenants WHERE id=%s", (survivor,)); assert cur.fetchone()[0] == 1  # survivor stays
    cur.execute("SELECT count(*) FROM ledger WHERE actor_user=%s", (vuid,)); assert cur.fetchone()[0] == 0  # footprint cleared


def test_user_delete_member_vs_sole_owner(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    tid = _seller(cur, "TeamCo")
    cur.execute("INSERT INTO users(email,tenant_id,role,pw_hash,pw_salt,name) "
                "VALUES('owner@team.co',%s,'owner','h','s','Owner') RETURNING id", (tid,))
    _own = cur.fetchone()[0]
    cur.execute("INSERT INTO users(email,tenant_id,role,pw_hash,pw_salt,name) "
                "VALUES('mem@team.co',%s,'member','h','s','Member') RETURNING id", (tid,))
    mem = cur.fetchone()[0]
    owner_conn.commit()
    # deleting a MEMBER leaves the org: member gone, tenant + owner intact
    rid = client.post("/api/ops/deletions/request", headers=H, json={"entity_type": "user", "entity_ref": str(mem)}).json()["id"]
    assert client.post(f"/api/ops/deletions/{rid}/execute", headers=H, json={}).json()["ok"]
    owner_conn.rollback()
    cur.execute("SELECT count(*) FROM users WHERE id=%s", (mem,)); assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM tenants WHERE id=%s", (tid,)); assert cur.fetchone()[0] == 1
    # a SOLE-owner tenant: deleting the last user escalates to a full brand wipe
    solo = _seller(cur, "SoloUserCo")
    cur.execute("INSERT INTO users(email,tenant_id,role,pw_hash,pw_salt,name) "
                "VALUES('solo@x.co',%s,'owner','h','s','Solo') RETURNING id", (solo,))
    suid = cur.fetchone()[0]; owner_conn.commit()
    rid2 = client.post("/api/ops/deletions/request", headers=H, json={"entity_type": "user", "entity_ref": str(suid)}).json()["id"]
    assert client.post(f"/api/ops/deletions/{rid2}/execute", headers=H, json={}).json()["ok"]
    owner_conn.rollback()
    cur.execute("SELECT count(*) FROM tenants WHERE id=%s", (solo,)); assert cur.fetchone()[0] == 0   # escalated to brand delete
