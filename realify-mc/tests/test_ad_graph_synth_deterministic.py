"""Same tenant + scenario -> identical ad graph across runs (clear-before-rebuild is deterministic)."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_agd_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, scheduler                                       # noqa: E402
from realify.ingest.synthetic import SyntheticSource                    # noqa: E402
from realify.ingest.synth_ad_graph import synthesize_ad_graph           # noqa: E402
from realify.repositories.tenant_repo import TenantRepository           # noqa: E402


def _snapshot(tid):
    with db.connect() as con:
        rows = con.execute(
            "SELECT campaign, ad_group, advertised_asin, internal_sku, spend, sales, clicks, orders "
            "FROM ad_entity_perf WHERE tenant_id=? ORDER BY campaign, ad_group, advertised_asin",
            (tid,)).fetchall()
        terms = con.execute(
            "SELECT campaign, customer_search_term, spend, sales FROM ad_search_term WHERE tenant_id=? "
            "ORDER BY campaign, customer_search_term", (tid,)).fetchall()
    return [tuple(r) for r in rows], [tuple(t) for t in terms]


def test_same_tenant_scenario_is_identical_across_runs():
    with db.connect() as con:
        tid = TenantRepository(con).create("Tester"); db.set_account_type(con, tid, "tester"); con.commit()
    scheduler.provision_own_data(tid, SyntheticSource(), log=lambda *a: None)   # sets internal_sku
    with db.connect() as con:
        synthesize_ad_graph(con, tid, "ads_full"); con.commit()
    snap1 = _snapshot(tid)
    with db.connect() as con:
        synthesize_ad_graph(con, tid, "ads_full"); con.commit()
    snap2 = _snapshot(tid)
    assert snap1 == snap2 and len(snap1[0]) > 0, (len(snap1[0]), len(snap2[0]))


if __name__ == "__main__":
    test_same_tenant_scenario_is_identical_across_runs()
    print("ad_graph_synth_deterministic OK")
