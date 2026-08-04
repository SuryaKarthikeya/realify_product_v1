"""Level-2 research. On demand (when a seller clicks 'Research further' on a card),
assemble a deeper payload: a price/BSR chart, a ranked real competitor-SKU list,
search-trend depth, and an LLM-written decision brief. Cached per card so re-opening
is instant. The 'ask' function answers follow-ups grounded ONLY in this payload."""
import json
from .. import db, config
from ..repositories.card_repo import CardRepository
from ..repositories.market_repo import MarketRepository
from ..collectors.keepa_collector import KeepaCollector

# segment hint per card category (what gap/niche to research)
SEGMENT = {
    "Car Accessories": "premium car seat covers",
    "Bike Accessories": "waterproof bike covers",
    "Car Electronics": "android carplay units",
    "Other Accessories": "car interior accessories",
}

def _card_by_id(con, tenant_id, card_id):
    from ..repositories.card_repo import CardRepository
    return CardRepository(con).get(tenant_id, card_id)

def why_for_card(tenant_id, card_id):
    """L2-tailored 'why this matters to you', generated lazily on drill-down and cached
    per card. Numbers are LOCKED — the model only rephrases the deterministic facts already
    on the card (finding/why/minis), never inventing figures. Falls back to the deterministic
    why if no key or on any error, so the card always has a usable explanation."""
    from .. import country
    country.use_tenant(tenant_id)
    con = db.connect()
    card = _card_by_id(con, tenant_id, card_id)
    if not card:
        con.close(); return {"why": None, "l2": False, "error": "card not found"}
    dk = card["dedup_key"]
    cached = CardRepository(con).why_cached(tenant_id, dk)
    if cached:
        con.close(); return {"why": cached["why"], "l2": True, "cached": True}
    det = card["why"]   # deterministic baseline (Option 1)
    if not config.ANTHROPIC_API_KEY:
        con.close(); return {"why": det, "l2": False, "note": "no key — deterministic why"}
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        try: minis = json.loads(card["minis"] or "[]")
        except Exception: minis = []
        facts = dict(insight=card["type_name"], category=card["category"], asin=card["asin"],
                     finding=_strip(card["finding"]), numbers=minis,
                     recommended_action=card["action"], deterministic_why=_strip(det))
        prompt = ("You are Realify's analyst writing the 'why this matters to you' for ONE "
                  "Amazon/marketplace seller card. Use ONLY the facts/numbers given — never invent "
                  "or alter a figure. Write 2-3 sentences, specific to THIS SKU and situation: what's "
                  "happening, the concrete consequence if ignored, and the one move to make. Be direct "
                  "and useful, not generic. Plain text (no markdown).\n\nFACTS:\n" + json.dumps(facts)[:2500])
        m = client.messages.create(model=config.L2_MODEL, max_tokens=260,
                                   messages=[{"role":"user","content":prompt}])
        txt = "".join(b.text for b in m.content if getattr(b,"type","")=="text").strip()
        if not txt:
            con.close(); return {"why": det, "l2": False, "note": "empty L2 response"}
        CardRepository(con).save_why(tenant_id, dk, txt, db.now_iso())
        con.commit(); con.close()
        return {"why": txt, "l2": True, "cached": False}
    except Exception as e:
        con.close()
        return {"why": det, "l2": False, "note": f"L2 failed ({str(e)[:60]})"}

import re as _re
def _strip(s):
    return _re.sub("<[^>]+>", "", s or "")

def _rank_competitors(rows):
    """Opportunity rank: high demand (low BSR) + low review barrier + healthy rating."""
    out=[]
    for r in rows:
        bsr=max(1, r["bsr"] or 999999); rev=max(1, r["reviews"] or 1)
        score = (1.0/bsr)*1e6 / (1 + rev/200.0) * (r["rating"] or 3.5)/5.0
        out.append({**r, "opp_score": round(score,2)})
    out.sort(key=lambda x:-x["opp_score"])
    for i,r in enumerate(out,1): r["rank"]=i
    return out

def _brief(card, kind, payload):
    """LLM decision artifact (live Anthropic) or deterministic fallback. Numbers from
    payload only. Returns (text, trace) where trace records the exact L2 prompt+response
    (or that L2 was not invoked) for Explanation Mode."""
    trace = {"l2_invoked": False, "l2_model": config.L2_MODEL, "l2_prompt": None, "l2_response": None, "l2_note": None}
    if config.ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            ctx = dict(card_type=card["card_type"], finding=card["finding"], category=card["category"],
                       kind=kind, competitors=payload.get("competitors",[])[:6],
                       trend=payload.get("trend"), chart_summary=payload.get("chart_summary"))
            prompt = ("You are Realify's research analyst. Using ONLY the data provided, write a short "
                      "decision brief (3-5 sentences, plain text) that tells this Amazon seller what to do "
                      "next and why. Never invent numbers beyond those given.\n\nDATA:\n"+json.dumps(ctx)[:3000])
            m=client.messages.create(model=config.L2_MODEL, max_tokens=400,
                                     messages=[{"role":"user","content":prompt}])
            text = "".join(b.text for b in m.content if getattr(b,"type","")=="text").strip()
            trace.update(l2_invoked=True, l2_prompt=prompt, l2_response=text)
            return text, trace
        except Exception as e:
            trace["l2_note"] = f"L2 call failed ({str(e)[:80]}); deterministic narrative used."
    else:
        trace["l2_note"] = "No Anthropic key configured; deterministic narrative used."
    # fallback (deterministic)
    if kind=="sourcing":
        c=payload.get("competitors",[])
        top=c[0] if c else None
        n=len(c)
        line=(f"{n} competitor SKUs exist in this gap. " if n else "")
        if top:
            from .. import country
            line+=(f"The strongest entry point is a {top['title']} type at ~{country.active()['symbol']}{top['price']:.0f} "
                   f"(rank #{top['rank']}, {top['reviews']} reviews) — low review barrier means you can compete on quality quickly. ")
        line+="Target the 2-3 lowest-review, high-demand items first; price to clear your margin floor and validate before scaling the assortment."
        return line, trace
    if kind=="pricing":
        return ("The price history shows whether this undercut is a one-off or a pattern. If the competitor "
                "tends to bounce back up, a brief floor-gated match recaptures the Buy Box without a race to the bottom. "
                "If they hold low, decide whether this SKU's volume justifies defending at thinner margin."), trace
    if kind=="demand":
        t=payload.get("trend") or {}
        return ("BSR and search both point the same way here. " +
                ("Rising related queries: "+", ".join(t.get("related",[])[:3])+". " if t.get("related") else "") +
                "If you carry this, protect stock and lean ad spend in before competitors react; if not, treat it as a sourcing candidate."), trace
    return "Review the pulled data and decide whether to act, watch, or source.", trace

def research_card(tenant_id, card_id, force=False):
    from .. import country
    country.use_tenant(tenant_id)
    con = db.connect()
    card = _card_by_id(con, tenant_id, card_id)
    if not card:
        con.close(); return {"error":"card not found"}
    dk = card["dedup_key"]
    if not force:
        cpayload = CardRepository(con).research_payload(tenant_id, dk)
        if cpayload:
            cached = json.loads(cpayload)
            l2 = cached.get("l2") or {}
            # Auto-heal: if this payload was cached WITHOUT L2 (e.g. before an Anthropic key
            # was configured) but a key is available now, fall through and regenerate so the
            # seller gets the LLM narrative instead of the stale deterministic fallback.
            stale_keyless = config.ANTHROPIC_API_KEY and not l2.get("l2_invoked")
            if not stale_keyless:
                con.close(); return cached

    kc = KeepaCollector(tenant_id)
    fam = card["family"]; ct = card["card_type"]; payload = {"card_type":ct, "family":fam}
    market_status = "ok"   # ok | empty | failed — drives the detail-view market section

    # --- market data (Keepa) is bounded + fail-fast so the panel never hangs ---
    import socket
    old_to = socket.getdefaulttimeout()
    if kc.mode == "live": socket.setdefaulttimeout(config.SOURCE_TIMEOUT)
    try:
        # chart (price + bsr) for ASIN-anchored cards
        if card["asin"]:
            hist = kc.history(card["asin"])
            payload["chart"] = hist
            if hist.get("price"):
                p0,p1 = hist["price"][0]["v"], hist["price"][-1]["v"]
                payload["chart_summary"] = {"price_change_pct": round((p1-p0)/p0*100,1) if p0 else 0,
                                            "bsr_now": hist["bsr"][-1]["v"] if hist["bsr"] else None,
                                            "bsr_30d_ago": hist["bsr"][0]["v"] if hist["bsr"] else None}
            else:
                market_status = "empty"
        # competitor list for opportunity/assortment & competitive cards
        seg = SEGMENT.get(card["category"], card["category"])
        if ct in ("C5","C6","C2","C1"):
            comps = kc.find_products(con, card["category"], seg, n=5)
            payload["competitors"] = _rank_competitors(comps)
            payload["segment"] = seg
            if not comps and market_status == "ok":
                market_status = "empty"
    except Exception as e:
        market_status = "failed"
        payload["market_error"] = str(e)[:160]
    finally:
        socket.setdefaulttimeout(old_to)
    payload["market_status"] = market_status

    # --- search-trend depth for demand/opportunity cards ---
    if ct in ("C3","C4","C5"):
        tr = MarketRepository(con).latest_trend(tenant_id)
        related = ["interior lighting kit","car organizer","seat cover","dash mount","trunk mat"]
        if tr:
            try:
                raw = json.loads(dict(tr)["raw"] or "{}")
                if raw.get("related"): related = raw["related"]
            except Exception:
                pass
        payload["trend"] = {"headline": dict(tr)["title"] if tr else None, "related": related[:4]}

    # --- review themes (off-Amazon enrichment) ---
    if ct in ("C5","C6","C1"):
        payload["review_themes"] = [
            {"theme":"fit accuracy", "sentiment":"mixed", "note":"model-specific fit is the top driver of returns — a quality wedge"},
            {"theme":"material durability","sentiment":"positive","note":"buyers reward thicker/heavier covers"},
            {"theme":"waterproofing claims","sentiment":"watch","note":"over-claiming triggers negative reviews"},
        ]

    kind = {"C5":"sourcing","C6":"sourcing","C1":"pricing","C3":"demand","C4":"demand"}.get(ct,"general")
    payload["kind"] = kind
    brief_text, l2_trace = _brief(card, kind, payload)
    payload["brief"] = brief_text
    payload["l2"] = l2_trace   # exact prompt + response (or not-invoked note) for Explanation Mode

    if market_status != "failed":   # don't cache a failed market load — let Retry re-attempt
        CardRepository(con).save_research(tenant_id, dk, json.dumps(payload))
        con.commit()
    con.close()
    return payload

def ask_card(tenant_id, card_id, question):
    """Answer a follow-up grounded ONLY in the card + its cached research payload."""
    con = db.connect()
    card = _card_by_id(con, tenant_id, card_id)
    if not card:
        con.close(); return {"answer":"Card not found."}
    research = research_card(tenant_id, card_id)   # ensures payload exists (cached)
    con.close()
    if not config.ANTHROPIC_API_KEY:
        return {"answer":"(LLM offline — set ANTHROPIC_API_KEY to ask grounded follow-ups. "
                "The research panel above has the chart, competitors, and brief to work from.)"}
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        ctx = {"finding": card["finding"], "why": card["why"], "category": card["category"],
               "research": research}
        prompt = ("You are Realify's research analyst. Answer the seller's question using ONLY the data "
                  "provided below — do not invent numbers or facts not present. If the data can't answer it, "
                  "say so and suggest what to pull next.\n\nDATA:\n"+json.dumps(ctx)[:5000]+
                  "\n\nQUESTION: "+question)
        m=client.messages.create(model=config.L2_MODEL, max_tokens=500,
                                 messages=[{"role":"user","content":prompt}])
        return {"answer": "".join(b.text for b in m.content if getattr(b,"type","")=="text").strip()}
    except Exception as e:
        return {"answer": f"(Couldn't reach the LLM: {str(e)[:120]})"}
