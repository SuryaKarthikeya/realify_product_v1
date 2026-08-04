"""Dynamic headline: deterministic phrasing branches + empty-tenant compute (no L2 key in tests)."""
import os, sys, tempfile

import pytest

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_hl_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, headline, config               # noqa: E402
from realify.repositories.tenant_repo import TenantRepository  # noqa: E402


def test_deterministic_branches():
    urgent = headline._deterministic(
        {"surface": "intelligence", "count": 5, "new": 2, "urgent": 3,
         "by_family": {"pricing": 2, "inventory": 1}, "top": {"finding": "Buy Box lost on 2 SKUs"}})
    assert urgent.startswith("3 actions need attention now") and "Buy Box" in urgent and "pricing" in urgent

    new = headline._deterministic(
        {"surface": "research", "count": 4, "new": 4, "urgent": 0,
         "by_family": {"opportunity": 4}, "top": {"finding": "New niche cleared threshold"}})
    assert new.startswith("4 new since yesterday")

    empty = headline._deterministic({"surface": "intelligence", "count": 0, "new": 0, "urgent": 0,
                                     "by_family": {}, "top": None})
    assert "all clear" in empty

    nolead = headline._deterministic({"surface": "research", "count": 3, "new": 0, "urgent": 0,
                                      "by_family": {}, "top": None})
    assert "3 market signals" in nolead


@pytest.mark.skipif(
    bool(config.ANTHROPIC_API_KEY),
    reason="asserts the no-L2-key deterministic path (l2 is False); an ANTHROPIC_API_KEY is configured "
           "in this environment, so L2 phrasing is live. The ONLY allowed skip per agency-plan §1c(6) "
           "(allowed_skips: ['test_headline']).")
def test_compute_empty_tenant_is_deterministic_without_key():
    con = db.connect()
    tid = TenantRepository(con).create("hl test")
    con.commit(); con.close()
    r = headline.compute(tid)                  # no cards; no ANTHROPIC_API_KEY in tests
    assert r["ok"] and r["l2"] is False and "all clear" in r["headline"]
    assert r["detail"] == ""                    # empty tenant -> no standfirst


def test_detail_standfirst_from_findings_and_counts():
    f = {"surface": "intelligence", "count": 12, "new": 2, "urgent": 3, "opportunities": 1,
         "by_family": {"moto": 7, "tools": 5},
         "top3": [{"finding": "Competitor undercut $2.10 on the all-weather liner"},
                  {"finding": "Cover-days on one tools SKU fell under 14"},
                  {"finding": "Two listings newly Buy-Box-eligible"}]}
    d = headline._detail(f)
    # supporting findings (cards 2 and 3, not the lead) + the counts tail
    assert "Cover-days on one tools SKU fell under 14" in d
    assert "Two listings newly Buy-Box-eligible" in d
    assert "2 new since yesterday" in d and "12 insights ranked by revenue exposure" in d
    assert headline._detail({"surface": "intelligence", "count": 0}) == ""


if __name__ == "__main__":
    test_deterministic_branches()
    print("headline deterministic OK")
