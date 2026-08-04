"""A8 (the core trust test): a campaign that is HEALTHY overall but bleeding on ONE SKU must be flagged
at the SKU slice — never hidden by the campaign average. Exercises graph -> slice -> diagnosis."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_diag_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db                                                     # noqa: E402
from realify.repositories.ad_entity_repo import AdEntityPerfRepository     # noqa: E402
from realify.domain import ad_diagnosis, cmaa                              # noqa: E402
from realify.domain.ad_fidelity import CAMPAIGN_SKU                        # noqa: E402

BE = 0.35   # break-even ACoS for SKU-A


def test_campaign_healthy_overall_but_bleeding_on_sku_is_flagged():
    con = db.connect()
    tid = db.create_tenant(con, "t")
    ep = AdEntityPerfRepository(con)
    # Camp A advertises BOTH SKUs: it BLEEDS on SKU-A (800/300 = 267% ACoS) but WINS big on SKU-B
    # (200/4000 = 5% ACoS). Blended, Camp A is 1000/4300 = 23% ACoS -> healthy < 35% break-even.
    ep.upsert(tid, "Camp A", "AG1", "ASIN1", "SKU-A", "SKU-A", "2026-06-01", "month", 800, 300, 100, 5)
    ep.upsert(tid, "Camp A", "AG1", "ASIN2", "SKU-B", "SKU-B", "2026-06-01", "month", 200, 4000, 90, 60)
    con.commit()

    # sanity: Camp A's BLENDED ACoS is healthy — a campaign-average view would NOT flag it
    blended_acos = cmaa.acos(1000, 4300)
    assert blended_acos < BE, blended_acos

    # but the diagnosis for SKU-A works off the SKU SLICE (800/300), so Camp A IS flagged for SKU-A
    slices = ep.campaign_slices_for_sku(tid, "SKU-A")
    assert len(slices) == 1 and abs(slices[0]["spend"] - 800.0) < 0.01 and abs(slices[0]["sales"] - 300.0) < 0.01
    dg = ad_diagnosis.diagnose("SKU-A", BE, slices, {}, CAMPAIGN_SKU)
    assert [c["campaign"] for c in dg["offending_campaigns"]] == ["Camp A"]
    assert dg["offending_campaigns"][0]["acos_for_sku"] > BE           # evaluated on the slice
    assert dg["wasted_spend_total"] > 0

    # and SKU-B (the winner in the same campaign) is NOT flagged
    slices_b = ep.campaign_slices_for_sku(tid, "SKU-B")
    dg_b = ad_diagnosis.diagnose("SKU-B", BE, slices_b, {}, CAMPAIGN_SKU)
    assert dg_b["offending_campaigns"] == []
    con.close()


if __name__ == "__main__":
    test_campaign_healthy_overall_but_bleeding_on_sku_is_flagged()
    print("diagnosis_sku_slice OK")
