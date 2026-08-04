"""Dynamic feed headline — the action-summary line at the top of the page.

Deterministic L1 decides WHAT matters (the ranked card list, urgency, counts); L2 only PHRASES it
into one punchy newsroom line and is forbidden from inventing or altering a number. When L2 is
unavailable (no API key / fixture / error) the deterministic line is returned as-is, so the
headline is always correct and never blank. Results are cached briefly per (tenant, surface,
filter) so flipping filters back and forth doesn't spam the model.
"""
import json
import re
import time

from . import config, api

_CACHE = {}          # (tid, surface, fam, cat, new) -> (ts, headline, l2)
_TTL = 120           # seconds
_URGENT = {"act", "crit"}


def _strip(s):
    return re.sub("<[^>]+>", "", s or "").strip()


def _facts(tid, surface, family, category, new_only):
    cards = api.get_feed(tid, category, family, new_only, surface)   # already ranked, top first
    by_family = {}
    for c in cards:
        fam = c.get("family") or "other"
        by_family[fam] = by_family.get(fam, 0) + 1
    top3 = [{"finding": _strip(c.get("finding") or "")[:200], "family": c.get("family"),
             "severity": c.get("severity"), "action": c.get("action")} for c in cards[:3]]
    return {
        "surface": surface,
        "filtered": bool((family and family != "all") or (category and category != "all") or new_only),
        "count": len(cards),
        "new": sum(1 for c in cards if c["is_new"]),
        "urgent": sum(1 for c in cards if c["severity"] in _URGENT),
        "opportunities": sum(1 for c in cards if c["severity"] == "opp"),
        "by_family": dict(sorted(by_family.items(), key=lambda kv: -kv[1])),
        "top": top3[0] if top3 else None,
        "top3": top3,
    }


def _fam_phrase(f):
    fams = list((f.get("by_family") or {}).keys())
    if len(fams) >= 2:
        return f"{fams[0]} and {fams[1]}"
    return fams[0] if fams else ""


def _deterministic(f):
    surf = f["surface"]
    noun = "market signals" if surf == "research" else (
        "cross-channel items" if surf == "channels" else "product insights")
    n = f["count"]
    if n == 0:
        return "Nothing needs your attention right now — you're all clear."
    top = f["top"] or {}
    lead = (top.get("finding") or top.get("type") or "").rstrip(".")
    fam_phrase = _fam_phrase(f)
    if f["urgent"]:
        s = "s" if f["urgent"] != 1 else ""
        head = f"{f['urgent']} action{s} need attention now"
        if fam_phrase:
            head += f" across {fam_phrase}"
        return f"{head} — {lead}." if lead else head + "."
    if f["new"]:
        return (f"{f['new']} new since yesterday — {lead}."
                if lead else f"{f['new']} new {noun} since yesterday.")
    if lead:
        return f"Top of your list tonight: {lead}."
    return f"{n} {noun} ranked by what touches your revenue."


def _phrase_l2(f, det):
    if not config.ANTHROPIC_API_KEY:
        return det, False
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        prompt = (
            "You write the single headline at the top of an Amazon/marketplace seller's dashboard — "
            "newsroom style: specific, insightful, action-oriented. Synthesize ACROSS the cards below "
            "to surface the through-line and the single highest-leverage move — do NOT just restate "
            "the top card. ONE line, AT MOST 18 words. Use ONLY the facts and numbers given — never "
            "invent, add, or alter a figure. No markdown, no quotes, no trailing notes.\n\nFACTS:\n"
            + json.dumps(f)[:2200] +
            "\n\nDeterministic baseline (be at least this specific; sharpen and synthesize it):\n" + det)
        m = client.messages.create(model=config.L2_MODEL, max_tokens=80,
                                   messages=[{"role": "user", "content": prompt}])
        txt = "".join(b.text for b in m.content if getattr(b, "type", "") == "text").strip()
        txt = txt.strip().strip('"').split("\n")[0].strip()
        return (txt or det), bool(txt)
    except Exception:
        return det, False


def _detail(f):
    """Deterministic standfirst — the supporting findings beneath the lead, plus counts. Built from
    facts L1 already computed (top3 findings, new/opportunity counts); no extra L2 call."""
    n = f["count"]
    if n == 0:
        return ""
    noun = ("market signals" if f["surface"] == "research"
            else "cross-channel items" if f["surface"] == "channels" else "insights")
    extras = [_strip(t.get("finding") or "").rstrip(".")
              for t in (f.get("top3") or [])[1:3] if t.get("finding")]
    sentences = []
    if extras:
        sentences.append("; ".join(extras) + ".")
    tail = []
    if f["new"]:
        tail.append(f'{f["new"]} new since yesterday')
    if f["opportunities"]:
        tail.append(f'{f["opportunities"]} flagged as opportunities')
    tail.append(f'{n} {noun} ranked by revenue exposure')
    s = ", ".join(tail)
    sentences.append(s[:1].upper() + s[1:] + ".")
    return " ".join(sentences)


def compute(tid, surface="intelligence", family="all", category="all", new_only=False):
    family = family or "all"
    category = category or "all"
    key = (tid, surface, family, category, bool(new_only))
    now = time.time()
    hit = _CACHE.get(key)
    if hit and now - hit[0] < _TTL:
        return {"ok": True, "headline": hit[1], "l2": hit[2], "detail": hit[3], "cached": True}
    f = _facts(tid, surface, family, category, new_only)
    det = _deterministic(f)
    txt, l2 = _phrase_l2(f, det)
    detail = _detail(f)
    _CACHE[key] = (now, txt, l2, detail)
    return {"ok": True, "headline": txt, "l2": l2, "detail": detail, "cached": False}
