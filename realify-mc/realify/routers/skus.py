"""SKU data-foundation tab (1b) — the leftmost cockpit.

GET  /api/skus         list every SKU with values, per-field provenance basis, the actual-vs-estimated
                       fee pairs, the free-replacement signal, and a completeness read (what's missing
                       and what each gap unlocks).
POST /api/skus/edit    seller edits a seller-owned field (COGS / margin floor / lifecycle flag) —
                       sticky against re-upload; economics recompute immediately.
POST /api/skus/upload  "Add / replace channel reports" — routes real Amazon reports through the
                       report-aware engine (paid-only ASP, actual fees, no fabrication) into own-data.
"""
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from realify import db
from realify.repositories.seller_repo import SellerRepository
from realify.repositories.provenance_repo import ProvenanceRepository
from realify.repositories.revenue_period_repo import RevenuePeriodRepository
from realify.repositories.cogs_suggestion_repo import CogsSuggestionRepository
from realify.repositories.ingested_report_repo import IngestedReportRepository
from realify.repositories.interpretation_repo import InterpretationRepository, ConfirmationRepository
from realify.ingest import report_ingest, report_writer, report_catalog as cat, marketplace_registry as reg
from realify.domain import economics
from .deps import require_tenant

router = APIRouter()
_log = logging.getLogger("realify.skus")

# field -> what filling it unlocks (drives the completeness UX)
_COMPLETENESS = [
    ("cogs", "margin & profit-after-ads"),
    ("price", "selling price & margin"),
    ("referral_fee", "true fee load"),
    ("fba_fee", "true fee load"),
    ("units_month", "velocity & reorder timing"),
    ("returns_rate", "returns impact"),
    ("buybox_pct", "Buy Box / Featured Offer alerts"),
]
_SELLER_OWNED = {"cogs", "margin_floor", "lifecycle_flag", "title_override", "optimize_for"}


def _catalog_derived(r, missing_title):
    """Per-SKU fields the Product Catalog needs beyond the base row: break-even vs actual ACOS,
    the modeled launch-margin baseline vs settled margin, and a health signal with a reason.
    Everything is per SKU; nothing is averaged. Values that can't be computed come back None so the
    UI shows '—' rather than a fabricated number."""
    P = r.get("price"); C = r.get("cogs")
    RF = r.get("referral_fee"); FB = r.get("fba_fee")
    RC = r.get("return_cost_unit") or 0
    have_costs = bool(P and P > 0 and C is not None and RF is not None and FB is not None)
    est_margin = round((P - C - RF - FB) / P * 100, 1) if have_costs else None  # modeled, pre returns/ads
    be_acos = round((P - C - RF - FB - RC) / P * 100, 1) if have_costs else None
    act_margin = r.get("net_margin_pct")  # settled: after fees, returns, ad spend
    tacos = r.get("tacos")
    act_acos = None
    if tacos is not None:
        act_acos = round(tacos * 100, 1) if tacos < 1.5 else round(tacos, 1)
    margin_gap = round(est_margin - act_margin, 1) if (est_margin is not None and act_margin is not None) else None

    bb = r.get("buybox_pct"); rr = r.get("returns_rate")
    reasons, health = [], "green"
    if (bb is not None and bb < 85) or (rr is not None and rr >= 20):
        health = "red"
        if bb is not None and bb < 85: reasons.append("Buy Box lost")
        if rr is not None and rr >= 20: reasons.append("Returns very high")
    elif (bb is not None and bb < 98) or (rr is not None and rr >= 12) or bb is None or missing_title:
        health = "yellow"
        if bb is not None and bb < 98: reasons.append("Buy Box slipping")
        if rr is not None and rr >= 12: reasons.append("Returns elevated")
        if bb is None: reasons.append("Buy Box unknown")
        if missing_title: reasons.append("Missing title")
    else:
        reasons = ["Listing active", "Buy Box held", "Returns normal"]
    return {"be_acos": be_acos, "act_acos": act_acos, "est_margin": est_margin,
            "act_margin": act_margin, "margin_gap": margin_gap,
            "health": health, "health_reason": " · ".join(reasons)}


def _completeness(row):
    missing = [{"field": f, "unlocks": u} for f, u in _COMPLETENESS if row.get(f) is None]
    filled = len(_COMPLETENESS) - len(missing)
    return {"filled": filled, "total": len(_COMPLETENESS), "missing": missing}


@router.get("/skus")
def list_skus(request: Request):
    tid = require_tenant(request)
    with db.connect() as con:
        rows = SellerRepository(con).all(tid)
        prov = ProvenanceRepository(con).all_for_tenant(tid)
        rev_by_sku = RevenuePeriodRepository(con).all_by_sku(tid)   # {sku: {period_start: revenue}}
        cogs_sugg = CogsSuggestionRepository(con).all(tid)          # {sku: {value, confidence, basis}}
    out = []
    for r in rows:
        sku = r.get("internal_sku") or r.get("asin")
        p = prov.get(sku, {})
        def basis(f):
            return next(iter(p.get(f, {}).keys()), None)
        def win_basis(f):  # value-of-record basis by rank (actual/seller win over reported/estimated)
            bs = list(p.get(f, {}).keys())
            rank = {"actual": 4, "seller": 4, "reported": 2, "estimated": 1}
            return max(bs, key=lambda b: rank.get(b, 0)) if bs else None
        def estimate(f):  # the estimated alternate beside an actual, if present
            e = p.get(f, {}).get("estimated")
            return float(e["value"]) if e and e.get("value") not in (None, "") else None
        margin_certainty = economics.certainty(
            {f: win_basis(f) for f in ("price", "cogs", "referral_fee", "fba_fee")})
        # trailing settled-revenue windows (monthly grain: 30d≈latest month, 60d≈last 2, 90d≈last 3);
        # cumulative. trend = the last up-to-3 monthly points (oldest→newest) for the row sparkline.
        rp = rev_by_sku.get(sku, {})
        series = [rp[p] for p in sorted(rp)][-3:]
        sales_30 = round(series[-1] or 0, 2) if series else None
        sales_60 = round(sum(v or 0 for v in series[-2:]), 2) if series else None
        sales_90 = round(sum(v or 0 for v in series), 2) if series else None
        row_out = {
            "sku": sku, "asin": r.get("asin"), "title": r.get("title"),
            "title_override": r.get("title_override"),
            "sales_30": sales_30, "sales_60": sales_60, "sales_90": sales_90,
            "trend": [round(v or 0, 2) for v in series],
            "price": r.get("price"), "price_basis": basis("price"),
            "cogs": r.get("cogs"), "cogs_basis": basis("cogs"),
            "referral_fee": r.get("referral_fee"), "referral_est": estimate("referral_fee"),
            "fba_fee": r.get("fba_fee"), "fba_est": estimate("fba_fee"),
            "net_margin_pct": r.get("net_margin_pct"), "breakeven_floor": r.get("breakeven_floor"),
            "margin_certainty": margin_certainty,
            "units_month": r.get("units_month"), "returns_rate": r.get("returns_rate"),
            "buybox_pct": r.get("buybox_pct"), "replacement_units": r.get("replacement_units"),
            "mcf_units": r.get("mcf_units"), "provisional_units": r.get("provisional_units"),
            "lifecycle_flag": r.get("lifecycle_flag"), "margin_floor": r.get("margin_floor"),
            "optimize_for": r.get("optimize_for"),
            "provisional": bool(r.get("provisional_units")),
            "completeness": _completeness(r),
        }
        sg = cogs_sugg.get(sku, {})
        row_out["cogs_suggested"] = sg.get("value")
        row_out["cogs_suggested_conf"] = sg.get("confidence")
        row_out["cogs_suggested_basis"] = sg.get("basis")
        row_out.update(_catalog_derived(r, missing_title=not (r.get("title_override") or r.get("title"))))
        out.append(row_out)
    out.sort(key=lambda x: (x["completeness"]["filled"], x.get("units_month") or 0), reverse=True)
    n = len(out)
    summary = {
        "skus": n,
        "avg_completeness": round(sum(s["completeness"]["filled"] for s in out) / max(1, n), 1),
        "missing_cogs": sum(1 for s in out if s["cogs"] is None),
        "fee_pairs": sum(1 for s in out if s["referral_est"] is not None or s["fba_est"] is not None),
        "provisional": sum(1 for s in out if s["provisional"]),
    }
    return JSONResponse({"ok": True, "skus": out, "summary": summary})


@router.post("/skus/edit")
async def edit_sku(request: Request):
    tid = require_tenant(request)
    b = await request.json()
    sku, field, value = b.get("sku"), b.get("field"), b.get("value")
    if field not in _SELLER_OWNED:
        return JSONResponse({"ok": False, "error": f"field '{field}' is not seller-editable"}, status_code=400)
    if field in ("cogs", "margin_floor") and value not in (None, ""):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "error": "numeric value required"}, status_code=400)
    if field in ("lifecycle_flag", "title_override", "optimize_for"):
        value = (str(value).strip() or None) if value is not None else None  # empty text clears the field
    with db.connect() as con:
        seller = SellerRepository(con)
        seller.update_fields_by_sku_or_asin(tid, sku, {field: value})
        ProvenanceRepository(con).set(tid, sku, field, "seller", "seller-entered", value, edited=1)
        row = report_writer.recompute_one(con, tid, sku)  # margin/break-even follow the new value
        if field == "cogs":
            from realify import models
            models.recompute_cogs(con, tid)  # a confirmed COGS changes the anchor set for suggestions
        con.commit()
    return JSONResponse({"ok": True, "sku": sku, "field": field, "value": value,
                         "net_margin_pct": (row or {}).get("net_margin_pct"),
                         "breakeven_floor": (row or {}).get("breakeven_floor")})


@router.post("/skus/export")
async def export_skus(request: Request):
    """Download a CSV of the selected SKU rows (all rows if none specified). Powers the Product
    Catalog checkbox selection -> 'Download CSV'."""
    import csv
    import io
    from starlette.responses import Response
    tid = require_tenant(request)
    try:
        body = await request.json()
    except Exception:
        body = {}
    wanted = set(body.get("skus") or [])
    with db.connect() as con:
        rows = SellerRepository(con).all(tid)
        rev_by_sku = RevenuePeriodRepository(con).all_by_sku(tid)
        cogs_sugg = CogsSuggestionRepository(con).all(tid)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["SKU", "Title", "Price", "COGS", "Suggested COGS", "Margin %", "Est Margin %",
                "Units/Mo", "Returns %", "Buy Box %", "Break-even ACOS %", "Actual ACOS %",
                "Sales 30D", "Sales 60D", "Sales 90D", "Lifecycle", "Optimize For", "Health"])
    for r in rows:
        sku = r.get("internal_sku") or r.get("asin")
        if wanted and sku not in wanted:
            continue
        rp = rev_by_sku.get(sku, {})
        series = [rp[p] for p in sorted(rp)][-3:]
        s30 = round(series[-1] or 0, 2) if series else ""
        s60 = round(sum(v or 0 for v in series[-2:]), 2) if series else ""
        s90 = round(sum(v or 0 for v in series), 2) if series else ""
        d = _catalog_derived(r, missing_title=not (r.get("title_override") or r.get("title")))
        w.writerow([sku, r.get("title_override") or r.get("title") or "", r.get("price"), r.get("cogs"),
                    cogs_sugg.get(sku, {}).get("value"), r.get("net_margin_pct"), d["est_margin"],
                    r.get("units_month"), r.get("returns_rate"), r.get("buybox_pct"),
                    d["be_acos"], d["act_acos"], s30, s60, s90,
                    r.get("lifecycle_flag"), r.get("optimize_for"), d["health"]])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="realify-catalog.csv"'})


@router.post("/skus/upload")
async def upload_reports(request: Request):
    """Multi-file Amazon report upload -> report-aware engine -> own-data + provenance.
    Also detects channel legs: known marketplaces get a default rule (overridable); unknown ones
    are filed as pending confirmations and their units held provisional until the seller confirms."""
    tid = require_tenant(request)
    form = await request.form()
    tables, unreadable = [], []
    for _k, v in form.multi_items():
        if hasattr(v, "filename") and v.filename:
            try:
                df = report_ingest.load_table(v.filename, await v.read())
            except Exception:  # noqa: BLE001 — a bad file shouldn't sink the batch
                df = None
            (tables.append((v.filename, df)) if df is not None else unreadable.append(v.filename))
    tables = [(n, df) for n, df in tables if df is not None]
    if not tables:
        return JSONResponse({"ok": False, "error": "No readable report files received.",
                             "files": [{"name": n, "status": "ignored",
                                        "reason": "Couldn't read the file — not a valid CSV/XLSX, or it was empty."}
                                       for n in unreadable]}, status_code=400)

    with db.connect() as con:
        interp = InterpretationRepository(con)
        conf = ConfirmationRepository(con)
        dedup = IngestedReportRepository(con)
        from realify.ingest import conflicts as cflt
        res_map = cflt.parse_resolutions(form.get("resolutions"))
        # fool-proof duplicate guard: 100%-identical re-uploads are skipped (repo.partition).
        fresh, duplicates = dedup.partition(tid, tables)
        fresh_tables = [(n, df) for n, df, _h in fresh]
        # A resolutions map means the user is RE-RESOLVING a conflict on files they already uploaded
        # (the "Apply changes & re-import" path): re-ingest those already-fingerprinted files so the
        # choice actually applies — the duplicate guard would otherwise skip them and silently drop the
        # resolution. Normal uploads still ingest only the fresh (non-duplicate) files.
        use_tables = tables if res_map else fresh_tables
        if res_map:
            duplicates = []                       # re-imported-on-purpose files aren't "duplicates" to report
        conflicts = cflt.detect_conflicts(use_tables, duplicates)   # structured, for inline resolution

        channels, overlaps, result, summary = [], [], None, {}
        if use_tables:
            # classify channels; record defaults (overridable) and raise unknowns as confirmations
            channels = report_ingest.detect_channels(use_tables, interp.resolver(tid))
            confirmed = interp.channel_map(tid)
            for ch in channels:
                mp = str(ch["marketplace"]).strip().lower()
                if ch["treatment"] == reg.UNKNOWN:
                    conf.upsert(tid, f"channel_map:{mp}", "channel_map",
                                f"Unrecognized sales channel: {ch['marketplace']}",
                                f"{ch['units']:.0f} units posted here. We're holding them out of Amazon "
                                f"metrics until you confirm what this channel is.",
                                suggested=reg.OFF_AMAZON_MCF, impact_units=ch["units"])
                elif mp not in confirmed:
                    interp.set_rule(tid, "channel_map", mp, ch["treatment"], confidence="default")
            # inline conflict resolution: apply the user's choice at ingest (else take-latest, today's
            # default), and persist the accurate "resolve later on Channels" record.
            overlaps = report_ingest.detect_overlaps(use_tables)
            cflt.record_overlap_confirmations(conf, tid, use_tables)
            result = report_ingest.ingest_tables(use_tables, interp.resolver(tid), resolutions=res_map)
            summary = report_writer.write_ingest(con, tid, result)
            # Parity with the onboarding upload path (/api/onboard/reports): extract the campaign->ASIN ad
            # graph (ad_entity_perf) so re-imports through this endpoint also get campaign-level ad
            # recommendations — write_ingest alone only populates SKU-level ad_performance. Additive +
            # take-latest; never blocks the core ingest (safe wrapper logs + returns None on failure).
            from realify.ingest.ad_extract import safe_ingest_ad_graph
            summary["ads"] = safe_ingest_ad_graph(con, tid, use_tables)
            dedup.record_fresh(tid, fresh, result.report_types if result else {})
        con.commit()
    if use_tables:
        from realify.pipeline.materialize import run_pipeline   # rebuild Intelligence cards on the new data
        try:
            run_pipeline(tid)
        except Exception:
            _log.exception("run_pipeline failed after in-app upload tid=%s", tid)

    report_types = result.report_types if result else {}
    summary["detected_reports"] = {n: t for n, t in report_types.items()}
    # per-file outcome for the in-app upload-status modal: used (+what for) / ignored (+why) / duplicate
    files_report = []
    for name, rt in report_types.items():
        if rt == report_ingest.UNKNOWN:
            files_report.append({"name": name, "status": "ignored", "report_type": rt,
                                 "reason": "Unrecognized report — its columns didn't match a known Amazon report."})
        else:
            files_report.append({"name": name, "status": "used", "report_type": rt,
                                 "label": cat.LABELS.get(rt, rt), "used_for": cat.UNLOCKS.get(rt, "own-data")})
    for name, src_name, when in duplicates:
        on = f" on {when[:10]}" if when else " earlier in this upload"
        who = f" ({src_name})" if src_name and src_name != name else ""
        files_report.append({"name": name, "status": "duplicate",
                             "reason": f"Duplicate — identical to a report you already uploaded{on}{who}. Skipped."})
    for name in unreadable:
        files_report.append({"name": name, "status": "ignored",
                             "reason": "Couldn't read the file — not a valid CSV/XLSX, or it was empty."})
    summary["files"] = files_report
    summary["channels"] = channels
    summary["overlaps"] = overlaps
    summary["conflicts"] = conflicts
    summary["pending_confirmations"] = len([c for c in channels if c["treatment"] == reg.UNKNOWN]) + len(overlaps)
    summary.setdefault("skus_written", 0)
    return JSONResponse({"ok": True, **summary})


@router.get("/interpretation")
def get_interpretation(request: Request):
    """Channel registry for this account: confirmed/default marketplace mappings + pending
    confirmations (with impact), for the Confirmations registry UI."""
    tid = require_tenant(request)
    with db.connect() as con:
        interp = InterpretationRepository(con)
        rows = con.execute(
            "SELECT key, value, confidence FROM account_interpretation "
            "WHERE tenant_id=? AND category='channel_map' ORDER BY key", (tid,)).fetchall()
        pending = ConfirmationRepository(con).pending(tid)
    mappings = [{"marketplace": r["key"], "treatment": r["value"], "confidence": r["confidence"],
                 "label": reg.default_treatment(r["key"])[1]} for r in rows]
    return JSONResponse({"ok": True, "mappings": mappings, "pending": pending,
                         "treatments": [reg.AMAZON_DIRECT, reg.OFF_AMAZON_MCF, reg.EXCLUDE]})


@router.post("/interpretation/confirm")
async def confirm_interpretation(request: Request):
    """Seller confirms/overrides a channel treatment. Applies on the next report upload."""
    tid = require_tenant(request)
    b = await request.json()
    mp = str(b.get("marketplace", "")).strip().lower()
    treatment = b.get("treatment")
    if treatment not in (reg.AMAZON_DIRECT, reg.OFF_AMAZON_MCF, reg.EXCLUDE):
        return JSONResponse({"ok": False, "error": "unknown treatment"}, status_code=400)
    with db.connect() as con:
        InterpretationRepository(con).set_rule(tid, "channel_map", mp, treatment, confidence="seller")
        ConfirmationRepository(con).resolve(tid, f"channel_map:{mp}", "confirmed")
        con.commit()
    return JSONResponse({"ok": True, "marketplace": mp, "treatment": treatment,
                         "note": "Applied. Re-upload the transaction report to reclassify existing units."})


@router.post("/interpretation/dismiss")
async def dismiss_confirmation(request: Request):
    """Acknowledge/dismiss a non-channel confirmation (e.g. a report-overlap warning)."""
    tid = require_tenant(request)
    b = await request.json()
    ckey = b.get("ckey")
    if not ckey:
        return JSONResponse({"ok": False, "error": "ckey required"}, status_code=400)
    with db.connect() as con:
        ConfirmationRepository(con).resolve(tid, ckey, "dismissed")
        con.commit()
    return JSONResponse({"ok": True, "ckey": ckey})
