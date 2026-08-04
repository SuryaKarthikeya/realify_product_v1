"""R14 Part C — cross-lens synthesis. After a sandbox world COMMITS, populate the OTHER four lenses
(Profit & Ads, Channels, Intelligence, Category Analyst) so all five render real, world-consistent,
deterministic data — not just Product Catalog. Reuses the EXACT deterministic builders that
scheduler.provision_own_data runs for a real/demo tenant (the sandbox's _seed_brand skipped them). Each
derives purely from the already-seeded seller_skus (+ the tenant's country setting), so the world stays
byte-identical per seed and locale-correct. Decisions were derived from seller_skus.tacos in
_seed_brand; synth_cmaa ties Profit&Ads ACoS to that same tacos, so the lenses and decisions agree.

Runs AFTER the world transaction commits (the builders open their own db.connect() and can't see
uncommitted rows). Each builder is best-effort — a failure logs but never aborts the world load."""


def finalize_world(brand_ids, log=None):
    """Synthesize every non-catalog lens for each brand tenant of a freshly-loaded world."""
    from .. import db as _db, multichannel, channels, seller
    from ..ingest import synth_cmaa, synth_ad_graph
    from ..pipeline import materialize
    _log = log or (lambda m: None)
    for tid in brand_ids:
        # Profit & Ads source-of-truth: ad_performance + sku_revenue_period (+ provenance), then the
        # ad-graph (entity/search-term) that the recommendations surface needs.
        con = _db.connect()
        try:
            synth_cmaa.synthesize_cmaa(con, tid)
            synth_ad_graph.synthesize_ad_graph(con, tid)
            con.commit()
        except Exception as e:                                  # pragma: no cover - defensive
            _log(f"[lens] cmaa/ad-graph t{tid}: {e}")
        finally:
            con.close()
        # Channels (orders → channels + channel_economics + channel layer) and Intelligence/Category
        # Analyst (the detector pipeline → cards). Each opens its own connection.
        for name, fn in (("orders", lambda: seller.generate_orders(tid)),
                         ("channels", lambda: multichannel.build_multichannel(tid, log=_log)),
                         ("channel_layer", lambda: channels.build_channel_layer(tid)),
                         ("pipeline", lambda: materialize.run_pipeline(tid))):
            try:
                fn()
            except Exception as e:                              # pragma: no cover - defensive
                _log(f"[lens] {name} t{tid}: {e}")


def finalize_current_world(log=None):
    """Resolve the just-loaded world's brand tenants (managed + direct) and synthesize their lenses."""
    from . import db as _adb
    from .sandbox import current_world_key
    conn = _adb.agency_connect()
    try:
        cur = conn.cursor()
        wk = current_world_key(cur)
        if not wk:
            conn.rollback(); return
        cur.execute("SELECT id FROM tenants WHERE sandbox_scenario IN (%s, %s) ORDER BY id",
                    (wk, wk + "::d"))                           # managed + direct ('::d') brands
        ids = [r[0] for r in cur.fetchall()]
        conn.rollback()
    finally:
        conn.close()
    finalize_world(ids, log=log)
