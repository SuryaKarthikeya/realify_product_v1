"""QW-2: the tester catalog carries ≥1 SKU with no COGS, and Profit & Ads surfaces it as the
margin-unavailable state ("Needs COGS") — the synth-reachable form of MARGIN_UNAVAILABLE. (The
topology-level flag itself is armed via reconcile/wizard, which is Tier-3, out of this spec.)"""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_mu_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, scheduler                                       # noqa: E402
from realify.ingest.synthetic import SyntheticSource                    # noqa: E402
from realify.repositories.tenant_repo import TenantRepository           # noqa: E402
from realify.repositories.seller_repo import SellerRepository           # noqa: E402
from realify.repositories.ad_performance_repo import AdPerformanceRepository       # noqa: E402
from realify.repositories.revenue_period_repo import RevenuePeriodRepository       # noqa: E402
from realify.repositories.provenance_repo import ProvenanceRepository             # noqa: E402
from realify.repositories.action_repo import ActionRepository           # noqa: E402
from realify.routers.cmaa import build_row_card                         # noqa: E402


def test_one_synth_sku_has_no_cogs_and_reads_as_needs_cogs():
    with db.connect() as con:
        tid = TenantRepository(con).create("Tester"); db.set_account_type(con, tid, "tester"); con.commit()
    scheduler.provision_own_data(tid, SyntheticSource(), log=lambda *a: None)

    with db.connect() as con:
        rows = SellerRepository(con).all(tid)
        null_cogs = [r for r in rows if r.get("cogs") is None]
        assert len(null_cogs) >= 1, "expected >=1 synth SKU with no COGS (QW-2)"
        r = null_cogs[0]
        card = build_row_card(r, "₹",
                              AdPerformanceRepository(con).totals(tid),
                              AdPerformanceRepository(con).all_by_sku(tid),
                              RevenuePeriodRepository(con).all_by_sku(tid),
                              RevenuePeriodRepository(con).units_by_sku(tid),
                              ProvenanceRepository(con).all_for_tenant(tid),
                              set(ActionRepository(con).acted_cmaa_skus(tid)))
    # cost-unknown SKU -> not judged, surfaced as the margin-unavailable "Needs COGS" state (not guessed)
    assert card is not None and card["quadrant"] == "Needs COGS" and card["judged"] is False


if __name__ == "__main__":
    test_one_synth_sku_has_no_cogs_and_reads_as_needs_cogs()
    print("margin_unavailable_trigger OK")
