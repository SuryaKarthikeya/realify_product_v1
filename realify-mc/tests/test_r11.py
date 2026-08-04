"""R11 (hermetic): the fleet-grid renderer (h7), the scope-switcher drill-in renderer (h8) with
envelope-driven lens locking, the shared hubkit component sheet, the env-drift boot guard, the
scheduler null-guard, and the hub Data-step re-open. Postgres behaviors (data resolution, $-at-stake,
server-side envelope enforcement, queue redirect) live in tests/agency/test_r11.py."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.site import hubkit, fleet, brandscope, hub          # noqa: E402
from realify import dbengine                                     # noqa: E402
from realify.pipeline import primitives                          # noqa: E402
from realify.pdp import ENVELOPES                                # noqa: E402


# ---------------- fleet grid (h7) ----------------

def _cards():
    return [
        {"tenant_id": 1, "name": "Suncrest Outdoors", "health": "sage", "am_name": "Jake T.",
         "owner_name": "Jake T.", "top_signal": "6 stockout risks", "top_action": "Reorder before stockout",
         "money_line": "$1.2M GMV · TACoS 9% · 12 open", "stake_usd": 251000.0,
         "stake_display": "$251,000", "symbol": "$", "paused": False},
        {"tenant_id": 2, "name": "Corva Audio", "health": "terra", "am_name": "Emily C.",
         "owner_name": "Emily C.", "top_signal": "connection expired", "top_action": "Fix connection",
         "money_line": "stale · 0 actionable", "stake_usd": 0.0,
         "stake_display": "$0", "symbol": "$", "paused": True},
    ]


def test_fleet_grid_renders_h7():
    class _R:  # minimal request stub — backbar reads .session
        session = {}
    html = fleet.fleet_html(_R(), "BrightPeak Commerce", _cards(), "all", 5, 8)
    assert "Fleet" in html and "2 brands · 1 need attention" in html      # header + at-risk count
    assert "hb-sage" in html and "hb-terra" in html                       # health bands (left edge)
    assert "at stake" in html and "$251,000 at stake" in html            # $-at-stake per brand (load-bearing)
    assert "My book (5)" in html and "All accounts (8)" in html          # book filter chips
    assert "/agency/brand/1" in html                                     # card links into the drill-in
    assert "Suncrest Outdoors" in html                                   # real brand name


# ---------------- scope-switcher drill-in (h8) ----------------

def test_drilldown_locks_pricing_under_ex_pricing():
    caps = {l: dict(c) for l, c in ENVELOPES["Operate ex-Pricing"].items()}
    items = [
        {"tenant_id": 1, "lens": "ads", "kind": "bid", "signal": "acos_high", "confidence": 88,
         "impact_currency": "USD", "rank_usd_minor": 120000, "display": "$1,200"},
        {"tenant_id": 1, "lens": "pricing", "kind": "price", "signal": "undercut", "confidence": 76,
         "impact_currency": "USD", "rank_usd_minor": 90000, "display": "$900"},
    ]
    sibs = [{"id": 1, "name": "Suncrest"}, {"id": 2, "name": "Meridian"}]
    class _R:
        session = {}
    html = brandscope.brandscope_html(_R(), "Suncrest", 1, "BrightPeak", "Operate ex-Pricing",
                                      caps, items, sibs)
    assert "Portfolio ▸" in html and "switch brand" in html             # scope bar + brand picker
    assert "Pricing 🔒 read-only" in html                               # pricing lens locked in the tabs
    assert "Product Catalog" in html and "Category Analyst" in html      # the five UX lenses
    # ads (executable under ex-Pricing) -> Approve; pricing (read-only) -> Propose, never Approve button
    assert ">Approve<" in html                                          # ads decision is executable
    assert "Propose to brand" in html                                   # pricing decision is suggest-only
    assert "/agency/brand/2" in html                                    # sibling in the ▾ picker


def test_drilldown_full_operate_all_executable():
    caps = {l: dict(c) for l, c in ENVELOPES["Full Operate"].items()}
    items = [{"tenant_id": 1, "lens": "pricing", "kind": "price", "signal": "x", "confidence": 70,
              "impact_currency": "USD", "rank_usd_minor": 5000, "display": "$50"}]
    class _R:
        session = {}
    html = brandscope.brandscope_html(_R(), "B", 1, "Ag", "Full Operate", caps, items, [{"id": 1, "name": "B"}])
    assert "🔒 read-only" not in html and ">Approve<" in html           # nothing locked; pricing executes


# ---------------- shared component sheet ----------------

def test_hubkit_component_sheet():
    assert ".frame" in hubkit.CSS and ".role" in hubkit.CSS and ".sandbar" in hubkit.CSS
    assert ".fleet" in hubkit.AGENCY_CSS and "hb-terra" in hubkit.AGENCY_CSS   # fleet additions
    assert "--terra:#C4785B" in hubkit.CSS                              # warm palette matches tokens


# ---------------- hub Data-step re-open (Part E-b) ----------------

def test_hub_change_world_reopens_data_step():
    h = hub.hub_html("staff@realify.ai")
    # R14 renamed reopenData → changeWorld (now clears the grant + re-locks Role before unlocking Data)
    assert "function changeWorld()" in h and "↻ Change world" in h
    assert "_setDataLocked(false)" in h                                 # Change world unlocks the Data step


# ---------------- env-drift guard (Part E-c) ----------------

def test_env_drift_aborts_on_missing_mail_driver(monkeypatch):
    monkeypatch.setenv("AGENCY_CONSOLE", "on")                          # prod/agency mode
    monkeypatch.delenv("MAIL_DRIVER", raising=False)
    with pytest.raises(SystemExit) as ei:
        dbengine.assert_prod_env()
    assert "MAIL_DRIVER" in str(ei.value) and "Refusing to start" in str(ei.value)


def test_env_drift_warns_on_missing_addressing(monkeypatch):
    monkeypatch.setenv("AGENCY_CONSOLE", "on")
    monkeypatch.setenv("MAIL_DRIVER", "ses")
    monkeypatch.delenv("EMAIL_DOMAIN", raising=False)
    monkeypatch.delenv("REPLY_TO_ADDRESS", raising=False)
    warnings = []
    dbengine.assert_prod_env(warn=warnings.append)                      # must NOT abort (defaults exist)
    assert any("EMAIL_DOMAIN" in w for w in warnings) and any("REPLY_TO_ADDRESS" in w for w in warnings)


def test_env_drift_noop_in_dev(monkeypatch):
    monkeypatch.delenv("AGENCY_CONSOLE", raising=False)
    monkeypatch.delenv("REQUIRE_POSTGRES", raising=False)
    monkeypatch.delenv("MAIL_DRIVER", raising=False)
    dbengine.assert_prod_env()                                          # dev/test: no abort, no requirement


def test_env_example_captures_prod_vars():
    txt = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.example")).read()
    for v in ("MAIL_DRIVER=ses", "EMAIL_DOMAIN=realifyai.app", "REPLY_TO_ADDRESS", "AGENCY_CONSOLE=on"):
        assert v in txt, f"{v} must be documented in .env.example (drift-restore guidance)"


# ---------------- scheduler null-guard (Part E-a) ----------------

def test_primitives_null_guarded():
    assert primitives.ratio_vs_baseline(None, 5, 2.0) is False         # None numerator (the tenant-121 crash)
    assert primitives.pop_pct(None, 10) == 0.0
    assert primitives.zscore(None, 1, 2) == 0.0
    assert primitives.ratio_vs_baseline(10, 5, 1.5) is True            # real inputs still compute
