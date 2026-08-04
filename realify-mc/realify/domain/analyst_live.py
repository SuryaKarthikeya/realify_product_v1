"""Category Analyst — Phase 1 LIVE assembly (reshape only).

Builds a real AnalystBrief from existing L1 tenant data — the C1–C9 feed cards (materiality =
rank_score), the category's own SKU economics, and the action ledger. NO new ingestion, NO scraping.

Three-plane rule: L1 owns every number, ranking and classification here; the prose is
deterministic-from-L1 (the `_phrase*` seam a real L2 later replaces, introducing no new number); the
client renders and never computes. Business numbers are emitted as structured Metrics (value +
explain part) so they plug into the same explain_mode ⓘ as Profit & Ads — the raw sort score is NOT
surfaced as a user-facing metric.

FLOOR DISCIPLINE (P0-2): a card finding may say "under your floor"; the analyst OWNS that verdict
here — it only lets a margin-below-floor framing through when L1 seller data confirms
net_margin_pct < margin_floor for the SKU, and phrases the floor value from L1. Cards that assert a
breach the data contradicts are dropped (not surfaced as a false problem).

Exposure gate: Whitespace / Voice of Customer are fixture — synthetic content is emitted ONLY for the
fixture tenant (account_type 'tester' or data_mode 'synthetic'); a real tenant gets an empty list +
coming-state copy, never a fabricated number.
"""
import hashlib, json, random, re

from .analyst import (
    OFFICIAL, SCRAPED, LIVE, PARTIAL, FIXTURE, COMING,
    Provenance, Metric, Move, BrandPosition, ScopeBar, Brief, SignalItem, CompetitiveItem,
    MarketPulseItem, MovesLoop, AskAnalyst, AnalystBrief, SectionState, AnalystStates,
)
from . import explain
from ..repositories.card_repo import CardRepository
from ..repositories.seller_repo import SellerRepository
from ..repositories.action_repo import ActionRepository
from ..repositories.tenant_repo import TenantRepository

_BANDS = ["Value (< ₹1,000)", "Mid (₹1,000–2,500)", "Premium (> ₹2,500)"]


def _bands_for(tid, con):
    """R14: locale-correct category price bands — US in $ (9.99/79.99), IN in ₹ (1,000/2,500)."""
    from .. import country as _c
    prof = _c.tenant_profile(tid, con)
    s = prof["symbol"]
    if prof["country"] == "IN":
        return [f"Value (< {s}1,000)", f"Mid ({s}1,000–2,500)", f"Premium (> {s}2,500)"]
    return [f"Value (< {s}20)", f"Mid ({s}20–50)", f"Premium (> {s}50)"]
_FIX_COMING = {"whitespace": "Opportunity scoring coming.",
               "voice": "Category + competitor sentiment coming."}
_HKIND = {"price_cut": "Price cut", "new_entrant": "New entrant",
          "assortment_shift": "Assortment shift", "ratings_surge": "Ratings surge"}
# human source label per L1 field tag / provenance label, so a section's provenance names its real
# source (not the raw column, e.g. "net_margin_pct" leaking across sections — P2-2).
_SRC = {"KEEPA": "Keepa · market", "OWN": "your catalog", "NEWS": "news / gov feed",
        "RULE": "your thresholds"}
_TAGS = re.compile(r"<[^>]+>")


def _off(src, note=""):
    return Provenance(OFFICIAL, src, note)


def _scr(src="competitor listing"):
    return Provenance(SCRAPED, src, "directional")


def _strip(s):
    return _TAGS.sub("", str(s or "")).strip()


def _coming_metric(label):
    return Metric(label, "—", _off("not built this phase"), field_state=COMING)


def _market_synth(tid, cat, skus):
    """R15: deterministic synthetic category position from the tenant's OWN catalog + a stable seed
    (hash of tenant+category+SKU set, mirroring seller.py's random.Random(md5(...))). Same world ⇒
    identical (share ∈ (0,1], rank ∈ 1..N int, N a plausible 8–40 count) — modeled, not a live read."""
    keys = "|".join(sorted(str(s.get("asin") or s.get("internal_sku") or "") for s in skus))
    rng = random.Random(int(hashlib.md5(f"{tid}|{cat}|{keys}".encode()).hexdigest(), 16) % 2**32)
    n_comp = 8 + rng.randint(0, 32)                     # modeled category set: 8..40 players
    share = 0.02 + rng.random() * 0.28                  # (0.02, 0.30] of the band — sane magnitude
    rank = max(1, min(n_comp, int(1 + round((1 - (share - 0.02) / 0.28) * (n_comp - 1)))))
    return share, rank, n_comp


def _card_provs(card):
    try:
        return [(p[0], p[1]) if isinstance(p, (list, tuple)) and len(p) == 2 else (str(p), "")
                for p in json.loads(card.get("provenance") or "[]")]
    except Exception:
        return []


def _human_src(lbl, tag):
    """Real, human source name for a provenance entry — never the raw metric column."""
    if "scrap" in lbl.lower() or "competitor listing" in lbl.lower():
        return None                      # scraped — handled by tier
    return _SRC.get((tag or "").upper()) or _SRC.get(lbl.upper()) or (lbl if lbl.isalpha() else "your L1 signals")


def _prov_list(cards):
    """Section-level provenance with accurate source names (P2-2)."""
    seen = {}
    for c in cards:
        for lbl, tag in _card_provs(c):
            if "scrap" in lbl.lower():
                seen.setdefault(SCRAPED, _scr())
            else:
                seen.setdefault(OFFICIAL, _off(_human_src(lbl, tag) or "your L1 signals"))
    return list(seen.values()) or [_off("your L1 signals")]


def _row_prov(card):
    """Per-row provenance (P2-2): scraped·directional if any source is a scrape, else official Keepa."""
    for lbl, tag in _card_provs(card):
        if "scrap" in lbl.lower() or "competitor listing" in lbl.lower():
            return _scr(lbl)
    return _off(_human_src(*(_card_provs(card)[0])) if _card_provs(card) else "Keepa · market")


def _minis(card):
    try:
        return [(m[0], m[1]) for m in json.loads(card.get("minis") or "[]")
                if isinstance(m, (list, tuple)) and len(m) == 2]
    except Exception:
        return []


def _name(card, smap):
    """Merchandiser-readable label: product title (truncated) or SKU code — never a raw ASIN (P2-4)."""
    sku = smap.get(card.get("asin")) or {}
    title = sku.get("title") or ""
    if title:
        return (title[:40] + "…") if len(title) > 41 else title
    return sku.get("internal_sku") or card.get("asin") or (card.get("category") or "your catalog")


def _effort(card):
    return {"crit": "high", "act": "medium", "opp": "medium", "watch": "low"}.get(card.get("severity"), "medium")


def _at_stake(card):
    """The ₹-at-stake as a STRUCTURED metric with an explain part (P1-3) — the number a VP acts on gets
    the ⓘ, not the internal sort score."""
    val = _strip(card.get("exposure_val"))
    if not val:
        return None
    return Metric("₹ at stake / mo", val, _off("your catalog"),
                  explain=explain.part(
        "Monthly ₹ at stake on this SKU", "monthly revenue exposed = annual revenue ÷ 12",
        [(lbl, _strip(v), None) for lbl, v in _minis(card)[:4]] or [("Exposure", val, None)],
        val, provenance=["your catalog"], timeframe_basis="current month"))


def _biz_metrics(card, smap):
    """Structured business metrics with explain ⓘ: ₹-at-stake, margin %, Buy Box % (P1-3)."""
    out = []
    a = _at_stake(card)
    if a:
        out.append(a)
    sku = smap.get(card.get("asin")) or {}
    if sku.get("net_margin_pct") is not None:
        out.append(Metric("Net margin", f"{sku['net_margin_pct']:.1f}%", _off("your unit economics"),
                    explain=explain.part("Net margin %", "net profit / unit ÷ price",
                        [("Net profit / unit", sku.get("net_profit_unit"), "₹"), ("Price", sku.get("price"), "₹")],
                        f"{sku['net_margin_pct']:.1f}%", provenance=["your unit economics"])))
    if sku.get("buybox_pct") is not None:
        out.append(Metric("Buy Box", f"{sku['buybox_pct']}%", _off("your orders"),
                    explain=explain.part("Buy Box win rate", "share of sessions you held the Buy Box",
                        [("Buy Box %", sku.get("buybox_pct"), "%")], f"{sku['buybox_pct']}%",
                        provenance=["your orders"])))
    return out


def _play(card, smap):
    """One-line play (L2 phrasing seam — introduces no number). Title/SKU-led, never a raw ASIN."""
    fam, nm = card.get("family"), _name(card, smap)
    if fam == "competitive":
        return f"Review pricing / Buy Box on {nm}"
    if fam == "demand":
        return f"Protect stock and lean ad spend into {nm}"
    if fam == "opportunity":
        return f"Evaluate the opportunity on {nm}"
    if fam == "news":
        return "Act on the regulatory / news trigger"
    return f"Review {nm}"


def _floor_finding(card, smap):
    """P0-2: phrase a margin-below-floor breach from L1 seller data (real net margin + real floor) —
    never relay the card's (possibly stale/mismatched) finding string or a hardcoded floor."""
    sku = smap.get(card.get("asin")) or {}
    m, fl = sku.get("net_margin_pct"), sku.get("margin_floor")
    return (f"Net margin on <b>{_name(card, smap)}</b> is <b>{m:.1f}%</b>, below your {float(fl):g}% floor."
            if m is not None and fl not in (None, "")
            else (card.get("finding") or ""))


def _finding(card, smap):
    return _floor_finding(card, smap) if _is_floor_card(card) else (card.get("finding") or "")


def _card_move(card, smap):
    return Move(id=f"mv-{card.get('id')}", headline=_play(card, smap),
                rationale=_finding(card, smap), effort=_effort(card),
                impact=_strip(card.get("exposure_val")) or "", status="recommended",
                prov=_row_prov(card))


def _classify(card):
    ct, f = card.get("card_type"), (card.get("finding") or "").lower()
    if ct == "C2" or "entrant" in f or "launched" in f:
        return "new_entrant"
    if "rating" in f or "review" in f:
        return "ratings_surge"
    if "assortment" in f or "gap" in f:
        return "assortment_shift"
    return "price_cut"


def _signal(card, smap):
    return SignalItem(
        id=f"sig-{card.get('id')}", materiality=int(round(card.get("rank_score") or 0)),
        changed=_finding(card, smap), why="",                      # one-liner; no duplicated label (P1-4)
        move=Move(id=f"pl-{card.get('id')}", headline=_play(card, smap), rationale="",
                  prov=_row_prov(card)),
        evidence=_biz_metrics(card, smap))


def _competitive(card, smap):
    kind = _classify(card)
    return CompetitiveItem(
        id=f"cmp-{card.get('id')}", competitor=(card.get("type_name") or "Competitor move"),
        moved=_finding(card, smap),                                # no "[enum]" prefix (P1-2)
        response=_card_move(card, smap), evidence=_biz_metrics(card, smap),
        kind=kind, kind_label=_HKIND.get(kind, kind), prov=_row_prov(card))


def _pulse(card):
    return MarketPulseItem(
        id=f"mp-{card.get('id')}", headline=card.get("finding") or "",
        so_what=_strip(card.get("exposure_label")) or "Why it matters to you",
        materiality=int(round(card.get("rank_score") or 0)),
        prov=(_prov_list([card]) or [_off("news / gov feed")])[0])


def _scope(con, tid, cat, categories):
    skus = [s for s in SellerRepository(con).all(tid) if (not cat or cat == "All" or s.get("category") == cat)]
    vel = sum((s.get("velocity_day") or 0) for s in skus)
    velocity = Metric("Velocity (today)", f"{vel:.1f} units/day", _off("your orders"),
                      explain=explain.part(
        "Category velocity (point-in-time)", "Σ velocity_day over your SKUs in the category",
        [(s.get("internal_sku") or s.get("asin"), s.get("velocity_day"), "u/day") for s in skus[:5]],
        f"{vel:.1f} units/day", provenance=["your orders"],
        note="Point-in-time; velocity_trend (Δ) is coming."))
    bands = _bands_for(tid, con)   # R14: locale-correct ($ US / ₹ IN)
    # R15: Share-of-band + Category-rank synthesized LIVE (locale-neutral: a % + integer rank) against a
    # deterministic modeled competitor set — same world ⇒ same values, exactly like velocity above.
    share, rank, n_comp = _market_synth(tid, cat, skus)
    share_pct, _psrc = f"{share * 100:.1f}%", "your catalog + modeled category set"
    _pnote = "Modeled category set (deterministic per world); not a live market read."
    def _pos(label, value, formula, first):
        return Metric(label, value, _off(_psrc), explain=explain.part(label, formula,
            [first, ("Modeled category players", n_comp, None)], value, provenance=[_psrc], note=_pnote))
    share_metric = _pos("Your share of band", share_pct,
        "your modeled units ÷ modeled band units across the category set", ("Your SKUs in category", len(skus), None))
    rank_metric = _pos("Category rank", f"#{rank} of {n_comp}",
        "your position among the modeled category competitor set, ordered by share", ("Your share of band", share_pct, None))
    return ScopeBar(category=cat or "All", price_band=bands[1], categories=categories or [cat or "All"],
                    price_bands=bands,
                    position=BrandPosition(share=share_metric, rank=rank_metric, velocity=velocity))


def _cat_phrase(cat):
    return "all categories" if (not cat or cat == "All") else cat


def _brief(cat, feed_cards, own_cards, smap, n_shown):
    """Assembly, not a new brain: rank the top category/competitive moves (dedupe one per product),
    memo count == the feed count shown, never leak 'None' (P1-1/P2-3/P2-4). Own-SKU findings are
    referenced as CONTEXT INPUTS here (the only place they appear on the Analyst — Fix 4), never
    re-listed as feed items."""
    seen, top = set(), []
    for c in feed_cards:
        key = c.get("asin") or c.get("id")
        if key in seen:
            continue
        seen.add(key); top.append(c)
        if len(top) == 3:
            break
    moves = [_card_move(c, smap) for c in top]
    body = " ".join(f"{m.headline} ({m.impact})." if m.impact else f"{m.headline}." for m in moves)
    lead = (f"{n_shown} live category signal{'s' if n_shown != 1 else ''} across {_cat_phrase(cat)} this cycle. "
            if n_shown else f"No live category signals across {_cat_phrase(cat)} yet. ")
    ctx = (f" Context: {len(own_cards)} own-SKU finding{'s' if len(own_cards) != 1 else ''} "
           f"(margin / Buy Box / ad spend) on your Profit & Ads worklist — factored in, not repeated here."
           if own_cards else "")
    return Brief(dated="", narrative=(lead + ("Top plays: " + body if body else
                 "Whitespace and Voice of Customer join the brief in a later phase.") + ctx),
                 moves=moves,
                 caption="Coverage: category/competitive signals only (own-SKU margin/Buy Box findings "
                         "live on Profit & Ads; Whitespace / Voice of Customer join later).")


def _moves(con, tid, ranked, smap):
    recommended, seen = [], set()
    for c in ranked:
        key = c.get("asin") or c.get("id")
        if key in seen:
            continue
        seen.add(key); recommended.append(_card_move(c, smap))
        if len(recommended) == 3:
            break
    acted = [Move(id=f"act-{a.get('id')}", headline=a.get("title") or a.get("task_type") or "Acted",
                  rationale=a.get("summary") or "", status="acted", outcome=a.get("summary") or "",
                  prov=_off("your action log")) for a in ActionRepository(con).recent(tid, 5)]
    return MovesLoop(recommended=recommended, acted=acted, dismissed=[],
                     attributed_margin=_coming_metric("Attributed margin"),
                     hit_rate=_coming_metric("Hit rate"))


def _below_floor(card, smap):
    """P0-2: the analyst OWNS the floor verdict. True only when L1 seller data confirms
    net_margin_pct < margin_floor for the SKU; None when undecidable. Cards that assert a floor
    breach the data contradicts are dropped upstream of phrasing."""
    sku = smap.get(card.get("asin")) or {}
    m, fl = sku.get("net_margin_pct"), sku.get("margin_floor")
    if m is None or fl in (None, ""):
        return None
    return m < float(fl)


# The external/category detectors (C1–C9) — these carry CATEGORY / COMPETITIVE change and are the
# ONLY things the Signal Feed surfaces (Fix 4). Everything else is an own-SKU operational finding
# (margin / Buy Box / ad spend / inventory) that P&A + Intelligence already show — kept out of the
# feed, available to the Brief as context inputs.
_C1_9 = {"C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"}


def _is_floor_card(card):
    """A genuine margin-BELOW-floor own-SKU finding — NOT a C1 competitive card that merely mentions
    'above your floor' (that false-match was dropping real competitive rows). External/category
    detectors (C1–C9) are never floor breaches."""
    if card.get("family") in ("competitive", "demand", "opportunity", "news") or card.get("card_type") in _C1_9:
        return False
    f = (card.get("finding") or "").lower()
    return "floor" in f and any(w in f for w in ("below", "under", "beneath"))


def assemble(con, tenant_id, category=None, price_band=None) -> AnalystBrief:
    tenant = TenantRepository(con).get(tenant_id) or {}
    is_fixture = (tenant.get("data_mode") == "synthetic") or (tenant.get("account_type") == "tester")
    categories = SellerRepository(con).distinct_categories(tenant_id) or []
    cat = category or (categories[0] if categories else "All")
    smap = {s.get("asin"): s for s in SellerRepository(con).all(tenant_id) if s.get("asin")}

    cards = CardRepository(con).feed(tenant_id, category=(cat if cat not in (None, "All") else None))
    # P0-2 floor discipline (belt-and-suspenders behind the interpret.py source fix): drop a
    # "below floor" own-SKU card the L1 seller data contradicts.
    cards = [c for c in cards if not (_is_floor_card(c) and _below_floor(c, smap) is not True)]
    ranked = sorted(cards, key=lambda c: (c.get("rank_score") or 0, c.get("exposure_pct") or 0), reverse=True)
    # Fix 4 (Decision A): the Signal Feed carries CATEGORY / COMPETITIVE change (C1–C9) ONLY — own-SKU
    # P&A/Intelligence findings are NOT re-listed here; they inform the Brief as context inputs.
    feed_cards = [c for c in ranked if c.get("card_type") in _C1_9]
    own_cards = [c for c in ranked if c.get("card_type") not in _C1_9]
    comp_cards = [c for c in feed_cards if c.get("family") == "competitive"][:6]
    news_cards = [c for c in feed_cards if c.get("family") == "news"][:6]
    sig_cards = feed_cards[:8]

    signals = [_signal(c, smap) for c in sig_cards]
    competitive = [_competitive(c, smap) for c in comp_cards]
    market_pulse = [_pulse(c) for c in news_cards]
    scope = _scope(con, tenant_id, cat, categories)
    brief = _brief(cat, feed_cards, own_cards, smap, len(sig_cards))   # memo count == feed count (P2-3)
    moves = _moves(con, tenant_id, feed_cards, smap)
    ask = AskAnalyst(scope=_cat_phrase(cat),
                     prompt=f"Ask about {_cat_phrase(cat)} — competitors, whitespace, pricing, or a SKU.",
                     suggested=[f"What's the fastest ₹ move in {_cat_phrase(cat)} this week?",
                                "How exposed am I if a competitor keeps cutting price?"])

    whitespace, voice = [], []
    if is_fixture:
        from .analyst_fixture import fixture_brief
        fx = fixture_brief(category, price_band)
        whitespace, voice = fx.whitespace, fx.voice

    states = AnalystStates(
        scope=SectionState(PARTIAL, _prov_list(cards)),
        brief=SectionState(LIVE, _prov_list(feed_cards[:3])),
        signals=SectionState(LIVE, _prov_list(sig_cards)),
        whitespace=SectionState(FIXTURE, [], _FIX_COMING["whitespace"]),
        competitive=SectionState(LIVE, _prov_list(comp_cards)),
        voice=SectionState(FIXTURE, [], _FIX_COMING["voice"]),
        market_pulse=SectionState(LIVE, _prov_list(news_cards)),
        moves=SectionState(PARTIAL, _prov_list(feed_cards[:3])),
        ask=SectionState(PARTIAL, [], "Conversational answers depend on the synthesis service — coming."),
    )
    return AnalystBrief(
        generated_at="", synthesis_source=("live+fixture" if is_fixture else "live"),
        scope=scope, brief=brief, signals=signals, whitespace=whitespace, competitive=competitive,
        voice=voice, market_pulse=market_pulse, moves=moves, ask=ask, states=states)
