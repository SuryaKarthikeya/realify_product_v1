"""Workspace Actions — projects the existing card/feed system (realify/api.py::get_feed) into
the per-domain action rows the Workspace page's Actions table needs. Reuses get_feed() verbatim
as the data source (JSON decoding, surface/group stamping, action_kind derivation, rank sort
already done there) rather than re-querying `cards` directly. Lives in its own module, not
api.py, because api.py is already over this repo's 400-line file cap (tests/test_file_length.py)
— adding more here would make an already-failing check worse.
"""
import html
import re

from . import api, db
from .repositories.seller_repo import SellerRepository
from .repositories.channel_repo import ChannelRepository
from .models import StockoutForecaster

# Cards are tagged with a group (via api._surface_map, sourced from the rule catalog). Intelligence-
# surface groups map onto the 5 Workspace KPI domains; Research-surface groups (Demand, Opportunity,
# Competitive, Risk, News) belong to a different, existing tab and are out of scope here.
# "Pricing & Buy Box" intentionally appears under BOTH revenue and margin — approved duplication,
# not a bug: buy-box ownership is a revenue lever, repricing is a margin lever, same rule group.
DOMAIN_GROUPS = {
    "revenue": {"Sales", "Pricing & Buy Box"},
    "margin": {"Margin", "Pricing & Buy Box"},
    "inventory": {"Inventory"},
    "ads": {"Ads"},
    "cash": {"Cash"},
}
INTEL_GROUPS = {"Sales", "Margin", "Cash", "Inventory", "Ads", "Pricing & Buy Box"}

_TAG_RE = re.compile(r"<[^>]+>")


def _plain(text):
    """Strip HTML tags AND unescape entities (e.g. '&#9881;' -> the gear glyph itself, not the
    literal escape sequence). cards.finding/why carry real markup (<b>, <span class='rupee'>,
    numeric entities) authored for a server-rendered HTML UI; this API is consumed as plain text,
    so none of that should leak through literally. get_feed()/the existing /feed endpoint keep
    the raw HTML unchanged — this stripping is local to the Actions projection only."""
    return html.unescape(_TAG_RE.sub("", text or "")).strip()


DEFAULT_LIMIT = 50


def actions(tenant_id, groups=INTEL_GROUPS, limit=DEFAULT_LIMIT):
    """Action rows for the Workspace page — all Intelligence-surface groups by default, or a
    single domain's groups via DOMAIN_GROUPS[domain]. Never fabricates a value: fields genuinely
    unavailable (no asin, no channel registry, insufficient forecast history) come back None
    with a note, matching the same honesty convention as the KPI sub-cards.

    Returns (rows, total): `total` is the full matching count BEFORE `limit` is applied, so a
    caller can tell the user more exist. `get_feed()` already sorts by rank_score/severity/
    exposure/is_new, so truncating to `limit` keeps the highest-priority rows, not an arbitrary
    slice. The slice happens BEFORE per-row enrichment (the StockoutForecaster call below is the
    expensive part — one model call per row) so response time stays bounded by `limit`, not by
    how many cards a tenant's real, continuously-growing data has produced."""
    rows = api.get_feed(tenant_id, surface="intelligence", groups=groups)
    total = len(rows)
    rows = rows[:limit] if limit else rows

    con = db.connect()
    try:
        asin_channel = {r["asin"]: r["channel"] for r in
                        SellerRepository(con).select_columns(tenant_id, ["asin", "channel"])}
        channel_fulfillment = {c["channel"]: c["fulfillment"] for c in ChannelRepository(con).active(tenant_id)}
        sf = StockoutForecaster()

        out = []
        for r in rows:
            asin = r.get("asin")
            channel = asin_channel.get(asin) if asin else None
            fulfillment = channel_fulfillment.get(channel, "FBA") if channel else None
            stockout_days, stockout_note = None, None
            if asin:
                pred = sf.predict(con, tenant_id, asin)
                if pred.get("value") is not None:
                    stockout_days = int(round(pred["value"]))
                else:
                    stockout_note = "insufficient history for a forecast"
            fabricated = r.get("exposure_fabricated")
            out.append({
                "id": r["id"],
                "description": _plain(r.get("finding")),
                "why": _plain(r.get("why")),
                "category": r.get("category"),
                "channel": channel,
                "skus": 1,
                "fulfillment": fulfillment,
                "stockout_days": stockout_days,
                "stockout_note": stockout_note,
                "confidence": r.get("confidence"),
                "confidence_label": r.get("conf_label"),
                "impact": None if fabricated else r.get("exposure_val"),
                "impact_pct": None if fabricated else r.get("exposure_pct"),
                "card_type": r.get("card_type"),
                "group": r.get("group"),
                "action": r.get("action"),
                "action_kind": r.get("action_kind"),
            })
        return out, total
    finally:
        con.close()
