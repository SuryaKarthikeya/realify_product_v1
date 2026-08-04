"""Multi-channel layer: fan a tenant's (Amazon-seeded) catalog out across five
marketplaces into the canonical `channel_economics` + `channels` tables.

THE SEAM: both the synthesizer (build_multichannel) and the future CSV report parsers
(CsvReportSource.ingest) write into the SAME canonical tables. The cross-channel view,
KPIs, and detectors read those tables and neither know nor care which source filled them
— so flipping from synthetic data to real uploaded reports is a source swap, not a rebuild.

Economics are plausible-but-approximate per channel (fee %, fulfillment), flagged
source='synthetic' so they're honestly replaceable by real settlement files later.
"""
import random, hashlib
from . import db, country as country_mod
from .repositories.seller_repo import SellerRepository
from .repositories.channel_repo import ChannelRepository, ChannelEconomicsRepository

# Per-channel model. fee_pct = marketplace commission/referral; fulfil_fee_pct = extra
# fulfillment fee (FBA/WFS/FBT) as a fraction of price; present = base probability the
# SKU is listed there; price_drift / velocity_mult = ranges sampled deterministically.
CHANNELS = [
    {"channel":"amazon",  "label":"Amazon",      "fee_pct":0.155, "fulfillment":"FBA",
     "present":1.00, "price_drift":(1.00,1.00), "velocity_mult":(1.00,1.00), "fulfil_fee_pct":0.12},
    {"channel":"shopify", "label":"Shopify",     "fee_pct":0.029, "fulfillment":"Self / 3PL",
     "present":0.80, "price_drift":(0.98,1.10), "velocity_mult":(0.15,0.45), "fulfil_fee_pct":0.05},
    {"channel":"walmart", "label":"Walmart",     "fee_pct":0.15,  "fulfillment":"WFS / Self",
     "present":0.55, "price_drift":(0.96,1.05), "velocity_mult":(0.10,0.32), "fulfil_fee_pct":0.10},
    {"channel":"ebay",    "label":"eBay",        "fee_pct":0.125, "fulfillment":"Self",
     "present":0.45, "price_drift":(0.90,1.02), "velocity_mult":(0.05,0.20), "fulfil_fee_pct":0.0},
    {"channel":"tiktok",  "label":"TikTok Shop", "fee_pct":0.08,  "fulfillment":"FBT / Self",
     "present":0.45, "price_drift":(0.82,1.00), "velocity_mult":(0.05,0.40), "fulfil_fee_pct":0.05,
     "creator_pct":0.06},
]

# R14: locale-correct channel set — Channels must reflect the world's country (US: Amazon/Walmart/
# Shopify · IN: Amazon.in/Flipkart/Shopzee), not a fixed US-centric list.
CHANNELS_IN = [
    {"channel":"amazon",   "label":"Amazon.in", "fee_pct":0.155, "fulfillment":"FBA",
     "present":1.00, "price_drift":(1.00,1.00), "velocity_mult":(1.00,1.00), "fulfil_fee_pct":0.10},
    {"channel":"flipkart", "label":"Flipkart",  "fee_pct":0.12,  "fulfillment":"Flipkart Fulfilment",
     "present":0.78, "price_drift":(0.95,1.08), "velocity_mult":(0.20,0.55), "fulfil_fee_pct":0.08},
    {"channel":"shopzee",  "label":"Shopzee",   "fee_pct":0.05,  "fulfillment":"Self / 3PL",
     "present":0.55, "price_drift":(0.90,1.05), "velocity_mult":(0.10,0.35), "fulfil_fee_pct":0.05},
]
_CHANNELS_BY_COUNTRY = {"US": CHANNELS, "IN": CHANNELS_IN}


def channels_for(country):
    return _CHANNELS_BY_COUNTRY.get((country or "US").upper(), CHANNELS)
CH_BY_NAME = {c["channel"]: c for c in CHANNELS}
ORDER = [c["channel"] for c in CHANNELS]

def _rng(*parts):
    return random.Random(int(hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest(), 16) % (2**32))

def register_channels(con, tenant_id, currency, chans=CHANNELS):
    for c in chans:
        ChannelRepository(con).upsert(tenant_id, c["channel"], c["label"], 1, c["fee_pct"], c["fulfillment"], currency)

def build_multichannel(tenant_id, log=print):
    """Fan the seller's SKUs across all channels into channel_economics (+ register
    channels). Idempotent per tenant. Amazon mirrors the seeded economics; other channels
    get drifted price, their own fee model, fulfillment mode, and velocity. Channel set is
    locale-correct (R14): US = Amazon/Walmart/Shopify/…, IN = Amazon.in/Flipkart/Shopzee."""
    prof = country_mod.tenant_profile(tenant_id)
    CHANS = channels_for(prof["country"])
    con = db.connect()
    register_channels(con, tenant_id, prof["currency"], CHANS)
    ChannelEconomicsRepository(con).delete_all(tenant_id)
    skus = SellerRepository(con).all(tenant_id)
    n = 0
    for s in skus:
        asin = s["asin"]; isku = s.get("internal_sku") or ("SKU-" + asin)
        base_price = s["price"]; cogs = s["cogs"]; base_units = s["units_month"]
        if cogs is None:
            continue                            # cost-unknown SKU (QW-2): no channel economics, not a fabricated margin
        for c in CHANS:
            r = _rng(tenant_id, asin, c["channel"])
            present = 1 if (c["channel"] == "amazon" or r.random() < c["present"]) else 0
            if not present:
                # still record an absent row so the cross-channel view can show the gap
                ChannelEconomicsRepository(con).insert_absent(tenant_id, isku, asin, s["title"], s["category"], c["channel"], c["fee_pct"], cogs, c["fulfillment"])
                continue
            price = round(base_price * r.uniform(*c["price_drift"]), 2)
            fee_unit = round(price * (c["fee_pct"] + c.get("fulfil_fee_pct", 0.0) + c.get("creator_pct", 0.0)), 2)
            ad_unit = round(price * r.uniform(0.03, 0.09), 2)
            net_unit = round(price - cogs - fee_unit - ad_unit, 2)
            margin_pct = round(net_unit / price * 100, 1) if price else 0
            units = int(base_units * r.uniform(*c["velocity_mult"]))
            revenue = round(price * units, 2)
            # inventory: channels draw from the seller's shared stock; allocate ~ by velocity
            on_hand = int(s["stock_on_hand"] * r.uniform(0.1, 0.5)) if c["channel"] != "amazon" else int(s["stock_on_hand"])
            dcov = round(on_hand / (units / 30.0), 1) if units else float(s["days_of_cover"])
            ChannelEconomicsRepository(con).insert_present(tenant_id, isku, asin, s["title"], s["category"], c["channel"], price, units, c["fee_pct"],
                fee_unit, ad_unit, cogs, net_unit, margin_pct, revenue, on_hand, dcov, c["fulfillment"])
            n += 1
    con.commit()
    counts = {c["channel"]: ChannelEconomicsRepository(con).count_present(tenant_id, c["channel"]) for c in CHANS}
    con.close()
    log(f"[multichannel][t{tenant_id}] {n} channel-SKU rows: {counts}")
    return counts

# ---------------- cross-channel aggregation (powers the Channels view) ----------------
def cross_channel(tenant_id):
    prof = country_mod.tenant_profile(tenant_id)
    sym = prof["symbol"]
    con = db.connect()
    chans = ChannelRepository(con).active(tenant_id)
    order = [c for c in ORDER if c in {ch["channel"] for ch in chans}] or ORDER
    rows = ChannelEconomicsRepository(con).all(tenant_id)
    con.close()
    by_sku = {}
    for r in rows:
        by_sku.setdefault(r["internal_sku"], {})[r["channel"]] = r

    skus = []
    for isku, chmap in by_sku.items():
        present = {k: v for k, v in chmap.items() if v["present"]}
        if not present:
            continue
        any_row = next(iter(present.values()))
        prices = [v["price"] for v in present.values() if v["price"]]
        pmin, pmax = (min(prices), max(prices)) if prices else (0, 0)
        spread_pct = round((pmax - pmin) / pmin * 100, 1) if pmin else 0
        margins = {k: v["margin_pct"] for k, v in present.items()}
        best = max(margins, key=margins.get) if margins else None
        worst = min(margins, key=margins.get) if margins else None
        total_units = sum(v["units_month"] for v in present.values())
        total_rev = round(sum(v["revenue_month"] for v in present.values()), 2)
        # inventory pooling: shared stock vs TOTAL cross-channel draw
        pooled_on_hand = max((v["on_hand"] for v in present.values()), default=0)  # amazon holds the shared pool
        pooled_days = round(pooled_on_hand / (total_units / 30.0), 1) if total_units else None
        skus.append(dict(
            internal_sku=isku, asin=any_row["asin"], title=any_row["title"], category=any_row["category"],
            channels=[dict(channel=k, label=CH_BY_NAME[k]["label"], price=present[k]["price"],
                           units=present[k]["units_month"], margin_pct=present[k]["margin_pct"],
                           net_unit=present[k]["net_unit"], fulfillment=present[k]["fulfillment"],
                           revenue=present[k]["revenue_month"])
                      for k in order if k in present],
            absent=[CH_BY_NAME[k]["label"] for k in order if k in chmap and not chmap[k]["present"]],
            price_min=pmin, price_max=pmax, price_spread_pct=spread_pct,
            best_margin_channel=CH_BY_NAME[best]["label"] if best else None,
            best_margin_pct=margins.get(best) if best else None,
            worst_margin_channel=CH_BY_NAME[worst]["label"] if worst else None,
            worst_margin_pct=margins.get(worst) if worst else None,
            total_units=total_units, total_revenue=total_rev,
            pooled_on_hand=pooled_on_hand, pooled_days_cover=pooled_days,
            pooling_risk=bool(pooled_days is not None and pooled_days < 21),
            price_drift_flag=bool(spread_pct >= 8),
        ))
    skus.sort(key=lambda x: -x["total_revenue"])

    # per-channel rollup
    chan_summary = []
    for k in order:
        crows = [r for r in rows if r["channel"] == k and r["present"]]
        rev = round(sum(r["revenue_month"] for r in crows), 2)
        units = sum(r["units_month"] for r in crows)
        # revenue-weighted margin
        wm = round(sum(r["margin_pct"] * r["revenue_month"] for r in crows) / rev, 1) if rev else 0
        chan_summary.append(dict(channel=k, label=CH_BY_NAME[k]["label"], skus=len(crows),
                                 revenue=rev, units=units, margin_pct=wm,
                                 fulfillment=CH_BY_NAME[k]["fulfillment"],
                                 fee_pct=round(CH_BY_NAME[k]["fee_pct"]*100, 1)))
    return dict(symbol=sym, currency=prof["currency"], order=order,
                channel_summary=chan_summary, skus=skus,
                totals=dict(revenue=round(sum(c["revenue"] for c in chan_summary), 2),
                            channels=len([c for c in chan_summary if c["skus"]>0]),
                            price_drift=len([s for s in skus if s["price_drift_flag"]]),
                            pooling_risks=len([s for s in skus if s["pooling_risk"]])))

# ---------------- the source seam ----------------
class MultiChannelSynthSource:
    """Synthetic adapter: fills channel_economics from the seeded catalog."""
    mode = "synthetic"
    def ingest(self, tenant_id, log=print):
        return build_multichannel(tenant_id, log=log)

class CsvReportSource:
    """Real adapter (stub): one parser per platform report → SAME canonical tables.
    When wired, each uploaded report (Amazon Sales&Traffic, Shopify Payouts, Walmart
    Settlement, …) parses into channel_economics / settlements / inventory rows exactly
    as the synthesizer does, so nothing downstream changes. Parsers are filled in per the
    per-site report list; this class is the seam the upload grid posts to."""
    mode = "upload"
    # report catalog drives the upload grid (Phase 5) and, later, the parser registry.
    REPORTS = {
        "amazon":  ["Sales & Traffic Business", "All Orders", "Settlement", "FBA Inventory",
                    "Returns by Return Date", "All Listings", "Storage / Aged-Inventory Fee"],
        "shopify": ["Finances / Sales summary", "Sessions / Conversion", "Payouts", "Orders export",
                    "Inventory on-hand", "Refunds", "Products export"],
        "walmart": ["Item Performance / Sales", "Buy Box & Traffic", "Settlement", "Inventory (WFS)",
                    "Returns", "Item / Full-Spec listings", "WFS Storage / Fees"],
        "ebay":    ["Sales / Performance", "Traffic", "Payouts / Transactions", "Orders",
                    "Active Listings", "Returns / cases"],
        "tiktok":  ["Sales / Product analytics", "Traffic (incl. video/live)", "Settlement / Income",
                    "Orders", "Inventory (FBT)", "After-sales / Returns", "Products export"],
    }
    def ingest(self, tenant_id, channel, report, rows, log=print):
        raise NotImplementedError("CSV parsers are stubbed; the synthesizer is the reference implementation.")
