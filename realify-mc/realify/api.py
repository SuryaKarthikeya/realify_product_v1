"""Read API — tenant-scoped reads of the materialized cards + category pulse.
tenant_id is supplied by the caller (resolved from the session), never the client."""
import json
from . import db
from .repositories.card_repo import CardRepository
from .repositories.rules_repo import RulesRepository
from .repositories.seller_repo import SellerRepository
from .repositories.order_repo import OrderRepository
from .repositories.fact_repos import TrafficRepository, InventoryRepository, SettlementRepository
from .repositories.pull_repo import PullLogRepository
from .repositories.ad_performance_repo import AdPerformanceRepository
from .repositories.ad_entity_repo import AdEntityPerfRepository
from .repositories.revenue_period_repo import RevenuePeriodRepository
from .repositories.channel_repo import ChannelRepository, ReturnsRepository, StorageFeeRepository
from .models import StockoutForecaster

SEV_RANK = {"crit":0,"act":1,"opp":2,"watch":3}

# ---- Model-owned decisions: these flat-threshold feed cards are SUPERSEDED by the
# backtested RIA model recommendations (reorder → forecast_demand, price position →
# optimize_price) shown in the model-recs panel, so the UI hides them from the feed.
# Everything else (margin, ACoS, cash, ratings, overstock, Buy-Box ownership) stays a
# rule-based fact. Computed from the rule catalog so it tracks rule edits. ----
def _model_superseded_card_types():
    from . import catalog
    s = set()
    for r in catalog.CATALOG:
        cond = r.get("cond") or {}
        h, g, f, op = r.get("action_handler"), r.get("group"), cond.get("field"), cond.get("op")
        # RESTOCK (understock) → forecast_demand. Keyed on semantics, not the handler:
        # a low days-of-cover / stock-on-hand is a reorder decision. OVERSTOCK (op 'gt')
        # and CASH trapped-capital stay as rule facts — we don't model liquidation.
        if f in ("days_of_cover", "stock_on_hand") and op == "lt" and g in ("Inventory", "Sales", "Demand"):
            s.add(r["card_type"])
        elif h == "reprice" and g == "Pricing & Buy Box":        # price position → optimize_price
            s.add(r["card_type"])
    s.add("C4")                                                  # seasonality restock (special detector)
    return s

MODEL_SUPERSEDED = _model_superseded_card_types()
# Exposure figures that are HARD-CODED constants in the detectors (not derived from the
# seller's data) — flagged so the UI drops the fabricated ₹ number instead of implying rigor.
FABRICATED_EXPOSURE = {"C5", "C6", "C7", "C8", "C9"}

def _surface_map(con):
    m = {}
    for r in RulesRepository(con).surface_map_rows():
        try:
            j = json.loads(r["inputs"] or "{}") or {}
            m[r["rule_id"]] = (j.get("surface","intelligence"), j.get("group","Demand"), r["action_handler"])
        except Exception:
            m[r["rule_id"]] = ("intelligence","Demand","monitoring_ticket")
    return m

# concrete execution handlers vs awareness handlers
_CONCRETE = {"reprice","ad_action","restock_task","listing_update","case_report","review_request"}
# for non-concrete (awareness) rules, the action depends on the group
_AWARENESS_BY_GROUP = {
    "Opportunity":("investigate","Investigate"), "Demand":("investigate","Investigate"),
    "News":("investigate","Investigate"),
    "Competitive":("watch","Add to watchlist"), "Risk":("watch","Add to watchlist"),
    "Pricing & Buy Box":("watch","Add to watchlist"),
    "Sales":("watch","Set alert"), "Margin":("watch","Set alert"), "Cash":("watch","Set alert"),
    "Inventory":("watch","Set alert"), "Ads":("watch","Set alert"),
}

def get_feed(tenant_id, category=None, family=None, new_only=False, surface=None, groups=None):
    con = db.connect()
    rows = CardRepository(con).feed(tenant_id, category, family, new_only)
    smap = _surface_map(con)
    con.close()
    for r in rows:
        r["sources"] = json.loads(r["sources"]); r["minis"] = json.loads(r["minis"])
        r["provenance"] = json.loads(r["provenance"])
        surf, grp, handler = smap.get(r["card_type"], ("intelligence","Demand","monitoring_ticket"))
        r["surface"] = surf; r["group"] = grp
        # Provenance for the UI: every feed card is a rule (vs the modeled recs panel).
        # `superseded` = a backtested model now owns this decision; `exposure_fabricated`
        # = the ₹ figure is a hard-coded constant, not computed.
        r["basis"] = "rule"
        r["superseded"] = r["card_type"] in MODEL_SUPERSEDED
        r["exposure_fabricated"] = r["card_type"] in FABRICATED_EXPOSURE
        if handler in _CONCRETE:
            r["action_kind"] = "execute"          # keep the concrete label already on the card
        else:
            kind, label = _AWARENESS_BY_GROUP.get(grp, ("investigate","Investigate"))
            r["action_kind"] = kind; r["action"] = label
    if surface and surface in ("intelligence", "research"):
        rows = [r for r in rows if r["surface"] == surface]
    if groups:
        rows = [r for r in rows if r["group"] in groups]
    rows.sort(key=lambda r: (-((r["rank_score"] if "rank_score" in r.keys() and r["rank_score"] is not None else 0)),
                             SEV_RANK.get(r["severity"], 9), -r["exposure_pct"], -r["is_new"]))
    return rows

def get_categories(tenant_id):
    con = db.connect()
    cards = CardRepository(con)
    cats = SellerRepository(con).distinct_categories(tenant_id)
    out = []
    for c in cats:
        agg = SellerRepository(con).category_aggregate(tenant_id, c)
        new_cards = cards.count_new_in_category(tenant_id, c)
        alerts = cards.count_alerts_in_category(tenant_id, c)
        out.append(dict(category=c, skus=agg["n"], gmv=agg["gmv"], buybox=round(agg["bb"] or 0),
                        new=new_cards, alerts=alerts))
    con.close()
    out.sort(key=lambda x: -x["gmv"])
    return out

def briefing_summary(tenant_id):
    con = db.connect()
    cards = CardRepository(con)
    total = cards.count_open(tenant_id)
    new = cards.count_new(tenant_id)
    act = cards.count_action(tenant_id)
    opp = cards.count_opportunity(tenant_id)
    con.close()
    return dict(total=total, new=new, action=act, opportunities=opp)

def source_health(tenant_id):
    con = db.connect()
    out = []
    for src in ("keepa","recalls","news","trends"):
        row = PullLogRepository(con).max_ok_by_source(tenant_id, src)
        out.append(dict(source=src, last_ok=row["t"] if row else None,
                        live=bool(row and row["t"]), records=(row["r"] if row else 0) or 0))
    con.close()
    return out

def kpis(tenant_id, window=30):
    """Five Intelligence KPIs. Accounts with a dated order feed (synthetic testers) window them
    from orders+settlements. Report-onboarded accounts have no dated order/settlement feed, so
    Revenue/Margin/Ad-spend are derived from the report-aware seller_skus economics (monthly,
    scaled to the window) and Cash from settled per-period revenue where present. Inventory is a
    current snapshot; a report account with no inventory feed is flagged rather than shown as 0."""
    import datetime as dt
    # Accept any positive day-count, not just the three UI toggle values — the frontend's "All
    # Time" option sends window=3650 (a literal ~10yr lookback), which used to silently collapse
    # to 30 here (anything not exactly 7/30/60 fell back), making "All Time" indistinguishable
    # from the 30-day default. Only truly invalid input (non-numeric, <=0) falls back to 30.
    try:
        window = int(window)
        window = window if window > 0 else 30
    except (TypeError, ValueError):
        window = 30
    con = db.connect()
    today = dt.date.today()
    since = (today - dt.timedelta(days=window)).isoformat()

    econ = {r["asin"]: dict(cogs=r["cogs"] or 0, ad=r["ad_cost_unit"] or 0)
            for r in SellerRepository(con).select_columns(tenant_id, ["asin", "cogs", "ad_cost_unit"])}

    rev = units = referral = fba = cogs_tot = ad_tot = 0.0
    for o in OrderRepository(con).window_rows(tenant_id, since):
        u = o["units"] or 0
        rev += o["gross"] or 0; units += u
        referral += o["referral_fee"] or 0; fba += o["fba_fee"] or 0
        e = econ.get(o["asin"], {"cogs":0,"ad":0})
        cogs_tot += e["cogs"] * u; ad_tot += e["ad"] * u
    # If per-unit ad cost isn't stamped on seller_skus, fall back to the ad report's own spend,
    # normalized from its reported periods to a monthly figure and scaled to this window — the
    # SAME fallback the reports-basis branch below already uses. A real orders-basis tenant can
    # have ad_performance data without ad_cost_unit ever being set on the catalog.
    if ad_tot <= 0 and rev > 0:
        try:
            ap = AdPerformanceRepository(con)
            total_spend = sum((v.get("spend") or 0) for v in ap.totals(tenant_id).values())
            nper = len(ap.periods(tenant_id)) or 1
            # Cap the scaling factor at 60 days: this is a "recent monthly run-rate" projection,
            # honest for a 7/30/60-day window but not for "All Time" (window=3650) — multiplying
            # one month's average spend by ~121x would fabricate a decade of extrapolated spend.
            ad_tot = (total_spend / nper) * (min(window, 60) / 30.0)
        except Exception:
            ad_tot = 0.0
    margin = rev - referral - fba - cogs_tot - ad_tot

    basis = "orders"
    cash = 0.0; short_paid = 0.0; cash_note = None
    if rev <= 0:
        # No dated order feed → report-onboarded account. Derive the same monthly economics the
        # SKUs/Profit&Ads tabs show (units_month x price, per-unit net profit, ad_cost) scaled to
        # the window. Nothing is fabricated: every input is a value the reports supplied.
        basis = "reports"
        factor = window / 30.0
        rev = units = margin = ad_tot = 0.0
        for k in SellerRepository(con).all(tenant_id):
            um = k.get("units_month") or 0
            rev += um * (k.get("price") or 0)
            units += um
            npu = k.get("net_profit_unit")
            if npu is not None:
                margin += npu * um
            ad_tot += (k.get("ad_cost_unit") or 0) * um
        # If per-unit ad cost isn't stamped on the SKUs, fall back to the ad report's own spend,
        # normalized from its reported periods to a monthly figure (what Profit & Ads reads).
        if ad_tot <= 0:
            try:
                ap = AdPerformanceRepository(con)
                total_spend = sum((v.get("spend") or 0) for v in ap.totals(tenant_id).values())
                nper = len(ap.periods(tenant_id)) or 1
                ad_tot = (total_spend / nper)
            except Exception:
                ad_tot = 0.0
        rev *= factor; units *= factor; margin *= factor; ad_tot *= factor
        # Cash received = settled per-period revenue where the transaction report gave us periods.
        try:
            settled = 0.0
            for _sku, periods in RevenuePeriodRepository(con).all_by_sku(tenant_id).items():
                for pstart, r in periods.items():
                    if pstart and pstart >= since:
                        settled += (r or 0)
            if settled > 0:
                cash = settled
            else:
                cash_note = "add settlement report"
        except Exception:
            cash_note = "add settlement report"
    else:
        crow = SettlementRepository(con).window_summary(tenant_id, since)
        cash = crow["payout"] or 0; short_paid = crow["short"] or 0

    margin_pct = (margin / rev * 100) if rev else 0
    tacos = (ad_tot / rev * 100) if rev else 0

    inv = InventoryRepository(con).list_on_hand(tenant_id)
    cogs_by_sku = {r["internal_sku"]: (r["cogs"] or 0)
                   for r in SellerRepository(con).select_columns(tenant_id, ["internal_sku", "cogs"])}
    inv_units = sum((r["on_hand"] or 0) for r in inv)
    inv_value = sum((r["on_hand"] or 0) * cogs_by_sku.get(r["sku"], 0) for r in inv)
    low = InventoryRepository(con).count_low_cover(tenant_id)
    # Report accounts with no inventory feed: say so instead of showing a hollow zero.
    inv_note = "add inventory report" if (basis == "reports" and inv_units == 0) else None
    has_inv_fact_data = inv_units != 0
    if not has_inv_fact_data:
        # The `inventory` per-channel fact table (a live snapshot report) is frequently never
        # populated — but seller_skus.stock_on_hand (from a Storage Fee report) often is. Real
        # data, just a different (equally valid) source; fall back rather than show a hollow 0.
        soh_rows = SellerRepository(con).select_columns(tenant_id, ["stock_on_hand", "cogs", "days_of_cover"])
        if any(r["stock_on_hand"] is not None for r in soh_rows):
            inv_units = sum((r["stock_on_hand"] or 0) for r in soh_rows)
            inv_value = sum((r["stock_on_hand"] or 0) * (r["cogs"] or 0) for r in soh_rows)
            low = sum(1 for r in soh_rows if r["days_of_cover"] is not None and r["days_of_cover"] < 14)
            inv_note = None

    # ---- Workspace inner-card substats (5 per domain, one domain viewed at a time). `trend` is
    # always None — no comparison-period baseline is computed here, so it's left honest rather
    # than faked. Values genuinely unavailable (no ingested feed) are None + a note, not zero. ----
    reports_note = "no dated order feed" if basis == "reports" else None
    since_month = since[:7]   # storage_fees.period is month-granular ('YYYY-MM'), not a full date

    order_agg = OrderRepository(con).window_aggregate(tenant_id, since)
    returns_win = ReturnsRepository(con).window_summary(tenant_id, since)
    net_revenue = order_agg["gross"] - returns_win["refund_amount"]
    orders_ct = order_agg["orders"]
    aov = (order_agg["gross"] / orders_ct) if orders_ct else None
    buybox_vals = [r["buybox_pct"] for r in SellerRepository(con).select_columns(tenant_id, ["buybox_pct"])
                   if r["buybox_pct"] is not None]
    buybox_avg = round(sum(buybox_vals) / len(buybox_vals), 1) if buybox_vals else None
    revenue_substats = [
        dict(key="net_revenue", label="Net Revenue", value=round(net_revenue), trend=None, note=reports_note),
        dict(key="orders", label="Orders", value=orders_ct, trend=None, note=reports_note),
        dict(key="units_sold", label="Units Sold", value=int(order_agg["units"]), trend=None, note=reports_note),
        dict(key="aov", label="AOV", value=(round(aov, 2) if aov is not None else None), trend=None,
             note=reports_note or (None if aov is not None else "no orders in window")),
        dict(key="buybox_pct", label="Buy Box %", value=buybox_avg, trend=None,
             note=None if buybox_avg is not None else "no Buy Box data"),
    ]

    margin_pct_by_sku = {r["internal_sku"]: r["net_margin_pct"] for r in
                         SellerRepository(con).select_columns(tenant_id, ["internal_sku", "net_margin_pct"])}
    unprofitable_skus = sum(1 for v in margin_pct_by_sku.values() if v is not None and v < 0)
    cm1 = net_revenue - cogs_tot
    gross_margin_pct = round(cm1 / rev * 100, 1) if rev else None
    storage_win = StorageFeeRepository(con).window_summary(tenant_id, since_month)
    settle_win = SettlementRepository(con).window_summary(tenant_id, since)
    gross_by_channel = SettlementRepository(con).window_gross_by_channel(tenant_id, since)
    active_channels = {c["channel"]: (c["fee_pct"] or 0) for c in ChannelRepository(con).active(tenant_id)}
    payment_proc_proxy = sum(gross_by_channel.get(ch, 0) * fee for ch, fee in active_channels.items())
    # returns_win["refund_amount"] is NOT subtracted again here — it's already netted out of
    # net_revenue (and therefore cm1) above; including it here too would double-count it.
    other_marketing = 0   # no data source for this yet (no report type supplies it) — an honest,
                          # explicitly-named placeholder rather than a fabricated figure.
    cm2 = cm1 - (fba + storage_win + referral + 0 + payment_proc_proxy)
    cm3 = cm2 - (ad_tot + other_marketing)
    cm1_pct = round(cm1 / rev * 100, 1) if rev else None
    cm2_pct = round(cm2 / rev * 100, 1) if rev else None
    cm3_pct = round(cm3 / rev * 100, 1) if rev else None
    margin_substats = [
        dict(key="cm1", label="CM1", value=round(cm1), pct=cm1_pct, trend=None, note=reports_note),
        dict(key="gross_margin_pct", label="Gross Margin %", value=gross_margin_pct, trend=None, note=reports_note),
        dict(key="cm2", label="CM2", value=round(cm2), pct=cm2_pct, trend=None, note=reports_note),
        dict(key="cm3", label="CM3", value=round(cm3), pct=cm3_pct, trend=None, note=reports_note),
        dict(key="unprofitable_skus", label="Unprofitable SKUs", value=unprofitable_skus, trend=None),
    ]

    sf = StockoutForecaster()
    oos_risk_ct = sum(1 for a in SellerRepository(con).asins(tenant_id)
                      if (sf.predict(con, tenant_id, a).get("value") or 999) < 7)
    days_cover_vals = [r["days_of_cover"] for r in SellerRepository(con).select_columns(tenant_id, ["days_of_cover"])
                       if r["days_of_cover"] is not None]
    days_cover_avg = round(sum(days_cover_vals) / len(days_cover_vals), 1) if days_cover_vals else None
    on_hand_by_sku = {}
    for r in inv:
        on_hand_by_sku[r["sku"]] = on_hand_by_sku.get(r["sku"], 0) + (r["on_hand"] or 0)
    if on_hand_by_sku:
        oos_skus_ct = sum(1 for v in on_hand_by_sku.values() if v <= 0)
    elif not has_inv_fact_data:
        # Same fallback as the top-level Inventory value above: the fact table is empty, use
        # seller_skus.stock_on_hand directly rather than report a vacuous 0.
        oos_skus_ct = sum(1 for r in SellerRepository(con).select_columns(tenant_id, ["stock_on_hand"])
                          if r["stock_on_hand"] is not None and r["stock_on_hand"] <= 0)
    else:
        oos_skus_ct = 0
    um_soh = SellerRepository(con).select_columns(tenant_id, ["units_month", "stock_on_hand"])
    has_stock_data = any(r["stock_on_hand"] is not None for r in um_soh)
    vel_soh = SellerRepository(con).select_columns(tenant_id, ["velocity_day", "stock_on_hand"])
    dead_inv_ct = (sum(1 for r in vel_soh if (r["velocity_day"] or 0) < 0.01 and (r["stock_on_hand"] or 0) > 0)
                  if has_stock_data else None)
    stock_note = None if has_stock_data else "add inventory report"
    # Sell Velocity = units sold in the window ÷ window length — units/day, tenant-wide. Reuses
    # order_agg (already fetched above for the Revenue substats' Units Sold card), so no new
    # query. window is always > 0 (validated at the top of this function); 0 units in the window
    # is a real, legitimate 0.0 (not missing) when a dated order feed exists at all.
    sell_velocity = round(order_agg["units"] / window, 2)
    inventory_substats = [
        dict(key="days_of_cover", label="Days of Cover", value=days_cover_avg, trend=None),
        dict(key="oos_risks", label="OOS Risks", value=oos_risk_ct, trend=None,
             note="stockout-forecaster model, <7 day horizon"),
        dict(key="oos_skus", label="OOS SKUs", value=oos_skus_ct, trend=None, note=inv_note),
        dict(key="sell_velocity", label="Sell Velocity", value=sell_velocity, trend=None, note=reports_note),
        dict(key="dead_inventory", label="Dead Inventory", value=dead_inv_ct, trend=None, note=stock_note),
    ]

    ap_totals = AdPerformanceRepository(con).totals(tenant_id)
    spend_tot = sum((v.get("spend") or 0) for v in ap_totals.values())
    sales_tot = sum((v.get("sales") or 0) for v in ap_totals.values())
    roas = round(sales_tot / spend_tot, 2) if spend_tot else None
    entity_tot = AdEntityPerfRepository(con).tenant_totals(tenant_id)
    entity_note = None if entity_tot["rows"] else "no click-level ad data ingested"
    cpc = round(entity_tot["spend"] / entity_tot["clicks"], 2) if entity_tot["clicks"] else None
    # CPA = ad_entity_perf.spend / orders attributed to that campaign; CVR = orders / clicks.
    # Both from the same click-level attributable-ads table CPC already reads (all-time, all
    # campaigns) — no fabrication when a tenant has no click-level data, same note as CPC.
    cpa = round(entity_tot["spend"] / entity_tot["orders"], 2) if entity_tot["orders"] else None
    cvr = round(entity_tot["orders"] / entity_tot["clicks"] * 100, 2) if entity_tot["clicks"] else None
    ads_substats = [
        dict(key="cvr", label="CVR", value=cvr, trend=None, note=entity_note),
        dict(key="roas", label="ROAS", value=roas, trend=None),
        dict(key="cpa", label="CPA", value=cpa, trend=None, note=entity_note),
        dict(key="ctr", label="CTR", value=None, trend=None, note="no impressions data tracked"),
        dict(key="cpc", label="CPC", value=cpc, trend=None, note=entity_note),
    ]

    settle_all = SettlementRepository(con).all_time_summary(tenant_id)
    ad_spend_all = sum((v.get("spend") or 0) for v in ap_totals.values())
    storage_all = StorageFeeRepository(con).all_time_summary(tenant_id)
    units_by_asin_all = OrderRepository(con).all_time_units_by_asin(tenant_id)
    cogs_by_asin = {r["asin"]: (r["cogs"] or 0)
                    for r in SellerRepository(con).select_columns(tenant_id, ["asin", "cogs"])}
    cogs_sold_all = sum(units_by_asin_all.get(a, 0) * cogs_by_asin.get(a, 0) for a in units_by_asin_all)
    outflow_all = ad_spend_all + settle_all["fees"] + storage_all + cogs_sold_all
    cash_balance = settle_all["payout"] - outflow_all
    cash_outflow = ad_tot + settle_win["fees"] + storage_win + cogs_tot
    net_cash_flow = cash - cash_outflow
    pending = OrderRepository(con).pending_deposit_sum(tenant_id)
    cash_substats = [
        dict(key="cash_balance", label="Cash Balance", value=round(cash_balance), trend=None,
             approximate=True, note="running approximation, not bank-reconciled"),
        dict(key="cash_inflow", label="Cash Inflow", value=round(cash), trend=None, note=reports_note),
        dict(key="cash_outflow", label="Cash Outflow", value=round(cash_outflow), trend=None, approximate=True),
        dict(key="net_cash_flow", label="Net Cash Flow", value=round(net_cash_flow), trend=None),
        dict(key="payouts_pending", label="Payouts Pending", value=round(pending), trend=None),
    ]

    con.close()

    return dict(
        window=window,
        basis=basis,
        revenue=dict(value=round(rev), units=int(units), label="Revenue", substats=revenue_substats),
        margin=dict(value=round(margin), pct=round(margin_pct,1), label="Margin", substats=margin_substats),
        cash=dict(value=round(cash), short_paid=round(short_paid), note=cash_note, label="Cash received",
                  substats=cash_substats),
        inventory=dict(value=round(inv_value), units=int(inv_units), low_cover=low,
                       snapshot=True, note=inv_note, label="Inventory value", substats=inventory_substats),
        ads=dict(value=round(ad_tot), tacos=round(tacos,1), modeled=True, label="Ad spend", substats=ads_substats),
    )

def explain_card(tenant_id, card_id):
    """Full provenance trace for Explanation Mode: L1 (deterministic — inputs by source,
    rule, formula, anomaly, calculation/output) and L2 (the exact LLM prompt+response, or
    a note that L2 was not invoked)."""
    con = db.connect()
    card = CardRepository(con).get(tenant_id, card_id)
    if not card:
        con.close(); return {"error": "card not found"}
    rule = RulesRepository(con).get_rule(card["card_type"])
    cond = {}
    if rule:
        try: cond = json.loads(rule["inputs"] or "{}")
        except Exception: cond = {}
    prov = json.loads(card["provenance"] or "[]")
    minis = json.loads(card["minis"] or "[]")
    sources = json.loads(card["sources"] or "[]")

    # inputs grouped by source family
    by = {"own_seller": [], "keepa_market": [], "news_other": []}
    for p in prov:
        label, tag = (p if isinstance(p, (list, tuple)) and len(p) == 2 else (str(p), ""))
        t = (tag or "").upper()
        if t == "OWN" or "own" in label.lower(): by["own_seller"].append(label)
        elif "keepa" in label.lower() or "market" in label.lower() or "competitor" in label.lower(): by["keepa_market"].append(label)
        elif "news" in label.lower() or "recall" in label.lower() or "trend" in label.lower() or "social" in label.lower(): by["news_other"].append(label)
        else: by["own_seller"].append(label) if t == "RULE" else by["news_other"].append(label)
    for s in sources:
        nm = s.get("name", "") if isinstance(s, dict) else str(s)
        low = nm.lower()
        if "keepa" in low and nm not in by["keepa_market"]: by["keepa_market"].append(nm)
        elif any(k in low for k in ("news","recall","trend","social","bis")) and nm not in by["news_other"]: by["news_other"].append(nm)

    # formula from the rule condition
    scope = cond.get("scope"); field = cond.get("field"); op = cond.get("op"); param = cond.get("param")
    params = cond.get("params_default", {})
    OPS = {"lt":"<","lte":"≤","gt":">","gte":"≥","eq":"=","ne":"≠"}
    if field and op:
        thr = params.get(param, param) if param else None
        formula = f"{scope or 'sku'}.{field} {OPS.get(op, op)} {thr if thr is not None else '(threshold)'}"
    else:
        formula = f"special detector {card['card_type']} (deterministic L1)"

    # cached L2 trace from the research payload, if present
    l2 = {"l2_invoked": False, "l2_note": "Open the card's research panel to run L2."}
    payload = CardRepository(con).research_payload(tenant_id, card["dedup_key"])
    if payload:
        try: l2 = json.loads(payload).get("l2", l2)
        except Exception: pass

    # Model layer (between L1 and L2): forecasts that READ metric history and INFORM the
    # card. They never change the L1 numbers. Surfaced here for full transparency:
    # which model, the exact input features it used, and its output + confidence.
    model_section = {"covered": False,
                     "note": "No model covers this detector — the card is fully deterministic (L1).",
                     "predictions": []}
    try:
        from .pipeline import interpret
        from . import models
        detector = interpret.card_type_to_detector_id(card["card_type"], field)
        if card.get("asin"):
            preds = models.predict_for(con, tenant_id, card["asin"], detector)
            if preds:
                model_section = {"covered": True, "detector": detector,
                                 "note": "Models read metric history and inform the card. "
                                         "They never change the L1 numbers — L1 decides what fires and on which figures.",
                                 "predictions": preds}
    except Exception as e:
        model_section = {"covered": False, "note": f"model trace unavailable: {str(e)[:80]}", "predictions": []}
    con.close()

    return {
        "card": {"id": card["id"], "type": card["card_type"], "name": card["type_name"],
                 "finding": card["finding"], "severity": card["severity"],
                 "exposure": {"label": card["exposure_label"], "pct": card["exposure_pct"], "value": card["exposure_val"]}},
        "l1": {
            "inputs_by_source": by,
            "rule": {"id": card["card_type"], "name": (rule["name"] if rule else card["type_name"]),
                     "family": card["family"], "group": cond.get("group"), "surface": cond.get("surface")},
            "formula": formula,
            "thresholds": params,
            "anomaly": {"field": field, "op": op, "threshold": (params.get(param) if param else None)},
            "calculation": minis,
            "output": {"finding": card["finding"], "exposure": card["exposure_label"]},
        },
        "model": model_section,
        "l2": l2,
    }

def load_status(tenant_id):
    """For the persistent header bar: how much data is loaded + last refresh time.
    Own-data is loaded as soon as the tenant is provisioned; the 4 market sources
    fill in via background enrichment."""
    con = db.connect()
    t = db.get_tenant(con, tenant_id)
    own_loaded = bool(t and t["provisioned"])
    last = PullLogRepository(con).max_ok(tenant_id)
    con.close()
    srcs = source_health(tenant_id)
    market_current = sum(1 for s in srcs if s["last_ok"] and s["records"] > 0)
    # 1 unit for own-data + 4 market sources = 5 total
    loaded = (1 if own_loaded else 0) + market_current
    total = 1 + len(srcs)
    return dict(own_loaded=own_loaded, market_current=market_current, market_total=len(srcs),
                loaded=loaded, total=total, pct=round(100*loaded/total),
                last_refresh=last, sources=srcs)


def data_completeness(tenant_id):
    """For customer accounts: which canonical fields are populated by real uploaded reports,
    and therefore which detector groups are active vs. still dark. Drives the completeness
    panel that nudges customers to upload more reports. 'provided' = at least one non-null
    value across the tenant's SKUs (or traffic, for conversion)."""
    con = db.connect()
    try:
        FIELDS = [
            ("price",          "Price",                 "Catalog / Listings"),
            ("cogs",           "COGS",                  "COGS template"),
            ("net_margin_pct", "Margin",                "Catalog + COGS (derived)"),
            ("buybox_pct",     "Buy Box %",             "Sales & Traffic"),
            ("velocity_day",   "Sales velocity",        "Sales / Orders"),
            ("stock_on_hand",  "Inventory & cover",     "Inventory report"),
            ("returns_rate",   "Return rate",           "Returns report"),
            ("tacos",          "Ad efficiency (TACoS)", "Ads / Sales report"),
            ("rating",         "Rating & reviews",      "Listings export"),
        ]
        out, active = [], 0
        for col, label, report in FIELDS:
            n = SellerRepository(con).count_non_null(tenant_id, col)
            provided = n > 0
            active += 1 if provided else 0
            out.append({"field": col, "label": label, "report": report, "provided": provided, "skus": n})
        conv = TrafficRepository(con).count_with_conversion(tenant_id)
        active += 1 if conv > 0 else 0
        out.append({"field": "conversion_pct", "label": "Conversion", "report": "Sales & Traffic",
                    "provided": conv > 0, "skus": conv})
        sku_total = SellerRepository(con).count(tenant_id)
        return {"fields": out, "active": active, "total": len(out), "skus": sku_total}
    finally:
        con.close()
