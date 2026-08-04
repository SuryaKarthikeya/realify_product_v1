"""Fix 3 (upstream durable): the shared L1 card pipeline must phrase 'below floor' ONLY for a
genuine margin breach (op='lt'). A high-margin opportunity (net_margin_pct op='gt') must read
"above", never "under/below your floor" — on Feed / Profit & Ads / Analyst alike.
"""
from realify.pipeline import interpret, generate


def _sig(op, value, thr=30.0):
    return {"card_type": "MARGIN-X", "family": "buybox", "type_name": "Margin", "rule": True,
            "asin": "AS1", "category": "Auto", "title": "Storm Cover", "exposure_inr": 120000,
            "nums": {"field": "net_margin_pct", "value": value, "op": op, "threshold": thr, "label": "Margin"}}


def test_detector_routing_splits_gt_from_below_floor():
    assert interpret.detector_for(_sig("lt", 8.0))[0] == "margin-vs-floor"      # genuine breach
    assert interpret.detector_for(_sig("gt", 48.7))[0] == "margin-headroom"     # high-margin opportunity


def test_gt_margin_is_never_phrased_below_floor():
    """A 48.7% margin firing a gt-30 opportunity rule must NOT read as under the floor."""
    finding, _why, _minis = generate._fallback(_sig("gt", 48.7))
    low = finding.lower()
    assert "above" in low, finding
    assert "under the" not in low and "below your" not in low and "beneath" not in low, finding


def test_lt_margin_still_fires_below_floor():
    finding, _why, _minis = generate._fallback(_sig("lt", 8.0))
    low = finding.lower()
    assert "below" in low or "under" in low, finding


if __name__ == "__main__":
    test_detector_routing_splits_gt_from_below_floor()
    test_gt_margin_is_never_phrased_below_floor()
    test_lt_margin_still_fires_below_floor()
    print("margin floor phrasing OK")
