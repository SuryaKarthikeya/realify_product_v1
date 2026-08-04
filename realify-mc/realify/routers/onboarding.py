"""Onboarding, data ingest & wipe — split from run.py in #005 1a/1f. Handlers moved verbatim; behavior unchanged."""
import os, json
from fastapi import APIRouter, Request, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, PlainTextResponse
from realify import db, config, auth, scheduler, api, statuscheck, opsdoc, analytics
from realify.repositories.card_repo import CardRepository
from realify.repositories.seller_repo import SellerRepository
from realify.repositories.pull_repo import PullLogRepository
from realify.repositories.metrics_repo import MetricsRepository
from realify.repositories.tenant_repo import TenantRepository
from realify.repositories.user_repo import UserRepository
from realify.repositories.channel_repo import ChannelRepository
from realify.repositories.analytics_repo import AnalyticsRepository, SystemRepository
from .deps import current, require_tenant, require_admin, _admin_key_ok
from .helpers import page, _track, _log_import, _is_customer, _is_seller, BASE_DIR as HERE

router = APIRouter()


@router.post("/api/onboard")
async def onboard(request: Request):
    tid = require_tenant(request)
    con = db.connect(); _at = db.get_account_type(con, tid); con.close()
    if _at == "customer":
        return JSONResponse({"ok": False, "error": "Customer accounts onboard by uploading real reports, not synthetic data."}, status_code=403)
    b = await request.json()
    mode = b.get("mode","synthetic")
    # persist the chosen marketplace country (IN default) for this tenant
    from realify import country as country_mod
    ctry = country_mod.normalize(b.get("country"))
    # Backstop: the bundled demo catalog (Autofy) is India-only, so the sample source
    # is always IN regardless of what the client sent. Upload may be any market.
    if mode == "synthetic" and b.get("source","sample") == "sample" and ctry != "IN":
        ctry = "IN"
    from realify.ingest.synth_ad_graph import AD_SCENARIOS   # tester ad-graph scenario (rules-as-data)
    scenario = b.get("scenario") if b.get("scenario") in AD_SCENARIOS else "ads_full"
    con = db.connect(); db.set_setting(con, tid, "country", ctry); db.set_setting(con, tid, "ad_scenario", scenario); con.close()
    from realify.ingest.synthetic import SyntheticSource
    if mode == "synthetic":
        source = b.get("source","sample")          # 'sample' | 'upload'
        seed_full = None
        if source == "upload":
            rows = b.get("seed") or []              # minimal rows parsed client-side
            from realify.ingest.seed import expand_minimal_seed
            seed_full = expand_minimal_seed(rows, prof=country_mod.profile(ctry))
            if not seed_full:
                return JSONResponse({"ok": False, "error": "No valid rows found. Each row needs a SKU, COGS (>0), and category."}, status_code=400)
        # kick off provisioning in the BACKGROUND; the browser polls /api/onboard/status
        scheduler.start_provision(tid, SyntheticSource(seed_skus=seed_full))
        return JSONResponse({"ok": True, "started": True})
    return JSONResponse({"ok": False, "error": "Unknown mode. Use the file upload endpoint for real store data."}, status_code=400)

@router.post("/api/onboard/upload")
async def onboard_upload(request: Request):
    """Multi-store catalog upload (CSV/XLSX), server-side & tolerant.
    Doubles as 'delete all data & reload': wipes the tenant, parses every file,
    expands the minimal seed into full economics, then (re)provisions."""
    tid = require_tenant(request)
    from realify import country as country_mod
    from realify.ingest.synthetic import SyntheticSource
    from realify.ingest.seed import expand_minimal_seed
    from realify.ingest.upload_parse import parse_many
    form = await request.form()
    ctry = country_mod.normalize(form.get("country"))
    files = []
    for _key, val in form.multi_items():
        if hasattr(val, "filename") and getattr(val, "filename", None):
            data = await val.read()
            ch = form.get("channel:" + val.filename) or None
            files.append((val.filename, data, ch))
    if not files:
        return JSONResponse({"ok": False, "error": "No files received."}, status_code=400)
    rows, report = parse_many(files)
    seed_full = expand_minimal_seed(rows, prof=country_mod.profile(ctry))
    if not seed_full:
        return JSONResponse({"ok": False, "error": "No valid rows found in the uploaded file(s).",
                             "report": report}, status_code=400)
    con = db.connect(); db.set_setting(con, tid, "country", ctry)
    db.wipe_tenant_data(con, tid); con.close()
    scheduler.start_provision(tid, SyntheticSource(seed_skus=seed_full))
    return JSONResponse({"ok": True, "started": True, "skus": len(seed_full), "report": report})


# --- organization members + invites -----------------------------------

@router.get("/api/cogs/template")
def cogs_template(request: Request):
    tid = require_tenant(request)
    from realify import cogs, country as country_mod
    con = db.connect(); ctry = db.get_setting(con, tid, "country") or "IN"; con.close()
    cur = country_mod.profile(ctry).get("currency", "INR")
    return PlainTextResponse(cogs.template_csv(cur), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=realify_cogs_template.csv"})

@router.post("/api/cogs/upload")
async def cogs_upload(request: Request):
    """Add/replace COGS for a customer at any time (onboarding or later from Account).
    Validates against the catalog, applies valid rows, persists, logs rejects, re-runs
    the pipeline so margins refresh. Partial application is allowed."""
    tid = require_tenant(request)
    if not _is_seller(tid):
        return JSONResponse({"ok": False, "error": "COGS upload is for seller accounts."}, status_code=403)
    from realify import cogs, country as country_mod
    from realify.pipeline.materialize import run_pipeline
    form = await request.form()
    f = None
    for _k, v in form.multi_items():
        if hasattr(v, "filename") and getattr(v, "filename", None):
            f = (v.filename, await v.read()); break
    if not f:
        return JSONResponse({"ok": False, "error": "No COGS file received."}, status_code=400)
    con = db.connect()
    try:
        ctry = db.get_setting(con, tid, "country") or "IN"
        prof = country_mod.profile(ctry)
        rows, err = cogs.parse(*f)
        if err:
            return JSONResponse({"ok": False, "error": err}, status_code=400)
        valid, rejects = cogs.validate(rows, cogs.known_skus(con, tid), prof.get("currency", "INR"))
        applied = cogs.apply(con, tid, valid, prof)
        _log_import(con, tid, "cogs", f[0], applied=applied, rejects=rejects)
    finally:
        con.close()
    run_pipeline(tid)
    return JSONResponse({"ok": True, "applied": applied, "rejected": len(rejects), "rejects": rejects[:50]})

# --- customer onboarding: real reports, NO synthesis -------------------

@router.post("/api/onboard/customer")
async def onboard_customer(request: Request):
    """CUSTOMER provisioning. Files: one COGS template (form field name 'cogs') plus one
    or more channel reports (any field name), each tagged 'channel:<filename>' and
    optionally 'report:<filename>' (the declared report type). Establishes the SKU spine
    from the catalog/listings file, applies validated COGS, layers every other report by
    kind, and provisions WITHOUT synthesizing anything. Floor: catalog + >=1 valid COGS."""
    tid = require_tenant(request)
    if not _is_customer(tid):
        return JSONResponse({"ok": False, "error": "This endpoint is for customer accounts."}, status_code=403)
    from realify import cogs, country as country_mod
    from realify.ingest import report_parse, seed as seed_mod
    from realify.ingest.upload_parse import read_table
    form = await request.form()
    ctry = country_mod.normalize(form.get("country"))
    prof = country_mod.profile(ctry)
    cogs_file = None
    reports = []   # (filename, data, channel, declared_report)
    for key, v in form.multi_items():
        if not (hasattr(v, "filename") and getattr(v, "filename", None)):
            continue
        data = await v.read()
        if key == "cogs":
            cogs_file = (v.filename, data)
        else:
            ch = form.get("channel:" + v.filename) or "amazon"
            rep = form.get("report:" + v.filename) or v.filename
            reports.append((v.filename, data, ch, rep))
    if not reports:
        return JSONResponse({"ok": False, "error": "Upload at least a catalog/listings export to establish your products."}, status_code=400)

    # 1) establish the SKU spine from the catalog/listings file(s)
    catalog_rows = []
    for fn, data, ch, rep in reports:
        if report_parse.classify(rep) == "catalog":
            headers, body = read_table(fn, data, report_parse.A)
            mrows, _ = report_parse._matrix_rows(headers, body)
            for r in mrows:
                catalog_rows.append({"asin": r["sku"], "price": r.get("price"),
                                     "title": r.get("title"), "category": r.get("category")})
    if not catalog_rows:
        return JSONResponse({"ok": False, "error": "No catalog/listings file detected. One report must be a product catalog or listings export."}, status_code=400)

    con = db.connect(); db.set_setting(con, tid, "country", ctry); db.wipe_tenant_data(con, tid); con.close()
    from realify.seller import load_seller_data
    n_skus = load_seller_data(tid, skus=seed_mod.catalog_only_seed(catalog_rows, prof))

    con = db.connect()
    ingested = []
    try:
        # 2) COGS — required floor; partial allowed
        cogs_applied, cogs_rejects = 0, []
        if cogs_file:
            crows, cerr = cogs.parse(*cogs_file)
            if cerr:
                con.close()
                return JSONResponse({"ok": False, "error": "COGS file: " + cerr}, status_code=400)
            valid, cogs_rejects = cogs.validate(crows, cogs.known_skus(con, tid), prof.get("currency", "INR"))
            cogs_applied = cogs.apply(con, tid, valid, prof)
            _log_import(con, tid, "cogs", cogs_file[0], applied=cogs_applied, rejects=cogs_rejects)
        if cogs_applied == 0:
            con.close()
            return JSONResponse({"ok": False, "error": "At least one valid COGS row is required (sku + cogs>0 matching your catalog).",
                                 "cogs_rejects": cogs_rejects[:50]}, status_code=400)
        # 3) layer every non-catalog report by kind (real data only)
        for fn, data, ch, rep in reports:
            kind = report_parse.classify(rep)
            if kind == "catalog":
                ingested.append({"file": fn, "channel": ch, "kind": kind, "skus": n_skus}); continue
            res = report_parse.ingest_report(con, tid, ch, rep, fn, data)
            con.commit()
            ingested.append({"file": fn, "channel": ch, "kind": res.get("kind", kind),
                             "applied": res.get("applied"), "matched": res.get("matched"),
                             "unmatched": res.get("unmatched"), "error": res.get("error")})
            _log_import(con, tid, "report:" + ch, fn, applied=res.get("applied", 0),
                        rejects=[{"reason": f"{res.get('unmatched',0)} rows had SKUs not in catalog"}] if res.get("unmatched") else [])
    finally:
        con.close()

    scheduler.start_provision_customer(tid)
    return JSONResponse({"ok": True, "started": True, "skus": n_skus,
                         "cogs_applied": cogs_applied, "cogs_rejected": len(cogs_rejects),
                         "cogs_rejects": cogs_rejects[:50], "reports": ingested})

@router.get("/api/onboard/status")
def onboard_status(request: Request):
    tid = require_tenant(request)
    job = scheduler.get_job(tid)
    if not job:
        # no active job — report provisioned state so the page can route correctly
        con=db.connect(); t=db.get_tenant(con, tid); con.close()
        return JSONResponse({"pct": 100 if (t and t["provisioned"]) else 0,
                             "stage": "Ready" if (t and t["provisioned"]) else "Not started",
                             "done": bool(t and t["provisioned"]), "error": None})
    return JSONResponse(job)

@router.post("/api/wipe")
def wipe(request: Request):
    tid = require_tenant(request)
    if _is_customer(tid):
        return JSONResponse({"ok": False, "error": "Wipe is disabled for customer accounts. Re-upload a report to replace its data."}, status_code=403)
    con=db.connect(); db.wipe_tenant_data(con, tid); con.close()
    return JSONResponse({"ok": True, "redirect": "/superlogin/hub"})   # R15 E.10: tester wipe → hub (server-decided; backdoor path stays out of the SPA)

# --- root: app if authed+provisioned, else login/onboarding handled client-side ---

@router.get("/api/ingest/reports")
def ingest_reports(request: Request):
    """The per-channel/per-report catalog that drives the upload grid (Phase 5)."""
    require_tenant(request)
    from realify.multichannel import CsvReportSource, CH_BY_NAME
    return JSONResponse({"reports": CsvReportSource.REPORTS,
                         "labels": {k: v["label"] for k, v in CH_BY_NAME.items()}})


@router.get("/api/ingest/catalog")
def ingest_catalog(request: Request):
    """Engine-backed channel + report catalog for the drag-drop onboarding checklist: the reports
    the ingestion engine actually recognizes, with the capability each unlocks."""
    require_tenant(request)
    from realify.ingest import report_catalog as cat
    return JSONResponse({"channels": [
        {"channel": c["channel"], "label": c["label"], "active": c["active"],
         "reports": cat.channel_checklist(c["channel"]) if c["active"] else []}
        for c in cat.CHANNELS]})


@router.post("/api/ingest/identify")
async def ingest_identify(request: Request):
    """Recognize dropped files WITHOUT persisting: per file what report type it is, rows, months; the
    Amazon + Shopify recognized-report checklist; same-type overlaps + conflicts; and the raw-path
    detection signals + stated-vs-detected reconcile prompts (rawpath.identify_payload). Powers the live
    green-check + reconcile UX before the user commits."""
    tid = require_tenant(request)
    from realify.ingest import report_ingest as ri, rawpath
    form = await request.form()
    tables, files = [], []
    for _k, v in form.multi_items():
        if hasattr(v, "filename") and getattr(v, "filename", None):
            try:
                df = ri.load_table(v.filename, await v.read())
                rt = ri.detect_report_type(df.columns)
            except Exception:
                df, rt = None, ri.UNKNOWN
            if df is not None:
                tables.append((v.filename, df))
            files.append(rawpath.file_meta(v.filename, df, rt))
    return JSONResponse(rawpath.identify_payload(tid, tables, files))


@router.post("/api/onboard/reports")
async def onboard_reports(request: Request):
    """Report-aware CUSTOMER commit: run the SAME engine as the in-app SKUs upload
    (report_ingest -> write_ingest, channel + overlap detection), mark the tenant provisioned, and
    hand off to the dashboard. This is what makes onboarding populate Profit & Ads directly."""
    tid = require_tenant(request)
    if not _is_seller(tid):     # full parity: customers AND testers upload/replace via this full pipeline
        return JSONResponse({"ok": False, "error": "This endpoint is for seller accounts."}, status_code=403)
    from realify import country as country_mod
    from realify.ingest import report_ingest, report_writer, report_catalog as cat, marketplace_registry as reg
    from realify.repositories.interpretation_repo import InterpretationRepository, ConfirmationRepository
    from realify.repositories.ingested_report_repo import IngestedReportRepository
    form = await request.form()
    ctry = country_mod.normalize(form.get("country"))
    tables = []
    for _k, v in form.multi_items():
        if hasattr(v, "filename") and getattr(v, "filename", None):
            try:
                tables.append((v.filename, report_ingest.load_table(v.filename, await v.read())))
            except Exception:
                pass
    tables = [(n, df) for n, df in tables if df is not None]
    if not tables:
        return JSONResponse({"ok": False, "error": "No readable report files received."}, status_code=400)

    con = db.connect()
    try:
        db.set_setting(con, tid, "country", ctry)
        interp = InterpretationRepository(con)
        conf = ConfirmationRepository(con)
        dedup = IngestedReportRepository(con)
        # fool-proof duplicate guard: 100%-identical re-uploads are skipped (repo.partition)
        fresh, duplicates = dedup.partition(tid, tables)
        fresh_tables = [(n, df) for n, df, _h in fresh]
        summary, result = {}, None
        if fresh_tables:
            for ch in report_ingest.detect_channels(fresh_tables, interp.resolver(tid)):
                mp = str(ch["marketplace"]).strip().lower()
                if ch["treatment"] == reg.UNKNOWN:
                    conf.upsert(tid, f"channel_map:{mp}", "channel_map", f"Unrecognized channel: {ch['marketplace']}",
                                f"{ch['units']:.0f} units — confirm what this channel is.",
                                suggested=reg.OFF_AMAZON_MCF, impact_units=ch["units"])
                elif mp not in interp.channel_map(tid):
                    interp.set_rule(tid, "channel_map", mp, ch["treatment"], confidence="default")
            from realify.ingest import conflicts as cflt
            cflt.record_overlap_confirmations(conf, tid, fresh_tables)
            result = report_ingest.ingest_tables(fresh_tables, interp.resolver(tid),
                                                 resolutions=cflt.parse_resolutions(form.get("resolutions")))
            summary = report_writer.write_ingest(con, tid, result)
            from realify.ingest.ad_extract import safe_ingest_ad_graph   # attributable ads (Part A):
            summary["ads"] = safe_ingest_ad_graph(con, tid, fresh_tables)  # additive graph + coverage
            dedup.record_fresh(tid, fresh, result.report_types if result else {})
        # Shopify tables (ignored by the Amazon extractors) commit through their own path: crosswalk +
        # seller_skus for Shopify-only SKUs, sku_parity/store_id sourced from the tenant's topology.
        shop_tables = [(n, df) for n, df in fresh_tables
                       if str(report_ingest.detect_report_type(df.columns)).startswith("SHOP_")]
        if shop_tables:
            from realify.ingest import shopify_commit
            from realify.repositories.topology_repo import TopologyRepository
            summary["shopify"] = shopify_commit.commit(con, tid, shop_tables, TopologyRepository(con).get(tid))
        con.commit()
    finally:
        con.close()
    # build the dashboard from the ingested own-data: run the deterministic pipeline (Intelligence
    # cards) synchronously so the app opens populated, then set provisioned. Market enrichment for
    # the Research tab runs in the background (real signals accrue after landing), same as the
    # customer provisioning path — without it, only SKUs and Profit & Ads would have data.
    from realify.pipeline.materialize import run_pipeline
    run_pipeline(tid)
    with db.connect() as con:
        db.set_tenant_provisioned(con, tid, "uploaded")
        con.commit()
    try:
        import threading; from realify import scheduler
        threading.Thread(target=scheduler.enrich_market, args=(tid,), daemon=True).start()
    except Exception:
        pass
    return JSONResponse({"ok": True, "provisioned": True, "skus_written": summary.get("skus_written", 0)})

@router.post("/api/ingest/upload")
async def ingest_upload(request: Request):
    """Real per-channel report ingestion. Accepts a multipart file for a given
    (channel, report), parses it tolerantly into the canonical tables, then
    re-runs the multichannel build + pipeline so the channel swaps to real data.
    Falls back to recording intent if no file is attached (back-compat)."""
    tid = require_tenant(request)
    ctype = request.headers.get("content-type", "")
    if "multipart/form-data" in ctype:
        form = await request.form()
        channel = (form.get("channel") or "").strip().lower()
        report = (form.get("report") or "").strip()
        up = None
        for _k, v in form.multi_items():
            if hasattr(v, "filename") and getattr(v, "filename", None):
                up = v; break
        if not channel or not report or up is None:
            return JSONResponse({"ok": False, "error": "channel, report and a file are required."}, status_code=400)
        data = await up.read()
        from realify.ingest import report_parse
        from realify.multichannel import build_multichannel
        from realify.pipeline import materialize
        con = db.connect()
        try:
            res = report_parse.ingest_report(con, tid, channel, report, up.filename, data)
            db.set_setting(con, tid, f"ingested:{channel}:{report}", db.now_iso())
        finally:
            con.close()
        if not res.get("ok"):
            return JSONResponse({"ok": False, **res}, status_code=400)
        # refresh derived tables + cards so the real data is reflected immediately
        try:
            build_multichannel(tid)
            materialize.run_pipeline(tid)
        except Exception as e:
            res["refresh_warning"] = str(e)
        return JSONResponse({"ok": True, "channel": channel, "report": report, **res})
    # back-compat: JSON body just records intent
    b = await request.json()
    con = db.connect()
    db.set_setting(con, tid, f"upload_intent:{b.get('channel')}:{b.get('report')}", db.now_iso())
    con.close()
    return JSONResponse({"ok": True, "queued": True, "channel": b.get("channel"), "report": b.get("report")})
