"""Materialize signals into the cards table. Dedup-key keeps a re-run from
duplicating; is_new is computed by comparing against dedup-keys already present
from prior runs (the 'new since yesterday' marker)."""
import json, hashlib
from .. import db
from ..repositories.action_repo import ActionRepository

from ..repositories.seller_repo import SellerRepository
from . import detect, generate

def _dedup_key(sig):
    base = f"{sig['card_type']}:{sig.get('asin') or sig['category']}"
    return hashlib.md5(base.encode()).hexdigest()[:16]

def _trend(con, tenant_id, asin, metric, window_days=14):
    """Deterministic % change of `metric` over ~window_days (Phase 0, no ML)."""
    import datetime as _dt
    s = db.metric_series(con, tenant_id, asin, metric)
    if len(s) < 4:
        return None
    last_ts, last_v = s[-1]
    try:
        cutoff = _dt.datetime.fromisoformat(last_ts) - _dt.timedelta(days=window_days)
        earlier = [v for t, v in s if _dt.datetime.fromisoformat(t) <= cutoff]
    except Exception:
        earlier = []
    base = earlier[-1] if earlier else s[0][1]
    if not base:
        return None
    return round((last_v - base) / base * 100, 1)

# The catalog has many rules (often across different families) that detect the SAME
# underlying metric on the same SKU in the same direction — e.g. ~15 rules all firing on
# net_margin_pct below floor. Those produce near-identical cards (same finding, same
# numbers), which read as duplicates. Collapse each (field, entity, direction) to ONE
# canonical card: prefer the card whose family matches the metric, then highest severity,
# then largest exposure. C1–C9 market cards have no `field` and are left untouched.
_FIELD_CANON_FAM = {"velocity_day":"SALES","days_of_cover":"INV","stock_on_hand":"INV",
    "net_margin_pct":"MARGIN","tacos":"ADS","own_skus":"ASST","rating":"RR",
    "review_count":"RR","rev_share_pct":"SHARE","conversion_pct":"SV"}
import re as _re
_C_MARKET = _re.compile(r"^C[1-9]$")   # ONLY the C1–C9 market cards (not CASH-/CONT-/etc.)
_SEV_RANK = {"crit":3,"act":2,"opp":1,"watch":0}
def _collapse_redundant(signals):
    groups = {}; passthrough = []
    for sig in signals:
        nums = sig.get("nums") or {}
        fld = nums.get("field"); op = nums.get("op")
        ent = sig.get("asin") or sig.get("category")
        if not fld or _C_MARKET.match(sig.get("card_type","")):
            passthrough.append(sig); continue   # market/C-cards or fieldless: keep all
        groups.setdefault((fld, ent, op), []).append(sig)
    kept = []
    for (fld, ent, op), grp in groups.items():
        canon = _FIELD_CANON_FAM.get(fld)
        grp.sort(key=lambda s: (s["card_type"].split("-")[0] == canon,
                                _SEV_RANK.get(s.get("severity"), 0),
                                s.get("exposure_inr") or 0), reverse=True)
        kept.append(grp[0])
    return passthrough + kept

def run_pipeline(tenant_id):
    from .. import country
    country.use_tenant(tenant_id)            # localize money formatting for this run
    con = db.connect()
    started = db.now_iso()
    run_id = ActionRepository(con).start_run(tenant_id, started)

    from ..repositories.card_repo import CardRepository
    cards_repo = CardRepository(con)
    existing = cards_repo.existing_dedup_keys(tenant_id)
    signals = detect.detect_all(con, tenant_id)
    signals = _collapse_redundant(signals)
    # Detector -> Interpretation layer: canonical names, data-gated interpretations,
    # non-duplicate phrasing. Additive; never changes the locked numbers.
    from . import interpret
    from ..repositories.seller_repo import SellerRepository as _Seller
    by_asin = {s["asin"]: s for s in _Seller(con).all(tenant_id)}
    interpret.annotate(signals, by_asin, con, tenant_id)
    # attach the product title so card *bodies* can name the SKU by title (falls back to ASIN in
    # generate._ent); the card header keeps the ASIN as-is via _headline.
    for sig in signals:
        srow = by_asin.get(sig.get("asin"))
        if srow:
            sig["title"] = srow.get("title_override") or srow.get("title")
    # Stage 2: snapshot this run's metrics (real ongoing history), then attach a
    # deterministic 14-day trend (Phase 0) and a model forecast + confidence (Phase 1)
    # to each own-data signal. Models inform only — they never change the locked numbers.
    db.snapshot_metrics(con, tenant_id, captured_at=started)
    from .. import models
    for sig in signals:
        fld = (sig.get("nums") or {}).get("field")
        asin = sig.get("asin")
        if fld and asin and fld in db.HISTORY_METRICS:
            t = _trend(con, tenant_id, asin, fld)
            if t is not None:
                sig["_trend"] = t
        det = sig.get("detector")
        if det and asin:
            for pred in models.predict_for(con, tenant_id, asin, det):
                if pred.get("value") is not None and pred.get("confidence") != "low":
                    sig["_forecast"] = pred   # forecast informs via its own labeled mini
                    break
    # Phase 2 action-ranker: a single score per card = severity band + exposure + model
    # urgency (imminent stockouts rise within their band) + recency. Feed sorts by this.
    SEV_WEIGHT = {"crit": 4, "act": 3, "opp": 2, "watch": 1}
    for sig in signals:
        sw = SEV_WEIGHT.get(sig.get("severity"), 1)
        expo = min(100, max(0, (sig.get("exposure_inr") or 0) / 250000 * 60))
        urgency = 0
        fc = sig.get("_forecast")
        if fc and fc.get("kind") == "stockout-forecaster" and fc.get("value") is not None:
            urgency = min(200, max(0, (21 - fc["value"]) * 8))   # <21d to stockout lifts rank
        sig["_rank"] = round(sw * 1000 + expo * 3 + urgency, 2)
    produced = set()
    new_n = upd_n = 0
    for sig in signals:
        dk = _dedup_key(sig)
        produced.add(dk)
        g = generate.generate(sig)
        # Stage 2: surface the deterministic trend and the model forecast as extra minis.
        minis = list(g["minis"])
        if sig.get("_trend") is not None:
            t = sig["_trend"]
            minis.append(["14-day trend", f"{'+' if t >= 0 else ''}{t}%", "pos" if t >= 0 else "neg"])
        fc = sig.get("_forecast")
        if fc and fc.get("value") is not None:
            minis.append([f"Forecast \u00b7 {fc['label']}", f"~{fc['value']} {fc['unit']} ({fc['confidence']})", "neg"])
        is_new = 0 if dk in existing else 1
        sources = sorted({src for _, src in sig["provenance"]})
        payload = dict(
            dedup_key=dk, tenant_id=tenant_id, run_id=run_id, card_type=sig["card_type"], family=sig["family"],
            type_name=g.get("type_name") or sig["type_name"], asin=sig.get("asin"), category=sig["category"],
            finding=g["finding"], why=g["why"], severity=g["severity"], sev_label=g["sev_label"],
            confidence=g["confidence"], conf_label=g["conf_label"], exposure_label=sig["exposure_label"],
            exposure_pct=g["exposure_pct"], exposure_val=g["exposure_val"], action=sig["action"],
            sources=json.dumps(sources), minis=json.dumps(minis),
            provenance=json.dumps(sig["provenance"]), is_new=is_new,
            rank_score=sig.get("_rank", 0), exposure_inr=sig.get("exposure_inr"),
            created_at=db.now_iso(), updated_at=db.now_iso(),
        )
        cards_repo.upsert(payload)
        if is_new: new_n += 1
        else: upd_n += 1
    # prune stale ACTIVE cards no longer produced (e.g. rule disabled, or condition resolved);
    # preserve cards the seller already dismissed/marked done so they don't resurrect.
    pruned = cards_repo.prune_stale(tenant_id, existing, produced)
    ActionRepository(con).finish_run(run_id, db.now_iso(), new_n, upd_n)
    con.commit(); con.close()
    return dict(run_id=run_id, new=new_n, updated=upd_n, pruned=pruned, total=len(signals))
