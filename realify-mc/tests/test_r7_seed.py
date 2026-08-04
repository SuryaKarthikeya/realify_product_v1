"""R7 (hermetic): the pilot seed manifest loads CONNECTED by default with exactly 1-2 deliberately
expired brands (Part 1a), and the decision rules produce a realistic multi-lens spread with varied
confidence (Part 1b). Pure-data / pure-function — no DB. The Postgres seed/queue/admin behavior lives
in tests/agency/test_r7.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.agency.sandbox_scenarios import us_pilot, in_pilot   # noqa: E402  (R9: mixed pilot retired)
from realify.agency import decisions                        # noqa: E402


def test_pilots_connected_default_with_1_2_expired():
    # R9: two single-country pilots (US = 8 USD, India = 8 INR); each loads CONNECTED with exactly 2
    # deliberately-expired brands to demo the paused state (not all 8).
    assert len(us_pilot.SPEC["brands"]) == 8 and all(b["currency"] == "USD" for b in us_pilot.SPEC["brands"])
    assert len(in_pilot.SPEC["brands"]) == 8 and all(b["currency"] == "INR" for b in in_pilot.SPEC["brands"])
    for spec in (us_pilot.SPEC, in_pilot.SPEC):
        expired = [b for b in spec["brands"] if b.get("expired_conn")]
        assert 1 <= len(expired) <= 2, "exactly 1-2 brands demo the expired/paused state — not all 8"
        # the scenario default connections are all CONNECTED (a connected world is the default)
        assert all(state == "connected" for _p, state in spec["connections"])


def test_decision_rules_spread_and_positive_impacts():
    # a SKU that trips all three rules (low cover, high ACoS, undercut buy-box) — R9.1 makes
    # pricing selective (fires on an undercut buy-box < 75)
    out = decisions._rules("SB-000", price=2499, cogs=900, units=120,
                           days_of_cover=8, tacos=34, buybox=65)
    lenses = {lens for lens, _k, _s, _imp, _c in out}
    assert lenses == {"inventory", "ads", "pricing"}          # all three action types
    assert all(imp > 0 for _l, _k, _s, imp, _c in out)        # positive $-impacts
    confs = [c for _l, _k, _s, _imp, c in out]
    assert len(set(confs)) >= 2 and all(35 <= c <= 97 for c in confs)   # varied, bounded confidence


def test_confidence_jitter_is_deterministic():
    a = decisions._jitter("SB-007", "ads", 72)
    b = decisions._jitter("SB-007", "ads", 72)
    assert a == b                                             # stable hash → byte-identical run to run
    # different SKUs generally differ (not one flat value)
    vals = {decisions._jitter(f"SB-{i:03d}", "ads", 72) for i in range(12)}
    assert len(vals) >= 3
