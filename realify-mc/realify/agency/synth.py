"""R9 Part A/B — parametric world synthesizer. Turns generator params into a deterministic SPEC that the
existing sandbox seeding path (realify.agency.sandbox.load_world) consumes, so we REUSE the seller synth
stack + sandbox feeders rather than duplicating them. The two committed pilots (us_pilot / in_pilot) are
just fixed param sets run through the same builder.

A world = ONE agency (country-neutral) with N managed brands + M direct brands, all of ONE country
(country is a brand property). Every tenant is tenant_kind=sandbox, VERIFY-/sandbox-named (reaper-safe),
excluded from aggregates. Same country+params+seed ⇒ byte-identical world."""
import json

from . import locale

_MAX_SKUS = 2000


def brand_slot(country, cats, global_idx):
    """(primary_category, display_name) for the `global_idx`-th tenant in a world. Managed and direct
    brands share ONE index space, so names are UNIQUE world-wide and each name is drawn from a bank
    ALIGNED to the brand's primary category (R15 Part B). Deterministic — index-driven, no random/Date."""
    cat = cats[global_idx % len(cats)]
    return cat, locale.brand_name_for(country, cat, global_idx // len(cats))


def spec_from_params(p):
    """Build a deterministic SPEC dict from generator params. Locale-driven (currency, channels, COGS
    bands, product categories, brand names). `p` keys: country, categories, sku_count, brands_per_agency,
    direct_brands, depth ('rich'|'fast'), moments (list), seed, agency_name."""
    country = p["country"]
    if not locale.is_valid(country):
        raise ValueError(f"country must be one of {locale.VALID_COUNTRIES}")
    loc = locale.get(country)
    cats = p.get("categories") or loc["categories"][:3]
    n_brands = max(1, int(p.get("brands_per_agency", 8)))
    n_direct = max(0, int(p.get("direct_brands", 1)))
    sku_count = max(4, min(_MAX_SKUS, int(p.get("sku_count", 480))))
    per_brand = max(4, sku_count // max(1, n_brands + n_direct))
    seed = (p.get("seed") or "gen-default").strip()
    moments = set(p.get("moments") or [])
    depth = "fast" if p.get("depth") == "fast" else "rich"
    expired_n = 2 if "expired_conn" in moments else 0
    # connections: locale marketplaces (connected) + the ads platform; flagged brands expire amazon_ads
    conns = [(c.lower().replace(" ", "_").replace(".", "_"), "connected") for c in loc["channels"]]
    conns.append(("amazon_ads", "connected"))
    # Each brand carries a PRIMARY category + a category-aligned, world-unique name (R15 Part B); the
    # category also steers _seed_skus so the catalog (and the Category Analyst) agree with the name.
    brands = []
    for i in range(n_brands):
        cat, nm = brand_slot(country, cats, i)
        brands.append({"name": nm, "category": cat, "currency": loc["currency"], "expired_conn": i < expired_n})
    # R14 Part B: a custom "name this brand" input names the first managed brand — it then shows in the
    # role picker (and the fleet/drill-in), because _seed_brand renames the (reused) tenant to this name.
    # Only the NAME is overridden; the bank-assigned primary category stays so the SKUs remain coherent.
    bn = (p.get("brand_name") or "").strip()
    if bn and brands:
        brands[0]["name"] = bn
    # R15 Part G.5 — a Brand name with NO agency names a DIRECT brand (not a managed one); ensure a direct
    # slot exists to carry it. (The hub layer decides direct-vs-managed and sets exactly one of the names.)
    dbn = (p.get("direct_brand_name") or "").strip()
    if dbn:
        n_direct = max(1, n_direct)
    return {
        "seed": seed, "country": country, "currency": loc["currency"], "hq_country": country,
        "sku_count": per_brand, "categories": cats, "prices": loc["prices"],
        "cogs_lo": loc["cogs_lo"], "cogs_hi": loc["cogs_hi"], "primary_channel": loc["primary_channel"],
        "channels": loc["channels"], "connections": conns, "envelope": "Full Operate",
        "fx_inr_ppm": loc["fx_ppm"], "brands": brands, "direct_brands": n_direct,
        "direct_brand_name": dbn,
        "depth": depth, "moments": sorted(moments), "total_sku_target": sku_count,
        "agency_name": (p.get("agency_name") or "").strip() or locale.agency_name(country, seed),
    }


def world_key(seed):
    """The sandbox_scenario tag a generated world is stored under (distinct from Realify presets)."""
    return f"gen-{seed}"


def generate_world(cur, params):
    """Build (or reset) a generated world deterministically. Returns the sandbox state dict."""
    from . import sandbox
    spec = spec_from_params(params)
    return sandbox.load_world(cur, spec, world_key(spec["seed"]))


# ---- saved worlds (Part B: worlds a tester generated + named; Realify presets are separate/read-only) ----
def save_world(cur, owner_email, name, params):
    spec = spec_from_params(params)
    cur.execute(
        "INSERT INTO saved_worlds(owner_email,name,seed,country,params) VALUES(%s,%s,%s,%s,%s::jsonb) "
        "ON CONFLICT (owner_email,name) DO UPDATE SET seed=EXCLUDED.seed, country=EXCLUDED.country, "
        "params=EXCLUDED.params RETURNING id",
        (owner_email, name, spec["seed"], spec["country"], json.dumps(params)))
    return cur.fetchone()[0]


def list_saved(cur, owner_email):
    cur.execute("SELECT name, seed, country, params, created_at FROM saved_worlds WHERE owner_email=%s "
                "ORDER BY created_at DESC", (owner_email,))
    return [{"name": n, "seed": s, "country": c, "params": p, "created_at": str(ca)}
            for n, s, c, p, ca in cur.fetchall()]
