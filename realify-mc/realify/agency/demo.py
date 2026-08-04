"""Agency demo/sample brand (R18.10). Attaches ONE fully-synthesized SAMPLE brand to a REAL agency's
fleet so the agency can see what a populated brand looks like (drill in → operate → back to hub) BEFORE
onboarding any real data. Reuses the sandbox synth stack (_seed_brand); kept in its own module so
sandbox.py stays under the 400-line maintainability cap."""
from . import sandbox, synth, ops, tenancy


def ensure_demo_brand(cur, agency_id):
    """Idempotently ensure the SAMPLE brand exists in `agency_id`'s fleet. tenant_kind='sandbox' (so the
    drill-in grants seller access + renders the synth interior), tagged sandbox_scenario='agency-demo:<id>'.
    No-op (returns None) for sandbox/preset agencies (they already carry synth brands).

    Returns (tenant_id, needs_finalize). needs_finalize is True on first creation OR when the brand was
    seeded before the lens-synth step existed (no ad_entity_perf yet) — the CALLER must then run
    lens_synth.finalize_world([tid]) AFTER committing, in a fresh connection, to populate Profit&Ads
    (ad_performance/sku_revenue_period), the campaign ad-graph (ad_entity_perf → the ƒ modal), Channels,
    and the Intelligence cards. Seeds the catalog+decisions here; finalize does the rest post-commit."""
    cur.execute("SELECT sandbox_scenario, hq_country FROM agencies WHERE id=%s", (agency_id,))
    row = cur.fetchone()
    if not row or row[0]:                              # unknown, or a sandbox/preset agency → skip
        return None
    country = (row[1] or "US").upper()
    if country not in ("US", "IN"):
        country = "US"
    tag = f"agency-demo:{agency_id}"
    cur.execute("SELECT id FROM tenants WHERE sandbox_scenario=%s LIMIT 1", (tag,))
    r = cur.fetchone()
    if r:                                              # already exists — keep the engagement live
        t = r[0]
        tenancy.set_brand_scope(cur, [t])
        if sandbox._engagement_of(cur, agency_id, t) is None:
            ops.create_engagement(cur, None, agency_id, t)
        cur.execute("SELECT count(*) FROM ad_entity_perf WHERE tenant_id=%s", (t,))
        needs = cur.fetchone()[0] == 0                 # self-heal a brand seeded before finalize existed
        return t, needs
    cur.execute("INSERT INTO tenants(name,created_at,provisioned,data_mode,sandbox,tenant_kind,"
                "account_type,sandbox_scenario) VALUES(%s,now()::text,1,'synthetic',1,'sandbox','tester',%s) "
                "RETURNING id", ("Sample Brand (demo)", tag))
    t = cur.fetchone()[0]
    tenancy.set_brand_scope(cur, [t])
    ops.create_engagement(cur, None, agency_id, t)     # fleet membership
    spec = synth.spec_from_params({"country": country, "seed": f"demo-{str(agency_id)[:8]}",
                                   "brands_per_agency": 1, "direct_brands": 0, "sku_count": 60,
                                   # plant actionable problems so Profit&Ads/decisions are populated (a live
                                   # demo, not a clean-but-empty brand); NOT expired_conn (keeps it live).
                                   "moments": ["stockout", "acos_over_breakeven", "competitor_undercut"],
                                   "agency_name": "Demo", "brand_name": "Sample Brand (demo)"})
    sandbox._seed_brand(cur, agency_id, t, spec, spec["brands"][0], 0, sandbox._AS_OF)  # catalog+decisions
    return t, True                                     # freshly seeded → caller must finalize lenses
