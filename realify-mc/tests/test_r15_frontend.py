"""R15 frontend (static grep-lock on the server-rendered SPA `frontend.html`):
 · Part E.1  — "Refresh market data" is tester-only (gated by the isTester predicate)
 · Part E.10 — "Wipe & re-onboard" is tester-only and lands on the /superlogin hub
 · Part E.11 — the "Workspace ready · Market feeds" banner is gone from the header
 · Part I    — the 5-lens header shows dynamic identity (greeting + brand-first ident from /api/me + /api/scope)
 · Part J    — Intelligence metric filters are MULTI-select (UNION), default Revenue, warm slate ring
The SPA is a single static file, so behavior is asserted against its source (the repo's convention).
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8") as _f:
    SRC = _f.read()


def test_e1_refresh_market_is_tester_only():
    assert "const isTester =" in SRC
    assert "getElementById('marketBox').style.display = isTester" in SRC


def test_e10_wipe_is_tester_only_and_lands_on_hub():
    assert "getElementById('wipeBox').style.display = isTester" in SRC
    # the SPA must NOT embed the /superlogin backdoor path (security); the server returns the hub target.
    assert "superlogin" not in SRC
    assert "location.href = (r && r.redirect)" in SRC
    wipe = open(os.path.join(_ROOT, "realify", "routers", "onboarding.py"), encoding="utf-8").read()
    assert '"redirect": "/superlogin/hub"' in wipe        # tester wipe → hub, server-decided


def test_e11_workspace_ready_banner_removed_from_header():
    assert 'class="statusbar"' not in SRC                  # the header banner markup is gone
    assert ">Checking workspace…<" not in SRC
    assert "Workspace ready ✓" not in SRC                  # the literal readiness text no longer renders in-header


def test_i_header_identity_is_dynamic():
    assert 'id="mastGreet"' in SRC and 'id="mastIdent"' in SRC
    assert "Good morning, Shiva" not in SRC                # no longer hardcoded
    assert "/api/scope" in SRC and "_renderIdentity" in SRC


def test_j_intelligence_filters_multiselect_union_default_revenue():
    assert "new Set(['revenue'])" in SRC                   # default = Revenue only
    assert "selectedKpis.add(key)" in SRC and "selectedKpis.delete(key)" in SRC   # toggle, not replace
    assert "if(selectedKpis.size===0) selectedKpis.add('revenue')" in SRC          # clear-all → Revenue
    # feed unions the selected metrics' groups (multi-select honored downstream)
    assert "selectedKpis.forEach(k=>(KPI_GROUPS[k]||[]).forEach(g=>allowed.add(g)))" in SRC
    # warm slate selection ring (not leftover indigo)
    assert ".kpi-card.sel{border-color:var(--competitive)" in SRC


if __name__ == "__main__":
    for _n, _fn in list(globals().items()):
        if _n.startswith("test_") and callable(_fn):
            _fn()
    print("R15 frontend grep-lock tests passed")
