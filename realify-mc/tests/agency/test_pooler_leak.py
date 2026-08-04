"""T-P1-02 pooler-leak: 500 interleaved transactions as two users through PgBouncer (transaction
pooling) must never surface a foreign brand's canary. Proves transaction-local scope does not leak
across pooled backend reuse."""
import os

import psycopg

OWNER = os.environ["AGENCY_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
POOLER = os.environ["AGENCY_POOLER_URL"].replace("postgresql+psycopg://", "postgresql://")


def _seed_two_brands():
    with psycopg.connect(OWNER) as oc, oc.cursor() as o:
        o.execute("SET LOCAL row_security = off")
        o.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('PA',now()::text,1) RETURNING id")
        a = o.fetchone()[0]
        o.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('PB',now()::text,1) RETURNING id")
        b = o.fetchone()[0]
        ca, cb = f"CANARY_PA_{a}", f"CANARY_PB_{b}"
        o.execute("INSERT INTO ledger(tenant_id,action,hash) VALUES(%s,%s,'h')", (a, ca))
        o.execute("INSERT INTO ledger(tenant_id,action,hash) VALUES(%s,%s,'h')", (b, cb))
        oc.commit()
    return a, b, ca, cb


def test_no_foreign_canary_across_500_interleaved_pooled_txns(clean_agency):
    a, b, ca, cb = _seed_two_brands()
    conn_a = psycopg.connect(POOLER)
    conn_b = psycopg.connect(POOLER)
    leaks = 0
    saw_own = 0
    try:
        for i in range(500):
            conn, mine, foreign, scope = (conn_a, ca, cb, a) if i % 2 == 0 else (conn_b, cb, ca, b)
            cur = conn.cursor()
            cur.execute("SELECT set_config('app.brand_ids', %s, true)", ("{%d}" % scope,))
            cur.execute("SELECT action FROM ledger")
            actions = [r[0] for r in cur.fetchall()]
            if any(mine in x for x in actions):
                saw_own += 1
            if any(foreign in x for x in actions):
                leaks += 1
            conn.commit()
    finally:
        conn_a.close()
        conn_b.close()
    assert leaks == 0, f"{leaks}/500 transactions saw a foreign canary"
    assert saw_own == 500, "each transaction should see its own brand's canary"
