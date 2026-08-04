"""R0 fix 1: mobile-approval decide() must verify the signed deep-link token bound to (approval, user).
Wrong/absent token ⇒ 403; arbitrary code ⇒ 403; a valid token approves as the bound user."""
from realify.agency import approvals, tenancy


def _setup(cur):
    cur.execute("INSERT INTO agencies(name) VALUES('SecAg') RETURNING id")
    ag = cur.fetchone()[0]
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('SecBr',now()::text,1) RETURNING id")
    t = cur.fetchone()[0]
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status,maker_checker_threshold_usd_minor) "
                "VALUES(%s,%s,'active',0) RETURNING id", (ag, t))
    eng = cur.fetchone()[0]
    cur.execute("INSERT INTO users(email,created_at) VALUES(%s,now()::text) RETURNING id",
                (f"maker{ag}@x.com",))
    maker = cur.fetchone()[0]
    cur.execute("INSERT INTO users(email,created_at) VALUES(%s,now()::text) RETURNING id",
                (f"checker{ag}@x.com",))
    checker = cur.fetchone()[0]
    tenancy.set_brand_scope(cur, [t])
    aid = approvals.propose(cur, t, eng, maker, "ads", "bid", "sig", 1000)
    token = approvals.create_deeplink(cur, aid, checker)          # link issued to the checker
    return aid, token, checker


def test_decide_requires_valid_deeplink_token(agency_client, owner_conn):
    client, _ = agency_client
    cur = owner_conn.cursor()
    aid, token, checker = _setup(cur)
    owner_conn.commit()

    # absent token -> 403 (no non-empty free-pass)
    assert client.post(f"/api/agency/approvals/{aid}/decide",
                       data={"decision": "approve"}).status_code == 403
    # arbitrary code -> 403 (fails the (approval,user) hash match)
    assert client.post(f"/api/agency/approvals/{aid}/decide",
                       data={"decision": "approve", "token": "garbage-not-the-token"}).status_code == 403
    # happy path: the valid signed token approves, as the bound (checker) user
    r = client.post(f"/api/agency/approvals/{aid}/decide", data={"decision": "approve", "token": token})
    assert r.status_code == 200 and r.json()["status"] in ("approved", "cosign_pending")
    owner_conn.rollback()
    cur.execute("SELECT status, checker_user FROM approvals WHERE id=%s", (aid,))
    st, cu = cur.fetchone()
    assert st in ("approved", "cosign_pending") and cu == checker


def test_used_or_wrong_user_token_rejected(agency_client, owner_conn):
    client, _ = agency_client
    cur = owner_conn.cursor()
    aid, token, checker = _setup(cur)
    owner_conn.commit()
    # a token for a DIFFERENT approval must not work here
    cur.execute("INSERT INTO agencies(name) VALUES('Other') RETURNING id"); _ = cur.fetchone()
    other_token = "x" * 43
    owner_conn.commit()
    assert client.post(f"/api/agency/approvals/{aid}/decide",
                       data={"decision": "approve", "token": other_token}).status_code == 403
