"""R15.2 hermetic — fleet card renders the localized $-at-stake (never a hardcoded "$") and the
per-brand owner. Grep-locks the fleet template against the old hardcoded-dollar render.
"""
import os
from realify.site import fleet

_SRC = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "realify", "site", "fleet.py"), encoding="utf-8").read()


class _Req:
    session = {}


def test_fleet_template_has_no_hardcoded_dollar_stake():
    assert "'{:,.0f}'.format(c['stake_usd'])" not in _SRC     # old hardcoded "$"+stake_usd render gone
    assert "c.get(\"stake_display\")" in _SRC                  # uses the localized $-at-stake
    assert "owner_name" in _SRC                                # Part C — per-brand owner shown


def test_fleet_card_renders_localized_stake_and_owner():
    cards = [{"tenant_id": 1, "name": "ShieldFit Auto", "health": "sage", "am_name": "AM One",
              "owner_name": "Priya Sharma", "top_signal": "s", "top_action": "a",
              "money_line": "₹1.2cr GMV · TACoS 17% · 3 open", "stake_usd": 500.0,
              "stake_display": "₹40,000", "symbol": "₹", "paused": False, "currency": "INR"}]
    html = fleet.fleet_html(_Req(), "Deccan Traders", cards, "all", 1, 1)
    assert "₹40,000 at stake" in html                          # localized $-at-stake (₹), not "$500 at stake"
    assert "$500 at stake" not in html and "$40,000" not in html
    assert "Deccan Traders" in html and "Priya Sharma" in html


if __name__ == "__main__":
    test_fleet_template_has_no_hardcoded_dollar_stake()
    test_fleet_card_renders_localized_stake_and_owner()
    print("R15.2 fleet hermetic tests passed")
