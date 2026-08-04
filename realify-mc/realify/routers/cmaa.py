"""CMAA 'Profit & Ads' tab (Step 3).

The second caller of realify/domain/{cmaa,economics}. It computes per-unit economics with the SAME
economics.per_unit() call the SKU tab (1b) uses — so SKU tab, this tab, and any future detector agree
by construction — then runs the ad verdict through domain/cmaa.evaluate().

Trust rules, straight from the plan:
  * CONFIRMED values only — a SKU with units on an unconfirmed channel (provisional_units) is held
    out of the numbers and reported separately, never folded into a headline.
  * ₹ above break-even is split into CERTAIN (economics rest only on settled/seller inputs) vs
    ESTIMATED (any fee-preview/modelled input) — the robust-vs-total distinction from the PoC.
  * Never fabricates: a SKU without a decidable margin (missing price/COGS) or without ad spend is
    listed but not judged, not guessed.
"""
import json
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from realify import db
from realify import country
from realify.repositories.seller_repo import SellerRepository
from realify.repositories.provenance_repo import ProvenanceRepository
from realify.repositories.ad_performance_repo import AdPerformanceRepository
from realify.repositories.revenue_period_repo import RevenuePeriodRepository
from realify.repositories.action_repo import ActionRepository
from realify.repositories.card_repo import CardRepository
from realify.domain import cmaa, economics, trust, explain
from realify import catalog
from .deps import require_tenant
from .helpers import agency_caps

EXPO_REF, EXPO_SCALE = 250000, 60    # inverse of the stored exposure bar (generate.py) → a directional ₹ gap
# card_type -> rule cond (field/op/threshold default). The catalog is the code-level source of truth,
# always present even before the rules table is seeded; tenant overrides only adjust the threshold value.
_CATALOG_COND = {c["card_type"]: c["cond"] for c in catalog.CATALOG}

router = APIRouter()

# Actions we record for a Profit & Ads SKU. We DO NOT write to Amazon Ads (no ad-write scope) — a
# recorded Move is our own decision→outcome ledger + an exportable change set the seller applies.
_CMAA_ACTIONS = {"fix_ads", "scale", "cut", "fix_margin"}

_RANK = {"actual": 4, "seller": 4, "reported": 2, "estimated": 1}


def _pct(x):  # ratio -> percentage, None-safe
    return None if x is None else round(x * 100, 1)


def build_row_card(r, sym, ad, ad_by_period, rev_by_period, units_by_period, prov, acted):
    """Build ONE Profit & Ads row card from L1 tenant data — the SINGLE source of a row's numbers,
    shared by the /cmaa feed and /cmaa/simulate (so a simulation projects off the exact same figures
    the worklist shows, never a client-supplied value). Returns None for a provisional (held) SKU."""
    sku = r.get("internal_sku") or r.get("asin")
    if r.get("provisional_units"):
        return None
    price, cogs = r.get("price"), r.get("cogs")
    a = ad.get(sku) or {}
    spend, sales = a.get("spend"), a.get("sales")
    econ = economics.per_unit(price, cogs, r.get("referral_fee"), r.get("fba_fee"))
    gross_unit = econ["gross_contribution_unit"]
    mf = (float(r["margin_floor"]) / 100.0) if r.get("margin_floor") not in (None, "") else 0.0
    ev = cmaa.evaluate(spend, sales, gross_unit, price, margin_floor=mf)
    gc_after_returns = economics.per_unit(price, cogs, r.get("referral_fee"), r.get("fba_fee"),
                                          r.get("return_cost_unit"))["gross_contribution_unit"]
    sku_rev = rev_by_period.get(sku, {}); sku_spend = ad_by_period.get(sku, {}); sku_units = units_by_period.get(sku, {})
    window = list(sku_spend) or list(sku_rev)
    win_units = sum(v for p, v in sku_units.items() if p in window and v is not None) or None
    win_rev = sum(v for p, v in sku_rev.items() if p in window and v is not None) or None
    if win_units is not None and win_rev:
        settled_up = [pp for pp in window if sku_units.get(pp) is not None]
        cmaa_spend_w = sum(sku_spend.get(pp, 0) for pp in settled_up) or spend
        cmaa_val = cmaa.contribution_after_ads(gc_after_returns, win_units, cmaa_spend_w, win_rev)
        denom_est = False; cmaa_units, cmaa_net_rev, cmaa_spend = win_units, win_rev, cmaa_spend_w
    else:
        units = r.get("units_month"); n = len(sku_spend) or 1
        net_rev_period = (price * units) if (price and units) else None
        monthly_spend = (spend / n) if spend else spend
        cmaa_val = cmaa.contribution_after_ads(gc_after_returns, units, monthly_spend, net_rev_period)
        denom_est = True; cmaa_units, cmaa_net_rev, cmaa_spend = units, net_rev_period, monthly_spend
    p = prov.get(sku, {})
    def wb(f):
        return max(p.get(f, {}), key=lambda b: _RANK.get(b, 0)) if p.get(f) else None
    certainty = economics.certainty({f: wb(f) for f in ("price", "cogs", "referral_fee", "fba_fee")})
    t_trend = trust.tacos_trend(trust.tacos_series(sku_rev, sku_spend))
    n_per = len(sku_spend) or len(sku_rev)
    total_rev = sum(sku_rev.values()) if sku_rev else None
    cannibal = trust.cannibalization_risk(r.get("buybox_pct"), sales, total_rev, n_per)
    guarded, lifecycle_note = trust.lifecycle_guard(ev["quadrant"], r.get("lifecycle_flag"))
    is_judged = spend not in (None, 0) and gross_unit is not None
    above = ev["wasted_spend"]
    reliable = cmaa.cmaa_reliable(spend, sales, cmaa_units, cmaa_net_rev)
    settled_periods = [pp for pp in window if (sku_units.get(pp) is not None or sku_rev.get(pp) is not None)]
    cmaa_window_mismatch = bool(is_judged and sku_spend and set(settled_periods) != set(sku_spend))
    cmaa_tf = explain.window_basis(settled_periods if settled_periods else window)
    if is_judged:
        final_q, cmaa_held, gate_reason = cmaa.scale_gate(ev["quadrant"], cmaa_val["amount"], reliable)
    else:
        final_q, cmaa_held, gate_reason = None, False, None
    scale_up = ev["scale_upside"] if (is_judged and final_q == "SCALE" and not cmaa_held) else None
    card = {
        "sku": sku, "asin": r.get("asin"), "title": r.get("title_override") or r.get("title"),
        "category": r.get("category"),
        "units_month": r.get("units_month"), "price": price, "cogs": cogs,
        "referral_fee": r.get("referral_fee"), "fba_fee": r.get("fba_fee"), "margin_floor": r.get("margin_floor"),
        "gcm_pct": _pct(ev["gcm_pct"]), "breakeven_acos": _pct(ev["breakeven_acos"]),
        "ad_spend": round(spend, 2) if spend else None, "ad_sales": round(sales, 2) if sales else None,
        "actual_acos": _pct(ev["actual_acos"]),
        "above_breakeven": round(above, 2) if above else (0.0 if is_judged else None),
        "scale_upside": scale_up, "cmaa": cmaa_val["amount"],
        "cmaa_pct": (None if (is_judged and not reliable) else cmaa_val["pct"]),
        "cmaa_denom_est": denom_est if is_judged else None,
        "cmaa_reliable": reliable if is_judged else None, "cmaa_held": cmaa_held,
        "cmaa_window_mismatch": cmaa_window_mismatch, "scale_gate_reason": gate_reason,
        "quadrant": final_q if is_judged else ("Not advertised" if gross_unit is not None else "Needs COGS"),
        "margin_certainty": certainty, "tacos_trend": t_trend, "cannibalization": cannibal,
        "lifecycle_guarded": guarded, "lifecycle_note": lifecycle_note, "judged": is_judged,
        "acted": sku in acted,
    }
    card["recommendation"] = cmaa.recommend(card, symbol=sym)
    be_spend = round((sales or 0) * ev["breakeven_acos"], 2) if (sales and ev["breakeven_acos"] is not None) else None
    incr_sales = round((sales or 0) * (cmaa.SCALE_MAX_MULTIPLE - 1), 2) if sales else None
    card["explain"] = explain.cmaa_parts(card, sym, {
        "gross_unit": gross_unit, "gc_after_returns": gc_after_returns,
        "cmaa_spend": cmaa_spend, "cmaa_units": cmaa_units, "cmaa_net_rev": cmaa_net_rev,
        "be_spend": be_spend, "incr_sales": incr_sales, "timeframe": explain.window_basis(window),
        "certainty": certainty, "denom_est": denom_est, "max_multiple": cmaa.SCALE_MAX_MULTIPLE,
        "cmaa_reliable": reliable, "cmaa_held": cmaa_held, "gate_reason": gate_reason,
        "cmaa_window_mismatch": cmaa_window_mismatch, "cmaa_tf": cmaa_tf,
    })
    return card


@router.get("/cmaa")
def cmaa_tab(request: Request):
    tid = require_tenant(request)
    with db.connect() as con:
        t = db.get_tenant(con, tid)
        rows = SellerRepository(con).all(tid)
        prov = ProvenanceRepository(con).all_for_tenant(tid)
        ad = AdPerformanceRepository(con).totals(tid)   # {internal_sku: {spend, sales}}
        ad_by_period = AdPerformanceRepository(con).all_by_sku(tid)      # {sku: {period: spend}}
        rev_by_period = RevenuePeriodRepository(con).all_by_sku(tid)     # {sku: {period: revenue}}
        units_by_period = RevenuePeriodRepository(con).units_by_sku(tid) # {sku: {period: units}}
        acted = set(ActionRepository(con).acted_cmaa_skus(tid))          # SKUs with a recorded Move
    data_mode = (t or {}).get("data_mode")
    sym = country.tenant_profile(tid).get("symbol", "\u20b9")

    out = []
    held = judged = below_cost = 0
    cannibal_flags = guarded_count = 0
    total_above = certain_above = 0.0
    total_scale_upside = total_cut_bleed = 0.0
    above_contrib, upside_contrib, bleed_contrib = [], [], []   # (sku, value) for aggregate explains
    quad_counts = {"SCALE": 0, "FIX ADS": 0, "FIX MARGIN": 0, "CUT/DIVEST": 0}

    for r in rows:
        card = build_row_card(r, sym, ad, ad_by_period, rev_by_period, units_by_period, prov, acted)
        if card is None:                     # provisional SKU — held out of the numbers
            held += 1
            continue
        out.append(card)
        if not card["judged"]:
            continue
        judged += 1
        q = card["quadrant"]
        quad_counts[q] = quad_counts.get(q, 0) + 1
        if card["gcm_pct"] is not None and card["gcm_pct"] < 0:
            below_cost += 1
        if card["cannibalization"]:
            cannibal_flags += 1
        if card["lifecycle_guarded"]:
            guarded_count += 1
        ab = card["above_breakeven"]
        if ab:
            total_above += ab
            above_contrib.append((card["sku"], ab))
            if card["margin_certainty"] == "certain":
                certain_above += ab
        if q == "SCALE" and card["scale_upside"]:
            total_scale_upside += card["scale_upside"]
            upside_contrib.append((card["sku"], card["scale_upside"]))
        if q == "CUT/DIVEST" and card["ad_spend"]:
            total_cut_bleed += card["ad_spend"]
            bleed_contrib.append((card["sku"], card["ad_spend"]))

    out.sort(key=lambda x: (x["above_breakeven"] or -1), reverse=True)
    # portfolio TACoS over time: Σspend_period / Σrevenue_period
    port_rev, port_spend = {}, {}
    for m in rev_by_period.values():
        for p, v in m.items():
            port_rev[p] = port_rev.get(p, 0) + (v or 0)
    for m in ad_by_period.values():
        for p, v in m.items():
            port_spend[p] = port_spend.get(p, 0) + (v or 0)
    portfolio_tacos = trust.tacos_series(port_rev, port_spend)
    tf_port = explain.window_basis(list(port_spend) or list(port_rev))
    s_spend, s_rev = round(sum(port_spend.values()), 2), round(sum(port_rev.values()), 2)
    agg = {
        "total_above_breakeven": explain.aggregate(
            "Recoverable across the portfolio", "max(ad spend − ad sales × break-even ACoS, 0)",
            above_contrib, timeframe_basis=tf_port),
        "total_scale_upside": explain.aggregate(
            "Scale upside (directional)",
            f"incremental ad-sales × (break-even − actual ACoS), capped at {cmaa.SCALE_MAX_MULTIPLE:g}× run-rate",
            upside_contrib, timeframe_basis=tf_port,
            note="Directional — each SKU's upside is a bounded ceiling, not a settled figure."),
        "total_cut_bleed": explain.aggregate(
            "Ad bleed you would stop", "ad spend on CUT/DIVEST SKUs (losing on margin and ads)",
            bleed_contrib, timeframe_basis=tf_port),
    }
    if s_rev:
        agg["portfolio_tacos"] = explain.part(
            "Portfolio TACoS", "Σ ad spend ÷ Σ revenue (all periods)",
            [("Σ ad spend", s_spend, sym), ("Σ revenue", s_rev, sym)],
            round(s_spend / s_rev * 100, 1), timeframe_basis=tf_port)
    summary = {
        "judged": judged, "held_provisional": held, "below_cost": below_cost,
        "total_above_breakeven": round(total_above, 2),
        "certain_above_breakeven": round(certain_above, 2),
        "estimated_above_breakeven": round(total_above - certain_above, 2),
        "total_scale_upside": round(total_scale_upside, 2),   # directional — badged in the UI
        "total_cut_bleed": round(total_cut_bleed, 2),         # ad spend stopped if CUT/DIVEST ads pulled
        "quadrants": quad_counts,
        "cannibalization_flags": cannibal_flags,
        "lifecycle_guarded": guarded_count,
        "portfolio_tacos": portfolio_tacos,
        "portfolio_tacos_trend": trust.tacos_trend(portfolio_tacos),
        "explain": agg,
    }
    # Empty Profit & Ads for a CUSTOMER with no ad data yet: show a labeled sample preview + tell
    # them exactly which reports unlock it. Auto-clears the moment real ad data lands. Tenants that
    # already have ad data (even if all held as provisional) get their real summary, not a sample.
    if judged == 0 and not ad and data_mode != "synthetic":
        from realify.domain import cmaa_sample
        have = {
            "sales": bool(rev_by_period) or bool(rows),
            "ad_report": bool(ad),
            "cogs": any(r.get("cogs") not in (None, "") for r in rows),
        }
        need = []
        if not have["ad_report"]:
            need.append("Sponsored Products – Advertised Product report")
        if not have["cogs"]:
            need.append("COGS / unit costs")
        sample = cmaa_sample.sample_payload()
        return JSONResponse({"ok": True, "sample": True, "have": have, "need": need,
                             "skus": sample["skus"], "summary": sample["summary"]})

    return JSONResponse({"ok": True, "sample": False, "synthetic": data_mode == "synthetic",
                         "skus": out, "summary": summary})


@router.post("/cmaa/action")
async def cmaa_action(request: Request):
    """Record a Profit & Ads Move (recommended → acted). This is a ledger write to OUR actions_log
    only — it never touches Amazon Ads (no ad-write scope; that push is a TODO gated on team-7). The
    seller applies the change via the exported change set; recording the Move makes the tab remember
    it (the SKU shows 'acted' on reload). Accepts one SKU or a bulk list (apply-to-all-in-bucket)."""
    tid = require_tenant(request)                              # server-side tenant scope; 401 if none
    b = await request.json()
    action = b.get("action")
    if action not in _CMAA_ACTIONS:
        return JSONResponse({"ok": False, "error": "unknown action"}, status_code=400)
    # R15 Part 0 — envelope gate: an agency operator drilled into a brand can only RECORD a Profit & Ads
    # Move when the 'ads' lens grants execute; otherwise it must be proposed for the brand to co-sign.
    caps = agency_caps(request)
    if caps is not None and caps.get("ads", "read") != "execute":
        return JSONResponse({"ok": False, "proposal_required": True, "lens": "ads",
                             "kind": action, "signal": b.get("title") or f"Profit & Ads: {action}",
                             "impact_usd_minor": int(b.get("recoverable") or 0)})
    skus = b.get("skus") or ([b["sku"]] if b.get("sku") else [])
    skus = [s for s in skus if s]
    if not skus:
        return JSONResponse({"ok": False, "error": "no sku"}, status_code=400)
    ts = datetime.now(timezone.utc).isoformat()
    title = b.get("title") or f"Profit & Ads: {action}"
    summary = b.get("summary") or ""
    payload = json.dumps({k: b.get(k) for k in ("projected", "bucket", "recoverable",
                                                "scale_upside", "bleed") if b.get(k) is not None})
    with db.connect() as con:
        repo = ActionRepository(con)
        for sku in skus:
            repo.log_action(tid, ts, sku, "cmaa_sku", action, title, summary,
                            b.get("explanation") or "", "change_set_export", None, payload)
        con.commit()
    return JSONResponse({"ok": True, "recorded": len(skus), "skus": skus})


def _latest_traffic(con, tid, internal_sku):
    if not internal_sku:
        return {}
    r = con.execute("SELECT sessions, conversion_pct, buybox_pct FROM traffic "
                    "WHERE tenant_id=? AND internal_sku=? ORDER BY date DESC LIMIT 1",
                    (tid, internal_sku)).fetchone()
    return dict(r) if r else {}


def _intel_ctx(con, tid, card, er_all):
    """Assemble the context an Intelligence-card simulation projects over — the card's own-product SKU
    row (seller_skus + latest traffic), the rule's field/op, and the tenant's effective threshold for
    that rule (the 'your floor/ceiling/line' default). Never client-supplied."""
    ct = card["card_type"]; asin = card.get("asin")
    seller = SellerRepository(con).by_asin(tid, asin) if asin else None
    cond = _CATALOG_COND.get(ct, {})                       # field/op/threshold-default (code source of truth)
    er = er_all.get(ct, {}) or {}
    params = er.get("params", {}) or {}                    # tenant EFFECTIVE params (rules table seeded in prod)
    # target-threshold default: catalog cond for the ~73 data-driven rules; effective-rules default for the
    # C-code / BB-OWN special detectors (_CATALOG_COND doesn't carry them). C4/seasonal-cover targets its
    # own days-of-cover line, whose param key is days_of_cover_lt (not the generic "threshold").
    pdef = cond.get("params_default") or er.get("params_default") or {}
    tkey = "days_of_cover_lt" if ct == "C4" else "threshold"
    threshold = params.get(tkey, pdef.get(tkey))
    row = dict(seller or {})
    for k, v in _latest_traffic(con, tid, (seller or {}).get("internal_sku")).items():
        if v is not None:
            row[k] = v                                     # latest sessions/CVR/BuyBox win the day-of value
    gap = round((card.get("exposure_pct") or 0) / EXPO_SCALE * EXPO_REF) or None
    finding = re.sub(r"<[^>]+>", "", card.get("finding") or "")   # findings carry <b> markup; strip for the modal header
    return {"card_type": ct, "field": cond.get("field"), "op": cond.get("op"),
            "sku": (seller or {}).get("internal_sku") or asin, "asin": asin,
            "title": (seller or {}).get("title") or asin, "category": card.get("category"),
            "finding": finding, "family": card.get("family"), "exposure_inr": gap,
            "threshold": threshold,
            "threshold_customized": (tkey in params and params.get(tkey) != pdef.get(tkey)),
            "row": row, "portfolio_rev": None}


@router.post("/cmaa/simulate")
async def cmaa_simulate(request: Request):
    """Deterministic scenario projection for one recommendation. For a Profit & Ads SKU ({sku}) the row
    is REBUILT server-side via build_row_card; for an Intelligence card ({card_id}) the ctx is rebuilt
    from the card's own-product SKU + the tenant's detector threshold. Never a client-supplied value;
    projected by realify.domain.{simulate,sim_intel} over the posted assumptions. Tenant-scoped, fail-closed."""
    tid = require_tenant(request)
    b = await request.json()
    sku = b.get("sku"); card_id = b.get("card_id")
    assumptions = b.get("assumptions") or {}
    if card_id is not None:                                # Intelligence card path
        from realify import rules as rules_mod
        from realify.domain import sim_intel
        er_all = rules_mod.effective_rules(tid)
        with db.connect() as con:
            card = CardRepository(con).get(tid, card_id)
            if not card:
                return JSONResponse({"ok": False, "error": "card not found"}, status_code=404)
            ctx = _intel_ctx(con, tid, card, er_all)
        return JSONResponse({"ok": True, "simulation": sim_intel.simulate_card(ctx, assumptions)})
    if not sku:
        return JSONResponse({"ok": False, "error": "no sku or card_id"}, status_code=400)
    sym = country.tenant_profile(tid).get("symbol", "₹")
    with db.connect() as con:
        rows = SellerRepository(con).all(tid)
        prov = ProvenanceRepository(con).all_for_tenant(tid)
        ad = AdPerformanceRepository(con).totals(tid)
        ad_by_period = AdPerformanceRepository(con).all_by_sku(tid)
        rev_by_period = RevenuePeriodRepository(con).all_by_sku(tid)
        units_by_period = RevenuePeriodRepository(con).units_by_sku(tid)
        acted = set(ActionRepository(con).acted_cmaa_skus(tid))
    row = None
    for r in rows:
        if (r.get("internal_sku") or r.get("asin")) == sku:
            row = build_row_card(r, sym, ad, ad_by_period, rev_by_period, units_by_period, prov, acted)
            break
    if not row:
        return JSONResponse({"ok": False, "error": "sku not found"}, status_code=404)
    from realify.domain import simulate as sim_mod
    return JSONResponse({"ok": True, "simulation": sim_mod.simulate(row, assumptions)})
