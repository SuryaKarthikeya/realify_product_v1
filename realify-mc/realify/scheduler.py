"""Orchestration — now tenant-aware. provision_tenant() runs a tenant's data source
(synthetic now, report parsers later) then pulls market data + runs the pipeline for
that tenant. The background scheduler loops over all provisioned tenants every N hours."""
import threading, datetime as dt
from . import config, db
from .repositories.seller_repo import SellerRepository
from .repositories.pull_repo import PullLogRepository
from .repositories.tenant_repo import TenantRepository
from .collectors.keepa_collector import KeepaCollector
from .collectors.amazon_pdp_collector import AmazonPdpCollector
from .collectors.tierc_collector import RecallsCollector, NewsCollector, TrendsCollector
from .pipeline.materialize import run_pipeline

def collectors(tenant_id):
    # Order matters: Keepa first (competitor offers + history), then Amazon PDP so its
    # per-ASIN live snapshot carries a later captured_at and wins the "current" fields.
    return [KeepaCollector(tenant_id), AmazonPdpCollector(tenant_id), RecallsCollector(tenant_id),
            NewsCollector(tenant_id), TrendsCollector(tenant_id)]

def run_all_once(tenant_id, force=False, run_pipeline_after=True, log=print):
    results = {}
    for c in collectors(tenant_id):
        n = c.run(force=force); results[c.source] = n
        log(f"[pull][t{tenant_id}] {c.source:8s} mode={c.mode:7s} records={n}")
    if run_pipeline_after:
        r = run_pipeline(tenant_id)
        log(f"[pipeline][t{tenant_id}] {r['new']} new, {r['updated']} updated, {r['total']} cards")
        results["pipeline"] = r
    return results

_MKT = {}
def get_market_refresh(tenant_id):
    with _JOBS_LOCK:
        j = _MKT.get(tenant_id)
        return dict(j) if j else None

def start_market_refresh(tenant_id, log=print):
    """On-demand: force-run every market collector in the background and capture each
    source's pull result + diagnostic note (so we can see exactly what Keepa did).
    Browser polls /api/settings/refresh_market/status."""
    job = _Job(done=False, sources={}, error=None)
    with _JOBS_LOCK: _MKT[tenant_id] = job
    def _run():
        try:
            con0 = db.connect()
            for c in collectors(tenant_id):
                t0 = time.time()
                try:
                    n = c.run(force=True)
                    ok = True; err = None
                except Exception as e:
                    n = 0; ok = False; err = str(e)[:160]
                # read back the most recent pull_log row for this source (status + note)
                row = PullLogRepository(con0).last_by_source(tenant_id, c.source)
                cur = dict(job.get("sources", {}))
                cur[c.source] = {"records": (row["records"] if row else n),
                                 "status": (row["status"] if row else ("ok" if ok else "failed")),
                                 "note": (row["note"] if row else err),
                                 "secs": round(time.time()-t0, 1)}
                job.update(dict(sources=cur))
            con0.close()
            run_pipeline(tenant_id)
            job.update(dict(done=True))
        except Exception as e:
            log(f"[refresh_market][t{tenant_id}] ERROR {e}")
            job.update(dict(done=True, error=str(e)[:200]))
    _threading.Thread(target=_run, daemon=True).start()
    return job

import time
def provision_own_data(tenant_id, source, job=None, log=print):
    """FAST phase: own data + channel layer + conditions + pipeline. No market pulls,
    so the app can open in seconds on the seller's own-data insights."""
    from . import channels, synth_conditions
    def stage(pct, msg):
        if job is not None: job.update(dict(pct=pct, stage=msg))
        log(f"[provision][t{tenant_id}] {msg}")
    stage(8, "Loading your catalog")
    summary = source.provision(tenant_id)
    seed = None
    if source.mode == "synthetic":
        seed = synth_conditions.make_seed(tenant_id, "spread")
        synth_conditions.inject_sku_conditions(tenant_id, seed, "spread")
    stage(35, "Building the channel layer")
    channels.build_channel_layer(tenant_id)
    from . import multichannel
    multichannel.build_multichannel(tenant_id, log=log)   # fan out across all channels
    if source.mode == "synthetic":
        synth_conditions.inject_traffic_conditions(tenant_id, seed, "spread")
    # Stage 2 Phase 0: seed metric history so trends + the forecaster have data on day one.
    from . import history
    con = db.connect()
    try:
        history.backfill_synthetic(con, tenant_id)
    finally:
        con.close()
    if source.mode == "synthetic":
        # Tier-2: campaign->SKU ad entity-graph so Fix-Ads renders for a tester (scenario = data row)
        from .ingest.synth_ad_graph import synthesize_ad_graph
        con = db.connect()
        try:
            synthesize_ad_graph(con, tenant_id, db.get_setting(con, tenant_id, "ad_scenario", "ads_full"))
            con.commit()
        finally:
            con.close()
    stage(62, "Detecting insights from your data")
    run_pipeline(tenant_id)
    con = db.connect(); db.set_tenant_provisioned(con, tenant_id, source.mode); con.close()
    stage(80, "Opening your workspace")
    return summary

def enrich_market(tenant_id, job=None, log=print):
    """BACKGROUND phase: live/fixture market pulls with fail-fast timeouts + circuit
    breaker, then re-run the pipeline so market cards (Buy Box, competitor moves, news)
    fill in. Never blocks onboarding — runs after the user is already in the app."""
    if job is not None: job.update(dict(stage="Enriching with market data", enriching=True))
    try:
        run_all_once(tenant_id, force=True, run_pipeline_after=False, log=log)
        import time; time.sleep(1.0)
        run_all_once(tenant_id, force=True, log=log)
    except Exception as e:
        log(f"[enrich][t{tenant_id}] market enrichment error: {e}")
    if job is not None: job.update(dict(enriching=False, pct=100, stage="Ready", done=True))

def provision_tenant(tenant_id, source, log=print):
    """Synchronous full provision (used by tests/CLI): own-data then market enrichment."""
    s = provision_own_data(tenant_id, source, log=log)
    enrich_market(tenant_id, log=log)
    return s

# ---- background job tracking for the onboarding progress bar ----
import threading as _threading
_JOBS = {}
_JOBS_LOCK = _threading.Lock()

class _Job(dict):
    def update(self, d):
        with _JOBS_LOCK:
            super().update(d)

def get_job(tenant_id):
    with _JOBS_LOCK:
        j = _JOBS.get(tenant_id)
        return dict(j) if j else None

def start_provision(tenant_id, source, log=print):
    """Kick off provisioning in the background; return immediately. The browser polls
    /api/onboard/status. done=True flips once own-data is ready (app opens); market
    enrichment continues after."""
    job = _Job(pct=0, stage="Starting", done=False, error=None, enriching=False)
    with _JOBS_LOCK: _JOBS[tenant_id] = job
    def _run():
        try:
            provision_own_data(tenant_id, source, job=job, log=log)
            job.update(dict(done=True))          # app can open now (own-data ready)
            enrich_market(tenant_id, job=job, log=log)
        except Exception as e:
            log(f"[provision][t{tenant_id}] ERROR {e}")
            job.update(dict(error=str(e)[:200], done=True))
    _threading.Thread(target=_run, daemon=True).start()
    return job

def start_provision_customer(tenant_id, log=print):
    """CUSTOMER path. SKUs + COGS + reports have already been ingested synchronously by the
    upload endpoint (no synthesis). Here we just run the deterministic pipeline over the real
    data, then enrich with real market signals in the background. No synthetic seed, no
    synthetic history backfill — history accrues from real snapshots over time."""
    from .pipeline.materialize import run_pipeline
    job = _Job(pct=0, stage="Analysing your data", done=False, error=None, enriching=False)
    with _JOBS_LOCK: _JOBS[tenant_id] = job
    def _run():
        try:
            run_pipeline(tenant_id)
            con = db.connect(); db.set_tenant_provisioned(con, tenant_id, "uploaded"); con.close()
            job.update(dict(done=True))          # app opens on real own-data
            enrich_market(tenant_id, job=job, log=log)   # market signals stay ON for customers
        except Exception as e:
            log(f"[provision-customer][t{tenant_id}] ERROR {e}")
            job.update(dict(error=str(e)[:200], done=True))
    _threading.Thread(target=_run, daemon=True).start()
    return job

_REBUILD = {}
def get_rebuild(tenant_id):
    with _JOBS_LOCK:
        j = _REBUILD.get(tenant_id)
        return dict(j) if j else None

def start_rebuild(tenant_id, log=print):
    """Re-run detection with current effective rules in the BACKGROUND so the Apply
    button returns immediately. Browser polls /api/settings/rebuild/status."""
    from .pipeline.materialize import run_pipeline
    from . import synth_conditions
    job = _Job(done=False, error=None, changed=None, total=None)
    with _JOBS_LOCK: _REBUILD[tenant_id] = job
    def _run():
        try:
            r = run_pipeline(tenant_id)
            cov = synth_conditions.coverage(tenant_id)
            job.update(dict(done=True, total=r.get("total"), new=r.get("new"),
                            active=r.get("active"), coverage=cov))
        except Exception as e:
            log(f"[rebuild][t{tenant_id}] ERROR {e}")
            job.update(dict(done=True, error=str(e)[:200]))
    _threading.Thread(target=_run, daemon=True).start()
    return job

def resynthesize(tenant_id, mode="reroll", seed=None, log=print):
    """Re-roll synthetic conditions so different rules fire (testing). SYNTHETIC ONLY.

    'full' mode re-runs the SAME cross-lens builders scheduler.provision_own_data runs, so every one
    of the five lenses (Product Catalog, Profit & Ads, Channels, Intelligence, Category Analyst)
    repopulates non-empty, world-consistent and locale-correct — never a partial/legacy path.
    `seed` pins the condition RNG (default: a fresh per-call random seed via make_seed); pass a fixed
    value for a deterministic, byte-identical resynth (testing / reproducible demos)."""
    from . import channels, synth_conditions, multichannel
    from .ingest.synthetic import SyntheticSource
    from .pipeline.materialize import run_pipeline
    con = db.connect(); t = db.get_tenant(con, tenant_id); con.close()
    if not t or t.get("data_mode") != "synthetic":
        return {"ok": False, "error": "Resynthesize applies to synthetic data only."}
    seed = synth_conditions.make_seed(tenant_id, mode) if seed is None else int(seed)
    if mode == "full":
        # Regenerate from the TENANT'S OWN catalog — NOT the bundled demo seed. Re-derive a
        # minimal seed (asin/cogs/category/price/title) from the current seller_skus and
        # re-expand it, so the seller's ASINs + categories + currency are preserved while the
        # economics reset cleanly. Falls back to the demo seed only if no catalog exists yet.
        from .ingest.seed import expand_minimal_seed
        from . import country as _country
        con2 = db.connect()
        rows = SellerRepository(con2).select_columns(tenant_id, ["asin", "title", "category", "cogs", "price"])
        con2.close()
        minimal = [{"asin": r["asin"], "title": r["title"], "category": r["category"],
                    "cogs": r["cogs"], "price": r["price"]} for r in rows]
        if minimal:
            seed_full = expand_minimal_seed(minimal, prof=_country.tenant_profile(tenant_id))
            SyntheticSource(seed_skus=seed_full).provision(tenant_id)
        else:
            SyntheticSource().provision(tenant_id)        # no catalog yet -> demo
        # the catalog was regenerated — drop stale per-card research so briefs re-derive
        from .repositories.card_repo import CardRepository
        con3 = db.connect(); CardRepository(con3).clear_research(tenant_id)
        con3.commit(); con3.close()
        # parity with provision_own_data: seed metric history so trends + the forecaster have data
        # (no-op when history already exists, so it never double-seeds an existing tenant).
        from . import history
        con6 = db.connect()
        try:
            history.backfill_synthetic(con6, tenant_id)
        finally:
            con6.close()
        # full resynth OWNS the ad entity-graph: regenerate (clear+rebuild) from the fresh catalog.
        # reroll/coverage deliberately leave the graph intact (they don't rebuild the catalog).
        from .ingest.synth_ad_graph import synthesize_ad_graph
        con5 = db.connect()
        try:
            synthesize_ad_graph(con5, tenant_id, db.get_setting(con5, tenant_id, "ad_scenario", "ads_full"))
            con5.commit()
        finally:
            con5.close()
    synth_conditions.inject_sku_conditions(tenant_id, seed, mode)
    channels.build_channel_layer(tenant_id)
    multichannel.build_multichannel(tenant_id, log=log)   # keep channel economics in sync
    synth_conditions.inject_traffic_conditions(tenant_id, seed, mode)
    # regenerate ad + revenue periods so Profit & Ads reflects the re-rolled economics (idempotent)
    from .ingest.synth_cmaa import synthesize_cmaa
    con4 = db.connect(); synthesize_cmaa(con4, tenant_id); con4.commit(); con4.close()
    r = run_pipeline(tenant_id)
    cov = synth_conditions.coverage(tenant_id)
    log(f"[resynth][t{tenant_id}] mode={mode} coverage={cov['pct']}% ({cov['fired']}/{cov['total']})")
    return {"ok": True, "mode": mode, "coverage": cov, **r}

def all_tenant_ids():
    con = db.connect()
    ids = TenantRepository(con).list_provisioned_ids()
    con.close(); return ids

_stop = threading.Event()
from .agency_jobs import (run_agency_jobs_once, run_feeders_once,  # noqa: F401
                          run_billing_once)


def _loop(interval_hours, log):
    # Run an immediate pass on startup so provisioned tenants enrich on boot — no dead window
    # after a restart (the old code waited a full interval before the first pull, which left
    # migrated/existing tenants with market sources stuck "pending"). Then pull every interval.
    while True:
        try:
            for tid in all_tenant_ids():
                log(f"[scheduler] periodic pull tenant {tid}")
                try:
                    run_all_once(tid, force=False, log=log)
                except Exception as e:
                    log(f"[scheduler] tenant {tid} pull error: {e}")
        except Exception as e:
            log(f"[scheduler] loop error: {e}")
        try:
            run_agency_jobs_once(log=log)          # agency maintenance: health, pilot lapse, cosign expiry
        except Exception as e:
            log(f"[scheduler] agency jobs error: {e}")
        try:
            run_feeders_once(log=log)              # real-brand feeders: decisions + rollups + daily FX
        except Exception as e:
            log(f"[scheduler] feeders error: {e}")
        try:
            run_billing_once(log=log)              # monthly invoice build (idempotent per period)
        except Exception as e:
            log(f"[scheduler] billing error: {e}")
        if _stop.wait(interval_hours * 3600):
            break

def start_background(interval_hours=None, log=print):
    interval = interval_hours or config.PULL_INTERVAL_HOURS
    t = threading.Thread(target=_loop, args=(interval, log), daemon=True); t.start()
    log(f"[scheduler] started — every {interval}h across all provisioned tenants")
    return t

def stop(): _stop.set()
