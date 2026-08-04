"""Agency periodic jobs (split from scheduler for the file-line cap): maintenance (health,
pilot lapse, cosign/gate expiry), real-brand feeders (decisions/rollups/FX), and the monthly
invoice build. All no-op without Postgres; called from scheduler._loop."""

def run_agency_jobs_once(log=print):
    """Periodic agency maintenance (agency-plan): expire stale integrations (health sweep), lapse
    unsigned pilots to read-only at day 90 (never auto-converts), and cancel expired brand co-sign
    windows (silence never executes). No-op unless a Postgres backend is configured."""
    try:
        from .agency import db as agency_db, connections, pilots, approvals, gates
        conn = agency_db.agency_connect()
    except Exception as e:
        return {"skipped": str(e)[:80]}
    try:
        cur = conn.cursor()
        flipped = connections.health_run(cur)
        cur.execute("SELECT agency_id FROM agency_pilots")
        lapsed = sum(1 for (aid,) in cur.fetchall() if pilots.lapse_job(cur, aid).get("read_only"))
        cur.execute("SELECT id FROM tenants")
        tids = [r[0] for r in cur.fetchall()]
        expired = approvals.expire_cosigns(cur, tids) if tids else 0
        gates_expired = gates.expire_gates(cur)                        # R3: flip lapsed attestations (was orphaned)
        conn.commit()
        log(f"[scheduler][agency] connections_expired={flipped} pilots_lapsed={lapsed} "
            f"cosigns_expired={expired} gates_expired={gates_expired}")
        return {"connections_expired": flipped, "pilots_lapsed": lapsed, "cosigns_expired": expired,
                "gates_expired": gates_expired}
    finally:
        conn.close()


_FALLBACK_FX_PPM = {"INR": 83_000_000}     # manual daily-rate fallback until a live FX feed is wired


def run_feeders_once(log=print, as_of=None):
    """Real-brand feeders (R3): for every ACTIVE-engaged brand that has ingested SKU data, (re)generate
    open decisions + refresh the USD-normalized rollup, and lock the daily FX rate for non-USD brands
    (manual-rate fallback). Sandbox brands flow through the same path — nothing here is sandbox-specific.
    No-op without Postgres. Idempotent (decisions.generate replaces prior open decisions)."""
    import datetime
    try:
        from .agency import db as agency_db, decisions, rollups, fx, tenancy
        conn = agency_db.agency_connect()
    except Exception as e:
        return {"skipped": str(e)[:80]}
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM tenants")
        ids = [r[0] for r in cur.fetchall()]
        if ids:
            tenancy.set_brand_scope(cur, ids)                          # scope before RLS engagements read
        cur.execute("SELECT DISTINCT tenant_id FROM engagements WHERE status='active'")
        brands = [r[0] for r in cur.fetchall()]
        as_of = as_of or datetime.date.today()
        res = {"brands": 0, "decisions": 0}
        for t in brands:
            tenancy.set_brand_scope(cur, [t])
            cur.execute("SELECT count(*) FROM seller_skus WHERE tenant_id=%s", (t,))
            if cur.fetchone()[0] == 0:
                continue                                               # no ingested data yet -> skip
            cur.execute("SELECT currency FROM agency_ingest_rows WHERE tenant_id=%s ORDER BY id DESC LIMIT 1",
                        (t,))
            r = cur.fetchone()
            ccy = (r[0] if r and r[0] else None)
            if not ccy:
                # DIRECT-uploaded brand (no agency CSV rows, e.g. a customer that onboarded via
                # /api/onboard/reports) — use its own marketplace currency, not a bare USD default,
                # else a ₹/₹-native brand's decisions (and fleet $-at-stake) come out mis-normalized or 0.
                cur.execute("SELECT value FROM tenant_settings WHERE tenant_id=%s AND key='country'", (t,))
                cr = cur.fetchone()
                try:
                    from . import country as _country
                    ccy = (_country.profile(cr[0]).get("currency") if cr and cr[0] else None) or "USD"
                except Exception:
                    ccy = "USD"
            if ccy != "USD" and ccy in _FALLBACK_FX_PPM:
                fx.lock_rate(cur, as_of, ccy, _FALLBACK_FX_PPM[ccy])
            made = decisions.generate(cur, t, ccy, as_of)
            rollups.compute(cur, t, ccy, as_of)
            res["brands"] += 1
            res["decisions"] += len(made)
        conn.commit()
        log(f"[scheduler][feeders] brands={res['brands']} decisions={res['decisions']}")
        return res
    finally:
        conn.close()


def run_billing_once(log=print, as_of=None):
    """Monthly invoice build (R4): one invoice per agency-subscription for the current period, from
    metering (billing_agency.build_invoice — pure DB math; Stripe stays TEST-mode and is not called
    here). Idempotent: skips an agency that already has an invoice for the period. No-op w/o Postgres."""
    import datetime
    try:
        from .agency import db as agency_db, billing_agency, tenancy
        conn = agency_db.agency_connect()
    except Exception as e:
        return {"skipped": str(e)[:80]}
    try:
        cur = conn.cursor()
        as_of = as_of or datetime.date.today()
        ps = as_of.replace(day=1)
        cur.execute("SELECT agency_id, per_account_price_minor, platform_fee_minor, usage_unit_price_minor,"
                    " hq_country FROM agency_subscriptions s LEFT JOIN agencies a ON a.id=s.agency_id")
        subs = cur.fetchall()
        cur.execute("SELECT id FROM tenants")
        ids = [r[0] for r in cur.fetchall()]
        built = 0
        for ag, pa, pf, up, hq in subs:
            if ids:
                tenancy.set_brand_scope(cur, ids)
            cur.execute("SELECT 1 FROM invoices WHERE agency_id=%s AND period_start=%s", (ag, ps))
            if cur.fetchone():
                continue                                               # idempotent for the period
            cur.execute("SELECT tenant_id FROM engagements WHERE agency_id=%s AND status='active'", (ag,))
            brands = [r[0] for r in cur.fetchall()]
            sub = {"per_account_price_minor": pa or 0, "platform_fee_minor": pf or 0,
                   "usage_unit_price_minor": up or 0, "hq_country": hq}
            billing_agency.build_invoice(cur, ag, brands, as_of, sub, period_start=ps, period_end=as_of)
            built += 1
        conn.commit()
        log(f"[scheduler][billing] invoices_built={built}")
        return {"invoices_built": built}
    finally:
        conn.close()


