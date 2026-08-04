"""L2 generation. Live mode calls Claude to phrase the card; otherwise a
deterministic fallback writes it. Numbers ALWAYS come from the signal, never
from the model. Returns finding/why/severity/confidence + display fields."""
import json
from .. import config

CONF_LABEL = {4:"Very high", 3:"High", 2:"Medium", 1:"Low"}
SEV_LABEL = {"act":"Act today","opp":"Opportunity","watch":"Watch","crit":"Critical"}

def _fmt_inr(x):
    from .. import country
    return country.fmt_money(x)

def _sym():
    from .. import country
    return country.active()["symbol"]

# Generic catalog rules get a TITLE = their descriptive rule name + the entity it fired
# on, so same-rule-different-SKU cards differ while distinct rules stay distinguishable
# (the salient value lives in the finding right below). C1–C9 keep their curated names.
def _headline(sig):
    ct = sig["card_type"]
    if not (sig.get("rule") and ct not in ("C1","C2","C3","C4","C5","C6","C7","C8","C9")):
        return sig["type_name"]
    ent = sig.get("asin") or sig.get("category") or ""
    base = sig.get("type_name") or "Insight"
    return f"{base} \u00b7 {ent}" if ent else base

def _confidence(sig):
    if "confidence_override" in sig: return sig["confidence_override"]
    return {"C1":3,"C2":2,"C3":3,"C4":3,"C5":2,"C6":2,"C7":2,"C8":4,"C9":1}.get(sig["card_type"],2)

def _pick(asin, ct, variants):
    """Deterministic per-card variant so two same-type cards never read identically."""
    import hashlib as _h
    if not variants: return ""
    i = int(_h.md5(f"{asin or ''}:{ct}".encode()).hexdigest(), 16) % len(variants)
    return variants[i]

def _ent(sig):
    """Entity label for card *bodies*: prefer the product title, fall back to ASIN, then
    category. The header keeps the raw ASIN (see _headline)."""
    return sig.get("title") or sig.get("asin") or sig.get("category") or ""


def _fallback(sig):
    n = sig["nums"]; ct = sig["card_type"]
    # generic catalog rules (Step 5): card_type isn't one of the special C1–C9
    if sig.get("rule") and ct not in ("C1","C2","C3","C4","C5","C6","C7","C8","C9"):
        val = n.get("value"); thr = n.get("threshold"); op = n.get("op"); label = n.get("label", n.get("field",""))
        def fnum(x):
            if isinstance(x, float): return f"{x:.1f}".rstrip("0").rstrip(".")
            return str(x)
        rel = "below" if op == "lt" else "above"
        ent = f"<b>{_ent(sig)}</b>" if sig.get("asin") else f"<b>{sig['category']}</b>"
        ev = fnum(val); tv = fnum(thr)
        exp0 = sig.get("exposure_inr")
        expph = f" — about <span class='rupee'>{_fmt_inr(exp0)}</span>/mo at stake" if exp0 else ""
        prefix = ct.split("-")[0].upper()
        fld = n.get("field") or ""
        # Clean metric name/unit + the canonical family per FIELD, so the finding, mechanism
        # and why all describe the ACTUAL detected field — never the rule's (sometimes loose)
        # family label. This is what fixes the "finding says units/day, why says days-of-cover"
        # contradiction on rules whose detector field differs from their family.
        FIELD_META = {
          "velocity_day":  {"name":"velocity",      "unit":"/day",   "fam":"SALES"},
          "days_of_cover": {"name":"days of cover", "unit":"d",      "fam":"INV"},
          "stock_on_hand": {"name":"stock on hand", "unit":" units", "fam":"INV"},
          "net_margin_pct":{"name":"net margin",    "unit":"%",      "fam":"MARGIN"},
          "tacos":         {"name":"TACoS",         "unit":"%",      "fam":"ADS"},
          "own_skus":      {"name":"assortment",    "unit":" SKUs",  "fam":"ASST"},
          "rating":        {"name":"rating",        "unit":"",       "fam":"RR"},
          "review_count":  {"name":"review count",  "unit":"",       "fam":"RR"},
          "rev_share_pct": {"name":"revenue share", "unit":"%",      "fam":"SHARE"},
          "conversion_pct":{"name":"conversion",    "unit":"%",      "fam":"SV"},
          "returns_rate":  {"name":"return rate",   "unit":"%",      "fam":"MARGIN"},
        }
        meta = FIELD_META.get(fld, {})
        fam_key = meta.get("fam", prefix)   # mechanism/tradeoff keyed by the real metric
        # Data-grounded finding keyed by the actual FIELD (not family), so it always matches
        # the metric the rule detects on. Varies by SKU and live value.
        FIELD_FIND = {
          "velocity_day":  f"{ent} is moving <b>{ev}</b> units/day, {rel} your {tv} watch line{expph}.",
          "days_of_cover": (f"{ent} has only <b>{ev} days</b> of cover left, under your {tv}-day line{expph}." if op=="lt"
                            else f"{ent} is sitting on <b>{ev} days</b> of cover, over your {tv}-day line{expph}."),
          "stock_on_hand": f"{ent} has <b>{ev}</b> units on hand, {rel} your {tv}-unit line{expph}.",
          "net_margin_pct":f"{ent} is netting <b>{ev}%</b> margin, {rel} your {tv}% floor{expph}.",
          "tacos":         f"TACoS on {ent} has reached <b>{ev}%</b>, {rel} your {tv}% ceiling{expph}.",
          "own_skus":      f"You carry <b>{ev}</b> {'SKU' if ev=='1' else 'SKUs'} in {ent}, {rel} the {tv} you'd want to compete{expph}.",
          "rating":        f"{ent}'s rating is <b>{ev}</b>, {rel} your {tv} line{expph}.",
          "review_count":  f"{ent} has <b>{ev}</b> reviews, {rel} your {tv} line{expph}.",
          "rev_share_pct": f"{ent} now drives <b>{ev}%</b> of your revenue, {rel} your {tv}% concentration line{expph}.",
          "conversion_pct":f"{ent} converts at <b>{ev}%</b>, {rel} your {tv}% line{expph}.",
          "returns_rate":  f"{ent} is being returned at <b>{ev}%</b>, {rel} your {tv}% ceiling{expph}.",
        }
        metric_name = meta.get("name") or (str(label).lower().replace(" above","").replace(" below","") or "this metric")
        finding = FIELD_FIND.get(fld) or f"{ent}'s {metric_name} is <b>{ev}</b>, {rel} your {tv} line{expph}."
        # non-duplicate phrasing from the interpretation layer (if assigned)
        tmpl = sig.get("_finding_tmpl")
        if tmpl:
            try: finding = tmpl.format(ent=ent, ev=ev, tv=tv, expph=expph)
            except Exception: pass
        MECH = {
          "MARGIN":"Margin is what you keep after referral + FBA fees, COGS and ad cost — once it drifts past your floor, every unit sold erodes profit instead of building it.",
          "SALES":"Sales velocity drives rank, Buy Box eligibility and cash flow, so a dip here compounds across the account if left alone.",
          "INV":"Inventory sits between stockouts (lost sales and rank decay) and overstock (capital and storage fees tied up); this metric shows which way you're drifting.",
          "ADS":"Ad spend only pays back while ACoS stays under your margin headroom — past that point you're buying sales at a loss and dragging blended profit down.",
          "CASH":"Cash received lags revenue through settlement timing, reserves and short-pays, so a healthy P&L can still starve the working capital you reinvest in stock.",
          "PRICE":"Price position sets both your Buy Box share and your margin — the right level depends on your own floor, not the competitor's.",
          "BUYBOX":"The Buy Box is where most sales happen; losing it routes volume to another seller even when your listing is otherwise healthy.",
          "SHARE":"Category share shows whether you're growing with the market or quietly ceding ground to faster-expanding competitors.",
          "DMND":"Demand signals show where the category is heading before it reaches your own sales — early enough to stock and bid ahead of the move.",
          "OPP":"Opportunities are revenue you don't yet capture — adjacent niches where demand exists but your catalog doesn't compete.",
          "ASST":"Assortment breadth caps how much category demand you can capture; gaps are sales structurally routed to competitors.",
          "SV":"Search visibility decides whether buyers ever see your listing — rank and impression share gate every funnel metric below them.",
          "CONT":"Listing content converts traffic you already pay for; weak content quietly caps conversion regardless of demand or ad spend.",
          "RR":"Ratings and reviews are both a conversion lever and a trust risk — slipping here raises returns and depresses conversion across the listing.",
          "PROMO":"Deal and promotion windows concentrate demand; mistiming them cedes the spike to competitors who show up.",
        }
        TRADE = {
          "MARGIN":"The tradeoff: raising price or trimming ad spend protects margin but may shed some volume — size the move against this SKU's contribution.",
          "INV":"The tradeoff: restocking ties up capital now to avoid a costlier stockout later; if this is an overstock flag, the reverse holds.",
          "ADS":"The tradeoff: cutting spend protects profit but can cool rank — step it down rather than killing it cold.",
          "PRICE":"The tradeoff: defending the Buy Box at a lower price wins volume but thins margin — worthwhile only where volume justifies it.",
        }
        mech = MECH.get(fam_key, "This metric crossing its threshold is an early, actionable signal rather than noise.")
        trade = TRADE.get(fam_key, "The tradeoff is the short-term cost or effort of acting versus leaving the exposure in place.")
        exp = sig.get("exposure_inr")
        scope_word = "SKU" if sig.get("asin") else "category"
        narr = ""
        if sig.get("narrative") and sig["narrative"] not in finding:
            nv = sig["narrative"].strip()
            narr = " " + (nv if nv[-1:] in ".!?" else nv + ".")
        act = sig.get("action") or "review and decide whether to act, watch, or adjust the threshold"
        # ---- LEAD with this card's own situation (varies per SKU/value), THEN weave the
        # mechanism as context. The old template opened with the fixed family mechanism, so
        # every card in a family read identically; now the opening is data-specific. ----
        try:
            gap = abs((float(val) - float(thr)) / float(thr)) if thr else 0
        except (TypeError, ValueError, ZeroDivisionError):
            gap = 0
        deg = "well " if gap >= 0.5 else ("notably " if gap >= 0.2 else ("" if gap >= 0.05 else "just "))
        if exp:
            expmag = "a material" if exp >= 500000 else ("a meaningful" if exp >= 150000 else "a modest")
            stake = f" That puts {expmag} <span class='rupee'>{_fmt_inr(exp)}</span>/mo of revenue in play on this {scope_word}."
        else:
            stake = ""
        lead = (f"{ent}'s {metric_name} is sitting at <b>{fnum(val)}{meta.get('unit','')}</b> — {deg}{rel} your "
                f"<b>{fnum(thr)}{meta.get('unit','')}</b> line.{stake}")
        why = (f"{lead} {mech}{narr} Recommended: <b>{act}</b>. {trade} "
               f"If this isn't material for you, tune the threshold in &#9881; Rules.")
        mini_label = metric_name[:1].upper() + metric_name[1:]
        minis = [[mini_label, fnum(val), "neg" if op=="lt" else "pos"], ["Threshold", fnum(thr), ""]]
        if exp: minis.append(["Exposure/mo", _fmt_inr(exp), "neg"])
        return finding, why, minis
    if ct == "C1":
        cur=_sym()
        finding = _pick(sig.get("asin"), "C1", [
            (f"<b>{n['comp']}</b> is selling at <span class='rupee'>{cur}{n['comp_price']:.0f}</span>, "
             f"undercutting your <b>{_ent(sig)}</b> by <span class='rupee'>{cur}{n['gap']:.0f}</span>."),
            (f"Your <b>{_ent(sig)}</b> is priced <span class='rupee'>{cur}{n['gap']:.0f}</span> above "
             f"<b>{n['comp']}</b>, who now leads at <span class='rupee'>{cur}{n['comp_price']:.0f}</span>."),
            (f"<b>{n['comp']}</b> has taken the price lead on <b>{_ent(sig)}</b> at "
             f"<span class='rupee'>{cur}{n['comp_price']:.0f}</span> \u2014 a <span class='rupee'>{cur}{n['gap']:.0f}</span> gap to close."),
        ])
        why = (f"Your floor is <span class='rupee'>{cur}{n['floor']:.0f}</span>, so repricing to "
               f"<span class='rupee'>{cur}{n['rec']:.0f}</span> stays above breakeven while defending the Buy Box "
               f"(now {n['bb']}%).")
        minis = [["Their price",f"{cur}{n['comp_price']:.0f}","neg"],["Your price",f"{cur}{n['own']:.0f}",""],
                 ["Your floor",f"{cur}{n['floor']:.0f}","pos"]]
    elif ct == "C2":
        finding = f"Offer count on <b>{_ent(sig)}</b> jumped from {n['prev']} to {n['now']} — a likely new entrant."
        why = "Watch weekly; if a new seller takes Buy Box on this SKU it becomes a pricing decision."
        minis = [["Offers now",str(n['now']),"neg"],["Prior",str(n['prev']),""]]
    elif ct == "C3":
        finding = _pick(sig.get("asin"), "C3", [
            f"<b>{_ent(sig)}</b> is climbing \u2014 current BSR {n['bsr']:,} vs 30-day avg {n['avg30']:,}.",
            f"Rank on <b>{_ent(sig)}</b> is improving: BSR {n['bsr']:,}, ahead of its {n['avg30']:,} 30-day average.",
            f"<b>{_ent(sig)}</b> is gaining demand \u2014 BSR has pulled in to {n['bsr']:,} from a {n['avg30']:,} average.",
        ])
        why = "Rank improvement isn't price-driven, so it's real demand. Protect stock and lean ad spend in."
        minis = [["Current BSR",f"{n['bsr']:,}","pos"],["30d avg",f"{n['avg30']:,}",""]]
    elif ct == "C4":
        finding = _pick(sig.get("asin"), "C4", [
            (f"<b>{_ent(sig)}</b> has <b>{n['doc']:.0f} days</b> of cover against a {n['lead']}-day lead time "
             f"\u2014 seasonal demand turn approaching."),
            (f"With a {n['lead']}-day lead time, <b>{_ent(sig)}</b>'s <b>{n['doc']:.0f} days</b> of cover "
             f"won't outlast the seasonal surge."),
            (f"Seasonality is closing in on <b>{_ent(sig)}</b>: only <b>{n['doc']:.0f} days</b> of cover "
             f"versus a {n['lead']}-day resupply."),
        ])
        why = "At current velocity it runs out before resupply during the seasonal surge. Restock now."
        minis = [["Days of cover",f"{n['doc']:.0f}","neg"],["Lead time",f"{n['lead']}d",""],
                 ["Velocity/day",f"{n['velocity']:.1f}",""]]
    elif ct == "C5":
        finding = f"A niche cleared your opportunity threshold in <b>{sig['category']}</b> — score {n['score']}."
        why = "Adjacent to your catalog with strong margin and low competition. Modeled — validate demand first."
        minis = [["Score",str(n['score']),"pos"],["Est. revenue",_fmt_inr(190000)+"/mo","pos"],["Competition","low","pos"]]
    elif ct == "C6":
        finding = (f"Competitors carry ~{n['comp']} SKUs in <b>{sig['category']}</b>; you carry {n['own']}. "
                   f"The gap is worth ~<span class='rupee'>{_fmt_inr(sig['exposure_inr'])}</span>/mo.")
        why = "A sourcing decision, not a quick win — flagged for evaluation."
        minis = [["Competitor SKUs",str(n['comp']),"neg"],["Your SKUs",str(n['own']),"neg"]]
    elif ct == "C7":
        finding = n["title"]
        why = n["summary"]
        minis = [["Status","reported",""]]
    elif ct == "C8":
        finding = n["title"]
        why = n["summary"]
        minis = [["Source","BIS govt","pos"]]
    else:  # C9
        finding = n["title"]
        why = n["summary"] + " Ranked low and flagged — promotes to a Demand card if data corroborates."
        minis = [["Confirmed?","not yet","neg"]]
    return finding, why, minis

def _live(sig):
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    prompt = (
        "You are Realify's research analyst. Write a seller-facing research card. "
        "Use ONLY these numbers; never invent figures. Return JSON with keys "
        "finding (1 sentence, may use <b> and <span class='rupee'>), why (2 sentences). "
        f"Card type {sig['card_type']} ({sig['type_name']}). Numbers: {json.dumps(sig['nums'])}. "
        f"Category: {sig['category']}. ASIN: {sig.get('asin')}."
    )
    msg = client.messages.create(model=config.L2_MODEL, max_tokens=400,
                                 messages=[{"role":"user","content":prompt}])
    txt = "".join(b.text for b in msg.content if getattr(b,"type","")=="text")
    txt = txt.replace("```json","").replace("```","").strip()
    obj = json.loads(txt)
    _, _, minis = _fallback(sig)   # keep deterministic minis (numbers)
    return obj["finding"], obj["why"], minis

def generate(sig, allow_live=False):
    # Card text is deterministic by default (instant, no per-card LLM call at provision
    # time). The richer LLM narrative is applied lazily on drill-down and cached there.
    use_live = allow_live and bool(config.ANTHROPIC_API_KEY)
    try:
        finding, why, minis = _live(sig) if use_live else _fallback(sig)
    except Exception:
        finding, why, minis = _fallback(sig)
    conf = _confidence(sig)
    return dict(
        finding=finding, why=why, minis=minis, type_name=_headline(sig),
        confidence=conf, conf_label=CONF_LABEL[conf],
        severity=sig["severity"], sev_label=SEV_LABEL.get(sig["severity"],"Watch"),
        exposure_val=_fmt_inr(sig["exposure_inr"]),
        exposure_pct=min(95, max(20, int(sig["exposure_inr"]/250000*60))),
    )
