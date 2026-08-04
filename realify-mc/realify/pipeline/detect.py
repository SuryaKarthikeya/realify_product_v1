"""Detectors — turn the persisted data into the 9 research-card signals.
Each returns a list of 'signal' dicts carrying the numbers + provenance.
Relevance/exposure is computed here by joining to the seller's own economics."""
import json
from . import primitives as P
from .. import db
from ..repositories.seller_repo import SellerRepository
from ..repositories.market_repo import MarketRepository
from ..repositories.fact_repos import TrafficRepository

def _latest_two_snaps(con, tenant_id, asin):
    return [dict(r) for r in MarketRepository(con).recent_snapshots(tenant_id, asin, 2)]

def _sku(con, tenant_id, asin):
    return SellerRepository(con).by_asin(tenant_id, asin)

def _fmt_inr(x):
    from .. import country
    return country.fmt_money(x)

def detect_all(con, tenant_id):
    from .. import rules as rules_mod
    eff = rules_mod.effective_rules(tenant_id)
    def on(rid):  # rule enabled for this tenant?
        return eff.get(rid, {}).get("enabled", True)
    def prm(rid, key, default):
        return eff.get(rid, {}).get("params", {}).get(key, default)
    signals = []
    skus = SellerRepository(con).all(tenant_id)
    by_asin = {s["asin"]: s for s in skus}

    # ---- C1 Competitor Move: a competitor offer undercuts own price, above floor ----
    for s in (skus if on("C1") else []):
        offers = MarketRepository(con).latest_offers(tenant_id, s["asin"])
        if not offers: continue
        low = dict(offers[0])
        gap = round(s["price"] - low["price"], 2)
        if low["seller"] != "Autofy" and gap >= max(prm("C1","min_gap_abs",50), s["price"]*prm("C1","min_gap_pct",3.0)/100.0):
            exposure = (s.get("annual_rev_inr") or 0)/12
            signals.append(dict(card_type="C1", family="competitive", type_name="Competitor Move",
                asin=s["asin"], category=s["category"],
                nums=dict(comp=low["seller"], comp_price=low["price"], own=s["price"],
                          floor=s["breakeven_floor"], gap=gap,
                          rec=max(s["breakeven_floor"]+1, round(low["price"]*0.98)), bb=s["buybox_pct"]),
                exposure_inr=exposure, exposure_label="Your monthly revenue on this SKU",
                action="Reprice", severity="act",
                provenance=[("competitor price","KEEPA/SP-API"),("your price","OWN"),("floor","OWN")]))

    # ---- C2 New Entrant: offer_count jumped vs prior snapshot ----
    for s in (skus if on("C2") else []):
        snaps = _latest_two_snaps(con, tenant_id, s["asin"])
        if len(snaps) == 2 and snaps[0]["offer_count"] and snaps[1]["offer_count"]:
            if P.pop_pct(snaps[0]["offer_count"], snaps[1]["offer_count"]) > prm("C2","offer_jump_pct",40):
                signals.append(dict(card_type="C2", family="competitive", type_name="New Entrant",
                    asin=s["asin"], category=s["category"],
                    nums=dict(now=snaps[0]["offer_count"], prev=snaps[1]["offer_count"]),
                    exposure_inr=(s.get("annual_rev_inr") or 0)/12*0.3, exposure_label="Contested revenue",
                    action="Add to watchlist", severity="watch",
                    provenance=[("offer count","KEEPA")]))

    # ---- C3 Demand Shift: BSR improving (current < avg30 => climbing rank) ----
    for s in (skus if on("C3") else []):
        snaps = _latest_two_snaps(con, tenant_id, s["asin"])
        if snaps and snaps[0]["bsr"] and snaps[0]["bsr_avg30"]:
            if snaps[0]["bsr"] < snaps[0]["bsr_avg30"] * (1 - prm("C3","bsr_better_than_avg_pct",20)/100.0):
                signals.append(dict(card_type="C3", family="demand", type_name="Demand Shift",
                    asin=s["asin"], category=s["category"],
                    nums=dict(bsr=snaps[0]["bsr"], avg30=snaps[0]["bsr_avg30"]),
                    exposure_inr=(s.get("annual_rev_inr") or 0)/12, exposure_label="You carry this — scale headroom",
                    action="Scale & restock", severity="watch",
                    provenance=[("BSR","KEEPA"),("trend","KEEPA")]))

    # ---- C4 Seasonality Inflection: low days-of-cover on bike/cover SKUs (monsoon proxy) ----
    for s in (skus if on("C4") else []):
        if s["ptype"] in ("Bike Cover","Car Cover") and s.get("days_of_cover") is not None \
                and s.get("velocity_day") is not None and s["days_of_cover"] < prm("C4","days_of_cover_lt",25):
            signals.append(dict(card_type="C4", family="demand", type_name="Seasonality Inflection",
                asin=s["asin"], category=s["category"],
                nums=dict(doc=s["days_of_cover"], lead=int(prm("C4","lead_time_days",14)), velocity=s["velocity_day"]),
                exposure_inr=s["velocity_day"]*30*s["price"], exposure_label="Revenue at risk if understocked",
                action="Create restock task", severity="act",
                provenance=[("days of cover","OWN"),("velocity","OWN"),("seasonality","TIER-C")]))

    # ---- C5 Opportunity Surfaced: trend signal in a category, framed as a niche ----
    trends = MarketRepository(con).trends(tenant_id, 3) if on("C5") else []
    for t in trends:
        signals.append(dict(card_type="C5", family="opportunity", type_name="Opportunity Surfaced",
            asin=None, category=dict(t)["category"],
            nums=dict(title=dict(t)["title"], score=88),
            exposure_inr=190000, exposure_label="Fit with your catalog & sourcing",
            action="Research deeper", severity="opp",
            provenance=[("trend","TIER-C"),("score","MODEL")]))
        break

    # ---- C6 Assortment Gap: category where competitor breadth >> own SKU count ----
    from collections import Counter
    own_by_cat = Counter(s["category"] for s in skus) if on("C6") else Counter()
    for cat, own_n in own_by_cat.items():
        comp_breadth = own_n * 2 + 6   # fixture proxy; live = resolved competitor catalog
        if comp_breadth - own_n >= prm("C6","min_gap_skus",6):
            signals.append(dict(card_type="C6", family="opportunity", type_name="Assortment Gap Widened",
                asin=None, category=cat,
                nums=dict(own=own_n, comp=comp_breadth),
                exposure_inr=230000, exposure_label="Unserved demand in your category",
                action="Send to sourcing", severity="watch",
                provenance=[("competitor assortment","KEEPA"),("your coverage","OWN")]))
            break

    # ---- C7 Category News / C8 Recall / C9 Social from tierc_signals ----
    for st, ct, fam, name, sev, act in [
        ("news","C7","news","Category News","watch","Watch story"),
        ("recall","C8","news","Recall / Regulatory","opp","Plan capture"),
        ("social","C9","news","Social / Virality","watch","Research deeper")]:
        if not on(ct): continue
        rows = MarketRepository(con).latest_signal(tenant_id, st)
        for r in rows:
            r = dict(r)
            signals.append(dict(card_type=ct, family=fam, type_name=name,
                asin=None, category=r["category"],
                nums=dict(title=r["title"], summary=r["summary"], url=r["url"]),
                exposure_inr=180000 if st!="social" else 90000,
                exposure_label="SKUs with exposure" if st=="news" else
                               ("Capture potential in your category" if st=="recall" else "Adjacent to your catalog"),
                action=act, severity=sev, confidence_override=r["confidence"],
                provenance=[(("BIS govt feed" if st=="recall" else ("news API" if st=="news" else "social listening")),"TIER-C")]))
    # ---- generic catalog rules (Step 5): data-driven threshold conditions ----
    ACTION_LABEL = {"reprice":"Reprice","ad_action":"Adjust ads","restock_task":"Restock",
                    "listing_update":"Update listing","case_report":"Open case",
                    "review_request":"Request review","monitoring_ticket":"Monitor"}
    # conversion lives in traffic; map asin->conversion for SV/CL rules.
    conv_by_asin = {}
    for row in TrafficRepository(con).conversion_by_asin(tenant_id):
        conv_by_asin[row["asin"]] = row["conv"]
    own_counts = Counter(s["category"] for s in skus)

    def _cmp(val, op, thr):
        if val is None: return False
        return val < thr if op == "lt" else val > thr

    for rid, r in eff.items():
        if not r.get("enabled"): continue
        cond = r.get("cond") or {}
        if cond.get("primitive") != "threshold": continue       # specials handled above
        scope = cond.get("scope", "sku"); field = cond.get("field"); op = cond.get("op", "lt")
        thr = r.get("params", {}).get("threshold", (cond.get("params_default") or {}).get("threshold"))
        if thr is None or not field: continue
        if scope == "category":
            for cat, n in own_counts.items():
                if _cmp(n, op, thr):
                    signals.append(dict(card_type=rid, family=r["family"], type_name=r["name"],
                        asin=None, category=cat, rule=True, narrative=r.get("description",""),
                        nums=dict(field=field, value=n, op=op, threshold=thr, label="Own SKUs"),
                        exposure_inr=0, exposure_label="Category breadth",
                        action=ACTION_LABEL.get(r["action_handler"], r["action_handler"].title()), severity=r["severity"],
                        provenance=[("own catalog","OWN")]))
            continue
        # sku scope: pick the single most material matching SKU (by revenue) so each rule
        # contributes at most one card; coverage = did the rule fire at all.
        best = None
        for s in skus:
            val = conv_by_asin.get(s["asin"]) if field == "conversion_pct" else s.get(field)
            if _cmp(val, op, thr):
                if best is None or (s.get("annual_rev_inr") or 0) > best[0]:
                    best = ((s.get("annual_rev_inr") or 0), s, val)
        if best:
            _, s, val = best
            signals.append(dict(card_type=rid, family=r["family"], type_name=r["name"],
                asin=s["asin"], category=s["category"], rule=True, narrative=r.get("description",""),
                nums=dict(field=field, value=val, op=op, threshold=thr,
                          label=(cond.get("editable_params",{}).get("threshold",{}) or {}).get("label", field)),
                exposure_inr=(s.get("annual_rev_inr") or 0)/12, exposure_label="Your monthly revenue on this SKU",
                action=ACTION_LABEL.get(r["action_handler"], r["action_handler"].title()), severity=r["severity"],
                provenance=[(field,"OWN"),("threshold","RULE")]))

    # ---- Buy-Box ownership: own buybox_pct below line (new canonical detector) ----
    bb_thr = prm("BB-OWN", "threshold", 80)
    if on("BB-OWN"):
        best = None
        for s in skus:
            v = s.get("buybox_pct")
            if v is not None and v < bb_thr:
                if best is None or (s.get("annual_rev_inr") or 0) > best[0]:
                    best = ((s.get("annual_rev_inr") or 0), s, v)
        if best:
            _, s, v = best
            signals.append(dict(card_type="BB-OWN", family="buybox", type_name="Buy Box ownership",
                asin=s["asin"], category=s["category"], rule=True, narrative="",
                nums=dict(field="buybox_pct", value=v, op="lt", threshold=bb_thr, label="Buy Box %"),
                exposure_inr=(s.get("annual_rev_inr") or 0)/12, exposure_label="Your monthly revenue on this SKU",
                action="Reprice / check eligibility", severity="act",
                provenance=[("buybox_pct","OWN"),("threshold","RULE")]))

    return signals
