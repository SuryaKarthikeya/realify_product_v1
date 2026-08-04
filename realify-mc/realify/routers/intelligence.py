"""Explainability + governance surface for the Intelligence tab.

Reads the RIA bot's governance tables (ria_recommendations, ria_forecast_accuracy)
— which live in the SAME Postgres realify_mc this app is bound to — and serves:

  GET  /recommendations            pending AI recommendations with their FULL
                                   auditable reason trace + backtested accuracy
  GET  /model/accuracy             catalog-level forecast accuracy (the trust badge)
  POST /recommendation/{id}/approve|reject   human-in-the-loop decision

The reason trace is written by ria_forecast/explain.py into agent_reasoning; the
accuracy is written by ria_forecast/backtest.py. This router only reads/renders it
— no model logic here. Approve/reject mirror the bot's DecisionStore transitions
so the CLI and the UI act on one queue.
"""
import asyncio
import json
import os
import urllib.parse
import urllib.request
from datetime import date, datetime
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from realify import db
from .deps import current, require_tenant

_BOT_URL = os.environ.get("RIA_BOT_URL", "http://localhost:8090").rstrip("/")
_VOICE_URL = os.environ.get("RIA_VOICE_URL", "http://gx10-f54a.local:8200").rstrip("/")

router = APIRouter()


def _clean(d):
    """Coerce non-JSON types (PG datetimes) so JSONResponse can serialize the row."""
    if not isinstance(d, dict):
        return d
    return {k: (v.isoformat() if isinstance(v, (datetime, date)) else v) for k, v in d.items()}

# Governance tables may be absent if the bot never ran (fresh dev DB). Every handler
# soft-fails to an empty/steady result so the tab renders regardless.


def _jsonb(v):
    """jsonb comes back as a dict from psycopg, but as a str on sqlite — normalize."""
    if isinstance(v, (dict, list)) or v is None:
        return v
    try:
        return json.loads(v)
    except (ValueError, TypeError):
        return None


def _accuracy_row(con, tenant_id, sku, backend=None):
    """Best accuracy row for a SKU (fallback to catalog rollup), any backend if unset."""
    for skey in ([sku, "*ALL*"] if sku else ["*ALL*"]):
        q = ("SELECT internal_sku, backend, horizon_days, n_folds, n_skus, mape, wape, "
             "bias_pct, coverage_80, mae, naive_mae, skill, computed_at "
             "FROM ria_forecast_accuracy WHERE tenant_id=? AND internal_sku=?")
        params = [tenant_id, skey]
        if backend:
            q += " AND backend=?"; params.append(backend)
        q += " ORDER BY computed_at DESC LIMIT 1"
        try:
            row = con.execute(q, params).fetchone()
        except Exception:
            return None
        if row:
            return _clean(dict(row))
    return None


@router.get("/recommendations")
def recommendations(request: Request, limit: int = 20):
    """Pending AI recommendations for the seller, each with its reason trace + badge."""
    tid = require_tenant(request)
    con = db.connect()
    try:
        try:
            rows = con.execute(
                """SELECT r.id, r.internal_sku, s.title, r.channel, r.rec_type, r.action,
                          r.expected_impact, r.impact_metric, r.confidence, r.priority,
                          r.agent_reasoning, r.action_payload, r.created_at, r.expires_at
                   FROM ria_recommendations r
                   LEFT JOIN seller_skus s
                     ON s.tenant_id = r.tenant_id AND s.internal_sku = r.internal_sku
                   WHERE r.tenant_id=? AND r.status='pending' AND r.expires_at > now()
                   ORDER BY CASE r.priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3 ELSE 4 END,
                            r.expected_impact DESC, r.confidence DESC
                   LIMIT ?""",
                [tid, limit]).fetchall()
        except Exception:
            return JSONResponse({"recommendations": [], "model_accuracy": None,
                                 "note": "governance not initialized"})
        out = []
        for r in rows:
            r = dict(r)
            reasoning = _jsonb(r.get("agent_reasoning")) or {}
            trace = reasoning.get("trace")
            acc = None
            if trace and isinstance(trace, dict):
                acc = trace.get("accuracy")
            if not acc:
                row = _accuracy_row(con, tid, r.get("internal_sku"))
                if row:
                    acc = {"metrics": row, "scope": row.get("internal_sku")}
            out.append({
                "id": str(r["id"]),
                "internal_sku": r.get("internal_sku"),
                "title": r.get("title"),
                "rec_type": r.get("rec_type"),
                "action": r.get("action"),
                "priority": r.get("priority"),
                "confidence": r.get("confidence"),
                "expected_impact": r.get("expected_impact"),
                "impact_metric": r.get("impact_metric"),
                "explanation": reasoning.get("explanation"),
                "accuracy_badge": reasoning.get("accuracy_badge"),
                "trace": trace,
                "accuracy": acc,
            })
        return JSONResponse({"recommendations": out,
                             "model_accuracy": _accuracy_row(con, tid, "*ALL*")})
    finally:
        con.close()


@router.get("/outcomes")
def outcomes(request: Request, limit: int = 20):
    """Approved recs graded against reality (outcome_impact written by the outcome
    loop): predicted vs realized units + error. The loop-closing trust signal."""
    tid = require_tenant(request)
    con = db.connect()
    try:
        try:
            rows = con.execute(
                """SELECT r.id, r.internal_sku, s.title, r.rec_type, r.action,
                          r.expected_impact, r.outcome_impact, r.impact_metric, r.approved_at
                   FROM ria_recommendations r
                   LEFT JOIN seller_skus s
                     ON s.tenant_id=r.tenant_id AND s.internal_sku=r.internal_sku
                   WHERE r.tenant_id=? AND r.outcome_impact IS NOT NULL
                   ORDER BY r.updated_at DESC LIMIT ?""", [tid, limit]).fetchall()
        except Exception:
            return JSONResponse({"outcomes": [], "summary": None})
        out, errs = [], []
        for r in rows:
            r = dict(r)
            pred = float(r.get("expected_impact") or 0)
            real = float(r.get("outcome_impact") or 0)
            err = abs(pred - real) / max(real, 1.0) * 100
            errs.append(err)
            out.append({"id": str(r["id"]), "internal_sku": r.get("internal_sku"),
                        "title": r.get("title"), "action": r.get("action"),
                        "predicted": round(pred, 1), "realized": round(real, 1),
                        "error_pct": round(err, 1), "metric": r.get("impact_metric")})
        summary = {"n": len(out), "avg_error_pct": round(sum(errs) / len(errs), 1)} if out else None
        return JSONResponse({"outcomes": out, "summary": summary})
    finally:
        con.close()


@router.get("/model/accuracy")
def model_accuracy(request: Request):
    """Catalog-level backtested accuracy — the headline trust badge for the tab."""
    tid = require_tenant(request)
    con = db.connect()
    try:
        return JSONResponse({"accuracy": _accuracy_row(con, tid, "*ALL*")})
    finally:
        con.close()


# The full RIA model program — every family, the model behind it, and its honest
# verdict band. Static taxonomy (from the model-program review) enriched with LIVE
# metrics/predictions pulled from the ria_* tables in /models below.
MODEL_PROGRAM = [
    {"num": 1, "family": "Inventory & Demand", "band": "shipped",
     "predicts": "Daily demand · reorder point · days-to-stockout",
     "algo": "chronos-2 — zero-shot time-series foundation model"},
    {"num": 3, "family": "Sales", "band": "shipped",
     "predicts": "Forward revenue & velocity",
     "algo": "derived from the chronos-2 demand forecast"},
    {"num": 2, "family": "Pricing & Buy Box", "band": "shipped",
     "predicts": "Profit/revenue-optimal price + elasticity curve",
     "algo": "LightGBM elasticity regression",
     "caveat": "Now anchored to REAL COGS (Autofy cost file) — margins were ~2× overstated; "
               "elasticity still on a synthetic price panel until real repricing history lands"},
    {"num": 6, "family": "Competitive", "band": "shipped",
     "predicts": "Why a SKU is at risk (undercut / new entrant) + learned lead–lag",
     "algo": "signal-graph RCA — Neo4j traversal + learned PRECEDES lifts"},
    {"num": 7, "family": "News & External", "band": "shipped",
     "predicts": "Typed external signals (recall / cost / demand-shift) mapped to your SKUs",
     "algo": "fine-tuned Gemma-4-E4B structured extraction → signal graph"},
    {"num": 11, "family": "Rating Risk", "band": "shipped",
     "predicts": "Projected rating N days out + floor-crossing warning",
     "algo": "damped linear drift (beat chronos-2 & naive)"},
    {"num": 0, "family": "Listing / Content (Vision)", "band": "shipped",
     "predicts": "Product attributes + SEO keyword gaps read from product photos",
     "algo": "Qwen2.5-VL-7B vision-language model"},
    {"num": 5, "family": "Opportunity / Conversion", "band": "held",
     "predicts": "Which SKUs convert well, from listing quality",
     "algo": "LightGBM + TabPFN v2 classifier",
     "caveat": "Re-run on the REAL Unit-Session% label (Business Report): LOO-AUC 0.59 on the "
               "n=14 SKUs with real traffic — content features don't help. It's the label, not features",
     "data_ask": "Daily conversion time-series (repeat Business Report pulls)"},
    {"num": 4, "family": "Demand — Covariates", "band": "held",
     "predicts": "Demand conditioned on price / ad covariates",
     "algo": "Moirai-1.1-R covariate forecaster",
     "caveat": "Re-run with the REAL daily ad-spend covariate: -0.2% catalog WAPE lift. Helps the "
               "~8 advertised SKUs but dilutes catalog-wide; 46-day series too short",
     "data_ask": "6+ months of daily demand + ad spend"},
    {"num": 10, "family": "Ads Uplift", "band": "held",
     "predicts": "Bid → sales uplift (causal ACoS response)",
     # NOT EconML — that was the aspiration, never implemented. What exists is a per-SKU OLS of total
     # daily units on ad spend with trend + day-of-week controls, used as a SCREEN (ria_forecast/
     # ads_uplift_probe.py). It fails, so nothing ships. Corrected 2026-07-26: the previous entry
     # claimed "a correlational ROAS response ships", which was never true.
     "algo": "EconML LinearDML + CausalForestDML (active estimator; artifact ria_ads_response)",
     "caveat": "DML is live as the estimator and it HELPED: effect halved (0.0069 -> 0.0035 units/Rs1, "
               "95% CI [0.0020,0.0051]) and out-of-sample harm went -60% -> -0.8% (flagship -134% -> -6.7%). "
               "Still HELD for customers on TWO counts: skill -0.8% misses the +5% gate, and the "
               "reverse-direction refutation (units->spend, CI [+18.3,+53.0]) is equally significant, so "
               "causal DIRECTION is unidentified. Placebo separation 3.3x (ok), random-common-cause stable",
     "data_ask": "Bid/budget-change log (dates + magnitudes) — the recorded treatment causal ID needs"},
    {"num": 12, "family": "Rating — the “why”", "band": "held",
     "predicts": "Which product aspects drive rating drops",
     "algo": "aspect-based sentiment (Gemma-4-12B / Ollama)",
     "caveat": "Runs on 102 REAL return comments: used_item 31%, not-as-described 25%, functionality "
               "20% (97/102 negative). Ships as a return-aspect insight; full rating-why still needs reviews",
     "data_ask": "Review text (SP-API / Brand Analytics)"},
    {"num": 8, "family": "Margin", "band": "rule",
     "predicts": "Net margin vs breakeven floor",
     "algo": "deterministic threshold — a fact, not a prediction"},
    {"num": 9, "family": "Cash", "band": "rule",
     "predicts": "Trapped capital / days-of-cover extremes",
     "algo": "deterministic threshold — a fact, not a prediction"},
]

# Real input → output → why for the models that have no live rec/trace (derived,
# held, or rule). The shipped forecast/price models attach their actual reason trace
# at request time in /model-program below.
STATIC_RUNS = {
    3: {"input": [{"l": "Input", "v": "the chronos demand forecast (units) × unit price"}],
        "output": [{"l": "Output", "v": "forward revenue & momentum — derived, no separate model"}],
        "why": "Sales = demand × price; it inherits the demand backtest, so no independent validation is needed."},
    5: {"input": [{"l": "Data", "v": "42 SKUs × 22 features + REAL Unit-Session% label (Business Report)"},
                  {"l": "Usable", "v": "n=14 with enough sessions for a meaningful conversion rate"}],
        "output": [{"l": "Real label", "v": "LOO-AUC 0.59 (baseline) · 0.55 (+VLM content)"},
                   {"l": "Gate 0.65", "v": "HOLD — content doesn't help; it's the label"}],
        "why": "Real conversion label confirmed the null: half the catalog has near-zero traffic in one "
               "snapshot, so n collapses and AUC≈0.59. The fix is a longitudinal series, not more features."},
    4: {"input": [{"l": "Data", "v": "44 SKUs, buybox%+TACoS (past) + REAL daily ad_spend (known), 14d holdout"}],
        "output": [{"l": "Moirai lift", "v": "-0.2% catalog WAPE (helps ~8 advertised SKUs, dilutes)"}],
        "why": "Real daily ad-spend covariate surfaced a genuine effect on advertised SKUs (e.g. 1.12→0.83 WAPE) "
               "but washes out across the catalog on a 46-day series. Below the 5% bar — revisit at 6+ months."},
    10: {"input": [{"l": "Data", "v": "REAL daily ad panel (Sponsored Products): 664 obs, 90 days, 10 SKUs"}],
         "output": [{"l": "ROAS CV", "v": "0.76 (was ~0.00) · 0% constant · within-SKU elasticity +0.59"}],
         "why": "The seeded/constant-ROAS blocker is GONE — a real correlational ROAS response now ships. "
                "Causal uplift misses identifiability by 0.018; needs a bid-change log to certify."},
    12: {"input": [{"l": "Data", "v": "102 REAL return comments (Gemma-4-12B aspect tagging)"}],
         "output": [{"l": "Top aspects", "v": "used_item 31% · not-as-described 25% · functionality 20%"},
                    {"l": "Signal", "v": "97/102 negative; concentrated in Car Electronics"}],
         "why": "Aspect model runs and attributes returns to product aspects — ships as a return-reason insight. "
                "Full rating-why still needs the review corpus (return text ≠ reviews, n small)."},
    8: {"input": [{"l": "Fact", "v": "net_margin_pct vs breakeven_floor (measured)"}],
        "output": [{"l": "Card", "v": "flags every SKU trading under its floor"}],
        "why": "Margin below the floor is a measured fact, not a prediction — a model would only add noise."},
    9: {"input": [{"l": "Fact", "v": "days_of_cover / capital locked in inventory (measured)"}],
        "output": [{"l": "Card", "v": "flags overstock & trapped cash"}],
        "why": "A deterministic fact — no model, by design."},
}


@router.get("/model-program")
def model_program(request: Request):
    """The full RIA model program — every family, its model, live prediction, and
    honest status band (shipped / held / rule). Powers the Models surface. Every
    live enrichment soft-fails so the registry renders regardless of DB state."""
    tid = require_tenant(request)
    con = db.connect()
    live: dict = {}
    runs: dict = {}

    def one(q, params=()):
        try:
            r = con.execute(q, list(params)).fetchone()
            return dict(r) if r else None
        except Exception:
            return None

    try:
        # #1/#3 demand + sales — catalog walk-forward accuracy
        acc = _accuracy_row(con, tid, "*ALL*")
        if acc:
            live[1] = {"metric": f"WAPE {acc.get('wape')}% · skill +{acc.get('skill')} · "
                                 f"80% coverage {acc.get('coverage_80')} ({acc.get('backend')})",
                       "metric_note": "walk-forward, out-of-sample on real data"}
            live[3] = {"metric": f"inherits the demand backtest (WAPE {acc.get('wape')}%)"}
        try:
            for r in con.execute("SELECT rec_type, count(*) c FROM ria_recommendations "
                                 "WHERE tenant_id=? AND status='pending' GROUP BY rec_type",
                                 [tid]).fetchall():
                d = dict(r)
                if d["rec_type"] == "replenishment":
                    live.setdefault(1, {})["live"] = f"{d['c']} live reorder recommendation(s) queued"
                elif d["rec_type"] == "pricing":
                    live.setdefault(2, {})["live"] = f"{d['c']} live price recommendation(s) queued"
        except Exception:
            pass
        rec = one("SELECT action FROM ria_recommendations WHERE tenant_id=? AND rec_type='replenishment' "
                  "AND status='pending' ORDER BY expected_impact DESC LIMIT 1", [tid])
        if rec:
            live.setdefault(1, {})["sample"] = rec.get("action")
        prec = one("SELECT action FROM ria_recommendations WHERE tenant_id=? AND rec_type='pricing' "
                   "AND status='pending' ORDER BY created_at DESC LIMIT 1", [tid])
        if prec:
            live.setdefault(2, {})["sample"] = prec.get("action")
        # #2 price fit
        pf = one("SELECT r2, mae FROM ria_price_fit WHERE tenant_id=? AND internal_sku='*ALL*' "
                 "ORDER BY computed_at DESC LIMIT 1", [tid])
        if pf:
            live.setdefault(2, {})["metric"] = f"holdout R² {pf.get('r2')} · MAE {pf.get('mae')}"
        # #11 rating fit + a live projection
        rf = one("SELECT mae, skill, drop_recall FROM ria_rating_fit WHERE tenant_id=? "
                 "ORDER BY computed_at DESC LIMIT 1", [tid])
        if rf:
            live.setdefault(11, {})["metric"] = (f"MAE {rf.get('mae')} · skill +{rf.get('skill')} · "
                                                 f"drop-recall {rf.get('drop_recall')}")
        rr = one("SELECT internal_sku, current, projected, horizon_days FROM ria_rating_risk "
                 "WHERE tenant_id=? ORDER BY drop_pts DESC LIMIT 1", [tid])
        if rr:
            live.setdefault(11, {})["live"] = (f"{rr.get('internal_sku')}: {rr.get('current')}→"
                                               f"{rr.get('projected')} in {rr.get('horizon_days')}d")
        # #7 news
        ns = one("SELECT count(*) c FROM ria_market_signals WHERE tenant_id=?", [tid])
        if ns:
            live.setdefault(7, {})["live"] = f"{ns.get('c')} external signals mapped to your SKUs"
        nsample = one("SELECT title FROM ria_market_signals WHERE tenant_id=? ORDER BY confidence DESC LIMIT 1", [tid])
        if nsample:
            live.setdefault(7, {})["sample"] = nsample.get("title")
        # #6 competitive
        cc = one("WITH latest AS (SELECT DISTINCT ON (asin, seller) asin, seller, price FROM competitor_offers "
                 "WHERE tenant_id=? ORDER BY asin, seller, captured_at DESC) "
                 "SELECT count(DISTINCT s.internal_sku) c FROM seller_skus s JOIN latest l ON l.asin=s.asin "
                 "WHERE s.tenant_id=? AND l.price < s.price", [tid, tid])
        if cc:
            live.setdefault(6, {})["live"] = f"{cc.get('c')} SKUs under live competitor undercut"
        st = one("SELECT count(*) c FROM ria_signal_transitions", [])
        if st and st.get("c"):
            live.setdefault(6, {})["metric"] = f"{st.get('c')} learned lead–lag (PRECEDES) rules"
        # #0 listing (VLM)
        lc = one("SELECT count(*) c FROM ria_listing_attrs WHERE tenant_id=?", [tid])
        if lc:
            live.setdefault(0, {})["live"] = f"{lc.get('c')} SKUs photo-read for attributes + keyword gaps"
        # #5 conversion — held, the honest null
        qf = one("SELECT loo_auc, n FROM ria_quality_fit WHERE tenant_id=? ORDER BY computed_at DESC LIMIT 1", [tid])
        if qf:
            live.setdefault(5, {})["metric"] = f"LOO-AUC {qf.get('loo_auc')} (n={qf.get('n')}, ship gate 0.65)"

        # ---- Real input → output → why for the SHIPPED models (the actual run on this data) ----
        # #1 demand + #2 price: attach the full reason trace (steps / inputs / formula / forecast
        # curve / accuracy) the model wrote when it ran.
        dem = one("SELECT agent_reasoning FROM ria_recommendations WHERE tenant_id=? AND "
                  "rec_type='replenishment' AND status='pending' ORDER BY created_at DESC LIMIT 1", [tid])
        if dem:
            tr = (_jsonb(dem.get("agent_reasoning")) or {})
            runs[1] = {"trace": tr.get("trace") or {}, "headline": tr.get("explanation")}
        prc = one("SELECT agent_reasoning FROM ria_recommendations WHERE tenant_id=? AND "
                  "rec_type='pricing' AND status='pending' ORDER BY created_at DESC LIMIT 1", [tid])
        if prc:
            trp = (_jsonb(prc.get("agent_reasoning")) or {})
            runs[2] = {"trace": trp.get("trace") or {}, "headline": trp.get("explanation")}
        # #11 rating-risk: a real projection row
        rr2 = one("SELECT internal_sku, current, projected, drop_pts, horizon_days, crosses_floor "
                  "FROM ria_rating_risk WHERE tenant_id=? ORDER BY drop_pts DESC LIMIT 1", [tid])
        if rr2:
            runs[11] = {
                "input": [{"l": "SKU", "v": rr2.get("internal_sku")},
                          {"l": "Current rating", "v": rr2.get("current")}],
                "output": [{"l": f"Projected in {rr2.get('horizon_days')}d", "v": rr2.get("projected")},
                           {"l": "Drop", "v": f"{rr2.get('drop_pts')} pts"},
                           {"l": "Crosses 4.0 floor", "v": "yes" if rr2.get("crosses_floor") else "no"}],
                "why": "Damped linear drift (φ=0.9) fit on the rating history — beat chronos-2 and naive in backtest."}
        # #6 competitive: one live undercut case
        cs = one("WITH latest AS (SELECT DISTINCT ON (asin, seller) asin, seller, price FROM competitor_offers "
                 "WHERE tenant_id=? ORDER BY asin, seller, captured_at DESC) "
                 "SELECT s.internal_sku, s.price AS own, "
                 "count(*) FILTER (WHERE l.price < s.price) AS uc, "
                 "min(l.price) FILTER (WHERE l.price < s.price) AS low "
                 "FROM seller_skus s JOIN latest l ON l.asin=s.asin "
                 "WHERE s.tenant_id=? AND s.internal_sku IS NOT NULL "
                 "GROUP BY s.internal_sku, s.price "
                 "HAVING count(*) FILTER (WHERE l.price < s.price) > 0 ORDER BY uc DESC LIMIT 1", [tid, tid])
        if cs:
            own, low = float(cs.get("own") or 0), float(cs.get("low") or 0)
            runs[6] = {
                "input": [{"l": "SKU", "v": cs.get("internal_sku")},
                          {"l": "Your price", "v": own},
                          {"l": "Signal", "v": "live competitor_offers, joined by ASIN"}],
                "output": [{"l": "Undercutters", "v": cs.get("uc")},
                           {"l": "Lowest rival", "v": low},
                           {"l": "Gap", "v": round(own - low, 2) if low else None}],
                "why": "Graph traversal over live offers + learned PRECEDES lead–lag "
                       "(e.g. rating_drop → margin_drop, lift ×2.31 @ 7d)."}
        # #7 news: one typed signal
        ms = one("SELECT event_type, direction, category, impact, title, source "
                 "FROM ria_market_signals WHERE tenant_id=? ORDER BY confidence DESC LIMIT 1", [tid])
        if ms:
            runs[7] = {
                "input": [{"l": "Raw source", "v": ms.get("source") or "news feed"},
                          {"l": "Headline", "v": ms.get("title")}],
                "output": [{"l": "Type", "v": ms.get("event_type")},
                           {"l": "Direction", "v": ms.get("direction")},
                           {"l": "Category", "v": ms.get("category")},
                           {"l": "Impact", "v": ms.get("impact")}],
                "why": "Fine-tuned Gemma-4-E4B reads the article and emits a typed MarketSignal mapped to your category."}
        # #0 listing (VLM): one photo read
        la = one("SELECT internal_sku, product_type, primary_color, material, image_quality, suggested_keywords "
                 "FROM ria_listing_attrs WHERE tenant_id=? ORDER BY image_quality ASC NULLS FIRST LIMIT 1", [tid])
        if la:
            kws = _jsonb(la.get("suggested_keywords")) or []
            runs[0] = {
                "input": [{"l": "SKU", "v": la.get("internal_sku")},
                          {"l": "Input", "v": "the product’s primary photo (Keepa)"}],
                "output": [{"l": "Product type", "v": la.get("product_type")},
                           {"l": "Colour", "v": la.get("primary_color")},
                           {"l": "Material", "v": la.get("material")},
                           {"l": "Keyword gaps", "v": ", ".join([k for k in kws if isinstance(k, str)][:4])}],
                "why": "Qwen2.5-VL-7B reads the image; keyword gaps = suggested terms not yet in your title."}
    finally:
        con.close()

    out = []
    for spec in MODEL_PROGRAM:
        e = dict(spec)
        e.update(live.get(spec["num"], {}))
        e["run"] = runs.get(spec["num"]) or STATIC_RUNS.get(spec["num"])
        out.append(e)
    counts = {b: sum(1 for m in out if m["band"] == b) for b in ("shipped", "held", "rule")}
    return JSONResponse({
        "models": out, "counts": counts,
        "bands": {
            "shipped": "Models we trust — validated and serving",
            "held": "Built, didn’t clear the bar — an honest null, with the data that unlocks it",
            "rule": "Deterministic facts — no model, by design",
        }})


def _run_one(domain, sku, objective):
    """Proxy a single per-SKU model run to the bot's LLM-free /v1/run-tool."""
    try:
        req = urllib.request.Request(
            f"{_BOT_URL}/v1/run-tool",
            data=json.dumps({"domain": domain, "sku": sku, "objective": objective}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"ok": False, "sku": sku, "domain": domain, "error": f"model service unavailable ({e})"}


def _ads_preview_allowed(tid):
    """Delegates to the single allowlist gate (routers/helpers) so the API and the UI can't diverge."""
    from .helpers import ads_preview_allowed
    return ads_preview_allowed(tid)


# ---------------------------------------------------------------- reorder allocation (family #9)
_CASH_KEY = "cash.inventory_budget"


def _cash_suggestion(con, tid):
    """A defensible starting figure from REAL data: what it cost to replace the goods sold in the last
    complete month (units x COGS).

    Deliberately NOT derived from `settlements`. That table is stale synthetic data for report-onboarded
    tenants — for tenant 12 it reports 4-6x the real order gross and covers all 44 SKUs when only 18
    actually sell. Inferring cash from it would overstate the budget several-fold and make the allocator
    recommend far too much stock. (The Cash KPI already sidesteps it, showing "add settlement report".)
    """
    try:
        row = con.execute(
            """SELECT SUM(o.units * s.cogs) AS repl
                 FROM seller_orders o
                 JOIN seller_skus s ON s.tenant_id=o.tenant_id AND s.internal_sku=o.internal_sku
                WHERE o.tenant_id=?
                  AND substr(o.order_date,1,7) = (SELECT substr(max(order_date),1,7)
                                                    FROM seller_orders WHERE tenant_id=?)""",
            [tid, tid]).fetchone()
        v = float((dict(row).get("repl") if row else 0) or 0)
        return round(v) if v > 0 else None
    except Exception:
        return None


@router.get("/cash-budget")
def cash_budget_get(request: Request):
    """The seller's inventory cash budget — the input the reorder allocator needs. `suggested` comes
    from real orders; `value` is None until the seller sets one (we never invent their cash position)."""
    tid = require_tenant(request)
    con = db.connect()
    try:
        raw = db.get_setting(con, tid, _CASH_KEY, None)
        suggested = _cash_suggestion(con, tid)
    finally:
        con.close()
    try:
        value = float(raw) if raw not in (None, "") else None
    except (TypeError, ValueError):
        value = None
    return JSONResponse({"ok": True, "value": value, "suggested": suggested,
                         "basis": "replacement cost of goods sold last complete month (units x COGS)"})


@router.post("/cash-budget")
async def cash_budget_set(request: Request):
    tid = require_tenant(request)
    body = await request.json()
    try:
        v = float(body.get("value"))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "error": "A numeric value is required."}, status_code=400)
    if v <= 0:
        return JSONResponse({"ok": False, "error": "Budget must be greater than zero."}, status_code=400)
    con = db.connect()
    try:
        db.set_setting(con, tid, _CASH_KEY, str(int(v)))
        con.commit()
    finally:
        con.close()
    return JSONResponse({"ok": True, "value": v})


@router.get("/reorder-plan")
async def reorder_plan(request: Request, cash: float = None, horizon: int = 30):
    """One funded reorder plan for the whole catalogue, instead of N independent 'reorder X' cards.
    Uses the saved cash budget unless `cash` overrides it. Proxies the LP to the bot; writes nothing."""
    tid = require_tenant(request)
    if cash is None:
        con = db.connect()
        try:
            raw = db.get_setting(con, tid, _CASH_KEY, None)
        finally:
            con.close()
        try:
            cash = float(raw) if raw not in (None, "") else None
        except (TypeError, ValueError):
            cash = None
    if not cash or cash <= 0:
        return JSONResponse({"ok": False, "needs_budget": True,
                             "error": "Set your inventory cash budget to see a funded plan."})

    def _call():
        req = urllib.request.Request(
            f"{_BOT_URL}/v1/reorder-plan",
            data=json.dumps({"cash": float(cash), "horizon": int(horizon)}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())

    try:
        return JSONResponse(await asyncio.to_thread(_call))
    except Exception as e:                       # noqa: BLE001
        return JSONResponse({"ok": False, "error": f"Allocator unavailable ({e})."}, status_code=502)


@router.post("/run-model")
async def run_model(request: Request):
    """Run a shipped model on the selected ASIN(s) in real time (Product Catalog action).
    Proxies each SKU to the bot's LLM-free tool runner; never queues governance."""
    tid = require_tenant(request)
    body = await request.json()
    domain = (body.get("domain") or "").strip().lower()
    objective = (body.get("objective") or "profit")
    skus = body.get("skus") or ([body["sku"]] if body.get("sku") else [])
    skus = [s for s in skus if s][:20]
    if domain == "ads" and not _ads_preview_allowed(tid):
        # held model: refuse rather than half-answer, so nothing unvalidated can reach a seller
        return JSONResponse({"domain": domain, "results": [], "error":
                             "The ads model is held (family #10 fails out-of-sample validation). "
                             "Its internal preview needs the ads_preview flag and a tester account."},
                            status_code=403)
    results = await asyncio.to_thread(lambda: [_run_one(domain, s, objective) for s in skus])
    return JSONResponse({"domain": domain, "results": results, "unvalidated": domain == "ads"})


@router.post("/voice/stt")
async def voice_stt(request: Request):
    """Speech-to-text: proxy the mic audio to the DGX voice service (Whisper)."""
    require_tenant(request)
    audio = await request.body()
    ext = request.headers.get("x-audio-ext", "webm")

    def _call():
        req = urllib.request.Request(
            f"{_VOICE_URL}/stt", data=audio,
            headers={"Content-Type": "application/octet-stream", "x-audio-ext": ext}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    try:
        return JSONResponse(json.loads(await asyncio.to_thread(_call)))
    except Exception as e:
        return JSONResponse({"text": "", "error": f"voice STT unavailable ({e})"}, status_code=502)


@router.post("/voice/tts")
async def voice_tts(request: Request):
    """Text-to-speech: proxy RIA's answer text to the DGX voice service (F5-TTS,
    Meher's cloned voice) and stream back the WAV so the browser can play it."""
    require_tenant(request)
    body = await request.json()
    payload = json.dumps({"text": (body.get("text") or "")[:1200]}).encode()

    def _call():
        req = urllib.request.Request(
            f"{_VOICE_URL}/tts", data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.read()
    try:
        return Response(content=await asyncio.to_thread(_call), media_type="audio/wav")
    except Exception:
        return Response(status_code=502)


@router.get("/signal-intel")
def signal_intel(request: Request):
    """The three signal-graph wins, Postgres-backed so the tab needs no Neo4j:
       - market_signals : Gemma-structured external news/recall/trend  (family #7)
       - rating_risk    : drift-projected rating drops                 (family #11)
       - competitive    : SKUs under live competitor undercut          (family #6)
    Each block soft-fails to [] so the panel renders even before the bot jobs run."""
    tid = require_tenant(request)
    con = db.connect()
    market, rating, competitive, listing = [], [], [], []
    try:
        try:
            for r in con.execute(
                "SELECT event_type, direction, category, severity, impact, title, url, source "
                "FROM ria_market_signals WHERE tenant_id=? "
                "ORDER BY CASE direction WHEN 'adverse' THEN 0 WHEN 'favorable' THEN 1 "
                "ELSE 2 END, confidence DESC", [tid]).fetchall():
                market.append(_clean(dict(r)))
        except Exception:
            pass
        try:
            for r in con.execute(
                "SELECT s.internal_sku, sk.title, s.current, s.projected, s.drop_pts, "
                "s.horizon_days, s.crosses_floor, s.severity FROM ria_rating_risk s "
                "LEFT JOIN seller_skus sk ON sk.tenant_id=s.tenant_id "
                "  AND sk.internal_sku=s.internal_sku "
                "WHERE s.tenant_id=? ORDER BY s.drop_pts DESC", [tid]).fetchall():
                rating.append(_clean(dict(r)))
        except Exception:
            pass
        try:
            for r in con.execute(
                "WITH latest AS ("
                "  SELECT DISTINCT ON (asin, seller) asin, seller, price, is_buybox "
                "  FROM competitor_offers WHERE tenant_id=? "
                "  ORDER BY asin, seller, captured_at DESC) "
                "SELECT s.internal_sku, s.title, s.price AS own_price, "
                "  count(*) FILTER (WHERE l.price < s.price) AS undercutters, "
                "  min(l.price) FILTER (WHERE l.price < s.price) AS lowest_rival, "
                "  bool_or((l.is_buybox <> 0) AND l.price < s.price) AS rival_buybox "
                "FROM seller_skus s JOIN latest l ON l.asin = s.asin "
                "WHERE s.tenant_id=? AND s.internal_sku IS NOT NULL "
                "GROUP BY s.internal_sku, s.title, s.price "
                "HAVING count(*) FILTER (WHERE l.price < s.price) > 0 "
                "ORDER BY undercutters DESC LIMIT 12", [tid, tid]).fetchall():
                d = dict(r)
                own, low = float(d.get("own_price") or 0), float(d.get("lowest_rival") or 0)
                d["gap"] = round(own - low, 2) if low else None
                competitive.append(_clean(d))
        except Exception:
            pass
        # #5 listing content — VLM-extracted attributes from product images (ria_listing_attrs).
        # Actionable angle: keyword_gaps = suggested keywords NOT already in the title (SEO wins),
        # + a photo-quality flag. Ordered worst-photo / most-gaps first.
        try:
            for r in con.execute(
                "SELECT la.internal_sku, sk.title, la.product_type, la.primary_color, "
                "la.material, la.image_quality, la.clean_background, la.suggested_keywords "
                "FROM ria_listing_attrs la LEFT JOIN seller_skus sk "
                "  ON sk.tenant_id=la.tenant_id AND sk.internal_sku=la.internal_sku "
                "WHERE la.tenant_id=? ORDER BY la.image_quality ASC NULLS FIRST", [tid]).fetchall():
                d = dict(r)
                kws = _jsonb(d.get("suggested_keywords")) or []
                title = (d.get("title") or "").lower()
                gaps = [k for k in kws if isinstance(k, str) and k.lower() not in title][:5]
                low_photo = (d.get("image_quality") or 5) < 4 or not d.get("clean_background")
                d["keyword_gaps"] = gaps
                d["suggested_keywords"] = kws
                d["photo_flag"] = bool(low_photo)
                listing.append(_clean(d))
            # surface the actionable ones first (photo flag or has keyword gaps), cap the list
            listing.sort(key=lambda x: (0 if x.get("photo_flag") else 1, -len(x.get("keyword_gaps") or [])))
            listing = listing[:12]
        except Exception:
            pass
        # #12 return-reason aspects (Gemma-4-12B over real return comments -> ria_return_aspects).
        # Per SKU: total tagged comments + the dominant aspect. Actionable: "why this SKU comes back".
        raspect = []
        try:
            for r in con.execute(
                "SELECT ra.internal_sku, sk.title, sum(ra.n)::int total, "
                "  (array_agg(ra.aspect ORDER BY ra.n DESC))[1] AS top_aspect, "
                "  max(ra.n)::int AS top_n "
                "FROM ria_return_aspects ra LEFT JOIN seller_skus sk "
                "  ON sk.tenant_id=ra.tenant_id AND sk.internal_sku=ra.internal_sku "
                "WHERE ra.tenant_id=? GROUP BY ra.internal_sku, sk.title "
                "ORDER BY total DESC LIMIT 10", [tid]).fetchall():
                raspect.append(_clean(dict(r)))
        except Exception:
            pass
        return JSONResponse({"market_signals": market, "rating_risk": rating,
                             "competitive": competitive, "listing": listing,
                             "return_aspects": raspect})
    finally:
        con.close()




def _decide(request: Request, rid: str, status: str, note: str | None):
    uid, tid = current(request)
    if not tid:
        return JSONResponse({"ok": False, "error": "auth required"}, status_code=401)
    who = str(uid) if uid is not None else "seller"  # approved_by/agent_name are TEXT (uid is an int)
    con = db.connect()
    try:
        cur = con.execute(
            "UPDATE ria_recommendations SET status=?, seller_notes=?, updated_at=now(), "
            "approved_at=CASE WHEN ?='approved' THEN now() ELSE approved_at END, "
            "approved_by=CASE WHEN ?='approved' THEN ? ELSE approved_by END "
            "WHERE id=? AND tenant_id=? AND status='pending'",
            [status, note, status, status, who, rid, tid])
        ok = cur.rowcount > 0
        if ok:
            import uuid
            con.execute(
                "INSERT INTO ria_decision_logs (id, tenant_id, recommendation_id, "
                "decision_type, agent_name, decision_data, ts) VALUES (?,?,?,?,?,?,now())",
                [str(uuid.uuid4()), tid, rid,
                 "approve" if status == "approved" else "reject", who,
                 json.dumps({"notes": note, "via": "intelligence-tab"})])
        con.commit()
        return JSONResponse({"ok": ok, "status": status if ok else "not_pending"})
    finally:
        con.close()


@router.post("/recommendation/{rid}/approve")
async def approve(request: Request, rid: str):
    b = await request.json() if await request.body() else {}
    return _decide(request, rid, "approved", (b or {}).get("note"))


@router.post("/recommendation/{rid}/reject")
async def reject(request: Request, rid: str):
    b = await request.json() if await request.body() else {}
    return _decide(request, rid, "rejected", (b or {}).get("note"))
