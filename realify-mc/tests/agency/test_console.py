"""P4 console/queue: T-P4-01 rollup match, 02 rank determinism, 03 fairness, 04 grant-scoped fuzz,
05 fx determinism/swing."""
import datetime
import math
import os
import random

import psycopg

from realify.agency import decisions, queue, rollups, fx, tenancy, money

AS_OF = datetime.date(2026, 7, 14)
INR_PPM = 83_500_000
POOLER = os.environ.get("AGENCY_POOLER_URL", "").replace("postgresql+psycopg://", "postgresql://")


def _brand(cur, name):
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES(%s,now()::text,1) RETURNING id", (name,))
    return cur.fetchone()[0]


def _skus(cur, t, rows):
    for asin, price, cogs, units, doc, tacos, buybox in rows:
        cur.execute("INSERT INTO seller_skus(tenant_id,asin,internal_sku,channel,price,cogs,units_month,"
                    "days_of_cover,tacos,buybox_pct) VALUES(%s,%s,%s,'amazon',%s,%s,%s,%s,%s,%s)",
                    (t, asin, asin, price, cogs, units, doc, tacos, buybox))


# ---- T-P4-01 ----
def test_rollups_equal_independent_recompute(owner_conn):
    cur = owner_conn.cursor()
    fx.lock_rate(cur, AS_OF, "INR", INR_PPM); owner_conn.commit()
    t = _brand(cur, "R1")
    _skus(cur, t, [("A1", 1000, 400, 10, 30, 5, 90), ("A2", 500, 200, 5, 40, 8, 80)])
    cur.execute("INSERT INTO ad_performance(tenant_id,internal_sku,period_start,grain,spend,sales) "
                "VALUES(%s,'A1','2026-07-01','month',2000,10000)", (t,))
    owner_conn.commit()
    rollups.compute(cur, t, "INR", AS_OF); owner_conn.commit()

    gmv = int(round((1000 * 10 + 500 * 5) * 100))
    cogs = int(round((400 * 10 + 200 * 5) * 100))
    margin = gmv - cogs
    ad = int(round(2000 * 100))
    tacos_bps = int(round(ad * 10000 / gmv))
    _, rate = fx.get_rate(cur, AS_OF, "INR")
    gmv_usd = money.to_usd_minor(gmv, rate)
    margin_usd = money.to_usd_minor(margin, rate)

    tenancy.set_brand_scope(cur, [t])
    cur.execute("SELECT gmv_minor,gmv_usd_minor,margin_minor,margin_usd_minor,tacos_bps "
                "FROM rollup_cache WHERE tenant_id=%s", (t,))
    assert cur.fetchone() == (gmv, gmv_usd, margin, margin_usd, tacos_bps)


# ---- T-P4-02 ----
def test_ranking_byte_identical_across_10_runs(owner_conn):
    cur = owner_conn.cursor()
    fx.lock_rate(cur, AS_OF, "INR", INR_PPM); owner_conn.commit()
    t1, t2 = _brand(cur, "D1"), _brand(cur, "D2")
    _skus(cur, t1, [("A1", 1200, 400, 12, 10, 25, 95), ("A2", 600, 200, 8, 15, 12, 85)])
    _skus(cur, t2, [("B1", 900, 300, 20, 12, 30, 88)])
    owner_conn.commit()
    prev = None
    for _ in range(10):
        decisions.generate(cur, t1, "INR", AS_OF)
        decisions.generate(cur, t2, "USD", AS_OF)
        owner_conn.commit()
        key = [(i["tenant_id"], i["signal"], i["impact_usd_minor"]) for i in queue.build(cur, [t1, t2])]
        if prev is not None:
            assert key == prev
        prev = key
    assert len(prev) > 0


# ---- T-P4-03 ----
def test_fairness_no_account_starved(owner_conn):
    cur = owner_conn.cursor()
    accounts_best = {}
    for i in range(5):
        t = _brand(cur, f"F{i}")
        accounts_best[t] = {"impact_usd_minor": (5 - i) * 1000}
    owner_conn.commit()
    top_k, N = 2, 5
    D = math.ceil(N / top_k)                       # fairness bound = 3
    last_shown, appeared = {}, {a: [] for a in accounts_best}
    for day in range(24):
        for a in queue.fair_select(accounts_best, top_k, day, last_shown):
            appeared[a].append(day)
    for a, days in appeared.items():
        assert days, a
        assert days[0] <= D - 1                      # first appearance within the window
        gaps = [days[i] - days[i - 1] for i in range(1, len(days))]
        assert all(g <= D for g in gaps), (a, days)  # never absent for more than D days


# ---- T-P4-04 ----
def test_grant_scoped_queue_no_foreign_leak(owner_conn):
    cur = owner_conn.cursor()
    fx.lock_rate(cur, AS_OF, "INR", INR_PPM); owner_conn.commit()
    canary = {}
    for i in range(6):
        t = _brand(cur, f"G{i}")
        _skus(cur, t, [(f"CANARY-{t}", 1000, 400, 10, 10, 25, 90)])
        canary[t] = f"CANARY-{t}"
    owner_conn.commit()
    for t in canary:
        decisions.generate(cur, t, "USD", AS_OF)
    owner_conn.commit()

    ids = list(canary)
    rnd = random.Random(7)
    leaks = 0
    # Enforce via the NON-superuser app role through the pooler — realify_owner is a harness superuser
    # and would bypass RLS. prepare_threshold=None: pgbouncer transaction mode dislikes prepared stmts.
    app = psycopg.connect(POOLER, prepare_threshold=None)
    try:
        for _ in range(2000):
            scope = rnd.sample(ids, rnd.randint(1, 3))
            acur = app.cursor()
            for it in queue.build(acur, scope):
                if it["tenant_id"] not in scope:
                    leaks += 1
                for bt, can in canary.items():
                    if bt not in scope and can in (it["signal"] or ""):
                        leaks += 1
            app.commit()
    finally:
        app.close()
    assert leaks == 0



# ---- T-P4-05 ----
def _top_usd(cur, t):
    tenancy.set_brand_scope(cur, [t])
    cur.execute("SELECT impact_minor, impact_usd_minor, fx_rate_id FROM decisions WHERE tenant_id=%s "
                "ORDER BY impact_usd_minor DESC, signal LIMIT 1", (t,))
    return cur.fetchone()


def test_fx_locked_determinism_and_swing(owner_conn):
    cur = owner_conn.cursor()
    fx.lock_rate(cur, AS_OF, "INR", INR_PPM); owner_conn.commit()
    t = _brand(cur, "FX")
    _skus(cur, t, [("A1", 1000, 400, 10, 10, 25, 90)])
    owner_conn.commit()

    decisions.generate(cur, t, "INR", AS_OF); owner_conn.commit()
    im0, usd0, fxid0 = _top_usd(cur, t)
    assert fxid0 is not None                          # fx_locked: every figure references a rate row

    decisions.generate(cur, t, "INR", AS_OF); owner_conn.commit()   # same rate row
    im1, usd1, _ = _top_usd(cur, t)
    assert (im1, usd1) == (im0, usd0)                 # identical -> deterministic

    as_of2 = datetime.date(2026, 7, 15)
    new_ppm = int(INR_PPM * 1.06)                     # INR weakens 6%
    fx.lock_rate(cur, as_of2, "INR", new_ppm); owner_conn.commit()
    decisions.generate(cur, t, "INR", as_of2); owner_conn.commit()
    im2, usd2, _ = _top_usd(cur, t)
    assert im2 == im0                                 # brand-facing selling value unchanged
    assert usd2 < usd0                                # USD-normalized value dropped (predictable)
    assert usd2 == money.to_usd_minor(im0, new_ppm)   # exactly the locked-rate conversion
