"""Step 4: inject conditions into SYNTHETIC data so the rule catalog has signals to
fire on, and support a shuffle so a few refreshes reveal every rule.

IMPORTANT: this only ever runs on synthetic tenants. Real uploaded CSVs carry
whatever signals they carry — Realify never fabricates conditions on real data.

Three modes (the seller picks in ⚙ Account → Test data):
  - reroll   : keep the same ASINs/catalog & orders; just re-roll which conditions
               apply so different rules trigger each refresh.
  - full     : full re-synthesize (regenerate orders too), then inject a fresh spread.
  - coverage : deliberately place ≥1 SKU in every condition band to maximize the
               number of distinct rules that fire in a single pass (testing).
"""
import random, hashlib
from . import db
from .repositories.rules_repo import RulesRepository
from .repositories.card_repo import CardRepository
from .repositories.seller_repo import SellerRepository
from .repositories.fact_repos import TrafficRepository

# Each band writes fields onto a SKU to trip a family of rules.
def _b_high_tacos(u, rnd):      u["tacos"] = round(rnd.uniform(16, 32), 1)               # ADS-*
def _b_high_margin(u, rnd):     u["net_margin_pct"] = round(rnd.uniform(30, 45), 1); u["tacos"] = round(rnd.uniform(2, 8), 1)  # OPP-*
def _b_margin_low(u, rnd):      u["net_margin_pct"] = round(rnd.uniform(4, 7), 1)        # MARGIN-12
def _b_loss(u, rnd):            u["net_margin_pct"] = round(rnd.uniform(-4, 3), 1)       # MARGIN-16
def _b_aged(u, rnd):            u["days_of_cover"] = round(rnd.uniform(165, 260), 1)     # INV-21/CASH-31
def _b_stockout(u, rnd):        u["days_of_cover"] = round(rnd.uniform(8, 20), 1); u["stock_on_hand"] = rnd.randint(5, 40)  # INV-17/19/20
def _b_low_buybox(u, rnd):      u["buybox_pct"] = rnd.randint(50, 80)                    # BB/CT
def _b_low_rating(u, rnd):      u["rating"] = round(rnd.uniform(2.8, 3.7), 1); u["review_count"] = rnd.randint(5, 30)  # RR

SKU_BANDS = [_b_high_tacos, _b_high_margin, _b_margin_low, _b_loss, _b_aged,
             _b_stockout, _b_low_buybox, _b_low_rating]
# traffic-scope band handled post-build (conversion lives in the traffic table)
LOW_CONV = lambda rnd: round(rnd.uniform(2, 7), 1)                                       # SV/CL

def inject_sku_conditions(tenant_id, seed, mode):
    con = db.connect()
    sellers = SellerRepository(con)
    skus = [{"asin": a} for a in sellers.asins(tenant_id, ordered=True)]
    rnd = random.Random(seed)
    # normalize tacos to a consistent percent scale for any SKU we don't override
    sellers.normalize_tacos_random(tenant_id)
    n = len(skus)
    assign = {}  # asin -> band fn
    if mode == "coverage":
        # guarantee at least one SKU per band, round-robin across the rest
        for i, s in enumerate(skus):
            assign[s["asin"]] = SKU_BANDS[i % len(SKU_BANDS)]
    else:
        # realistic spread: ~40% of SKUs get a random band (seed rotates the picks)
        for s in skus:
            if rnd.random() < 0.40:
                assign[s["asin"]] = rnd.choice(SKU_BANDS)
    for asin, fn in assign.items():
        u = {}
        fn(u, rnd)
        if not u: continue
        sellers.update_fields_by_asin(tenant_id, asin, u)
    con.commit(); con.close()
    return len(assign)

def inject_traffic_conditions(tenant_id, seed, mode):
    """Post-build: drop conversion on a subset so Search/Content rules fire."""
    con = db.connect()
    rows = TrafficRepository(con).internal_skus_ordered(tenant_id)
    rnd = random.Random(seed + 7)
    picks = rows if mode == "coverage" else [s for s in rows if rnd.random() < 0.25]
    # in coverage mode only a few need low conversion; cap so it stays realistic
    if mode == "coverage": picks = rows[:max(1, len(rows)//8)]
    for isku in picks:
        TrafficRepository(con).set_conversion(tenant_id, isku, LOW_CONV(rnd))
    con.commit(); con.close()
    return len(picks)

def make_seed(tenant_id, mode):
    base = f"{tenant_id}:{mode}:{random.random()}"
    return int(hashlib.md5(base.encode()).hexdigest(), 16) % (2**31)

def coverage(tenant_id):
    """Explicit coverage measure: distinct rules fired / total enabled rules."""
    con = db.connect()
    total = RulesRepository(con).count_rules()
    fired = CardRepository(con).count_distinct_types(tenant_id)
    con.close()
    return dict(fired=fired, total=total, pct=round(100*fired/total) if total else 0)
