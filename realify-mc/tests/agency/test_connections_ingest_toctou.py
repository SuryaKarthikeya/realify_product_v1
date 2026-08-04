"""P3 domain: T-P3-06 connections health/pause, T-P3-05 CSV goldens, T-P3-04 envelope TOCTOU."""
import csv
import datetime
import os

from realify.agency import connections, ingest, toctou, ops, tenancy
from realify.pdp import ENVELOPES, ROLES, Action

GOLDENS = os.path.join(os.path.dirname(__file__), "goldens")


def _tenant(cur, name):
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES(%s,now()::text,1) RETURNING id", (name,))
    return cur.fetchone()[0]


def _read(name):
    with open(os.path.join(GOLDENS, name)) as f:
        r = csv.DictReader(f)
        rows = list(r)
        return r.fieldnames, rows


# ---- T-P3-06: expired connection pauses dependent decisions (never silently computed) ----
def test_expired_connection_pauses_decisions(owner_conn):
    cur = owner_conn.cursor()
    t = _tenant(cur, "C1"); owner_conn.commit()
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    connections.upsert_connection(cur, t, "amazon", "connected", past); owner_conn.commit()
    assert connections.health_run(cur) >= 1                      # stale -> expired
    owner_conn.commit()
    assert connections.decisions_paused(cur, t) is True
    out = connections.compute_decisions_guarded(cur, t, lambda: {"computed": 1})
    assert out["paused"] is True and out["decisions"] is None     # never silently computed


def test_active_connection_allows_decisions(owner_conn):
    cur = owner_conn.cursor()
    t = _tenant(cur, "C2"); owner_conn.commit()
    future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)
    connections.upsert_connection(cur, t, "shopify", "connected", future); owner_conn.commit()
    connections.health_run(cur); owner_conn.commit()
    assert connections.decisions_paused(cur, t) is False
    out = connections.compute_decisions_guarded(cur, t, lambda: {"computed": 1})
    assert out["paused"] is False and out["decisions"] == {"computed": 1}


# ---- T-P3-05: CSV goldens (>=6), detection, INR currency, source_class tagging, remembered mapping ----
def test_csv_goldens_detect_tag_and_remember(owner_conn):
    cur = owner_conn.cursor()
    t = _tenant(cur, "IG"); owner_conn.commit()
    files = [f for f in os.listdir(GOLDENS) if f.endswith(".csv")]
    assert len(files) >= 6
    expected = {"amazon_sales_traffic.csv": "amazon_sales_traffic",
                "amazon_all_orders.csv": "amazon_all_orders",
                "shopify_orders.csv": "shopify_orders",
                "google_ads_usd.csv": "google_ads", "google_ads_inr.csv": "google_ads",
                "meta_ads.csv": "meta_ads"}
    for fn, rtype in expected.items():
        headers, rows = _read(fn)
        assert ingest.detect_report_type(headers) == rtype, fn
        res = ingest.ingest_csv(cur, t, headers, rows); owner_conn.commit()
        assert res["report_type"] == rtype
        assert ingest.source_class_tagged_pct(res["rows"]) == 100.0     # every row tagged
        assert all(r["source_class"] == "csv" for r in res["rows"])
    # INR variant maps currency
    h, rows = _read("google_ads_inr.csv")
    assert ingest.detect_currency(h) == "INR"
    assert ingest.ingest_csv(cur, t, h, rows)["currency"] == "INR"
    owner_conn.commit()
    # remembered per-report-type mapping (the fix flow)
    fixed = dict(ingest.get_mapping(cur, "google_ads")); fixed["cost"] = "Cost (INR)"
    ingest.save_mapping(cur, "google_ads", fixed); owner_conn.commit()
    assert ingest.get_mapping(cur, "google_ads")["cost"] == "Cost (INR)"


# ---- T-P3-04: envelope-versioning TOCTOU enforced at execute ----
def test_toctou_narrow_mid_flight_denied_at_execute(owner_conn):
    cur = owner_conn.cursor()
    t = _tenant(cur, "TT")
    cur.execute("INSERT INTO agencies(name) VALUES('TTA') RETURNING id"); ag = cur.fetchone()[0]
    owner_conn.commit()
    tenancy.set_brand_scope(cur, [t])
    eid = ops.create_engagement(cur, None, ag, t)
    ops.publish_envelope(cur, None, eid, t, ENVELOPES["Full Operate"], {}); owner_conn.commit()
    grant_caps = ROLES["agency_admin"]
    action = Action("ads", "execute")

    tenancy.set_brand_scope(cur, [t])
    r1 = toctou.check_at_execute(cur, eid, 1, grant_caps, action)   # composed & executed under v1
    assert r1["allow"] is True and r1["current_version"] == 1 and r1["toctou_changed"] is False

    ops.publish_envelope(cur, None, eid, t, ENVELOPES["Read-only"], {}); owner_conn.commit()  # narrow -> v2
    tenancy.set_brand_scope(cur, [t])
    r2 = toctou.check_at_execute(cur, eid, 1, grant_caps, action)   # composed under v1, executes vs v2
    assert r2["allow"] is False and r2["toctou_changed"] is True and r2["current_version"] == 2
