"""R11 — fleet/drill-in data resolution. The FIX for the "0 clients" bug: the console resolved brands
from the actor's GRANTS (empty for an agency admin who holds engagements but no per-brand grant); here
we resolve the agency and its brands from ENGAGEMENTS (the authoritative agency↔brand mapping the queue
already used), grant-independently. Per-brand cards carry health, top signal/action, and the load-
bearing $-at-stake (sum of the brand's open decisions, USD-normalized) — cards sort by it."""
from . import queue, connections, money, tenancy, locale

_ACTION = {"inventory": "Reorder before stockout", "ads": "Lower bids over break-even ACoS",
           "pricing": "Reprice within Buy-Box tolerance", "listings": "Fix listing content",
           "reporting": "Review reporting"}

_TACOS_TERRA = 40.0        # % — portfolio TACoS at/above this is bleeding ad spend → at risk
_STAKE_TERRA = 10000.0     # $ — this much open exposure across a brand's decisions → at risk


def _ccy_for_country(code):
    """The brand's selling currency from its country setting (locale-correct; never hardcode ₹/$)."""
    if not code:
        return "USD"
    try:
        from .. import country as _country
        return _country.profile(code).get("currency", "USD")
    except Exception:                                          # pragma: no cover - defensive
        return "USD"


def _sym_for_country(code):
    """R15.2 — the brand's currency SYMBOL from its country (for the fleet card's localized figures)."""
    try:
        from .. import country as _country
        return _country.profile(code or "US").get("symbol", "$")
    except Exception:                                          # pragma: no cover - defensive
        return "$"


def resolve_agency(cur, uid, tid, agency_ids=None):
    """(agency_id, agency_name) for the acting operator — from actor.agency_ids, else the acting brand's
    engagement. Grant-INDEPENDENT so an admin with no per-brand grant still resolves their agency."""
    agency_id = (agency_ids or [None])[0]
    if agency_id is None and tid:
        cur.execute("SELECT agency_id FROM engagements WHERE tenant_id=%s AND status<>'terminated' LIMIT 1", (tid,))
        r = cur.fetchone()
        agency_id = r[0] if r else None
    if agency_id is None and uid:
        # R17.2 — a FRESH agency admin has membership but no brands yet (no engagements/grants), so resolve
        # from agency_members too, else their console shows "No agency in scope" the moment they sign in.
        cur.execute("SELECT agency_id FROM agency_members WHERE user_id=%s LIMIT 1", (uid,))
        r = cur.fetchone()
        agency_id = r[0] if r else None
    if agency_id is None:
        return None, None
    cur.execute("SELECT name FROM agencies WHERE id=%s", (agency_id,))
    r = cur.fetchone()
    return agency_id, (r[0] if r else "Agency")


def agency_brand_ids(cur, agency_id):
    """Every non-terminated engagement's brand — the authoritative agency book (not grant-scoped). Reads
    the RLS-forced `engagements` table, so it MUST run in the SAME transaction as resolve_actor (which
    sets the app.actor_user_id GUC). The selfread policies then let the actor see their agency's
    engagements via a per-brand grant OR via agency MEMBERSHIP (migration 0037) — the latter is what lets
    a fresh admin with no grant still resolve their book."""
    cur.execute("SELECT tenant_id FROM engagements WHERE agency_id=%s AND status<>'terminated'", (agency_id,))
    return sorted(x[0] for x in cur.fetchall())


def _health(paused, top_lens, open_count, tacos_pct=0.0, stake_usd=0.0):
    if paused:
        return "terra"                   # expired connection → decisions paused, at risk
    if (tacos_pct or 0) >= _TACOS_TERRA or (stake_usd or 0) >= _STAKE_TERRA:
        return "terra"                   # very high ad waste / large open exposure → at risk
    if open_count and top_lens == "ads":
        return "gold"                    # ACoS over break-even → watch
    return "sage"                        # healthy (reorder/price headroom or nothing open)


def brand_cards(cur, ids, grant_ids=None):
    """One card dict per brand id, sorted by $-at-stake DESC (paused sink to the end).

    R15: every card derives from the SAME synthesized world the interior five lenses read — NOT the
    stale rollup_cache (whose seller_skus GMV basis showed ~$54K and a 0% TACoS whenever ads hadn't
    synthesized). TACoS, GMV and $-at-stake now reconcile with the brand interior:
      • TACoS   = Σ ad_performance.spend ÷ Σ sku_revenue_period.revenue × 100  (interior Profit&Ads basis)
      • GMV     = Σ sku_revenue_period.revenue                                  (selling currency, locale)
      • $-stake = Σ decisions.impact_usd_minor / 100 WHERE status='open'        (interior FIX-ADS recoverable)
    Every brand-table read sets the brand scope AND carries an explicit tenant_id = ANY(%s) filter
    (R2/R11: never rely on RLS alone — the harness owner bypasses it). Unsynthesized brands degrade to
    0 / '—' rather than crashing."""
    if not ids:
        return []
    tenancy.set_brand_scope(cur, ids)
    idlist = list(ids)
    cur.execute("SELECT id, name FROM tenants WHERE id = ANY(%s)", (idlist,))
    names = {tid: nm for tid, nm in cur.fetchall()}
    # AM owner = first grant-holder's name per brand (their "book")
    cur.execute("SELECT e.tenant_id, u.name FROM grants g JOIN engagements e ON e.id=g.engagement_id "
                "JOIN users u ON u.id=g.user_id WHERE e.tenant_id = ANY(%s) ORDER BY g.id", (idlist,))
    am = {}
    for tid, nm in cur.fetchall():
        am.setdefault(tid, nm)
    # Synthesized per-brand aggregates (batched; each keeps the explicit tenant filter under RLS scope).
    cur.execute("SELECT tenant_id, COALESCE(SUM(revenue),0) FROM sku_revenue_period "
                "WHERE tenant_id = ANY(%s) AND grain='month' GROUP BY tenant_id", (idlist,))
    revenue = {tid: float(v or 0) for tid, v in cur.fetchall()}
    cur.execute("SELECT tenant_id, COALESCE(SUM(spend),0) FROM ad_performance "
                "WHERE tenant_id = ANY(%s) AND grain='month' GROUP BY tenant_id", (idlist,))
    spend = {tid: float(v or 0) for tid, v in cur.fetchall()}
    # R15.2 — sum BOTH the USD-normalized minor (cross-brand sort) and the NATIVE minor (localized display).
    cur.execute("SELECT tenant_id, COALESCE(SUM(impact_usd_minor),0), COALESCE(SUM(impact_minor),0) FROM decisions "
                "WHERE status='open' AND tenant_id = ANY(%s) GROUP BY tenant_id", (idlist,))
    open_stake = {tid: (int(u or 0), int(n or 0)) for tid, u, n in cur.fetchall()}
    # per-brand selling currency (locale): the brand's decision currency, else its country default.
    cur.execute("SELECT tenant_id, MIN(impact_currency) FROM decisions "
                "WHERE tenant_id = ANY(%s) GROUP BY tenant_id", (idlist,))
    ccy = {tid: c for tid, c in cur.fetchall()}
    cur.execute("SELECT tenant_id, value FROM tenant_settings "
                "WHERE key='country' AND tenant_id = ANY(%s)", (idlist,))
    country = {tid: v for tid, v in cur.fetchall()}
    cards = []
    for idx, tid in enumerate(ids):
        items = queue.build(cur, [tid], top_k=None)          # ranked open decisions for this brand
        paused = connections.decisions_paused(cur, tid)
        usd_minor, native_minor = open_stake.get(tid, (0, 0))
        stake_usd = usd_minor / 100.0 if not paused else 0.0   # USD-normalized: cross-brand sort key
        top = items[0] if items else None
        rev_t, sp_t = revenue.get(tid, 0.0), spend.get(tid, 0.0)
        tacos = (sp_t / rev_t * 100.0) if rev_t > 0 else 0.0
        code = country.get(tid)                                 # R15.2: stored country is authoritative (like the interior)
        currency = _ccy_for_country(code) if code else (ccy.get(tid) or "USD")
        # symbol follows the COUNTRY when set, else the resolved currency (never hard-default to $ for a
        # brand whose data is INR but is missing a country row) — R19.1.
        symbol = _sym_for_country(code) if code else money._SYMBOL.get(currency, "$")
        gmv_minor = int(round(rev_t * 100))
        gmv = money.format_money(gmv_minor, currency) if gmv_minor > 0 else "—"
        stake_display = money.format_money(native_minor if not paused else 0, currency)   # localized $-at-stake
        owner_name = locale.person_name(code or "US", idx)     # R15.2 Part C: distinct owner per brand
        if paused:
            money_line = "stale · 0 actionable"
            top_signal, top_action = "Connection expired — decisions paused.", "Fix the connection to resume."
        else:
            money_line = f"{gmv} GMV · TACoS {tacos:.0f}% · {len(items)} open"
            top_signal = top["signal"] if top else "No open decisions."
            top_action = _ACTION.get(top["lens"], "Review") if top else "Nothing to do right now."
        cards.append({
            "tenant_id": tid, "name": names.get(tid, f"brand {tid}"),
            "health": _health(paused, (top["lens"] if top else None), len(items), tacos, stake_usd),
            "am_name": am.get(tid), "owner_name": owner_name, "top_signal": top_signal, "top_action": top_action,
            "money_line": money_line, "stake_usd": stake_usd, "stake_display": stake_display, "paused": paused,
            "tacos_pct": round(tacos, 1), "currency": currency, "symbol": symbol,
            "in_book": (grant_ids is None or tid in grant_ids), "open_count": len(items),
        })
    cards.sort(key=lambda c: (c["paused"], -c["stake_usd"]))   # $-at-stake DESC; paused last
    return cards


def pending_consents(cur, agency_id):
    """Invited/viewed consents for this agency — the h5 Add-client rows (short-circuit approve button)."""
    cur.execute("SELECT id, email, envelope_template, status FROM brand_consents "
                "WHERE agency_id=%s AND status IN ('invited','viewed') ORDER BY id DESC LIMIT 10", (agency_id,))
    return [{"id": cid, "email": em, "template": tm, "status": st} for cid, em, tm, st in cur.fetchall()]
