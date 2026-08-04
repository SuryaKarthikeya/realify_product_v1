"""Typed fixture for Your Category Analyst — a fully-populated AnalystBrief that conforms to the
contract in analyst.py. This is the concrete target the future analyst service must reproduce; it is
NOT synthesis logic. Numbers are illustrative but pre-formatted the way L1 would emit them, and every
one carries a provenance tier (official vs scraped) so the UI can badge scraped figures as directional.
"""
from .analyst import (
    OFFICIAL, SCRAPED, Provenance, Metric, Move, BrandPosition, ScopeBar, Brief,
    SignalItem, WhitespaceItem, CompetitiveItem, VoiceItem, MarketPulseItem, MovesLoop,
    AskAnalyst, AnalystBrief,
)

_CATEGORIES = ["Auto Accessories", "Car Electronics", "Bike Accessories", "Home & Kitchen"]
_BANDS = ["Value (< ₹1,000)", "Mid (₹1,000–2,500)", "Premium (> ₹2,500)"]

# provenance shortcuts
def _off(source, note=""): return Provenance(tier=OFFICIAL, source=source, note=note)
def _scr(source="competitor listing"): return Provenance(tier=SCRAPED, source=source, note="directional")


def fixture_brief(category=None, price_band=None) -> AnalystBrief:
    cat = category or _CATEGORIES[0]
    band = price_band or _BANDS[1]

    scope = ScopeBar(
        category=cat, price_band=band, categories=_CATEGORIES, price_bands=_BANDS,
        position=BrandPosition(
            share=Metric("Your share of band", "14.2%", _off("your catalog + Keepa")),
            rank=Metric("Category rank", "#4 of 31", _off("Keepa BSR")),
            velocity=Metric("Velocity (30d)", "▲ +8.1%", _off("your orders")),
        ),
    )

    m_reprice = Move("mv-reprice", "Reprice AUTOFY-COVER-01 to ₹2,049",
                     "MotoShield now undercuts you by ₹293 on the contested 3-layer cover; a ₹43 trim "
                     "regains Buy Box share without breaching your ₹1,761 floor.",
                     effort="low", impact="₹2.4L/mo protected", prov=_off("your catalog"))
    m_capture = Move("mv-capture", "Line up the phthalate-compliant SKU for the freed demand",
                     "A BIS order will likely delist 2 competitor covers; you already stock a compliant "
                     "3-layer alternative — stage inventory + ads to capture the window.",
                     effort="medium", impact="₹1.8L/mo capture", prov=_off("BIS govt feed"))
    m_whitespace = Move("mv-ambient", "Pilot an ambient interior lighting kit",
                        "Clear whitespace adjacent to your mounts line: 42% margin, low competition, "
                        "rising search — enter with one hero SKU.",
                        effort="high", impact="₹1.9L/mo est.", prov=_off("Keepa + search trends"))

    brief = Brief(
        dated="Fri · Jul 3",
        narrative=("Overnight, the Auto Accessories mid-band tilted in your favour on regulation and "
                   "against you on price. A BIS phthalate order threatens two competitor covers just as "
                   "MotoShield cut the 3-layer cover 12% to take your Buy Box. Net: defend the cover on "
                   "price today, then move on the demand a delisting frees. One clean whitespace opened "
                   "in interior lighting."),
        moves=[m_reprice, m_capture, m_whitespace],
    )

    signals = [
        SignalItem("sig-1", 92,
                   "MotoShield cut its 3-layer car cover to ₹2,099 (−12%) overnight.",
                   "It now undercuts your AUTOFY-COVER-01 by ₹293 on your highest-revenue SKU.",
                   m_reprice,
                   [Metric("Their price", "₹2,099", _scr("Keepa offer + listing")),
                    Metric("Your price", "₹2,392", _off("your catalog")),
                    Metric("Your floor", "₹1,761", _off("your unit economics"))]),
        SignalItem("sig-2", 84,
                   "BIS quality order tightens phthalate limits on PVC car covers.",
                   "Two competitor SKUs look non-compliant and likely to be pulled — demand you can take.",
                   m_capture,
                   [Metric("Affected competitor SKUs", "2", _scr("competitor listings")),
                    Metric("Freed monthly demand", "₹1.8L", _off("category model")),
                    Metric("Your compliant SKUs ready", "4", _off("your catalog"))]),
        SignalItem("sig-3", 61,
                   "Search for 'magnetic car phone mount' up +41% over 14 days.",
                   "You carry K713A-MOUNT here — real, rank-confirmed demand, not a promo blip.",
                   Move("mv-scale", "Protect stock + lean ad spend into the mount",
                        "Both search and BSR slope agree; scale before competitors notice.",
                        effort="medium", impact="₹90K/mo", prov=_off("your catalog")),
                   [Metric("Search 14d", "+41%", _off("search trends")),
                    Metric("BSR slope", "rising", _off("Keepa BSR"))]),
    ]

    whitespace = [
        WhitespaceItem("ws-1", "Ambient interior lighting kit",
                       "Adjacent to your mounts/electronics line; buyers of your mounts co-purchase "
                       "lighting. Low competition, high margin, rising demand.",
                       88, Metric("Est. margin", "42%", _off("sourcing model")),
                       "Car Electronics", m_whitespace, _off("Keepa + search trends")),
        WhitespaceItem("ws-2", "Monsoon-grade bike cover (heavy-duty)",
                       "Your bike-cover velocity spikes +38% in monsoon; the heavy-duty tier is thin in "
                       "your catalog and competitors are out of stock.",
                       74, Metric("Est. margin", "36%", _off("your unit economics")),
                       "Bike Accessories",
                       Move("mv-hd", "Add a heavy-duty monsoon SKU", "Fill the tier before the surge.",
                            effort="high", impact="₹1.2L/mo", prov=_off("your catalog")),
                       _off("your orders")),
    ]

    competitive = [
        CompetitiveItem("cmp-1", "MotoShield", "Cut 3-layer cover 12% and is buying Buy Box share.",
                        m_reprice,
                        [Metric("Price move", "−12%", _scr()),
                         Metric("Est. Buy Box win rate", "~63%", _scr("marketplace scrape")),
                         Metric("Overlap with your SKUs", "6", _off("your catalog"))]),
        CompetitiveItem("cmp-2", "RoadArmour (new entrant)",
                        "Launched 18 SKUs 15–20% below category median.",
                        Move("mv-watch", "Track weekly; hold price",
                             "Buying share on price, not rank yet — respond only if they take a Buy Box.",
                             effort="low", impact="watch", prov=_off("your catalog")),
                        [Metric("Their SKUs", "18", _scr("seller landscape scrape")),
                         Metric("Avg price vs median", "−18%", _scr()),
                         Metric("Overlap with you", "6 SKUs", _off("your catalog"))]),
    ]

    voice = [
        VoiceItem("Waterproofing", Metric("You", "4.4★", _off("your reviews")),
                  Metric("Peer set", "4.1★", _scr("competitor reviews")),
                  "You lead on waterproofing — lean into it in copy and ads.", "Competitive"),
        VoiceItem("Fit / sizing", Metric("You", "3.8★", _off("your reviews")),
                  Metric("Peer set", "4.3★", _scr("competitor reviews")),
                  "Sizing complaints drag your covers vs the set — a fit guide could close the gap.",
                  "Whitespace"),
        VoiceItem("Value for money", Metric("You", "4.0★", _off("your reviews")),
                  Metric("Peer set", "4.0★", _scr("competitor reviews")),
                  "At parity on value — price moves won't swing sentiment much.", ""),
    ]

    market_pulse = [
        MarketPulseItem("mp-1", "BIS notifies revised phthalate limits for PVC auto textiles.",
                        "This is the regulation behind Signal #2 — it's the delisting trigger; act on the "
                        "capture move now, not when competitors are already pulled.", 90,
                        _off("BIS govt feed")),
        MarketPulseItem("mp-2", "Monsoon forecast: early onset in western states.",
                        "Pulls your bike-cover surge forward ~2 weeks — compress the restock timeline.",
                        66, _off("IMD forecast")),
        MarketPulseItem("mp-3", "Marketplace ad CPCs reported up in auto category.",
                        "Directional only (trade press) — watch your TACoS but don't reprice ads on this "
                        "alone; wait for your own spend data to confirm.", 40, _scr("trade press")),
    ]

    moves = MovesLoop(
        recommended=[m_reprice, m_capture, m_whitespace],
        acted=[Move("mv-past-1", "Raised LED footwell kit price to clear the margin floor",
                    "Acted on last week's memo.", effort="low", impact="₹0.4L/mo recovered",
                    status="acted", outcome="Margin +6pts; units flat — net positive.",
                    prov=_off("your catalog"))],
        dismissed=[Move("mv-past-2", "Match RoadArmour launch pricing",
                        "Dismissed — they hadn't taken any Buy Box.", status="dismissed",
                        outcome="Held; no share lost 3 weeks on.", prov=_off("your catalog"))],
    )

    ask = AskAnalyst(
        scope=cat,
        prompt=f"Ask about {cat} — competitors, whitespace, pricing, or a specific SKU.",
        suggested=[f"What's the fastest ₹ move in {cat} this week?",
                   "How exposed am I if MotoShield keeps cutting price?",
                   "Which whitespace has the best margin-to-effort ratio?"],
    )

    return AnalystBrief(
        generated_at="2026-07-03T06:00:00+05:30",
        synthesis_source="fixture",
        scope=scope, brief=brief, signals=signals, whitespace=whitespace,
        competitive=competitive, voice=voice, market_pulse=market_pulse, moves=moves, ask=ask,
    )
