"""SC-Reports reconcile — bake REAL Seller-Central prod data (2mo old) into a tenant.

The live crawl fixed CURRENT market fields (price/rating/reviews/competitors). This fills the
DEMAND + ECONOMICS the crawl can't see, from the seller's own Seller-Central exports in
docs/SC Reports/. Scoped to a tenant's existing ASINs — never touches the live-crawled
price/rating/reviews/cogs; only the fields below.

Phases (each idempotent, keyed by ASIN → the tenant's internal_sku 'SKU-<ASIN>'):
  1. orders+demand  Unified Transaction (Mar/Apr/May) -> REBUILD seller_orders (real daily
                    units/gross/fees; the forecast's Chronos series reads this) and recompute
                    seller_skus units_month/units_year/velocity_day/annual_rev_inr/
                    rev_share_pct/returns_rate. Fixes the synthetic velocity (e.g. B09ZVQ29FB
                    was 3777/mo synthetic -> ~0-1/mo real).
  2. business       BusinessReport -> traffic (sessions/conversion/buybox) + seller_skus.buybox_pct.
  3. returns        FBA Returns -> ria_return_aspects (reason -> aspect, quality-negative flag).
  4. ads            Sponsored-Products reports -> ad_performance (monthly spend/sales) + tacos.

Real data is Mar-May 2026 (3 months). Low-volume SKUs correctly resolve to near-zero demand.
"""
import os, glob, datetime as dt
from .. import db, config

SC_DIR = os.environ.get("SC_REPORTS_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "SC Reports"))
# Amazon return-reason codes that indicate a PRODUCT-QUALITY problem (the negative signal #12
# cares about) vs neutral logistics/change-of-mind reasons.
_QUALITY_NEG = {"DEFECTIVE", "NOT_AS_DESCRIBED", "SWITCHEROO", "MISSING_PARTS",
                "DAMAGED_BY_CARRIER", "DAMAGED_BY_FC", "QUALITY_UNACCEPTABLE",
                "NEVER_ARRIVED", "PRODUCT_NOT_AS_DESCRIBED"}


def _pd():
    import pandas as pd
    return pd


def _f(x):
    """Parse an Amazon money/number cell: strip currency/commas, () = negative."""
    if x is None:
        return 0.0
    s = str(x).strip().replace(",", "").replace("₹", "").replace("$", "")
    if not s or s.lower() in ("nan", "none"):
        return 0.0
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()%").strip()
    try:
        v = float(s)
    except ValueError:
        return 0.0
    return -v if neg else v


def sku_asin_map():
    """merchant SKU -> ASIN, from the Fee Preview report (the only report with both)."""
    pd = _pd()
    fp = pd.read_csv(_find("439433"), dtype=str)
    return {r["sku"]: r["asin"] for _, r in fp.iterrows() if r.get("sku") and r.get("asin")}


def _find(token):
    hits = glob.glob(os.path.join(SC_DIR, f"*{token}*"))
    if not hits:
        raise FileNotFoundError(f"SC report matching {token!r} not in {SC_DIR}")
    return hits[0]


def _load_unified():
    """Concat the 3 monthly Unified Transaction files. Header is at row 14 (skiprows=13)."""
    pd = _pd()
    frames = []
    for f in sorted(glob.glob(os.path.join(SC_DIR, "2026*MonthlyUnifiedTransaction.csv"))):
        df = pd.read_csv(f, skiprows=13, dtype=str, on_bad_lines="skip")
        df.columns = [c.strip().lower() for c in df.columns]
        frames.append(df)
    return pd.concat(frames, ignore_index=True), len(frames)


# ---------------- phase 1: orders + demand ----------------
def rebuild_orders_and_demand(con, tenant_id, log=print):
    pd = _pd()
    uni, n_months = _load_unified()
    s2a = sku_asin_map()
    tenant_asins = set(_tenant_asins(con, tenant_id))
    uni["asin"] = uni["sku"].map(s2a)
    uni = uni[uni["asin"].isin(tenant_asins)].copy()
    uni["qty"] = uni["quantity"].map(_f)
    uni["sales"] = uni["product sales"].map(_f)
    uni["sfee"] = uni.get("selling fees", 0).map(_f) if "selling fees" in uni else 0
    uni["ffee"] = uni.get("fba fees", 0).map(_f) if "fba fees" in uni else 0
    uni["typ"] = uni["type"].astype(str).str.lower()
    # date/time is like "30 Apr 2026 6:40:12 pm UTC" — extract "<d> <Mon> <YYYY>" and
    # normalise to ISO so the forecast's daily series sorts/grids correctly (a bare [:10]
    # would truncate to "30 Apr 202").
    dparts = uni["date/time"].astype(str).str.extract(r"(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})")[0]
    uni["date"] = pd.to_datetime(dparts, format="%d %b %Y", errors="coerce").dt.strftime("%Y-%m-%d")
    uni = uni[uni["date"].notna()]

    orders = uni[uni["typ"].str.contains("order", na=False) & (uni["qty"] > 0)]
    refunds = uni[uni["typ"].str.contains("refund", na=False)]

    # REBUILD seller_orders: one row per (asin, date), summed. The forecast groups by date.
    con.execute("DELETE FROM seller_orders WHERE tenant_id=?", (tenant_id,))
    daily = orders.groupby(["asin", "date"]).agg(
        units=("qty", "sum"), gross=("sales", "sum"),
        sfee=("sfee", "sum"), ffee=("ffee", "sum")).reset_index()
    for _, r in daily.iterrows():
        asin = r["asin"]
        con.execute(
            "INSERT INTO seller_orders(tenant_id,order_id,asin,order_date,units,gross,"
            "referral_fee,fba_fee,status,channel,internal_sku) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (tenant_id, f"UT-{asin}-{r['date']}", asin, r["date"], int(r["units"]),
             round(float(r["gross"]), 2), round(abs(float(r["sfee"])), 2),
             round(abs(float(r["ffee"])), 2), "shipped", "amazon", f"SKU-{asin}"))

    # recompute seller_skus demand fields per ASIN
    ord_units = orders.groupby("asin")["qty"].sum()
    ref_units = refunds.groupby("asin")["qty"].apply(lambda s: abs(s).sum())
    ord_sales = orders.groupby("asin")["sales"].sum()
    changed = []
    price_rows = {r["asin"]: r["price"] for r in con.execute(
        "SELECT asin, price FROM seller_skus WHERE tenant_id=?", (tenant_id,)).fetchall()}
    rev = {}
    for asin in tenant_asins:
        u = float(ord_units.get(asin, 0.0))
        um = int(round(u / max(1, n_months)))
        rev[asin] = um * 12 * float(price_rows.get(asin) or 0)
    total_rev = sum(rev.values()) or 1.0
    for asin in tenant_asins:
        u = float(ord_units.get(asin, 0.0))
        um = int(round(u / max(1, n_months)))
        uy = um * 12
        vel = round(u / max(1, n_months * 30), 3)
        # refunds can be for orders placed BEFORE the 3-mo window; cap at 100% so a
        # low-volume SKU can't report a nonsensical >100% return rate.
        rr = min(1.0, round(float(ref_units.get(asin, 0.0)) / u, 4)) if u > 0 else 0.0
        ar = round(rev[asin], 2)
        rs = round(100.0 * rev[asin] / total_rev, 3)
        con.execute(
            "UPDATE seller_skus SET units_month=?, units_year=?, velocity_day=?, "
            "annual_rev_inr=?, rev_share_pct=?, returns_rate=? WHERE tenant_id=? AND asin=?",
            (um, uy, vel, ar, rs, round(rr * 100, 2), tenant_id, asin))
        changed.append((asin, um, round(rr * 100, 1)))
    con.commit()
    log(f"[sc][t{tenant_id}] rebuilt {len(daily)} daily order rows over {n_months}mo; "
        f"recomputed demand for {len(changed)} SKUs")
    return changed


# ---------------- phase 2: business report ----------------
def apply_business_report(con, tenant_id, log=print):
    pd = _pd()
    br = pd.read_csv(_find("BusinessReport"), dtype=str)
    key = [c for c in br.columns if "Child" in c and "ASIN" in c][0]
    cS = "Sessions - Total"; cU = "Unit Session Percentage"; cB = "Featured Offer Percentage"
    cP = [c for c in br.columns if c.startswith("Page Views - Total") and "B2B" not in c][0]
    tenant_asins = set(_tenant_asins(con, tenant_id))
    rdate = "2026-06-29"
    n = 0
    for _, r in br.iterrows():
        asin = r[key]
        if asin not in tenant_asins:
            continue
        sess = int(_f(r.get(cS))); pv = int(_f(r.get(cP)))
        conv = round(_f(r.get(cU)), 2); bb = int(round(_f(r.get(cB))))
        isku = f"SKU-{asin}"
        con.execute("DELETE FROM traffic WHERE tenant_id=? AND internal_sku=? AND date=?",
                    (tenant_id, isku, rdate))
        con.execute("INSERT INTO traffic(tenant_id,channel,internal_sku,date,sessions,"
                    "page_views,conversion_pct,buybox_pct) VALUES(?,?,?,?,?,?,?,?)",
                    (tenant_id, "amazon", isku, rdate, sess, pv, conv, bb))
        con.execute("UPDATE seller_skus SET buybox_pct=? WHERE tenant_id=? AND asin=?",
                    (bb, tenant_id, asin))
        n += 1
    con.commit()
    log(f"[sc][t{tenant_id}] business report applied to {n} SKUs (sessions/conversion/buybox)")
    return n


# ---------------- phase 3: returns -> aspects ----------------
def apply_returns(con, tenant_id, log=print):
    pd = _pd()
    ret = pd.read_csv(_find("439451"), dtype=str)
    s2a = sku_asin_map()
    if "asin" not in ret or ret["asin"].isna().all():
        ret["asin"] = ret["sku"].map(s2a)
    tenant_asins = set(_tenant_asins(con, tenant_id))
    ret = ret[ret["asin"].isin(tenant_asins)]
    ret["qty"] = ret["quantity"].map(_f) if "quantity" in ret else 1
    now = db.now_iso()
    con.execute("DELETE FROM ria_return_aspects WHERE tenant_id=?", (tenant_id,))
    n = 0
    for (asin, reason), g in ret.groupby(["asin", "reason"]):
        cnt = int(g["qty"].sum())
        if cnt <= 0:
            continue
        neg = int(str(reason).upper() in _QUALITY_NEG) * cnt
        con.execute("INSERT INTO ria_return_aspects(tenant_id,internal_sku,aspect,n,negative,"
                    "computed_at) VALUES(?,?,?,?,?,?)",
                    (tenant_id, f"SKU-{asin}", str(reason), cnt, neg, now))
        n += 1
    con.commit()
    log(f"[sc][t{tenant_id}] returns -> {n} (asin,reason) aspect rows")
    return n


# ---------------- phase 4: ads -> ad_performance + tacos ----------------
def apply_ads(con, tenant_id, log=print):
    pd = _pd()
    frames = []
    for f in glob.glob(os.path.join(SC_DIR, "Sponsored_Products_Advertised_product_report*.xlsx")):
        frames.append(pd.read_excel(f, dtype=str))
    if not frames:
        log(f"[sc][t{tenant_id}] no ad reports found"); return 0
    ad = pd.concat(frames, ignore_index=True)
    acol = [c for c in ad.columns if "Advertised ASIN" in c][0]
    scol = [c for c in ad.columns if c.strip() == "Spend"][0]
    # The exports can use different attribution windows -> "7 Day Total Sales" vs
    # "14 Day Total Sales" become SEPARATE columns after concat; a row has exactly one.
    # Coalesce by summing across all of them (the others are NaN -> 0).
    salecols = [c for c in ad.columns if "Total Sales" in c]
    ad["asin"] = ad[acol]
    ad["month"] = ad["Date"].astype(str).str[:7] + "-01"
    ad["spend_"] = ad[scol].map(_f)
    ad["sales_"] = sum(ad[c].map(_f) for c in salecols)
    tenant_asins = set(_tenant_asins(con, tenant_id))
    ad = ad[ad["asin"].isin(tenant_asins)]
    now = db.now_iso()
    con.execute("DELETE FROM ad_performance WHERE tenant_id=? AND source=?", (tenant_id, "sp_report"))
    g = ad.groupby(["asin", "month"]).agg(spend=("spend_", "sum"), sales=("sales_", "sum")).reset_index()
    n = 0
    tot_spend, tot_sales = {}, {}
    for _, r in g.iterrows():
        isku = f"SKU-{r['asin']}"
        con.execute("INSERT INTO ad_performance(tenant_id,internal_sku,period_start,grain,spend,"
                    "sales,source,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                    (tenant_id, isku, r["month"], "month", round(float(r["spend"]), 2),
                     round(float(r["sales"]), 2), "sp_report", now))
        tot_spend[r["asin"]] = tot_spend.get(r["asin"], 0) + float(r["spend"])
        tot_sales[r["asin"]] = tot_sales.get(r["asin"], 0) + float(r["sales"])
        n += 1
    # TACoS = ad spend / total revenue (use real annual_rev from phase 1 as the denominator base)
    for asin in tot_spend:
        row = con.execute("SELECT annual_rev_inr FROM seller_skus WHERE tenant_id=? AND asin=?",
                          (tenant_id, asin)).fetchone()
        ar = float(row["annual_rev_inr"]) if row and row["annual_rev_inr"] else 0.0
        # ad spend is ~3 months in the reports; annualize to compare with annual_rev
        ann_spend = tot_spend[asin] * 4
        tacos = round(100.0 * ann_spend / ar, 2) if ar > 0 else None
        if tacos is not None:
            con.execute("UPDATE seller_skus SET tacos=? WHERE tenant_id=? AND asin=?",
                        (tacos, tenant_id, asin))
    con.commit()
    log(f"[sc][t{tenant_id}] ads -> {n} monthly ad_performance rows; tacos updated")
    return n


def _tenant_asins(con, tenant_id):
    return [r["asin"] for r in con.execute(
        "SELECT asin FROM seller_skus WHERE tenant_id=?", (tenant_id,)).fetchall()]


def reconcile_all(tenant_id, log=print):
    con = db.connect()
    try:
        demand = rebuild_orders_and_demand(con, tenant_id, log)
        br = apply_business_report(con, tenant_id, log)
        ret = apply_returns(con, tenant_id, log)
        ads = apply_ads(con, tenant_id, log)
    finally:
        con.close()
    return {"demand_skus": len(demand), "business": br, "return_rows": ret, "ad_rows": ads}
