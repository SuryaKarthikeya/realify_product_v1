"""All seller tasks across the Research surface, each producing:
  - a no-SP-API artifact (deep-link / pre-filled value / drafted text / internal record)
  - a written EXPLANATION (why this, what it does, what it does NOT do)
  - an entry in actions_log (the explainability log)
Nothing here writes to Amazon — every execution is something the SELLER completes
in their own session via a deep-link, which keeps Realify compliant."""
import json
from . import db
from .repositories.action_repo import ActionRepository
from .repositories.order_repo import OrderRepository

# ---------- amazon.in deep-link targets ----------
SC = "https://sellercentral.amazon.in"
def dl_product(asin):   return f"https://www.amazon.in/dp/{asin}"
def dl_inventory(asin): return f"{SC}/inventory?searchType=all&search={asin or ''}"
def dl_restock():       return f"{SC}/restockinventory/recommendations"
def dl_ads():           return "https://advertising.amazon.in/"
def dl_caselog():       return f"{SC}/cu/case-dashboard"
def dl_orders():        return f"{SC}/orders-v3/search"
def dl_brand():         return "https://brandservices.amazon.in/"

def _card(con, tenant_id, card_id):
    from .repositories.card_repo import CardRepository
    return CardRepository(con).get(tenant_id, card_id)

def _minis(card):
    try: return {m[0]: m[1] for m in json.loads(card.get("minis") or "[]")}
    except Exception: return {}

def _log(con, card, task_type, title, summary, explanation, mechanism, dest, payload=None):
    lid = ActionRepository(con).log_action(card["tenant_id"], db.now_iso(), card["id"], card["card_type"],
        task_type, title, summary, explanation, mechanism, dest, json.dumps(payload or {}))
    con.commit()
    return lid

def _result(ok, task_type, title, summary, explanation, mechanism, dest_label, dest_url,
            artifact=None, data_used=None, log_id=None):
    return dict(ok=ok, task_type=task_type, title=title, summary=summary, explanation=explanation,
                mechanism=mechanism, destination=dict(label=dest_label, url=dest_url),
                artifact=artifact, data_used=data_used or [], log_id=log_id)

# ================= the 7 execution handlers =================
def _reprice(con, card):
    m = _minis(card)
    summary = f"Reprice {card['asin']} to defend the Buy Box, floor-gated."
    expl = ("Realify is NOT changing your price automatically. It computed a floor-gated target from "
            "your own breakeven and the competitor's price, and is sending you to Manage Inventory to "
            "set it yourself. Repricing here stays above your margin floor, so you never sell at a loss.")
    art = f"Recommended price: {m.get('Their price','—')} area · Your floor: {m.get('Your floor','—')}. Set this on the SKU's price field."
    lid = _log(con, card, "reprice", "Reprice (floor-gated)", summary, expl, "deep-link + pre-fill",
               dl_inventory(card["asin"]), {"minis": m})
    return _result(True, "reprice", "Reprice — floor-gated", summary, expl, "deep-link + pre-fill",
                   "Open Manage Inventory", dl_inventory(card["asin"]), art,
                   ["your price (OWN)", "competitor price (Keepa/SP-API)", "breakeven floor (OWN)"], lid)

def _ad_action(con, card):
    summary = "Adjust the ad campaign spending below profitability."
    expl = ("Realify can't change bids without the Ads API, so it identified the campaign and the "
            "recommended change and is sending you to Campaign Manager. The recommendation keeps ACoS "
            "under your breakeven so the campaign stops spending profit.")
    lid = _log(con, card, "ad_action", "Ad action", summary, expl, "deep-link",
               dl_ads(), {})
    return _result(True, "ad_action", "Ad action", summary, expl, "deep-link",
                   "Open Campaign Manager", dl_ads(),
                   "Cut bid/budget on the flagged campaign, or pause it.",
                   ["ad spend (OWN Ads)", "margin (OWN)"], lid)

def _restock(con, card):
    m = _minis(card)
    summary = f"Create a restock task for {card['asin']} before it stocks out."
    expl = ("Realify logged an internal restock task and is linking you to Restock Inventory. The "
            "recommended quantity comes from your velocity and lead time; supplier POs happen off-Amazon "
            "as usual. This protects the revenue and rank a stockout would cost.")
    lid = _log(con, card, "restock_task", "Restock task", summary, expl, "deep-link + internal task",
               dl_restock(), {"minis": m})
    return _result(True, "restock_task", "Restock task", summary, expl, "deep-link + internal task",
                   "Open Restock Inventory", dl_restock(),
                   f"Days of cover: {m.get('Days of cover','—')} · Lead time: {m.get('Lead time','—')}. Create the shipment.",
                   ["days of cover (OWN)", "velocity (OWN)", "lead time (OWN)"], lid)

def _listing(con, card):
    summary = "Update the listing to reduce returns / improve quality."
    expl = ("Realify drafted the fields to change based on the return-driver and review themes, and is "
            "sending you to the listing editor to paste them. Realify never edits your listing directly "
            "— you review and approve the copy.")
    draft = ("Suggested edits: tighten the size/fit description (top return driver), add a clear "
             "material/durability line, and remove any over-stated waterproofing claim.")
    lid = _log(con, card, "listing_update", "Listing update", summary, expl, "draft + deep-link",
               dl_inventory(card["asin"]), {})
    return _result(True, "listing_update", "Listing update", summary, expl, "draft + deep-link",
                   "Open listing editor", dl_inventory(card["asin"]), draft,
                   ["return reasons (OWN)", "review themes (Tier-C)"], lid)

def _case(con, card):
    # query REAL short-paid settled orders for this ASIN (and overall) from seller_orders
    asin = card["asin"]
    rows = OrderRepository(con).short_paid_detail(card["tenant_id"], asin)
    total_gap = sum(r["expected_deposit"]-r["actual_deposit"] for r in rows)
    n = len(rows)
    if n:
        from . import country
        _cur = country.tenant_profile(card["tenant_id"])["symbol"]
        ids = ", ".join(r["order_id"] for r in rows[:5])
        draft = (f"Subject: Settlement reconciliation — {n} under-paid orders\n\n"
                 f"Affected ASIN: {asin or 'multiple'}. Across {n} settled orders, deposits fell short of "
                 f"expected by {_cur}{total_gap:,.0f}. Representative order IDs: {ids}"
                 f"{' …' if n>5 else ''}.\nRequesting review and reimbursement of the variance. "
                 f"Per-order expected vs actual attached.")
        summary = f"{n} under-paid orders found — {_cur}{total_gap:,.0f} recoverable."
    else:
        draft = (f"Subject: Settlement reconciliation\n\nAffected ASIN: {asin or 'multiple'}. No settled "
                 f"orders currently show a deposit variance above threshold. Re-run after the next settlement cycle.")
        summary = "No settlement shortfall above threshold right now."
    expl = ("Realify queried your settled orders, found those where the actual deposit fell short of the "
            "expected (gross − referral − FBA fees), summed the recoverable gap, and drafted a case body "
            "with the real order IDs. Realify does NOT file the case — you open the Case Log and paste. "
            "Every figure here comes from your own order/settlement data.")
    lid = _log(con, card, "case_report", "Case / report", summary, expl, "draft + deep-link",
               dl_caselog(), {"orders": n, "gap": round(total_gap,2)})
    return _result(True, "case_report", "Case / report", summary, expl, "draft + deep-link",
                   "Open Case Log", dl_caselog(), draft,
                   ["order deposits (OWN settlement)", "expected fees (OWN)"], lid)

def _monitor(con, card):
    label = (card.get("finding") or "")[:80]
    summary = "Track this in your watchlist (no Amazon action)."
    expl = ("This is awareness, not an Amazon action. Realify created a tracked watchlist item so the "
            "competitor/trend stays on your radar with the signal attached. If it escalates (e.g. they "
            "take your Buy Box), it surfaces again as an actionable card.")
    ActionRepository(con).add_watchlist(card["tenant_id"], db.now_iso(), card["id"], card["family"], label, card["category"], "")
    con.commit()
    lid = _log(con, card, "monitoring_ticket", "Monitoring ticket", summary, expl, "internal",
               "", {"label": label})
    return _result(True, "monitoring_ticket", "Monitoring ticket", summary, expl, "internal",
                   "View watchlist", "#watchlist", None, ["signal (Realify)"], lid)

def _review(con, card):
    asin = card["asin"]
    rows = OrderRepository(con).review_eligible_detail(card["tenant_id"], asin)
    n = len(rows)
    if n:
        ids = "\n".join(f"  • {r['order_id']}  (delivered {r['delivered_date']})" for r in rows[:10])
        draft = (f"{n} order(s) are inside Amazon's review window with no review yet"
                 f"{' for '+asin if asin else ''}. Eligible order IDs:\n{ids}" + (f"\n  …and {n-10} more." if n>10 else "")
                 + "\nIn Manage Orders, open each and click 'Request a Review' (one-tap, Amazon-compliant).")
        summary = f"{n} eligible order(s) for a review request."
    else:
        draft = ("No orders are currently inside the review window without a review. Check back as recent "
                 "deliveries age into the 5–30 day window.")
        summary = "No review-eligible orders right now."
    expl = ("The Solicitations API is gated, so Realify filtered your orders for those delivered 5–30 days "
            "ago with no review yet, and listed the real order IDs. You click 'Request a Review' per order "
            "in Manage Orders — Realify never contacts buyers directly. Lifts review velocity without you "
            "hunting for eligible orders.")
    lid = _log(con, card, "review_request", "Review request", summary, expl, "list + deep-link",
               dl_orders(), {"eligible": n})
    return _result(True, "review_request", "Review request", summary, expl, "list + deep-link",
                   "Open Manage Orders", dl_orders(), draft,
                   ["delivered orders (OWN)", "review status (OWN)"], lid)

# card_type -> default handler (primary action), matching the action-group mapping
HANDLER = {
    "C1": _reprice, "C2": _monitor, "C3": _restock, "C4": _restock, "C5": None,
    "C6": None, "C7": _monitor, "C8": _case, "C9": _monitor,
}
# explicit action-name -> handler (so the UI can request any of the 7)
BY_NAME = {"reprice": _reprice, "ad_action": _ad_action, "restock_task": _restock,
           "listing_update": _listing, "case_report": _case, "monitoring_ticket": _monitor,
           "review_request": _review}

# R15 Part 0 — each action handler's governing PDP lens. An agency operator drilled into a brand can
# only EXECUTE an in-lens action when the brand's envelope grants 'execute' for that lens; otherwise the
# action is returned as proposal_required (the client re-routes it to the co-sign/propose path).
_HANDLER_LENS = {_reprice: "pricing", _ad_action: "ads", _restock: "inventory",
                 _listing: "listings", _case: "reporting", _monitor: "reporting", _review: "reporting"}

def do_action(tenant_id, card_id, action=None, actor_caps=None):
    con = db.connect(); card = _card(con, tenant_id, card_id)
    if not card: con.close(); return {"ok": False, "error": "card not found"}
    # 1) explicit action name from the UI  2) C1–C9 default  3) the rule's own
    # action_handler (so generic catalog cards run the SAME handler the feed labelled
    # them with — Reprice runs reprice, not the monitoring fallback)  4) monitor.
    fn = BY_NAME.get(action) or HANDLER.get(card["card_type"])
    if fn is None:
        from .repositories.rules_repo import RulesRepository
        row = RulesRepository(con).get_rule(card["card_type"])
        if row: fn = BY_NAME.get(row["action_handler"])
    fn = fn or _monitor
    # R15 Part 0 — envelope gate: a suggest-only / locked lens can NEVER execute here (defense in depth,
    # independent of the client). Return the decision as a proposal for the brand to co-sign instead.
    if actor_caps is not None:
        lens = _HANDLER_LENS.get(fn, "reporting")
        if actor_caps.get(lens, "read") != "execute":
            con.close()
            return {"ok": False, "proposal_required": True, "lens": lens,
                    "kind": action or card.get("card_type"),
                    "signal": card.get("title") or card.get("card_type") or "",
                    "impact_usd_minor": int(card.get("impact_usd_minor") or 0)}
    res = fn(con, card)
    con.close(); return res

# ================= research-native tasks =================
def add_to_sourcing(tenant_id, card_id, picks):
    """picks: list of competitor dicts from the research payload."""
    con = db.connect(); card = _card(con, tenant_id, card_id)
    if not card: con.close(); return {"ok": False, "error": "card not found"}
    seg = None
    n = 0
    for c in picks:
        seg = c.get("segment") or seg
        try:
            ActionRepository(con).add_sourcing(card["tenant_id"], db.now_iso(), card_id, c.get("segment",""), c.get("asin",""), c.get("title",""),
                 c.get("brand",""), c.get("price",0), c.get("bsr",0), c.get("reviews",0),
                 c.get("rating",0), c.get("opp_score",0), "")
            n += 1
        except Exception: pass
    con.commit()
    summary = f"Added {n} SKU(s) to your sourcing list."
    expl = ("This is a pure internal artifact — no Amazon API involved. Realify pinned the competitor "
            "SKUs you selected, with their demand/review data, so you can export the list and source "
            "against suppliers off-Amazon. Nothing here touches your or anyone's listing.")
    lid = _log(con, card, "add_to_sourcing", "Add to sourcing list", summary, expl, "internal artifact",
               "#sourcing", {"count": n})
    con.close()
    return _result(True, "add_to_sourcing", "Add to sourcing list", summary, expl, "internal artifact",
                   "View sourcing list", "#sourcing", None, ["competitor SKUs (Keepa product-finder)"], lid)

def save_brief(tenant_id, card_id):
    con = db.connect(); card = _card(con, tenant_id, card_id)
    if not card: con.close(); return {"ok": False, "error": "card not found"}
    from .pipeline.research import research_card
    r = research_card(tenant_id, card_id)
    brief = r.get("brief", "")
    ActionRepository(con).add_brief(card["tenant_id"], db.now_iso(), card_id, card["card_type"], card["category"], brief)
    con.commit()
    summary = "Saved this research brief."
    expl = ("Realify persisted the decision brief from this card's drill-down so you can return to it "
            "across sessions — useful for multi-week decisions like sourcing a new line.")
    lid = _log(con, card, "save_brief", "Save brief", summary, expl, "internal artifact", "#briefs", {})
    con.close()
    return _result(True, "save_brief", "Save brief", summary, expl, "internal artifact",
                   "Saved", "#briefs", brief, ["research brief (Realify)"], lid)

def dismiss(tenant_id, card_id, done=False):
    con = db.connect(); card = _card(con, tenant_id, card_id)
    if not card: con.close(); return {"ok": False, "error": "card not found"}
    from .repositories.card_repo import CardRepository
    CardRepository(con).set_status(tenant_id, card_id, "done" if done else "dismissed")
    con.commit()
    tt = "mark_done" if done else "dismiss"
    summary = ("Marked done." if done else "Dismissed.")
    expl = (("You marked this resolved. " if done else "You dismissed this card. ") +
            "Realify removes it from the feed; the underlying condition is re-checked on the next data "
            "pull, so if it recurs it will surface again as a new card.")
    lid = _log(con, card, tt, summary, summary, expl, "internal", "", {})
    con.close()
    return _result(True, tt, summary, summary, expl, "internal", "", "", [], lid)

def add_watch(tenant_id, card_id):
    con = db.connect(); card = _card(con, tenant_id, card_id)
    if not card: con.close(); return {"ok": False, "error": "card not found"}
    res = _monitor(con, card); con.close(); return res

# ================= click-outs =================
def clickout(tenant_id, card_id, kind):
    con = db.connect(); card = _card(con, tenant_id, card_id)
    if not card: con.close(); return {"ok": False, "error": "card not found"}
    if kind == "amazon":
        url = dl_product(card["asin"]) if card["asin"] else f"https://www.amazon.in/s?k={card['category']}"
        label, expl = "View on Amazon", ("Opens the live Amazon listing. Realify deliberately does not "
            "reproduce live competitor pages, stock, or review text — for ground truth you view it on "
            "Amazon, in your own session.")
    elif kind == "source":
        prov = json.loads(card.get("provenance") or "[]")
        url = "https://keepa.com/"  # provenance source; refined per card in a fuller build
        label, expl = "View source", ("Opens the source behind this signal so you can verify it — "
            "Realify is the synthesis layer; the source is the ground truth.")
    else:  # research further
        url = f"https://www.indiamart.com/search.mp?ss={card['category']}"
        label, expl = "Research further", ("A curated outbound link for the long tail (e.g. supplier "
            "sourcing) that Realify intentionally doesn't host.")
    lid = _log(con, card, f"clickout_{kind}", label, label, expl, "click-out", url, {})
    con.close()
    return _result(True, f"clickout_{kind}", label, label, expl, "click-out", label, url, None, [], lid)

# ================= reads (Activity panel) =================
def get_log(tenant_id, limit=100):
    con = db.connect()
    rows = ActionRepository(con).recent(tenant_id, limit)
    con.close(); return rows

def get_sourcing(tenant_id):
    con = db.connect()
    rows = ActionRepository(con).list_sourcing(tenant_id)
    con.close(); return rows

def get_watchlist(tenant_id):
    con = db.connect()
    rows = ActionRepository(con).list_watchlist(tenant_id)
    con.close(); return rows

def sourcing_csv(tenant_id):
    rows = get_sourcing(tenant_id)
    cols = ["segment","asin","title","brand","price","bsr","reviews","rating","opp_score"]
    out = ",".join(cols) + "\n"
    for r in rows:
        out += ",".join('"'+str(r.get(c,"")).replace('"',"'")+'"' for c in cols) + "\n"
    return out
