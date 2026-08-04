"""Seed handling for onboarding.

Two synthesize sub-paths:
  - 'sample'  -> use the bundled Autofy ASIN set (prototype-2 shortcut); handled by
                 SyntheticSource(seed_skus=None) loading seller_data.json directly.
  - 'upload'  -> the user supplies a minimal list (ASIN, COGS, category, optional price);
                 expand_minimal_seed() fabricates the full economics/velocity/inventory so
                 the rows flow through the existing pipeline. (Richer all-report synthesis
                 with >=75% rule coverage is Step 4; this is the input mechanism for now.)

CSV columns accepted (case-insensitive, order-free): asin, cogs, category, price, title.
Only asin + cogs + category are required; price/title are optional."""
import csv, io, random, hashlib

REQUIRED = ("asin", "cogs", "category")

def parse_seed_csv(text):
    """Parse uploaded CSV text into minimal seed rows. Defensive: skips blank/bad rows."""
    rows = []
    rdr = csv.DictReader(io.StringIO(text))
    norm = {h: (h or "").strip().lower() for h in (rdr.fieldnames or [])}
    for raw in rdr:
        r = {norm.get(k, k): (v or "").strip() for k, v in raw.items()}
        asin = (r.get("asin") or "").strip()
        if not asin:
            continue
        try:
            cogs = float(r.get("cogs") or 0)
        except ValueError:
            cogs = 0.0
        if cogs <= 0:
            continue  # COGS is required to synthesize economics
        rows.append({
            "asin": asin,
            "cogs": cogs,
            "category": (r.get("category") or "Other Accessories").strip() or "Other Accessories",
            "price": _num(r.get("price")),
            "title": (r.get("title") or "").strip(),
        })
    return rows

def _num(v):
    try:
        return float(v) if v not in (None, "") else 0.0
    except (ValueError, TypeError):
        return 0.0

def catalog_only_seed(rows, prof=None):
    """CUSTOMER path — NO synthesis. Create seller_skus rows from a real catalog/listings
    export: asin/sku, title, category, price (real). Referral fee is the exact marketplace
    %. COGS is applied separately from the validated COGS template. Every behavioural metric
    (velocity, units, stock, days_of_cover, buybox_pct, tacos, returns_rate, rating, reviews)
    is left NULL so detectors that need it stay dark until the relevant report is uploaded.
    annual_rev_inr is 0 (a numeric 'unknown' sentinel — it's used in > comparisons)."""
    from ..country import profile as _profile
    prof = prof or _profile("IN")
    referral_rate = prof["referral_pct"]
    out = []
    for i, r in enumerate(rows):
        asin = str(r.get("asin", "")).strip()
        if not asin:
            continue
        cat = (str(r.get("category") or "Other Accessories").strip()) or "Other Accessories"
        try:
            price = float(r.get("price") or 0) or None
        except (ValueError, TypeError):
            price = None
        referral = round(price * referral_rate, 2) if price else None
        out.append(dict(
            asin=asin, title=(r.get("title") or f"{cat} item {i+1}"), category=cat,
            ptype=cat, amazon_cat=cat, price=price, cogs=None,
            referral_fee=referral, fba_fee=None, ad_cost_unit=None, return_cost_unit=None,
            net_profit_unit=None, net_margin_pct=None, breakeven_floor=None,
            units_month=None, units_year=None, velocity_day=None, annual_rev_inr=0,
            stock_on_hand=None, days_of_cover=None, buybox_pct=None,
            tacos=None, returns_rate=None, rating=None, review_count=None,
        ))
    return out


def expand_minimal_seed(rows, prof=None):
    """Expand [{asin,cogs,category,price?,title?}] -> full seller_skus rows.
    Derives Amazon-style economics from COGS/price and synthesizes velocity/inventory
    with a Pareto skew, deliberately injecting a spread of conditions (low cover, low
    Buy Box, high returns, overstock) so the rule engine has signals to fire on.
    `prof` is the tenant's country profile (referral %, FBA schedule); defaults to IN."""
    from ..country import profile as _profile
    prof = prof or _profile("IN")
    referral_rate = prof["referral_pct"]
    n = max(1, len(rows))
    # assign revenue ranks for a Pareto-ish velocity distribution
    expanded = []
    for i, r in enumerate(rows):
        asin = str(r.get("asin", "")).strip()
        try:
            cogs = float(r.get("cogs") or 0)
        except (ValueError, TypeError):
            cogs = 0.0
        if not asin or cogs <= 0:
            continue                                   # skip invalid rows defensively
        cat = (str(r.get("category") or "Other Accessories").strip()) or "Other Accessories"
        rnd = random.Random(int(hashlib.md5(asin.encode()).hexdigest(), 16) % (2**32))
        price = float(r.get("price") or 0) or round(cogs * rnd.uniform(2.0, 3.4), 2)
        from ..country import estimate_fees as _fees
        referral, fba = _fees(price, prof, rnd)          # R11.1: price-scaled FBA (was a flat constant)
        ad = round(price * rnd.uniform(0.02, 0.06), 2)
        ret_cost = round(price * rnd.uniform(0.01, 0.04), 2)
        net = round(price - cogs - referral - fba - ad - ret_cost, 2)
        margin = round(net / price * 100, 2) if price else 0
        floor = round((cogs + fba + ad + ret_cost) / (1 - referral_rate), 2)
        # velocity: top ~20% are high movers (Pareto). rank by a stable hash bucket.
        bucket = (int(hashlib.md5((asin+"v").encode()).hexdigest(), 16) % 100)
        if bucket >= 82:   units_month = rnd.randint(900, 4000)
        elif bucket >= 55: units_month = rnd.randint(150, 900)
        else:              units_month = rnd.randint(8, 150)
        velocity = round(units_month / 30.0, 2)
        units_year = units_month * 12
        annual_rev = round(price * units_year, 2)
        # inventory + health, with injected conditions:
        doc = rnd.choices(
            [rnd.uniform(5, 24), rnd.uniform(25, 90), rnd.uniform(120, 400)],
            weights=[22, 55, 23])[0]                       # ~22% near-stockout, ~23% overstock
        stock = int(velocity * doc)
        buybox = rnd.choices([rnd.randint(45, 80), rnd.randint(85, 100)], weights=[28, 72])[0]
        returns = round(rnd.choices([rnd.uniform(8, 22), rnd.uniform(1, 7)], weights=[30, 70])[0], 1)
        tacos = round(rnd.uniform(4, 18), 1)
        rating = round(rnd.uniform(3.5, 4.8), 1)
        reviews = rnd.randint(5, 1800)
        expanded.append(dict(
            asin=asin, title=(r.get("title") or f"{cat} item {i+1}"), category=cat,
            ptype=cat, amazon_cat=cat, price=price, cogs=cogs, referral_fee=referral,
            fba_fee=fba, ad_cost_unit=ad, return_cost_unit=ret_cost, net_profit_unit=net,
            net_margin_pct=margin, breakeven_floor=floor, units_month=units_month,
            units_year=units_year, velocity_day=velocity, annual_rev_inr=annual_rev,
            stock_on_hand=stock, days_of_cover=round(doc, 1), buybox_pct=buybox,
            tacos=tacos, returns_rate=returns, rating=rating, review_count=reviews,
        ))
    return expanded
