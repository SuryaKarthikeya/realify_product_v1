"""Attributable-ads delivery API (spec A7) — the instruction-mode surface. Kept OUT of routers/cmaa.py
(at the 400-line cap) as its own router.

  GET /api/ads/coverage         — the honest confidence banner: coverage_pct, unmapped_spend, fidelity,
                                   and the AD_GRANULARITY_INSUFFICIENT flag.
  GET /api/ads/recommendations  — per-SKU prescriptive recommendations. Reuses the CMAA tab's
                                   build_row_card (the single source of a SKU's break-even + CMAA) so the
                                   numbers match the feed exactly, then layers the campaign->target
                                   diagnosis + the shared Fix-Ads payload on top.

No write/execute path exists here — REALIFY_ACTIONABLE actions ship as instruction + deep link, and
ADVISORY_ONLY as how-to steps. One-click execution is Part B, gated on write-API access.
"""
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from realify import db, country
from realify.repositories.seller_repo import SellerRepository
from realify.repositories.provenance_repo import ProvenanceRepository
from realify.repositories.ad_performance_repo import AdPerformanceRepository
from realify.repositories.revenue_period_repo import RevenuePeriodRepository
from realify.repositories.action_repo import ActionRepository
from realify.repositories.ad_entity_repo import (
    AdEntityPerfRepository, AdSearchTermRepository, AdIngestSummaryRepository)
from realify.domain import ad_diagnosis, ad_recommend, ad_resolution, ad_simulate
from realify.routers.cmaa import build_row_card
from .deps import require_tenant

router = APIRouter()
_log = logging.getLogger("realify.ads")


def _build_recs(con, tid):
    """Per-SKU Fix-Ads prescriptions. Reuses build_row_card (single source of break-even + CMAA) then
    layers the campaign->target diagnosis. Raises on a genuine query failure — the caller turns that into
    QUERY_ERROR (never a silent fallback)."""
    rows = SellerRepository(con).all(tid)
    prov = ProvenanceRepository(con).all_for_tenant(tid)
    ad = AdPerformanceRepository(con).totals(tid)
    ad_by_period = AdPerformanceRepository(con).all_by_sku(tid)
    rev_by_period = RevenuePeriodRepository(con).all_by_sku(tid)
    units_by_period = RevenuePeriodRepository(con).units_by_sku(tid)
    acted = set(ActionRepository(con).acted_cmaa_skus(tid))
    summary = AdIngestSummaryRepository(con).get(tid) or {}
    ep = AdEntityPerfRepository(con)
    terms_grouped = AdSearchTermRepository(con).grouped(tid)
    sym = country.tenant_profile(tid).get("symbol", "₹")
    fidelity, coverage = summary.get("fidelity"), summary.get("coverage_pct")
    recs = []
    for r in rows:
        card = build_row_card(r, sym, ad, ad_by_period, rev_by_period, units_by_period, prov, acted)
        if not card or not card.get("judged"):
            continue
        sku = card["sku"]
        slices = ep.campaign_slices_for_sku(tid, sku)
        if not slices:
            continue
        # PER-SKU fidelity (§4): keyword-level only if THIS SKU's campaigns/ad-groups carry search-term
        # data; otherwise campaign-level — the row is labeled "no search-term data", never silently dropped.
        sku_pairs = {(s["campaign"], s["ad_group"]) for s in slices}
        sku_fidelity = "KEYWORD" if any(p in terms_grouped for p in sku_pairs) else "CAMPAIGN_SKU"
        be = card.get("breakeven_acos")
        be = (be / 100.0) if be is not None else None    # card is % ; diagnosis works in fractions
        cmaa_now = card.get("cmaa")
        dg = ad_diagnosis.diagnose(sku, be, slices, terms_grouped, sku_fidelity)
        losing = cmaa_now is not None and cmaa_now < 0
        if not (losing or dg["offending_campaigns"] or (cmaa_now and cmaa_now > 0)):
            continue
        rec = ad_recommend.build(
            sku, {"cmaa_now": cmaa_now, "monthly_loss": (-cmaa_now if losing else 0.0),
                  "title": card.get("title"), "sym": sym},
            dg, sku_fidelity, coverage)
        if rec["actions"]:
            recs.append(rec)
    recs.sort(key=lambda x: -(x.get("est_recovery_monthly") or 0.0))
    return recs


def _resolve(con, tid):
    """Compute the AdResolution + the recs. entity_rows/mapped_rows are read DIRECTLY from the table
    (independent of the recommendation pipeline). Recs are built inside a try — a caught exception is
    QUERY_ERROR, never a fallback. Every decision is logged so any SKU-level view is diagnosable.
    (R20: demo/tester brands get their campaign ad-graph at provisioning — lens_synth.finalize_world for
    agency demo brands, the scheduler synth for testers — so no read-time modeling here; real customers
    with SKU-only ads correctly stay NO_ENTITY_DATA and see the upload CTA.)"""
    counts = AdEntityPerfRepository(con).counts(tid)          # independent tiebreaker, read first
    summary = AdIngestSummaryRepository(con).get(tid) or {}
    coverage = summary.get("coverage_pct")
    if coverage is None:
        coverage = AdEntityPerfRepository(con).coverage(tid).get("coverage_pct")
    recs, error = [], False
    try:
        recs = _build_recs(con, tid)
    except Exception as e:                                    # never fall back inside a catch
        error = True
        _log.exception("ads recs build failed tid=%s: %s", tid, e)
    res = ad_resolution.resolve(counts["entity_rows"], counts["mapped_rows"], coverage,
                                len(recs), summary_fidelity=summary.get("fidelity"), error=error)
    _log.info("ads_resolution tid=%s reason=%s fidelity=%s entity_rows=%s mapped_rows=%s recs=%s fell_back=%s",
              tid, res["reason"], res["fidelity"], res["entity_rows"], res["mapped_rows"],
              res["recommendations"], res["fell_back"])
    return res, recs


@router.get("/ads/coverage")
def ads_coverage(request: Request):
    tid = require_tenant(request)
    with db.connect() as con:
        res, _recs = _resolve(con, tid)
        summary = AdIngestSummaryRepository(con).get(tid) or {}
    return JSONResponse({"ok": True, **res, "unmapped_spend": summary.get("unmapped_spend"),
                         "granularity_flag": summary.get("granularity_flag")})


@router.get("/ads/recommendations")
def ads_recommendations(request: Request):
    tid = require_tenant(request)
    with db.connect() as con:
        res, recs = _resolve(con, tid)
    return JSONResponse({"ok": True, **res, "count": len(recs), "recommendations": recs})


@router.get("/ads/simulate")
def ads_simulate(request: Request, sku: str, bid: float = 30.0, target_acos: float = None):
    """Interactive re-simulation (spec §5): re-invoke the project() seam for one SKU with the customer's
    edited params (bid = cut %, target_acos = optional % cap) and return fresh 30/60/90 + probability +
    tripwire. GET-only compute — NOT a write path (Realify has no live Amazon write). `bid`/`target_acos`
    are percents from the modal control; converted to fractions for the seam."""
    tid = require_tenant(request)
    with db.connect() as con:
        recs = _build_recs(con, tid)
    rec = next((r for r in recs if r["sku"] == sku), None)
    if not rec:
        return JSONResponse({"ok": False, "error": "No recommendation for that SKU."}, status_code=404)
    tac = (target_acos / 100.0) if target_acos else None
    sim = ad_simulate.project(rec.get("est_recovery_monthly"), (rec.get("confidence") or {}).get("coverage_pct"),
                              rec.get("fidelity"), bid_change_pct=(bid or 30.0) / 100.0, target_acos=tac)
    return JSONResponse({"ok": True, "sku": sku, "simulate": sim})
