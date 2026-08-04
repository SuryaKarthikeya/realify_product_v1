"""Acceptance tests for the Fix-Ads modal-per-SKU rebuild (spec §8).

Covers: the worklist reworked to summary-only rows that open a modal (catalog table / inline-expand gone),
keyboard-wired cohort tabs that filter the list, the modal's structure (header/metrics/fidelity/expl-toggle,
per-recommendation actionable cards each with its own Apply/Preview/Open/Why + Simulate, advisory cards with
NO Apply, footer projected-if-all + Export + Apply-all + guardrails), in-modal Preview with no native popup,
explainability mirroring the tenant flag, interactive Re-simulate through the project() seam, and the
GET-only no-live-write invariant. Frontend structure is asserted against frontend.html; the projection
math is asserted against domain/ad_simulate.
"""
import os
import re
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_fmv3_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.domain import ad_simulate as AS                      # noqa: E402
from realify.routers import ads                                    # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HTML = open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8").read()


def _fn(name):
    """Return the source of a JS function `name` (up to its top-level closing brace heuristic)."""
    m = re.search(r"function " + re.escape(name) + r"\(.*?\n\}", _HTML, re.S)
    assert m, f"{name} not found in frontend.html"
    return m.group(0)


# ---- §1: catalog table removed / rows summary-only ----
def test_catalog_table_and_inline_expand_removed():
    # the worklist no longer renders an inline per-row detail expander
    assert "cm-detail" not in _HTML, "inline-expand worklist detail must be removed (folded into the modal)"
    assert 'data-for="${ix}"' not in _HTML, "the inline expander (data-for) must be gone"
    # the recommendation body (_cmRec, with its action buttons) is now shown inside the modal, not inline
    assert "_cmRec(rec,k)" in _fn("_cmBasicModal")
    # the per-SKU catalog table lives in the Catalog view, not Profit & Ads
    assert "cat-tbl" in _HTML and "paintCatalog" in _HTML


def test_portfolio_band_above_list():
    # a band above the list: cohort label · N SKUs · recoverable/value total
    assert "cmaaSecHead" in _HTML
    band = _HTML[_HTML.index("portfolio band"):]
    assert "SKU${rows.length==1?'':'s'}" in band and "bandTot" in band


def test_rows_are_summary_only_and_open_modal():
    # the worklist row carries only the SKU/sub, and full-row click/keyboard opens the modal
    assert "cm-cardrow" in _HTML
    assert "_famOpenSku(k.sku)" in _HTML and "_cmBasicModal(k)" in _HTML
    # row is a real button: role + tabindex + Enter/Space handler
    assert 'role="button" tabindex="0"' in _HTML
    assert "e.key==='Enter'||e.key===' '" in _HTML


# ---- §1: cohort tabs are real, keyboard-focusable, wired ----
def test_cohort_tabs_keyboard_and_wired():
    quad = _fn("_cmBindQuad")
    assert "'role','tablist'" in _HTML and 'role="tab"' in _HTML
    assert 'aria-selected' in _HTML and 'tabindex="${sel?0:-1}"' in _HTML
    assert "ArrowRight" in quad and "ArrowLeft" in quad          # arrow-key navigation
    assert "_cmBucket=el.dataset.bucket" in quad and "_cmPaint()" in quad
    # _cmPaint actually filters the list by the active bucket
    assert "k.quadrant===_cmBucket" in _HTML


# ---- §2: modal structure ----
def test_modal_structure():
    op = (_fn("_famOpen") + _fn("_famContentHtml"))
    assert "Recommendations — each acts on its own" in op          # actionable section
    assert "Advisory — you do this yourself" in op                 # advisory section
    assert "Projected if all applied" in op                        # footer projection
    assert "Explainability" in op and "fam-explOn" in op           # top-right expl toggle
    assert "Fidelity:" in op and "fam-pill" in op                  # fidelity pill
    assert "aria-modal" in op                                       # centered dialog
    # scrim-click + Esc + ✕ all close
    assert "if(e.target===_famScrim) _famClose()" in op
    assert "e.key==='Escape'" in _fn("_famEsc")


def test_per_recommendation_actions_and_advisory_no_apply():
    card = _fn("_famActCard")
    # each actionable card acts on its own: Apply / Preview / Open in Amazon (gated helper) / Why (+ Simulate)
    assert "Apply this change" in card and "Preview" in card
    assert "_famAmazonBtn(a" in card and ">Why<" in card
    assert "Open in Amazon" in _fn("_famAmazonBtn")
    assert "_famToggleSim" in card or "fam-simbox" in card
    # advisory cards (built in _famOpen) offer How to + Open, never Apply. Scope to the advisory card
    # template only (between the 'fam-card adv' block and the in-modal preview panel that follows it).
    op = (_fn("_famOpen") + _fn("_famContentHtml"))
    # advisory block spans from the how-to construction (const how=) through the advisory card render
    adv = op[op.index("const how="):op.index("fam-preview")]
    assert "How to" in adv and "_famAmazonBtn(a" in adv
    assert "Apply" not in adv, "advisory cards must never carry an Apply control"


def test_footer_has_apply_all_export_guardrails():
    op = (_fn("_famOpen") + _fn("_famContentHtml"))
    assert "Apply all" in op and ">Export<" in op
    assert "Guardrails:" in op


def test_inline_campaign_detail_restored():
    # R20: the always-visible inline campaign list is restored into the ads tab (it was folded into the
    # modal only by 032bbb6). It renders into #cmaaRecs and REUSES the modal's shared _famContentHtml, so
    # campaign detail + interactive Simulate + ƒ show inline — one source of truth with the modal.
    ra = _fn("renderAdRecs")
    assert "cmaaRecs" in ra and "fam-inline" in ra and "_faiToggle(" in ra      # inline expandable rows
    assert "ad-cta" in ra                                                       # real-customer upload CTA
    assert "_famContentHtml(_faRecs[i])" in _fn("_faiToggle")                    # inline reuses shared detail
    assert "_famContentHtml(rec)" in _fn("_famOpen")                            # modal reuses the same builder
    assert ".fam-inline.expl .fx" in _HTML                                      # ƒ gated inline too


# ---- §3: preview renders in-modal, no native popup ----
def test_preview_no_popup():
    for fn in ("_famPreview", "_famApply", "_famExport", "_famResim"):
        src = _fn(fn)
        for banned in ("window.open", "alert(", "confirm(", "prompt("):
            assert banned not in src, f"{fn} must not use {banned} (in-modal only)"
    assert "fam-preview" in _fn("_famPreview")                     # renders into the in-modal panel


# ---- §4: explainability mirrors the tenant flag ----
def test_explainability_mirrors_tenant_flag():
    assert "_famExplOn=explainMode" in _HTML                        # modal mirrors /api/settings/app explain_mode
    assert ".fam-modal.expl .fx" in _HTML                          # ƒ tags gated on the modal expl class
    assert "onchange=\"_famSetExpl(this.checked)\"" in _HTML
    # every ƒ tag carries a data-fx formula_id (enforced registered elsewhere)
    assert "data-fx=" in _fn("_famFx")


# ---- §5: interactive re-simulation through the project() seam ----
def test_resimulate_calls_seam_endpoint():
    src = _fn("_famResim")
    assert "/api/ads/simulate?sku=" in src and "bid=" in src and "target_acos" in src
    assert "data-simd" in src and "data-simp" in src               # updates 30/60/90 delta + probability
    assert "fam-combo" in src                                       # footer recomputes


def test_projection_seam_is_deterministic_and_parameterized():
    a = AS.project(1000, 90, "KEYWORD", bid_change_pct=0.30)
    b = AS.project(1000, 90, "KEYWORD", bid_change_pct=0.30)
    assert a == b                                                   # deterministic
    assert [h["days"] for h in a["horizons"]] == [30, 60, 90]
    assert a["formula_id"] == "cmaa_projection" and a["tripwire_formula_id"] == "tripwire_units"
    # a deeper cut captures more but is less certain
    deep = AS.project(1000, 90, "KEYWORD", bid_change_pct=0.50)
    assert deep["horizons"][2]["delta"] >= a["horizons"][2]["delta"]
    assert deep["horizons"][0]["prob"] <= a["horizons"][0]["prob"]
    # honest-empty
    assert AS.project(0, 90, "KEYWORD") is None and AS.project(None, 90, "KEYWORD") is None


# ---- §6: no live write ----
def test_ads_router_is_get_only():
    methods = set()
    for r in ads.router.routes:
        methods |= set(getattr(r, "methods", set()) or set())
    assert "POST" not in methods and "PUT" not in methods and "DELETE" not in methods, methods
    # the simulate endpoint exists and is GET
    paths = {getattr(r, "path", "") for r in ads.router.routes}
    assert any(p.endswith("/ads/simulate") for p in paths)


# ---- §7: the 4 honest resolution states still branch distinctly ----
def test_resolution_states_preserved():
    src = _fn("renderAdRecs")
    for reason in ("NO_ENTITY_DATA", "UNMAPPED", "QUERY_ERROR"):
        assert reason in src, f"resolution state {reason} must be handled distinctly"
    assert "recs.recommendations" in src and "_famBySku" in src    # RENDERED_OK folds recs into the modal map


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("fixads_modal_v3 OK")
