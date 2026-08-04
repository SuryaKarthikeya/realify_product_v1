"""Load synthetic Step-1 seller data into a TENANT's tables.
In production this loader is replaced by report ingestion; the table shape is
identical so it's a swap, not a rebuild. Every write is scoped to tenant_id."""
import json, os, hashlib, random
from . import db, country as country_mod
from .repositories.seller_repo import SellerRepository
from .repositories.order_repo import OrderRepository

# rough INR-per-USD divisor used only to map the bundled INR demo catalog into a
# US price band (synthetic data either way — this just makes US numbers realistic).
_FX_INR_PER_USD = 83.0

def reprice_for_country(skus, prof):
    """Transform the bundled INR demo economics into the target country's price band
    and fee schedule so US (etc.) data is data-correct, not rupee-logic with a $ sign.
    No-op for IN (the demo is already IN)."""
    if prof["country"] == "IN":
        return skus
    lo, hi = prof["price_band"]
    out = []
    for s in skus:
        rnd = random.Random(int(hashlib.md5((prof["country"]+s["asin"]).encode()).hexdigest(), 16) % (2**32))
        p_in = s["price"] or 1.0
        cogs_ratio = (s["cogs"] / p_in) if p_in else 0.4
        ad_ratio   = (s["ad_cost_unit"] / p_in) if p_in else 0.05
        ret_ratio  = (s["return_cost_unit"] / p_in) if p_in else 0.02
        price = p_in / _FX_INR_PER_USD
        price = max(lo, min(hi, price))
        price = (round(price) - 0.01) if price >= 5 else round(price, 2)
        cogs  = round(price * cogs_ratio, 2)
        referral, fba = country_mod.estimate_fees(price, prof, rnd)   # R11.1: price-scaled FBA (was flat)
        ad  = round(price * ad_ratio, 2)
        ret = round(price * ret_ratio, 2)
        net = round(price - cogs - referral - fba - ad - ret, 2)
        margin = round(net / price * 100, 2) if price else 0
        floor = round((cogs + fba + ad + ret) / (1 - prof["referral_pct"]), 2)
        annual_rev = round(price * s["units_year"], 2)
        t = dict(s)
        t.update(price=price, cogs=cogs, referral_fee=referral, fba_fee=fba, ad_cost_unit=ad,
                 return_cost_unit=ret, net_profit_unit=net, net_margin_pct=margin,
                 breakeven_floor=floor, annual_rev_inr=annual_rev)
        out.append(t)
    return out

def load_seller_data(tenant_id, path=None, skus=None):
    """skus: optional caller-supplied list (e.g. user-uploaded SKU/COGS/category seed).
    If None, load the bundled Autofy demo seed. Economics are localized to the
    tenant's configured country (IN default)."""
    prof = country_mod.tenant_profile(tenant_id)
    if skus is None:
        path = path or os.path.join(os.path.dirname(__file__), "seller_data.json")
        skus = json.load(open(path))
        skus = reprice_for_country(skus, prof)     # demo catalog -> tenant's market
        # QW-2: leave ONE deterministic SKU without COGS so the tester exercises the margin-unavailable
        # ("Needs COGS") state in Profit & Ads. Null ONLY cogs — build_row_card recomputes economics from
        # (price, cogs) so it reads "Needs COGS"; the other stored fields stay numeric so no downstream
        # aggregation hits None. The builders that need cost (multichannel / synth_cmaa / synth_ad_graph)
        # skip this SKU explicitly rather than fabricate a margin for it.
        if skus:
            skus[0] = {**skus[0], "cogs": None}
    gmv = sum(s["annual_rev_inr"] for s in skus) or 1
    con = db.connect()
    sellers = SellerRepository(con)
    sellers.delete_all(tenant_id)
    for s in skus:
        sellers.insert(tenant_id, s, round(s["annual_rev_inr"] / gmv * 100, 3))
    # Stamp the canonical internal_sku ('SKU-'+asin, the same id channels.link_channel sets) NOW, before
    # synth_cmaa runs, so ad_performance / sku_revenue_period and build_row_card key on the same value in
    # every path — including a bare SyntheticSource().provision() with no channel layer (tester tests).
    sellers.backfill_internal_sku(tenant_id)
    con.commit()
    n = sellers.count(tenant_id)
    con.close()
    return n

def all_skus(con, tenant_id):
    return SellerRepository(con).all(tenant_id)

def generate_orders(tenant_id, seed=45, recent_days=120):
    """Derive order-level rows FROM the tenant's SKU aggregates so they roll back up.
    Injects short-paid orders (settlement cases) and review-eligible orders."""
    import random, datetime as dt, hashlib
    con = db.connect()
    OrderRepository(con).delete_all(tenant_id)
    skus = all_skus(con, tenant_id)
    today = dt.date.today()
    batch = []
    for s in skus:
        rnd = random.Random(int(hashlib.md5((str(tenant_id)+s["asin"]+str(seed)).encode()).hexdigest(),16)%2**32)
        per_month = max(1, int(s["units_month"]))
        n_orders = max(1, int(per_month * (recent_days/30.0) / rnd.uniform(1.0, 2.2)))
        price = s["price"]; ref = s["referral_fee"]; fba = s["fba_fee"]
        for i in range(n_orders):
            days_ago = rnd.randint(0, recent_days)
            odate = today - dt.timedelta(days=days_ago)
            units = rnd.choices([1,2,3], weights=[80,15,5])[0]
            gross = round(price*units, 2)
            referral = round(ref*units, 2); fbaf = round(fba*units, 2)
            expected = round(gross - referral - fbaf, 2)
            settled = days_ago >= rnd.randint(7,14)
            sdate = (odate + dt.timedelta(days=rnd.randint(7,14))) if settled else None
            short = settled and rnd.random() < 0.06
            actual = round(expected * rnd.uniform(0.55,0.85),2) if short else (expected if settled else 0.0)
            delivered = days_ago >= 6
            ddate = (odate + dt.timedelta(days=rnd.randint(4,8))) if delivered else None
            in_window = delivered and 5 <= (today - (ddate or today)).days <= 30
            has_rev = 1 if (delivered and rnd.random() < 0.18) else 0
            elig = 1 if (in_window and not has_rev) else 0
            oid = f"{rnd.randint(402,408)}-{rnd.randint(1000000,9999999)}-{rnd.randint(1000000,9999999)}"
            batch.append((tenant_id, oid, s["asin"], odate.isoformat(), units, gross, referral, fbaf, expected, actual,
                 sdate.isoformat() if sdate else None, ddate.isoformat() if ddate else None,
                 has_rev, elig, "settled" if settled else "pending"))
    orders = OrderRepository(con)
    orders.insert_many_synthetic(batch)
    con.commit()
    n = orders.count(tenant_id)
    short_n = orders.count_short_paid(tenant_id)
    elig_n = orders.count_review_eligible(tenant_id)
    con.close()
    return dict(orders=n, short_paid=short_n, review_eligible=elig_n)
