"""Phase-0 CMAA proof harness (throwaway wrapper; the math lives in realify/domain/cmaa.py).

Revised: ASP and velocity use PAID order rows only (product sales > 0). The ₹0-value order rows
(free replacements / promo units) are counted separately as a warranty-cost signal and never
pollute ASP or per-unit margin.

The output CSV is fully explainable: every input column names the report it came from, every
computed column carries its formula, and all intermediate values are present so any single row
reproduces the whole calculation. A companion *_SOURCES.csv legend maps column -> sheet -> formula.
"""
import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from realify.domain import cmaa  # noqa: E402

MONEY = ["product sales", "shipping credits", "gift wrap credits", "promotional rebates",
         "selling fees", "fba fees", "other transaction fees", "other"]   # excludes GST/TCS/TDS + total

# column -> (source sheet, formula/basis) for the legend + header tags
SOURCES = {
    "sku": ("Unified Transaction / COGS sheet", "SKU key"),
    "title": ("Fee-preview report (439433)", "product-name"),
    "asins": ("SP Ad report <-> Fee-preview map", "advertised ASINs for this SKU"),
    "paid_units": ("Unified Transaction", "Σ quantity on Order rows where product sales > 0"),
    "replacement_units": ("Unified Transaction", "Σ qty, Order rows marketplace=amazon.in & product sales=0 (true free/promo)"),
    "mcf_units": ("Unified Transaction", "Σ qty, Order rows marketplace=si-prod-in.stores.amazon.in (Shopify via FBA)"),
    "refunded_units": ("Unified Transaction", "Σ quantity on Refund rows"),
    "net_units": ("Unified Transaction", "paid_units − refunded_units"),
    "asp_paid": ("Unified Transaction", "Σ product sales ÷ Σ quantity over PAID order rows"),
    "cogs_unit": ("Autofy_COGS_Data.xlsx", "seller-supplied unit cost"),
    "referral_fee_unit": ("Unified Transaction", "|selling fees + other tx fees| ÷ paid_units (ACTUAL)"),
    "fba_fee_unit": ("Unified Transaction", "|fba fees| ÷ paid_units (ACTUAL)"),
    "net_revenue": ("Unified Transaction", "Σ product sales (paid orders) + Σ product sales (refunds, negative)"),
    "amazon_net": ("Unified Transaction", "Σ non-tax money cols over paid orders + refunds (excludes GST/TCS/TDS)"),
    "cogs_total": ("computed", "cogs_unit × net_units"),
    "warranty_cost": ("computed", "cogs_unit × replacement_units (cost of free-replacement units)"),
    "contribution": ("computed", "amazon_net − cogs_total"),
    "gcm_pct": ("computed", "contribution ÷ net_revenue"),
    "breakeven_acos_pct": ("computed", "= gcm_pct (break-even ACoS)"),
    "ad_spend": ("SP Advertised Product report (14-day, Apr–May)", "Σ Spend"),
    "ad_sales": ("SP Advertised Product report (14-day, Apr–May)", "Σ 14 Day Total Sales"),
    "actual_acos_pct": ("computed", "ad_spend ÷ ad_sales"),
    "wasted_spend": ("computed", "max(ad_spend − ad_sales × gcm_pct, 0)"),
    "quadrant": ("computed (domain/cmaa.py)", "SCALE / FIX ADS / FIX MARGIN / CUT-DIVEST at margin_floor=0"),
}


def _num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", "", regex=False), errors="coerce").fillna(0.0)


def load_cogs(up):
    df = pd.read_excel(os.path.join(up, "Autofy_COGS_Data.xlsx"))
    df.columns = [str(c).strip().lower() for c in df.columns]
    sku_c = [c for c in df.columns if "sku" in c][0]
    cost_c = [c for c in df.columns if "price" in c or "cost" in c][0]
    return dict(zip(df[sku_c].astype(str).str.strip(), _num(df[cost_c])))


def load_identity(up):
    asin2sku, title = {}, {}
    fee = pd.read_csv(os.path.join(up, "439433020633.csv")); fee.columns = [c.strip().lower() for c in fee.columns]
    for _, r in fee.iterrows():
        a, s = str(r.get("asin", "")).strip(), str(r.get("sku", "")).strip()
        if a and s and a.lower() != "nan":
            asin2sku.setdefault(a, s); title.setdefault(s, str(r.get("product-name", ""))[:70])
    ret = pd.read_csv(os.path.join(up, "439451020633.csv")); ret.columns = [c.strip().lower() for c in ret.columns]
    for _, r in ret.iterrows():
        a, s = str(r.get("asin", "")).strip(), str(r.get("sku", "")).strip()
        if a and s and a not in asin2sku and a.lower() != "nan":
            asin2sku[a] = s
    return asin2sku, title


def load_economics(up, months):
    frames = [pd.read_csv(os.path.join(up, f"2026{m}MonthlyUnifiedTransaction.csv"), skiprows=13) for m in months]
    d = pd.concat(frames, ignore_index=True); d["Sku"] = d["Sku"].astype(str).str.strip()
    for c in MONEY:
        d[c] = _num(d[c])
    d["quantity"] = _num(d["quantity"]); d["amazon_net"] = d[MONEY].sum(axis=1)
    d["_shop"] = (d["marketplace"].astype(str).str.contains("stores.amazon.in", case=False, na=False)
                  if "marketplace" in d.columns else False)
    order = d[d["type"] == "Order"]; refund = d[d["type"] == "Refund"]
    paid = order[(order["product sales"] > 0) & (~order["_shop"])]   # direct Amazon paid
    zero = order[(order["product sales"] == 0) & (~order["_shop"])]  # true free replacements/promo
    mcf = order[order["_shop"]]                                      # Shopify via MCF (revenue in Shopify)
    econ = {}
    for sku in set(d["Sku"]) - {"nan", ""}:
        p = paid[paid["Sku"] == sku]; z = zero[zero["Sku"] == sku]; rf = refund[refund["Sku"] == sku]
        m = mcf[mcf["Sku"] == sku]
        paid_units = p["quantity"].sum()
        if paid_units <= 0:
            continue
        refunded = rf["quantity"].sum(); net_units = paid_units - refunded
        gross_paid = p["product sales"].sum()
        net_rev = gross_paid + rf["product sales"].sum()
        amazon_net = p["amazon_net"].sum() + rf["amazon_net"].sum()
        ref_pu = -(p["selling fees"].sum() + p["other transaction fees"].sum()) / paid_units
        fba_pu = -p["fba fees"].sum() / paid_units
        econ[sku] = dict(paid_units=paid_units, replacement_units=z["quantity"].sum(),
                         mcf_units=m["quantity"].sum(),
                         refunded_units=refunded, net_units=net_units,
                         asp_paid=gross_paid / paid_units, referral_fee_unit=ref_pu, fba_fee_unit=fba_pu,
                         net_revenue=net_rev, amazon_net=amazon_net)
    return econ


def load_ads(up, start, end):
    a = pd.read_excel(os.path.join(up, "Sponsored_Products_Advertised_product_report__1_.xlsx"))
    a["Date"] = pd.to_datetime(a["Date"]); a = a[(a["Date"] >= start) & (a["Date"] <= end)]
    sc = [c for c in a.columns if "Total Sales" in c][0]
    return a.groupby("Advertised ASIN").agg(spend=("Spend", "sum"), ad_sales=(sc, "sum")).reset_index()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uploads", default="/mnt/user-data/uploads")
    ap.add_argument("--out", default="/mnt/user-data/outputs/cmaa_autofy.csv")
    ap.add_argument("--margin-floor", type=float, default=0.0)
    args = ap.parse_args()
    up = args.uploads
    start, end = pd.Timestamp("2026-04-01"), pd.Timestamp("2026-05-31")

    cogs = load_cogs(up); asin2sku, title = load_identity(up)
    econ = load_economics(up, ["Apr", "May"]); ads = load_ads(up, start, end)
    total_ad_spend = float(ads["spend"].sum()); n_asins = ads["Advertised ASIN"].nunique()

    sku_ads = {}; unmapped_spend = 0.0; unmapped_asins = 0
    for _, r in ads.iterrows():
        a = str(r["Advertised ASIN"]).strip(); sku = asin2sku.get(a)
        if not sku:
            unmapped_spend += float(r["spend"]); unmapped_asins += 1; continue
        acc = sku_ads.setdefault(sku, {"spend": 0.0, "ad_sales": 0.0, "asins": set()})
        acc["spend"] += float(r["spend"]); acc["ad_sales"] += float(r["ad_sales"]); acc["asins"].add(a)

    rows = []; judged_spend = 0.0; excluded_no_econ = 0.0
    for sku, ad in sku_ads.items():
        e = econ.get(sku); uc = cogs.get(sku)
        if e is None or uc is None:
            if not ad["ad_sales"]:
                rows.append(_row(sku, title, ad, None, None, cmaa.evaluate(ad["spend"], 0, None, None), 0, 0))
                judged_spend += ad["spend"]
            else:
                excluded_no_econ += ad["spend"]
            continue
        cogs_total = uc * e["net_units"]; warranty = uc * e["replacement_units"]
        contribution = e["amazon_net"] - cogs_total
        res = cmaa.evaluate(ad["spend"], ad["ad_sales"], contribution, e["net_revenue"], args.margin_floor)
        judged_spend += ad["spend"]
        rows.append(_row(sku, title, ad, e, uc, res, cogs_total, warranty, contribution))

    cols = list(SOURCES.keys())
    out = pd.DataFrame(rows)[cols].sort_values("wasted_spend", ascending=False)
    # source-tagged headers
    out.columns = [f"{c} [{SOURCES[c][0]}]" if SOURCES[c][0] != "computed" else f"{c} [= {SOURCES[c][1]}]" for c in cols]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out.to_csv(args.out, index=False)
    legend = args.out.replace(".csv", "_SOURCES.csv")
    pd.DataFrame([{"column": c, "source_sheet": SOURCES[c][0], "formula_or_basis": SOURCES[c][1]} for c in cols]).to_csv(legend, index=False)

    raw = pd.DataFrame(rows)
    total = raw["wasted_spend"].sum()
    robust = raw.loc[raw["gcm_pct"].fillna(-1) >= 0, "wasted_spend"].sum()
    neg = raw.loc[raw["gcm_pct"].fillna(0) < 0, "wasted_spend"].sum()
    below_cost = raw[(raw["asp_paid"].notna()) & (raw["cogs_unit"].notna()) & (raw["cogs_unit"] > raw["asp_paid"])]
    print("=" * 74)
    print("  AUTOFY — CMAA PROOF (REVISED: paid-only ASP)  window Apr–May 2026, certain ₹ only")
    print("=" * 74)
    print(f"\n  (A) ₹{robust:,.0f}  confirmed ad waste on POSITIVE-margin SKUs (robust)")
    print(f"  (B) ₹{neg:,.0f}  on SKUs still negative-margin after the ASP fix")
    print(f"      SKUs now genuinely selling below cost: {len(below_cost)} (was 21 pre-fix)")
    print(f"  Mechanical total above break-even: ₹{total:,.0f}\n")
    print(f"  Coverage: {len(raw)} advertised SKUs judged / {n_asins} ASINs; "
          f"ad spend judged ₹{judged_spend:,.0f}/₹{total_ad_spend:,.0f} ({100*judged_spend/max(1,total_ad_spend):.0f}%).")
    print(f"  Excluded: {unmapped_asins} unmapped ASINs (₹{unmapped_spend:,.0f}); no-econ ₹{excluded_no_econ:,.0f}.")
    for q in ["SCALE", "FIX ADS", "CUT/DIVEST", "FIX MARGIN"]:
        s = raw[raw["quadrant"] == q]
        if len(s):
            print(f"   • {q:12s} {len(s):4d} SKUs   ₹{s['wasted_spend'].sum():,.0f}")
    print(f"\n  -> {args.out}\n  -> {legend}")


def _row(sku, title, ad, e, uc, res, cogs_total, warranty, contribution=None):
    r = {"sku": sku, "title": title.get(sku, ""), "asins": ",".join(sorted(ad["asins"])),
         "ad_spend": round(ad["spend"], 2), "ad_sales": round(ad["ad_sales"], 2),
         "cogs_unit": None if uc is None else round(uc, 2),
         "cogs_total": round(cogs_total, 2), "warranty_cost": round(warranty, 2),
         "contribution": None if contribution is None else round(contribution, 2),
         "gcm_pct": None if res["gcm_pct"] is None else round(100 * res["gcm_pct"], 1),
         "breakeven_acos_pct": None if res["breakeven_acos"] is None else round(100 * res["breakeven_acos"], 1),
         "actual_acos_pct": None if res["actual_acos"] is None else round(100 * res["actual_acos"], 1),
         "wasted_spend": round(res["wasted_spend"] or 0, 2), "quadrant": res["quadrant"] or "NO-SALES"}
    for f in ["paid_units", "replacement_units", "mcf_units", "refunded_units", "net_units", "asp_paid",
              "referral_fee_unit", "fba_fee_unit", "net_revenue", "amazon_net"]:
        r[f] = None if e is None else round(e[f], 2)
    return r


if __name__ == "__main__":
    main()
