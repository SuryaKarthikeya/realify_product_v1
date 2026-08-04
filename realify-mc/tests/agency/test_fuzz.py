"""T-P1-05 cross-tenant fuzz: 10,000 randomized scoped reads across the brand-scoped agency tables.
Every returned row must be within the transaction's brand scope (zero out-of-scope rows) and no
read may surface a foreign brand's canary. Routes land in P2; this fuzzes the RLS data layer they
will sit on.
"""
import os
import random

import psycopg

OWNER = os.environ["AGENCY_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
POOLER = os.environ["AGENCY_POOLER_URL"].replace("postgresql+psycopg://", "postgresql://")
BRAND_TABLES = ["engagements", "envelopes", "grants", "ledger"]
N = 10_000


def _seed(n=8):
    """n brands, each with one row in every brand-scoped table; ledger row carries the brand canary."""
    brands = []
    with psycopg.connect(OWNER) as oc, oc.cursor() as o:
        o.execute("SET LOCAL row_security = off")
        o.execute("INSERT INTO agencies(name) VALUES('FZ') RETURNING id")
        ag = o.fetchone()[0]
        o.execute("INSERT INTO users(email,created_at) VALUES('fuzz@x.com',now()::text) RETURNING id")
        u = o.fetchone()[0]
        for i in range(n):
            o.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES(%s,now()::text,1) RETURNING id",
                      (f"FZ{i}",))
            t = o.fetchone()[0]
            canary = f"CANARY_FZ_{t}"
            o.execute("INSERT INTO engagements(agency_id,tenant_id,status) VALUES(%s,%s,'active') RETURNING id",
                      (ag, t))
            eid = o.fetchone()[0]
            o.execute("INSERT INTO envelopes(engagement_id,tenant_id,version) VALUES(%s,%s,1)", (eid, t))
            o.execute("INSERT INTO grants(user_id,engagement_id,tenant_id,role) VALUES(%s,%s,%s,'viewer')",
                      (u, eid, t))
            o.execute("INSERT INTO ledger(tenant_id,action,hash) VALUES(%s,%s,'h')", (t, canary))
            brands.append((t, canary))
        oc.commit()
    return brands


def test_10k_randomized_scoped_reads_never_leak(clean_agency):
    brands = _seed(8)
    ids = [t for t, _ in brands]
    foreign_canaries = {t: c for t, c in brands}
    rnd = random.Random(20260714)
    conn = psycopg.connect(POOLER)
    out_of_scope = 0
    foreign_hits = 0
    calls = 0
    try:
        for _ in range(N):
            scope = rnd.sample(ids, rnd.randint(1, 3))
            table = rnd.choice(BRAND_TABLES)
            cur = conn.cursor()
            cur.execute("SELECT set_config('app.brand_ids', %s, true)", ("{" + ",".join(map(str, scope)) + "}",))
            if table == "ledger":
                cur.execute("SELECT tenant_id, action FROM ledger")
                rows = cur.fetchall()
                for tid, action in rows:
                    if tid not in scope:
                        out_of_scope += 1
                    # a foreign canary is any brand's canary not in scope
                    for ft, fc in foreign_canaries.items():
                        if ft not in scope and fc == action:
                            foreign_hits += 1
            else:
                cur.execute(f"SELECT tenant_id FROM {table}")
                for (tid,) in cur.fetchall():
                    if tid not in scope:
                        out_of_scope += 1
            conn.commit()
            calls += 1
    finally:
        conn.close()
    assert calls == N
    assert out_of_scope == 0, f"{out_of_scope} rows returned outside the brand scope"
    assert foreign_hits == 0, f"{foreign_hits} foreign canaries surfaced"
