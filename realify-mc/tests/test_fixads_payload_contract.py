"""Fix Ads row-pattern DATA contract (spec §6): action_class split + Apply count, the ads Simulate
projection behind the deterministic project() contract, per-SKU fidelity, and no live Amazon write."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_fapl_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.domain import ad_diagnosis as D, ad_recommend as R, ad_levers as LV   # noqa: E402
from realify.domain.ad_fidelity import KEYWORD, CAMPAIGN_SKU                        # noqa: E402
from realify.routers import ads                                                     # noqa: E402

_SLICES = [{"campaign": "Campaign A", "ad_group": "AG1", "spend": 800.0, "sales": 300.0, "orders": 5},
           {"campaign": "Campaign B", "ad_group": "AG2", "spend": 400.0, "sales": 250.0, "orders": 3}]
_TERMS = {("Campaign A", "AG1"): [{"customer_search_term": "car perfume", "targeting": "t",
                                   "match_type": "BROAD", "spend": 250.0, "sales": 0.0, "orders": 0.0}]}


def _rec(fidelity, terms):
    dg = D.diagnose("SKU-CAF-11", 0.25, _SLICES, terms, fidelity)
    return R.build("SKU-CAF-11", {"cmaa_now": -1240.0, "monthly_loss": 1240.0, "title": "Cabin Air Filter"},
                   dg, fidelity, 92.0)


def test_action_class_split_and_apply_count():
    rec = _rec(KEYWORD, _TERMS)
    actionable = [a for a in rec["actions"] if a["action_class"] == LV.REALIFY_ACTIONABLE]
    advisory = [a for a in rec["actions"] if a["action_class"] == LV.ADVISORY_ONLY]
    assert actionable and rec["actionable_count"] == len(actionable)     # Apply counts ONLY actionable
    # actionable levers are the three; advisory levers never leak into the actionable set
    assert all(a["lever_id"] in LV.ACTIONABLE_LEVERS for a in actionable)
    assert all(a["lever_id"] not in LV.ACTIONABLE_LEVERS for a in advisory)


def test_fidelity_per_sku_hides_negative_at_campaign_level():
    kw = _rec(KEYWORD, _TERMS)
    cl = _rec(CAMPAIGN_SKU, {})
    assert kw["has_search_terms"] is True and kw["fidelity_label"] == "keyword-level"
    assert "NEGATIVE_KEYWORD" in [a["lever_id"] for a in kw["actions"]]
    assert cl["has_search_terms"] is False and cl["fidelity_label"] == "campaign-level"
    assert "NEGATIVE_KEYWORD" not in [a["lever_id"] for a in cl["actions"]]   # hidden at campaign-level


def test_simulate_projection_contract():
    rec = _rec(KEYWORD, _TERMS)
    sim = rec["simulate"]
    assert [h["days"] for h in sim["horizons"]] == [30, 60, 90]          # the 30/60/90 horizons
    assert all("delta" in h and "prob" in h for h in sim["horizons"])
    assert sim["tripwire"] and "revert" in sim["tripwire"]
    # deterministic (same inputs -> same projection) and honest-empty (nothing recoverable -> None)
    assert R._projection(1000, 90, "KEYWORD") == R._projection(1000, 90, "KEYWORD")
    assert R._projection(0, 90, "KEYWORD") is None and R._projection(None, 90, "KEYWORD") is None


def test_no_live_amazon_write():
    # the ads router exposes NO write endpoint; Apply degrades to instruction/export (spec §5)
    methods = set()
    for r in ads.router.routes:
        methods |= set(getattr(r, "methods", set()) or set())
    assert "POST" not in methods and "PUT" not in methods and "DELETE" not in methods, methods
    # the client-side Apply/Preview/Export path calls no network write (instruction/export only)
    html = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend.html"), encoding="utf-8").read()
    re = __import__("re")
    for fn in ("_famExport", "_famPreview", "_famApply"):
        m = re.search(r"function " + fn + r"\(.*?\n\}", html, re.S)
        assert m, f"{fn} missing"
        assert "fetch(" not in m.group(0), f"{fn} must not call the network (no live write)"


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("fixads_payload_contract OK")
