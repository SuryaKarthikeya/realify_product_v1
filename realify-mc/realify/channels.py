"""Step 3: build the channel-aware layer for a tenant from its Amazon SKU/order data.
Derives the identity layer (products + channel_listings) and the normalized per-channel
fact tables (traffic, settlements, inventory, returns, storage_fees) so the same data
that powers the existing Amazon detectors now ALSO flows through the reconciled shape.
Everything is tagged channel='amazon'; Shopify/etc. adapters add rows the same way later."""
import random, hashlib, datetime as dt
from . import db
from .repositories.seller_repo import SellerRepository
from .repositories.order_repo import OrderRepository
from .repositories.fact_repos import TrafficRepository, InventoryRepository, SettlementRepository
from .repositories.channel_repo import (ProductRepository, ChannelListingRepository,
    ReturnsRepository, StorageFeeRepository)

RETURN_REASONS = ["wrong size/fit", "not as described", "defective", "no longer needed",
                  "quality below expectation", "shipping damage"]

def build_channel_layer(tenant_id, channel="amazon"):
    con = db.connect()
    today = dt.date.today()
    # clear this tenant's derived layer (idempotent)
    for _repo in (ProductRepository, ChannelListingRepository, TrafficRepository,
                  SettlementRepository, InventoryRepository, ReturnsRepository, StorageFeeRepository):
        _repo(con).delete_all(tenant_id)
    skus = SellerRepository(con).all(tenant_id)

    for s in skus:
        asin = s["asin"]
        internal_sku = "SKU-" + asin            # canonical id (synthetic: 1 product : 1 amazon listing)
        rnd = random.Random(int(hashlib.md5((str(tenant_id)+asin+"ch").encode()).hexdigest(),16)%2**32)
        # link internal_sku back onto the source rows
        SellerRepository(con).link_channel(tenant_id, asin, internal_sku, channel)
        OrderRepository(con).link_channel(tenant_id, asin, internal_sku, channel)
        # product (COGS lives here — channel-agnostic)
        ProductRepository(con).upsert(tenant_id, internal_sku, s["title"], s["category"], "Autofy", s["cogs"], db.now_iso())
        # channel listing (synthetic links are 'confirmed'; real auto-links would be 'auto' pending verify)
        ChannelListingRepository(con).upsert(tenant_id, internal_sku, channel, asin, asin, "active", "confirmed", s["price"], f"https://www.amazon.in/dp/{asin}")

        # ---- traffic (Sales & Traffic report): sessions implied by units / conversion ----
        conv = round(rnd.uniform(6, 18), 1)
        sessions = int(s["units_month"] / (conv/100.0)) if conv else s["units_month"]*8
        TrafficRepository(con).insert(tenant_id, channel, internal_sku, today.isoformat(), sessions, int(sessions*rnd.uniform(1.2,1.8)), conv, s["buybox_pct"])

        # ---- inventory (FBA Inventory report): split stock into states ----
        oh = int(s["stock_on_hand"])
        inbound = int(oh*rnd.uniform(0,0.3)); reserved=int(oh*rnd.uniform(0.02,0.12))
        unfulfillable = int(oh*rnd.uniform(0,0.05))
        InventoryRepository(con).insert(tenant_id, channel, internal_sku, today.isoformat(), oh, inbound, reserved, unfulfillable, s["days_of_cover"])

        # ---- storage fees (Storage/Aged Inventory report): surcharge for overstocked/aged ----
        vol = round(rnd.uniform(0.02, 0.6), 3)
        monthly = round(vol * rnd.uniform(30, 80), 2)
        aged = round(monthly * rnd.uniform(1.5, 4.0), 2) if s["days_of_cover"] > 120 else 0.0
        age_days = int(s["days_of_cover"]) if s["days_of_cover"] > 120 else rnd.randint(10, 90)
        StorageFeeRepository(con).insert(tenant_id, channel, internal_sku, today.strftime("%Y-%m"), monthly, aged, vol, age_days)

        # ---- returns (Returns report): return-level rows from returns_rate (already a fraction) ----
        n_returns = max(0, int(s["units_month"] * (s["returns_rate"] or 0) / 4))   # ~weekly slice
        for _ in range(min(n_returns, 40)):
            d = today - dt.timedelta(days=rnd.randint(0, 30))
            ReturnsRepository(con).insert(tenant_id, channel, internal_sku, d.isoformat(),
                f"{rnd.randint(402,408)}-{rnd.randint(1000000,9999999)}-{rnd.randint(1000000,9999999)}",
                1, rnd.choice(RETURN_REASONS), round(s["price"]*rnd.uniform(0.8,1.0),2))

    # ---- settlements (Settlement report): roll up from settled orders ----
    orders = OrderRepository(con).settled(tenant_id)
    sbatch = []
    for o in orders:
        o = dict(o)
        fees = round((o["referral_fee"] or 0) + (o["fba_fee"] or 0), 2)
        sbatch.append((tenant_id, channel, o["internal_sku"], o["order_id"],
            o["settlement_date"], o["gross"], fees, o["actual_deposit"], 0.0))
    SettlementRepository(con).insert_many(sbatch)
    con.commit()
    counts = {"products": ProductRepository(con).count(tenant_id),
              "channel_listings": ChannelListingRepository(con).count(tenant_id),
              "traffic": TrafficRepository(con).count(tenant_id),
              "inventory": InventoryRepository(con).count(tenant_id),
              "returns": ReturnsRepository(con).count(tenant_id),
              "settlements": SettlementRepository(con).count(tenant_id),
              "storage_fees": StorageFeeRepository(con).count(tenant_id)}
    con.close()
    return counts

def reconciled_products(tenant_id):
    """The single reconciled row per product across channels (the cross-channel promise).
    Currency single (INR). With only Amazon today, channels=['amazon']; the shape is ready
    for more channels to fan in without changing this function."""
    con = db.connect()
    prods = ProductRepository(con).all(tenant_id)
    out = []
    for p in prods:
        isku = p["internal_sku"]
        listings = ChannelListingRepository(con).by_sku(tenant_id, isku)
        # per-channel units/revenue from orders
        chan_rows = OrderRepository(con).channel_rollup(tenant_id, isku)
        per_channel = {r["channel"]: dict(units=r["units"] or 0, revenue=round(r["revenue"] or 0,2),
                                          orders=r["orders"]) for r in chan_rows}
        total_units = sum(c["units"] for c in per_channel.values())
        total_rev = round(sum(c["revenue"] for c in per_channel.values()), 2)
        # blended margin: revenue - COGS*units - fees(from settlements)
        fees = SettlementRepository(con).sum_fees_by_sku(tenant_id, isku)
        cogs_total = (p["cogs"] or 0) * total_units
        blended_margin = round(total_rev - cogs_total - fees, 2)
        blended_margin_pct = round(blended_margin/total_rev*100, 1) if total_rev else 0
        inv = InventoryRepository(con).sum_by_sku(tenant_id, isku)
        out.append(dict(internal_sku=isku, title=p["title"], category=p["category"], cogs=p["cogs"],
            channels=[l["channel"] for l in listings], listings=listings, per_channel=per_channel,
            total_units=total_units, total_revenue=total_rev, blended_margin=blended_margin,
            blended_margin_pct=blended_margin_pct, total_on_hand=inv["oh"], total_inbound=inv["ib"]))
    con.close()
    out.sort(key=lambda x: -x["total_revenue"])
    return out
