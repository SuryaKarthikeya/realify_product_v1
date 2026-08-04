"""Shared primitives for every SIMULATE model (Profit & Ads buckets + Intelligence-card detectors).

Owns the pieces every model reuses so there is ONE spine, not a parallel mechanism:
  • formatting (money / pct / units) — pre-formatted strings the client renders verbatim (Fix-1 rule);
  • the linear ramp curve + the explain-cell / projection-row builders (explain.part shape);
  • assumption plumbing — sourced defaults, presets, and server-side validate+clamp to declared [min,max];
  • the confidence BAND contract — re-derived around the current point so expected == the point estimate;
  • the degrade classification (sim_quality / degraded_reason) rendered as a caution banner, never an error.

L1 owns every number AND the quality classification + reason string; L2 phrases; the client renders.
"""
from . import explain, cmaa

HORIZONS = [30, 60, 90]
CHECKPOINTS = [7, 15, 30, 60]
PROV = ["projection over your L1 figures"]
BADGE = "L1 · projection · directional"
PRESETS = ("conservative", "expected", "optimistic")
DISCLAIMER = ("Scenario projection — directional, not a guarantee. Every number below is a current "
              "value × a stated assumption; effects ramp in, so 30-day ≠ full effect.")


# ---- formatting: None-safe, pre-formatted strings (client renders verbatim, never Number()-coerces)
def money(x):
    return None if x is None else f"₹{cmaa._inr_group(x)}"


def pctf(x):
    return None if x is None else f"{x:.1f}%"


def units(x):
    return None if x is None else f"{int(round(x)):,} units"


def days(x):
    return None if x is None else f"{int(round(x)):,} days"


def reached(day, ramp_days):
    return min(day / float(ramp_days or 60), 1.0)          # linear ramp to steady state


def contrib_unit(row):
    """Per-unit gross contribution ₹ = price × net-margin% — the tenant's own L1 economics. None if
    price or margin isn't on file (→ the model degrades honestly rather than fabricating)."""
    p, nm = row.get("price"), row.get("net_margin_pct")
    if p is None or nm is None:
        return None
    return round(p * nm / 100.0, 2)


# ---- explain: one projected number = one explain.part, result is the PRE-FORMATTED string
def cell(label, formula, inputs, result_str, note=None, prov=None, basis="ramped to steady state"):
    return explain.part(label, formula, inputs, result_str, provenance=list(prov or PROV),
                        timeframe_basis=basis, note=note)


def row(label, unit, now_str, steady_delta, base, fmt, ramp_days, formula, inputs_at):
    """One projection row across Now / Do-nothing D90 / Day 30·60·90. `steady_delta` is the day-∞
    change from `base`; each horizon applies the ramp fraction. `inputs_at(day, reached, value)` returns
    the input list for that cell's explain."""
    cells = []
    for h in HORIZONS:
        rf = reached(h, ramp_days)
        val = base + steady_delta * rf
        cells.append({"horizon": h, "reached": round(rf, 2),
                      "part": cell(f"{label} · day {h}", formula, inputs_at(h, rf, val), fmt(val),
                                   note=f"{int(rf*100)}% of the steady-state effect has landed by day {h}.")})
    return {"metric": label, "unit": unit, "now": now_str, "do_nothing": now_str, "cells": cells}


# ---- assumptions: spec entries are (name, default, min, max, unit, description, source, presets(c/e/o))
def defaults(spec):
    return {a[0]: a[1] for a in spec}


def assumption_meta(spec, asm):
    out = []
    for name, dflt, lo, hi, unit, desc, src, _pre in spec:
        out.append({"name": name, "value": asm.get(name, dflt), "default": dflt, "min": lo, "max": hi,
                    "unit": unit, "description": desc, "source": src})
    return out


def presets(spec):
    p = {k: {} for k in PRESETS}
    for name, _d, _lo, _hi, _u, _de, _s, pre in spec:
        for i, k in enumerate(PRESETS):
            p[k][name] = pre[i]
    return p


def validate_clamp(spec, assumptions):
    """Coerce client assumptions to float, drop malformed/NaN (→ keep the sourced default, never crash),
    and clamp to the declared [min,max] so an edited value can't blow past a ceiling. The only place
    client input touches a projection."""
    asm = defaults(spec)
    bounds = {a[0]: (a[2], a[3]) for a in spec}
    for k, v in (assumptions or {}).items():
        if k not in asm:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if fv != fv:                                       # NaN
            continue
        lo, hi = bounds[k]
        asm[k] = min(max(fv, lo), hi)
    return asm


def band(fn, cur, lo, hi, half, decreasing=False, fmt=None):
    """Confidence band re-derived AROUND the current point: expected == fn(cur) exactly, and the point
    always falls within [conservative, optimistic]. Vary the key assumption ±half (clamped to [lo,hi]);
    set decreasing=True when a LARGER key means a SMALLER result (so the +half side is the conservative
    edge). Returns {conservative, expected, optimistic} as fmt-strings."""
    fmt = fmt or money
    pt = fn(cur)
    down = fn(max(cur - half, lo))                         # key decreased
    up = fn(min(cur + half, hi))                           # key increased
    cons, opt = (up, down) if decreasing else (down, up)
    return {"conservative": fmt(cons), "expected": fmt(pt), "optimistic": fmt(opt)}


def monitor_line(day, metric, expected_str, tripwire, explain_part):
    return {"day": day, "metric": metric, "expected": expected_str, "tripwire": tripwire,
            "explain": explain_part}


def src_line(ctx, noun):
    """Source note for a target defaulted to the tenant's own detector threshold — labelled as theirs
    and flagged when they've customized it away from the shipped default."""
    return "your %s from detector settings%s" % (noun, " (customized)" if ctx.get("threshold_customized") else "")


# ---- degrade classification + final Simulation-dict assembly -------------------------------------
def base_dict(ident, quality=("useful", None)):
    """Shared header fields for a Simulation. `ident` supplies sku/asin/title/rec_headline/bucket."""
    sq, reason = quality
    return {"sku": ident.get("sku"), "asin": ident.get("asin"), "title": ident.get("title"),
            "bucket": ident.get("bucket"), "rec_headline": ident.get("rec_headline", ""),
            "badge": BADGE, "disclaimer": DISCLAIMER, "horizons": HORIZONS,
            "sim_quality": sq, "degraded_reason": reason}


def finalize(base, model, asm_spec, asm, active=None):
    """Assemble the full Simulation from a model result. `model` carries intervention/headline/projection/
    risks/monitoring (or {"missing": ...} for honest-empty). Attaches assumptions + presets so the modal
    can render + re-simulate. sim_quality/degraded_reason already live on `base`."""
    if "missing" in model:
        return {**base, "can_simulate": False, "missing": model["missing"],
                "assumptions": assumption_meta(asm_spec, asm), "presets": presets(asm_spec)}
    out = {**base, "can_simulate": True, "assumptions": assumption_meta(asm_spec, asm),
           "presets": presets(asm_spec), "active": active,
           "intervention": model["intervention"], "headline": model["headline"],
           "projection": model["projection"], "risks": model["risks"], "monitoring": model["monitoring"]}
    if model.get("disclaimer_only"):                       # C2: monitoring-plan-only, no fabricated projection
        out["disclaimer_only"] = True
    return out
