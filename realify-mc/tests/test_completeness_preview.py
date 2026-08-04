"""Goal completeness (spec §7/§9/§12): the blocks mapping per goal; the worked §9 example (FBA +
Shopify(MCF) + SP-only + COGS-in-Shopify + Meta, goal=profit-after-ads) is PARTIAL for the right
reasons; a hard missing input → UNAVAILABLE; CATEGORY_INTEL is never blocked by a financial flag."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import nodegraph as ng  # noqa: E402
from realify.pipeline import completeness as C  # noqa: E402
from realify.topology_model import (PROFIT_AFTER_ADS, AD_EFFICIENCY, CATEGORY_INTEL, EVERYTHING)  # noqa: E402


def _worked_example(cogs="In Shopify", ads=("Meta",)):
    topo, emitted = ng.resolve_answers({"CHANNELS": ["Amazon", "Shopify"], "A1": "FBA", "S1": ["MCF"],
                                        "S3": "Shopify Payments only", "C1": cogs, "AD1": list(ads),
                                        "G1": "Profit after ads"})
    return topo, emitted


def test_profit_after_ads_partial_for_mcf_and_pending_ad():
    topo, emitted = _worked_example()
    comp = C.compute(topo, emitted, received=set())
    e = comp[PROFIT_AFTER_ADS]
    assert e["state"] == C.PARTIAL
    joined = " ".join(e["reasons"]).lower()
    assert "mcf" in joined and ("meta" in joined or "ad" in joined)     # MCF fee + Meta ad pending
    line = C.preview_line(PROFIT_AFTER_ADS, comp)
    assert "unlocks once we have" in line and "MCF" in line


def test_category_intel_not_blocked_by_financial_flags():
    topo, emitted = _worked_example()
    comp = C.compute(topo, emitted, received=set())
    # category intel is light — armed financial flags don't block it (leans on out-of-scope competitive data)
    assert comp[CATEGORY_INTEL]["state"] in (C.AVAILABLE, C.PARTIAL)
    assert not any("mcf" in r.lower() for r in comp[CATEGORY_INTEL]["reasons"])


def test_missing_cogs_makes_profit_unavailable():
    topo, emitted = _worked_example(cogs="Not yet")     # arms MARGIN_UNAVAILABLE (hard input absent)
    comp = C.compute(topo, emitted, received=set())
    assert comp[PROFIT_AFTER_ADS]["state"] == C.UNAVAILABLE
    assert comp[EVERYTHING]["state"] == C.UNAVAILABLE
    assert "can't be computed" in C.preview_line(PROFIT_AFTER_ADS, comp)


def test_no_ads_makes_ad_efficiency_unavailable():
    topo, emitted = _worked_example(ads=("None yet",))   # arms AD_SPEND_ABSENT
    comp = C.compute(topo, emitted, received=set())
    assert comp[AD_EFFICIENCY]["state"] == C.UNAVAILABLE


def test_all_essentials_received_and_no_flags_is_available():
    topo, emitted = ng.resolve_answers({"CHANNELS": ["Amazon"], "A1": "FBM", "C1": "In Shopify",
                                        "AD1": ["Amazon Ads"], "G1": "Profit after ads"})
    comp = C.compute(topo, emitted, received=set(emitted))   # everything received, no armed flags
    assert comp[PROFIT_AFTER_ADS]["state"] == C.AVAILABLE
    assert "ready" in C.preview_line(PROFIT_AFTER_ADS, comp)


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("completeness_preview OK")
