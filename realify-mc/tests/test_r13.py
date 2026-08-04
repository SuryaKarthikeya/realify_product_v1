"""R13 (hermetic): the seller five-lens app (frontend.html) is re-tokenized to the warm design system
(matches docs/mockups/realify-interior-reskin.html + tokens.py) — warm :root, Georgia headings,
terracotta accent, warm semantic tints, charcoal BRIEF panel — WITHOUT breaking the R11.1/R11.2
behaviors that sit on top (SKU-panel offset, locale inheritance, demo-card localizer, guided-bar stacking)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FE = open(os.path.join(_REPO, "frontend.html")).read()
_BACKBAR = open(os.path.join(_REPO, "realify", "site", "backbar.py")).read()


# ---------------- warm palette + typography ----------------

def test_root_is_warm():
    for tok in ("--paper:#F7F4EE", "--ink:#1A1A1A", "--line:#E4DDD0", "--muted:#6E675C",
                "--action:#C4785B", "--accent-border:#C4785B", "--serif:Georgia"):
        assert tok in _FE, f"warm token missing: {tok}"


def test_no_cool_residue():
    for cool in ("#15233B", "#1E5FA8", "#0E7C66", "#EDEFF3", "#1c2f4f", "#243a5e"):
        assert cool not in _FE and cool.lower() not in _FE, f"cool value still present: {cool}"


def test_headings_georgia_not_grotesk():
    assert "Space Grotesk" not in _FE                       # heading display font swapped out
    assert "Space+Grotesk" not in _FE                       # ...and dropped from the web-font load
    assert _FE.count("Georgia") >= 20                       # headings now serif


def test_accent_terracotta_on_active_tab():
    assert ".surftab.on{color:var(--ink);border-color:var(--line);border-bottom:2px solid var(--action)" in _FE


# ---------------- semantic tint cards + BRIEF panel kept, re-tuned ----------------

def test_profit_ads_tint_cards_warm():
    # the four action buckets are KEPT but re-tuned to the mockup's warm tints
    assert "'SCALE':'#EDF3EC'" in _FE and "'FIX ADS':'#F8EFD9'" in _FE
    assert "'FIX MARGIN':'#F6E9E2'" in _FE and "'CUT/DIVEST':'#F3E0DC'" in _FE


def test_brief_panel_charcoal():
    # the dark "THE BRIEF" hero is KEPT but warmed navy → charcoal, with a terracotta kicker + Georgia
    assert "linear-gradient(180deg,#1A1A1A,#2A2620)" in _FE   # charcoal, not navy
    assert "color:#C4785B" in _FE                            # kicker terracotta (an-hero-k)


def test_health_dots_and_sku_link_semantic():
    # health bands stay semantic on the warm family; SKU link is terracotta via --action-adjacent tokens
    assert "--positive:#3F6B45" in _FE and "--critical:#B3402E" in _FE and "--warn:#B98A2E" in _FE


# ---------------- R11.1 / R11.2 preserved (regression guard) ----------------

def test_r111_r112_intact():
    # locale inheritance (CUR-aware money) + demo-card localizer
    assert "function _cur(v)" in _FE and "function _locd(s){" in _FE
    assert "function catINR(v){ return (v==null||v==='')?'—':_cur(Math.round(v)); }" in _FE
    # SKU detail panel top-offset for the bars (✕ stays clickable)
    assert "#r9backbar~.drawer{top:40px" in _BACKBAR
    # guided-run bar stacking offset
    assert "body.has-guided #r9backbar~.drawer{top:80px" in _BACKBAR
    # the real logo (R11.1) stays in the app nav
    assert 'src="/assets/Final-logo-full-Dark-V3.png"' in _FE
