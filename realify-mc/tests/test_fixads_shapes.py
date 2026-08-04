"""ads_full deliberately contains the Fix-Ads shapes: D3 (campaign healthy overall, one SKU bleeding),
D6 (SKUs above AND below break-even), D5 (search terms on some campaigns not others), D4 (coverage <100 & >0)."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_shp_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, scheduler                                       # noqa: E402
from realify.ingest.synthetic import SyntheticSource                    # noqa: E402
from realify.repositories.tenant_repo import TenantRepository           # noqa: E402
from realify.repositories.seller_repo import SellerRepository           # noqa: E402
from realify.repositories.ad_entity_repo import AdIngestSummaryRepository  # noqa: E402


def _tester():
    with db.connect() as con:
        tid = TenantRepository(con).create("Tester"); db.set_account_type(con, tid, "tester"); con.commit()
    scheduler.provision_own_data(tid, SyntheticSource(), log=lambda *a: None)
    return tid


def _be_map(con, tid):
    out = {}
    for r in SellerRepository(con).all(tid):
        sku = r.get("internal_sku") or r.get("asin")
        p, c = r.get("price"), r.get("cogs")
        if p and c is not None:
            gc = p - c - (r.get("referral_fee") or 0) - (r.get("fba_fee") or 0)
            out[sku] = max(gc / p, 0.01)
    return out


def test_fixads_shapes_present():
    tid = _tester()
    with db.connect() as con:
        be = _be_map(con, tid)
        ent = [dict(r) for r in con.execute(
            "SELECT campaign, internal_sku, spend, sales FROM ad_entity_perf "
            "WHERE tenant_id=? AND internal_sku IS NOT NULL AND sales>0", (tid,))]
        st_camps = {r["campaign"] for r in con.execute(
            "SELECT DISTINCT campaign FROM ad_search_term WHERE tenant_id=?", (tid,))}
        ent_camps = {r["campaign"] for r in ent}
        summary = AdIngestSummaryRepository(con).get(tid)

    # D4 — coverage below 100 but not zeroed
    cov = summary["coverage_pct"]
    assert cov is not None and 0 < cov < 100, cov

    # D5 — search terms on SOME campaigns, absent for others (fidelity ladder resolves both)
    assert 0 < len(st_camps) < len(ent_camps), (len(st_camps), len(ent_camps))

    # D6 — at the entity grain, some slices above and some below the SKU's break-even ACoS
    acos = [(r["spend"] / r["sales"], be.get(r["internal_sku"])) for r in ent if be.get(r["internal_sku"])]
    assert any(a > b for a, b in acos) and any(a < b for a, b in acos), "need mix above/below break-even"

    # D3 — a shared campaign healthy overall (blended below break-even) but one SKU slice well above it
    core = [r for r in ent if r["campaign"].startswith("SP Manual")]
    assert len(core) >= 2
    blended = sum(r["spend"] for r in core) / sum(r["sales"] for r in core)
    slice_acos = {r["internal_sku"]: r["spend"] / r["sales"] for r in core}
    core_be = min(be[s] for s in slice_acos if s in be)
    assert blended < core_be, (blended, core_be)                        # healthy overall
    assert max(slice_acos.values()) > core_be, slice_acos               # yet one slice bleeds


if __name__ == "__main__":
    test_fixads_shapes_present()
    print("fixads_shapes OK")
