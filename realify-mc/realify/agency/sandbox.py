"""Sandbox demo world (P7, rebuilt R6/R9/R14/R15.1). Deterministic agency book (N single-country brands
w/ real SKUs, connections, envelope, decisions); tenants sandbox=1, scenario-tagged, byte-identical/seed."""
import datetime
import hashlib
import random

from . import ops, decisions, connections, tenancy, fx, ledger
from .sandbox_scenarios import SCENARIOS, DEFAULT_SCENARIO
from ..pdp import ENVELOPES
from .. import country as _country

_AS_OF = datetime.date(2026, 7, 1)


def _rng(seed):
    return random.Random(int(hashlib.sha256(seed.encode()).hexdigest(), 16) % (2 ** 32))


def _skus(rng, spec):
    """Deterministic SKU rows (R9.1): real names per category×country, realistic price/COGS/units, problems on a MINORITY."""
    from . import locale
    lo, hi = spec.get("cogs_lo", 0.30), spec.get("cogs_hi", 0.50)
    country = spec.get("country") or spec.get("hq_country") or "US"
    n = spec["sku_count"]
    cats = spec["categories"]; primary = spec.get("primary_category") or cats[0]; others = [c for c in cats if c != primary] or [primary]
    moments = set(spec.get("moments") or [])
    # disjoint problem slots on a minority (hero SB-000 is the undercut target)
    under = ({0, 1} if "competitor_undercut" in moments else set())
    stock = set(range(2, 5)) if "stockout" in moments else set()          # 3 stockout SKUs
    acos = set(range(5, 8)) if "acos_over_breakeven" in moments else set()  # 3 ACOS SKUs
    rows = []
    for i in range(n):
        cat = primary if i % 3 != 2 else others[(i // 3) % len(others)]   # primary dominates (~2/3) so name/catalog/analyst agree
        title = locale.product_name(country, cat, i)
        price = rng.choice(spec["prices"])
        cogs = int(price * (lo + rng.random() * (hi - lo)))
        units = rng.randint(40, 250)
        doc, tacos, buybox = rng.choice([35, 45, 60, 75, 90]), round(6 + rng.random() * 10, 1), rng.choice([90, 94, 98])
        if i in stock:
            doc = rng.choice([4, 7, 10, 13])              # low cover -> stockout/reorder
        elif i in acos:
            tacos = round(28 + rng.random() * 14, 1)      # over break-even -> ads/bid
        elif i in under:
            buybox = rng.choice([55, 62, 70])             # competitor undercut -> reprice/pricing
        rows.append((f"SB-{i:03d}", title, cat, price, cogs, units, doc, tacos, buybox))
    return rows


def _brand_specs(spec):
    """The per-brand list. Single-brand scenarios (auto_in) get a one-element list."""
    return spec.get("brands") or [{"name": "Sandbox Brand", "currency": spec["currency"]}]


def _engagement_of(cur, agency_id, tenant_id):
    cur.execute("SELECT id FROM engagements WHERE agency_id=%s AND tenant_id=%s LIMIT 1",
                (agency_id, tenant_id))
    r = cur.fetchone()
    return r[0] if r else None


def _seed_skus(cur, tenant_id, spec, rng, chan):
    """One brand's SKUs (price-scaled fees, realistic margins, cross-lens inputs) + the brand country
    setting so the seller app localizes ccy/marketplace/fees (R11.1/R14)."""
    from .. import country as _country
    country_code = spec.get("country") or spec.get("hq_country") or "US"
    prof = _country.profile(country_code)
    cur.execute("DELETE FROM tenant_settings WHERE tenant_id=%s AND key='country'", (tenant_id,))
    cur.execute("INSERT INTO tenant_settings(tenant_id,key,value) VALUES(%s,'country',%s)", (tenant_id, country_code))
    cur.execute("DELETE FROM seller_skus WHERE tenant_id=%s", (tenant_id,))
    for asin, title, cat, price, cogs, units, doc, tacos, buybox in _skus(rng, spec):
        referral, fba = _country.estimate_fees(price, prof, rng)
        ad = round(price * 0.05, 2); ret = round(price * 0.02, 2)
        net = round(price - cogs - referral - fba - ad - ret, 2)
        margin = round(net / price * 100, 1) if price else 0
        floor = round((cogs + fba + ad + ret) / (1 - prof["referral_pct"]), 2) if price else 0
        vel = round(units / 30.0, 2)   # R14: cross-lens inputs (channels/pipeline)
        soh = int(units * doc / 30.0)
        rating = round(3.8 + rng.random() * 1.1, 1)
        reviews = rng.randint(20, 1400)
        annual_rev = round(price * units * 12, 2)                 # detectors read annual_rev_inr (monthly×12)
        units_year = units * 12
        cur.execute("INSERT INTO seller_skus(tenant_id,asin,internal_sku,channel,title,category,price,cogs,"
                    "referral_fee,fba_fee,ad_cost_unit,return_cost_unit,net_profit_unit,net_margin_pct,"
                    "breakeven_floor,units_month,days_of_cover,tacos,buybox_pct,velocity_day,stock_on_hand,"
                    "rating,review_count,annual_rev_inr,units_year) "
                    "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (tenant_id, asin, "SKU-" + asin, chan, title, cat, price, cogs, referral, fba, ad, ret, net,  # noqa: SKU-<asin> app convention keeps cross-lens ids aligned (R14)
                     margin, floor, units, doc, tacos, buybox, vel, soh, rating, reviews, annual_rev, units_year))


def _seed_brand(cur, agency_id, tenant_id, spec, bspec, idx, as_of):
    """Wipe + regenerate ONE brand's seeded world deterministically (idempotent). Reuses tenant_id."""
    currency = bspec["currency"]
    rng = _rng(f"{spec['seed']}-{idx}")
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute("UPDATE tenants SET name=%s WHERE id=%s", (bspec["name"], tenant_id))
    cur.execute("DELETE FROM decisions WHERE tenant_id=%s", (tenant_id,))
    _seed_skus(cur, tenant_id, {**spec, "primary_category": bspec.get("category")}, rng, spec.get("primary_channel", "amazon"))
    now = datetime.datetime.now(datetime.timezone.utc)
    # expired_conn brands get amazon_ads expired (PAUSED demo); most stay CONNECTED (R7 1a).
    conns = list(spec["connections"])
    if bspec.get("expired_conn"):
        conns = [(p, "expired" if p == "amazon_ads" else s) for p, s in conns]
    for provider, state in conns:
        exp = now - datetime.timedelta(days=1) if state == "expired" else now + datetime.timedelta(days=30)
        connections.upsert_connection(cur, tenant_id, provider, state, exp)
    eng = _engagement_of(cur, agency_id, tenant_id)
    ops.publish_envelope(cur, None, eng, tenant_id, ENVELOPES[spec["envelope"]], {})
    if currency != "USD":
        fx.lock_rate(cur, as_of, currency, spec["fx_inr_ppm"])
    decisions.generate(cur, tenant_id, currency, as_of)
    return eng


def cleanup_strays(cur):
    """Retire UNTAGGED old-loader sandbox singletons (tag+rename, terminate engagements). Returns count."""
    cur.execute("SELECT id FROM tenants WHERE COALESCE(sandbox,0) <> 0 AND sandbox_scenario IS NULL "
                "AND (name LIKE %s OR name LIKE %s)", ("Sandbox Brand%", "Direct Sandbox%"))
    strays = [r[0] for r in cur.fetchall()]
    for t in strays:
        cur.execute("UPDATE engagements SET status='terminated' WHERE tenant_id=%s", (t,))
        cur.execute("UPDATE tenants SET sandbox_scenario='retired', name='Retired sandbox brand' WHERE id=%s", (t,))
    cur.execute("UPDATE agencies SET sandbox_scenario='retired' "
                "WHERE sandbox_scenario IS NULL AND name=%s", ("Sandbox Agency",))
    return len(strays)


def _scenario_agency(cur, scenario):
    cur.execute("SELECT id FROM agencies WHERE sandbox_scenario=%s LIMIT 1", (scenario,))
    r = cur.fetchone()
    return r[0] if r else None


def _brand_tenants(cur, agency_id):
    cur.execute("SELECT tenant_id FROM engagements WHERE agency_id=%s AND status<>'terminated' "
                "ORDER BY tenant_id", (agency_id,))
    return [r[0] for r in cur.fetchall()]


def _scenario_brand_ids(cur, scenario):
    """Scenario's brand tenant ids from non-RLS `tenants` (works under realify_app; excludes directs)."""
    cur.execute("SELECT id FROM tenants WHERE sandbox_scenario=%s AND name NOT LIKE 'Direct Sandbox Brand%%' "
                "ORDER BY id", (scenario,))
    return [r[0] for r in cur.fetchall()]


def _ensure_user(cur, email, tenant_id=None, name=None):
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    r = cur.fetchone()
    if r:
        if tenant_id is not None:
            cur.execute("UPDATE users SET tenant_id=%s WHERE id=%s", (tenant_id, r[0]))
        if name is not None:
            cur.execute("UPDATE users SET name=%s WHERE id=%s", (name, r[0]))
        return r[0]
    cur.execute("INSERT INTO users(email,tenant_id,name,created_at) VALUES(%s,%s,%s,now()::text) RETURNING id",
                (email, tenant_id, name))
    return cur.fetchone()[0]


def load_world(cur, spec, world_key, as_of=None):
    """Build (or RESET) a world IDEMPOTENTLY under `world_key` (reuse or create). Returns state dict."""
    as_of = as_of or _AS_OF
    cleanup_strays(cur)
    brand_specs = _brand_specs(spec)
    ag = _scenario_agency(cur, world_key)
    if ag is None:
        cur.execute("INSERT INTO agencies(name,hq_country,sandbox_scenario) VALUES(%s,%s,%s) RETURNING id",
                    (spec.get("agency_name") or "Realify Pilot Agency", spec["hq_country"], world_key)); ag = cur.fetchone()[0]
    cur.execute("UPDATE agencies SET name=%s WHERE id=%s", (spec.get("agency_name") or "Realify Pilot Agency", ag))  # R15.2: rename REUSED agency to the current world (never leave a stale/placeholder name)
    tenant_ids = _scenario_brand_ids(cur, world_key)    # reuse detection via non-RLS tenants table
    while len(tenant_ids) < len(brand_specs):
        cur.execute("INSERT INTO tenants(name,created_at,provisioned,data_mode,sandbox,tenant_kind,"
                    "sandbox_scenario) VALUES('Sandbox Brand',now()::text,1,'synthetic',1,'sandbox',%s) "
                    "RETURNING id", (world_key,))
        tenant_ids.append(cur.fetchone()[0])
    tenant_ids = tenant_ids[:len(brand_specs)]
    # Self-healing: every brand tenant must have a live engagement under THIS agency (a fresh agency id
    # or truncated engagements — as in the test harness — get reconciled rather than left dangling).
    for t in tenant_ids:
        tenancy.set_brand_scope(cur, [t])
        if _engagement_of(cur, ag, t) is None:
            ops.create_engagement(cur, None, ag, t)
    brands = []
    for idx, (t, bspec) in enumerate(zip(tenant_ids, brand_specs)):
        _seed_brand(cur, ag, t, spec, bspec, idx, as_of)
        brands.append({"tenant_id": t, "name": bspec["name"], "currency": bspec["currency"]})
    loaded_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    cur.execute("UPDATE agencies SET sandbox_loaded_at=%s WHERE id=%s", (loaded_at, ag))
    personas = _wire_personas(cur, world_key, spec, ag, tenant_ids)
    from . import team as _team
    _team.seed_team(cur, world_key, ag, tenant_ids, personas,
                    country=(spec.get("country") or spec.get("hq_country") or "US"))
    tenancy.set_brand_scope(cur, [tenant_ids[0]])
    b0_eng = _engagement_of(cur, ag, tenant_ids[0])
    return {"loaded": True, "scenario": world_key, "world_key": world_key, "seed": spec["seed"],
            "country": spec.get("country") or spec["hq_country"], "currency": spec["currency"],
            "agency_id": ag, "brand_count": len(brands), "brands": brands, "loaded_at": loaded_at,
            "usd_count": sum(1 for b in brands if b["currency"] == "USD"),
            "inr_count": sum(1 for b in brands if b["currency"] != "USD"),
            "direct_brands": personas.get("direct_tenants", []),
            "tenant_id": tenant_ids[0], "engagement_id": b0_eng, "personas": personas}


def load_preset(cur, scenario=DEFAULT_SCENARIO, as_of=None):
    """Load a read-only Realify preset by name (us_pilot | in_pilot | auto_in)."""
    return load_world(cur, SCENARIOS[scenario], scenario, as_of)


def reset_to_seed(cur, scenario=DEFAULT_SCENARIO, as_of=None):
    """Restore a world's pristine state — a deterministic rebuild of the same tenant set."""
    return load_world(cur, SCENARIOS.get(scenario) or _spec_by_key(cur, scenario), scenario, as_of)


def _spec_by_key(cur, world_key):
    """Reconstruct a generated world's spec from its saved params (best-effort reset)."""
    from . import synth
    cur.execute("SELECT params FROM saved_worlds WHERE seed=%s LIMIT 1",
                (world_key[4:] if world_key.startswith("gen-") else world_key,))
    r = cur.fetchone()
    if r and r[0]:
        return synth.spec_from_params(r[0])
    raise KeyError(world_key)


def _wire_personas(cur, world_key, spec, agency_id, tenant_ids):
    """Deterministic persona identities (idempotent by email): Client Lead grant on every brand, Brand Owner on brand[0], direct tenants. Returns ids."""
    lead = _ensure_user(cur, f"sandbox-{world_key}-lead@realify.ai")
    for t in tenant_ids:
        tenancy.set_brand_scope(cur, [t])
        eng = _engagement_of(cur, agency_id, t)
        if eng:
            ops.grant_role(cur, lead, eng, t, lead, "account_manager")
    from . import synth as _synth, locale as _locale
    loc = _locale.get(spec.get("country") or spec.get("hq_country") or "US")
    owner = _ensure_user(cur, f"sandbox-{world_key}-owner@realify.ai", tenant_id=tenant_ids[0],
                         name=_locale.person_name(loc["country"], len(tenant_ids)))
    n_direct = int(spec.get("direct_brands", 1))
    # Direct brands: REAL names + a distinct '::d' scenario tag so _scenario_brand_ids (exact world_key)
    # naturally excludes them (a direct brand has no engagement — never a managed-book brand).
    dkey = world_key + "::d"
    cur.execute("SELECT id FROM tenants WHERE sandbox_scenario=%s ORDER BY id", (dkey,))
    directs = [r[0] for r in cur.fetchall()]
    while len(directs) < n_direct:
        cur.execute("INSERT INTO tenants(name,created_at,provisioned,data_mode,sandbox,tenant_kind,"
                    "sandbox_scenario) VALUES('Sandbox Brand',now()::text,1,'synthetic',1,'sandbox',%s) "
                    "RETURNING id", (dkey,))
        directs.append(cur.fetchone()[0])
    directs = directs[:max(1, n_direct)] if n_direct else directs[:0]
    chan = spec.get("primary_channel", "amazon")
    for j, direct in enumerate(directs):
        tenancy.set_brand_scope(cur, [direct])   # R15 G.5: name direct[0] from the form; else a category-aligned, world-unique bank name (managed+direct share one slot space, hence len(tenant_ids)+j)
        dcat, dname = _synth.brand_slot(loc["country"], spec["categories"], len(tenant_ids) + j)
        cur.execute("UPDATE tenants SET name=%s WHERE id=%s", (((spec.get("direct_brand_name") or "").strip() if j == 0 else "") or dname, direct))
        _seed_skus(cur, direct, {**spec, "primary_category": dcat}, _rng(f"{spec['seed']}-direct-{j}"), chan)   # R11.1: fees + country
    direct_uid = _ensure_user(cur, f"sandbox-{world_key}-direct@realify.ai",
                              tenant_id=(directs[0] if directs else None),
                              name=_locale.person_name(loc["country"], len(tenant_ids) + 1))
    return {"client_lead_uid": lead, "brand_owner_uid": owner, "brand_owner_tenant": tenant_ids[0],
            "direct_uid": direct_uid, "direct_tenant": (directs[0] if directs else None),
            "direct_tenants": directs}


def personas(cur, staff_email=None, scenario=DEFAULT_SCENARIO):
    """Back-compat entry (T-P7-08): ensure loaded, return P7-shape identities (managed/direct/staff)."""
    st = load_preset(cur, scenario)
    p = st["personas"]
    return {"staff_user": p["client_lead_uid"], "admin_persona": "Realify Admin",
            "managed_tenant": st["tenant_id"], "managed_engagement": st["engagement_id"],
            "direct_tenant": p["direct_tenant"], **p}


def current_world_key(cur):
    """The most-recently-loaded world (preset or generated), so hub reads reflect whatever is live."""
    cur.execute("SELECT sandbox_scenario FROM agencies WHERE sandbox_scenario IS NOT NULL "
                "AND sandbox_scenario<>'retired' AND sandbox_loaded_at IS NOT NULL "
                "ORDER BY sandbox_loaded_at DESC LIMIT 1")
    r = cur.fetchone()
    return r[0] if r else None


def _seed_of(key):
    if key in SCENARIOS:
        return SCENARIOS[key]["seed"]
    return key[4:] if key and key.startswith("gen-") else (key or "")


def persona_targets(cur, scenario=None):
    """The ids + destination URLs each persona doorway routes into (read WITHOUT rebuilding). None if no world is loaded."""
    scenario = scenario or current_world_key(cur)
    if not scenario:
        return None
    ag = _scenario_agency(cur, scenario)
    if ag is None:
        return None
    brands = _scenario_brand_ids(cur, scenario)
    if not brands:
        return None

    def uid(email):
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        r = cur.fetchone()
        return r[0] if r else None

    cur.execute("SELECT id FROM tenants WHERE sandbox_scenario=%s ORDER BY id", (scenario + "::d",))
    directs = [r[0] for r in cur.fetchall()]
    return {"client_lead_uid": uid(f"sandbox-{scenario}-lead@realify.ai"),
            "brand_owner_uid": uid(f"sandbox-{scenario}-owner@realify.ai"),
            "brand_owner_tenant": brands[0], "brands": brands,
            "direct_uid": uid(f"sandbox-{scenario}-direct@realify.ai"),
            "direct_tenant": (directs[0] if directs else None), "direct_tenants": directs,
            "admin_url": "/ops/agency/admin", "queue_url": "/agency/console",
            "portal_url": f"/brand/portal/{brands[0]}", "direct_url": "/", "agency_id": str(ag)}


def sandbox_state(cur, scenario=None):
    """State-header data for the hub: what's loaded, when, next reset. {loaded:False} if nothing yet."""
    scenario = scenario or current_world_key(cur)
    if not scenario:
        return {"loaded": False, "scenario": None, "next_reset": _next_reset()}
    ag = _scenario_agency(cur, scenario)
    if ag is None:
        return {"loaded": False, "scenario": scenario, "next_reset": _next_reset()}
    cur.execute("SELECT name, sandbox_loaded_at FROM agencies WHERE id=%s", (ag,))
    agrow = cur.fetchone() or ["Agency", None]
    agency_name, loaded_at = agrow[0], agrow[1]
    brand_ids = _scenario_brand_ids(cur, scenario)
    if brand_ids:
        tenancy.set_brand_scope(cur, brand_ids)          # decisions is RLS-forced; scope to the book
    cur.execute("SELECT value FROM tenant_settings WHERE tenant_id=%s AND key='country'", (brand_ids[0],)) if brand_ids else None  # R15.1: real country, not decisions ccy
    wc = ((cur.fetchone() or ["US"])[0] if brand_ids else "US"); wp = _country.profile(wc)
    brands = []
    for t in brand_ids:
        cur.execute("SELECT name FROM tenants WHERE id=%s", (t,))
        nm = (cur.fetchone() or ["?"])[0]
        brands.append({"tenant_id": t, "name": nm, "currency": wp["currency"], "symbol": wp["symbol"]})
    directs = []
    cur.execute("SELECT id, name FROM tenants WHERE sandbox_scenario=%s ORDER BY id", (scenario + "::d",))
    for t, nm in cur.fetchall():
        directs.append({"tenant_id": t, "name": nm, "symbol": wp["symbol"]})
    inr = sum(1 for b in brands if b["currency"] != "USD")
    return {"loaded": bool(brands), "scenario": scenario, "seed": _seed_of(scenario),
            "country": wc, "currency": wp["currency"], "symbol": wp["symbol"],
            "agency_id": ag, "agency_name": agency_name, "brand_count": len(brands), "brands": brands,
            "directs": directs, "loaded_at": loaded_at,
            "usd_count": sum(1 for b in brands if b["currency"] == "USD"), "inr_count": inr,
            "next_reset": _next_reset()}


def _next_reset():
    """Nightly reset is NOT yet scheduled (no cron). Report that honestly rather than a fake time."""
    return {"scheduled": False, "note": "Manual reset only — no nightly job configured yet."}


def advance_clock(cur, scenario=None, days=30):
    """World control: advance the clock `days`, regenerate each brand's decisions at the new as-of (fx re-locked)."""
    scenario = scenario or current_world_key(cur)
    ag = _scenario_agency(cur, scenario) if scenario else None
    if ag is None:
        return {"ok": False, "error": "Load a world first."}
    as_of = _AS_OF + datetime.timedelta(days=int(days))
    spec = SCENARIOS.get(scenario) or {"fx_inr_ppm": 83_500_000}
    for t in _scenario_brand_ids(cur, scenario):
        tenancy.set_brand_scope(cur, [t])
        cur.execute("SELECT impact_currency FROM decisions WHERE tenant_id=%s LIMIT 1", (t,))
        cr = cur.fetchone()
        currency = cr[0] if cr else "USD"
        if currency != "USD":
            fx.lock_rate(cur, as_of, currency, spec["fx_inr_ppm"])
        decisions.generate(cur, t, currency, as_of)
        ledger.append(cur, t, None, "sandbox.clock_advance", payload={"days": int(days), "as_of": str(as_of)})
    return {"ok": True, "scenario": scenario, "as_of": str(as_of), "days": int(days)}


# (R11.1: the old hub-bound guided_run() is retired — the guided run is now the teleprompter in
#  realify/agency/guided.py + the /api/ops/sandbox/guided-run/* routes, driving the real surfaces.)


# ---- injectors: mutate the seeded world deterministically (unchanged; ledger is written by callers) ----
def inject_undercut(cur, tenant_id, hero="SB-000", drop_pct=10):
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute("UPDATE seller_skus SET buybox_pct=GREATEST(buybox_pct-%s,0) WHERE tenant_id=%s AND asin=%s",
                (drop_pct, tenant_id, hero))
    return {"hero": hero, "drop_pct": drop_pct}


def inject_stockout(cur, tenant_id):
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute("UPDATE seller_skus SET days_of_cover=3 WHERE tenant_id=%s", (tenant_id,))
    return {"days_of_cover": 3}


def inject_ad_overspend(cur, tenant_id):
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute("UPDATE seller_skus SET tacos=tacos+20 WHERE tenant_id=%s", (tenant_id,))
    return {"tacos_delta": 20}


def inject_fx_swing(cur, tenant_id=None, as_of=None, ppm=83_500_000, quote="INR", pct=-6):
    return fx.lock_rate(cur, as_of or _AS_OF, quote, int(ppm * (1 + pct / 100.0)))
