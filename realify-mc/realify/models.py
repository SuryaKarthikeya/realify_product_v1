"""Stage 2 Phase 1 — the model layer.

Contract every model implements:
    predict(con, tenant_id, asin) -> {
        value, confidence ('low'|'medium'|'high'), top_features [[name,val],...],
        kind, label, unit, ...extras
    }

Principles (deliberate, for safety + trust):
  * Models READ history (metric_history) and INFORM. They never write the deterministic
    facts in seller_skus — L1 detectors still decide what fires and on what numbers.
  * If history is too thin or the fit is poor, confidence='low' and the deterministic
    detector stays authoritative; the model contributes nothing misleading.
  * Pure-Python (no external deps), no network at inference, no training job — fits the
    synth-seeded, single-machine, redeploy model of this prototype.

The one real model here is a velocity/stockout forecaster: it fits a linear trend with a
recent-bias blend over the velocity history and projects days-to-stockout against current
stock. Interpretable inputs surface as top_features.
"""
from . import db, config

MIN_POINTS = 10
CONF_NUM = {"low": 2, "medium": 3, "high": 4}   # maps to the card confidence scale (1..4)

def _linfit(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0, (ys[-1] if ys else 0.0), 0.0
    mx = sum(xs) / n; my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx else 0.0
    intercept = my - slope * mx
    ss_tot = sum((y - my) ** 2 for y in ys) or 1e-9
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = max(0.0, 1 - ss_res / ss_tot)
    return slope, intercept, r2

class StockoutForecaster:
    id = "stockout-forecaster"
    version = "1.0.0"
    label = "Stockout forecast"
    unit = "days"
    covers = {"days-of-cover", "seasonal-cover", "stock-level"}

    def predict(self, con, tenant_id, asin, detector=None):
        vel = db.metric_series(con, tenant_id, asin, "velocity_day")
        stock = db.metric_series(con, tenant_id, asin, "stock_on_hand")
        base = {"kind": self.id, "label": self.label, "unit": self.unit}
        if len(vel) < MIN_POINTS:
            return {**base, "value": None, "confidence": "low", "top_features": [],
                    "note": "insufficient history"}
        ys = [v for _, v in vel]; xs = list(range(len(ys)))
        slope, intercept, r2 = _linfit(xs, ys)
        fit_next = slope * len(ys) + intercept
        recent = sum(ys[-7:]) / min(7, len(ys))
        proj = max(0.01, (max(0.0, fit_next) + recent) / 2)     # blend trend + recent, floor > 0
        cur_stock = stock[-1][1] if stock else None
        value = round(cur_stock / proj, 1) if (cur_stock is not None) else None
        n = len(ys)
        conf = "high" if (n >= 20 and r2 >= 0.45) else ("medium" if n >= 12 else "low")
        return {**base, "value": value, "confidence": conf,
                "projected_velocity": round(proj, 2),
                "top_features": [["recent velocity/day", round(recent, 2)],
                                 ["trend slope/day", round(slope, 4)],
                                 ["history points", n],
                                 ["fit R\u00b2", round(r2, 2)]]}

class MetricTrendForecaster:
    """Projects where a metric is heading (+horizon days) from its own history, via the
    same linear fit. Broadens model coverage to the metric-based detectors. The projected
    value is informational — the deterministic detector still owns the firing decision."""
    id = "metric-trend-forecaster"
    version = "1.0.0"
    label = "Trend forecast"
    unit = ""
    # detector -> (metric, unit, friendly, horizon_days)
    METRICS = {
        "margin-vs-floor":   ("net_margin_pct", "%",   "Margin", 14),
        "tacos":             ("tacos",          "%",   "TACoS", 14),
        "returns-rate":      ("returns_rate",   "%",   "Return rate", 14),
        "velocity":          ("velocity_day",   "/day","Velocity", 14),
        "buy-box-ownership": ("buybox_pct",     "%",   "Buy Box", 14),
        "revenue-share":     ("rev_share_pct",  "%",   "Rev share", 14),
    }
    covers = set(METRICS.keys())

    def predict(self, con, tenant_id, asin, detector=None):
        spec = self.METRICS.get(detector)
        base = {"kind": self.id, "label": self.label, "unit": self.unit}
        if not spec:
            return {**base, "value": None, "confidence": "low", "top_features": [], "note": "no metric for detector"}
        metric, unit, friendly, horizon = spec
        series = db.metric_series(con, tenant_id, asin, metric)
        if len(series) < MIN_POINTS:
            return {**base, "label": f"{friendly} in {horizon}d", "unit": unit,
                    "value": None, "confidence": "low", "top_features": [], "note": "insufficient history"}
        ys = [v for _, v in series]; xs = list(range(len(ys)))
        slope, intercept, r2 = _linfit(xs, ys)
        proj = round(slope * (len(ys) - 1 + horizon) + intercept, 2)
        if metric.endswith("_pct") or unit == "%":
            proj = max(0.0, min(100.0, proj))
        n = len(ys)
        conf = "high" if (n >= 20 and r2 >= 0.45) else ("medium" if n >= 12 else "low")
        return {**base, "label": f"{friendly} in {horizon}d", "unit": unit,
                "value": proj, "confidence": conf,
                "top_features": [["recent avg", round(sum(ys[-7:]) / min(7, len(ys)), 2)],
                                 ["trend slope/day", round(slope, 4)],
                                 ["history points", n],
                                 ["fit R\u00b2", round(r2, 2)]]}

REGISTRY = [StockoutForecaster(), MetricTrendForecaster()]

def disabled_ids(con=None, tenant_id=None):
    if con is None or tenant_id is None:
        return set()
    import json as _j
    try:
        raw = db.get_setting(con, tenant_id, "models_disabled")
        return set(_j.loads(raw)) if raw else set()
    except Exception:
        return set()

def for_detector(detector_id, disabled=None):
    disabled = disabled or set()
    return [m for m in REGISTRY if detector_id in m.covers and m.id not in disabled]

def _degraded(m, note, error=None):
    """A silent, safe prediction: contributes nothing to the card, but is stamped + labelled."""
    d = {"kind": m.id, "model_id": m.id, "version": getattr(m, "version", None),
         "value": None, "confidence": "low", "top_features": [], "note": note}
    if error:
        d["error"] = error
    return d


def _serve(m, con, tenant_id, asin, detector_id, timeout):
    """The model-serving boundary (#005 1e): crash-isolated, version-stamped, degrades to 'low'.

    In-process pure-Python models run in-thread (they share the caller's DB connection and cannot
    hang). The `timeout` is the contract for an out-of-process / remote model — Team 4's
    build-and-deploy path serves a model behind a network call; exceeding `timeout` degrades to
    'low' exactly like a crash, so a slow model is silent, never wrong. Either way the deterministic
    L1 number stands. A model's `version` is stamped onto every prediction and flows into the card's
    provenance.
    """
    try:
        pred = m.predict(con, tenant_id, asin, detector_id)
    except Exception as e:
        return _degraded(m, "error", error=str(e)[:100])
    pred.setdefault("model_id", m.id)
    pred.setdefault("version", getattr(m, "version", None))
    return pred


def predict_for(con, tenant_id, asin, detector_id, timeout=None):
    timeout = config.MODEL_TIMEOUT if timeout is None else timeout
    disabled = disabled_ids(con, tenant_id)
    return [_serve(m, con, tenant_id, asin, detector_id, timeout)
            for m in for_detector(detector_id, disabled)]

def registry_view(con=None, tenant_id=None):
    disabled = disabled_ids(con, tenant_id)
    return [{"id": m.id, "label": m.label, "unit": m.unit, "covers": sorted(m.covers),
             "enabled": m.id not in disabled} for m in REGISTRY]


# ---- COGS estimator (Product Catalog) --------------------------------------------------------
# A deliberately simple, fully explainable v1: estimate a SKU's COGS as a median fraction of its
# price, learned from the seller's OWN SKUs that already have a confirmed COGS — same category
# first, catalog-wide as a low-confidence fallback. It never writes seller_skus; its output lands
# in cogs_suggestions and is advisory (the seller's Save is what sets the real cost). Swap this
# class for a trained model later without touching callers — the contract is suggest_all(rows).

def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


class CogsEstimator:
    id = "cogs_v1"
    label = "Suggested COGS"
    unit = "₹"
    version = "cogs-ratio-1"

    def _anchor_ratios(self, rows):
        by_cat, allr = {}, []
        for r in rows:
            p, c = r.get("price"), r.get("cogs")
            if p and c and p > 0 and c > 0:
                ratio = c / p
                allr.append(ratio)
                by_cat.setdefault((r.get("category") or "").strip().lower(), []).append(ratio)
        return by_cat, allr

    def suggest_all(self, rows):
        """-> list of (internal_sku, value|None, confidence, basis)."""
        by_cat, allr = self._anchor_ratios(rows)
        allr_med = _median(allr)
        out = []
        for r in rows:
            sku = r.get("internal_sku") or r.get("asin")
            p = r.get("price")
            if not p or p <= 0:
                out.append((sku, None, "low", "No price on file yet — can't estimate COGS."))
                continue
            cat = (r.get("category") or "").strip().lower()
            grp = by_cat.get(cat, [])
            if len(grp) >= 3:
                ratio = _median(grp)
                n = len(grp)
                conf = "high" if n >= 8 else "medium"
                scope = r.get("category") or "same-category"
                basis = f"~{round(ratio * 100)}% of price · median of {n} of your {scope} SKUs with confirmed COGS"
            elif allr_med is not None:
                ratio, n, conf = allr_med, len(allr), "low"
                basis = f"~{round(ratio * 100)}% of price · catalog-wide median ({n} SKUs) — too few in this category yet"
            else:
                out.append((sku, None, "low", "Not enough confirmed COGS anywhere yet to estimate."))
                continue
            out.append((sku, round(p * ratio, 2), conf, basis))
        return out

    def predict(self, con, tenant_id, asin, detector_id=None):
        from .repositories.seller_repo import SellerRepository
        rows = SellerRepository(con).all(tenant_id)
        for sku, val, conf, basis in self.suggest_all(rows):
            if sku == asin:
                return {"kind": self.id, "model_id": self.id, "version": self.version,
                        "value": val, "confidence": conf, "top_features": [], "basis": basis,
                        "label": self.label, "unit": self.unit}
        return _degraded(self, "no-sku")


def recompute_cogs(con, tenant_id):
    """Recompute + persist COGS suggestions for every SKU. Called after report ingest and after a
    SKU's cost inputs change, so suggestions stay current with the seller's confirmed data."""
    from .repositories.seller_repo import SellerRepository
    from .repositories.cogs_suggestion_repo import CogsSuggestionRepository
    rows = SellerRepository(con).all(tenant_id)
    CogsSuggestionRepository(con).replace_all(tenant_id, CogsEstimator().suggest_all(rows))
