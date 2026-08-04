"""R17 Part D (Postgres/agency) — catalog rescue → first-class hub reuse. Asserted on the ENDPOINTS the
hub posts to and the provisioned DB (never a helper): the captured-seed list, generate-from-seed
provisioning a sandbox seller tenant whose seller_skus carry the captured ASINs/titles/categories, and
the hub HTML rendering the rescued pick.
"""
import json

_CATALOG = [
    {"asin": "B0RESCUE01", "title": "Cedar Storage Box", "category": "Home & Kitchen", "cogs": 8.0, "price": 24.0},
    {"asin": "B0RESCUE02", "title": "Cedar Spice Rack", "category": "Home & Kitchen", "cogs": 6.5, "price": 19.0},
    {"asin": "B0RESCUE03", "title": "Cedar Pet Bed", "category": "Pet Supplies", "cogs": 11.0, "price": 39.0},
    {"asin": "B0RESCUE04", "title": "Cedar Leash", "category": "Pet Supplies", "cogs": 4.0, "price": 14.0},
    {"asin": "B0RESCUE05", "title": "Cedar Trowel", "category": "Outdoor", "cogs": 3.5, "price": 12.0},
    {"asin": "B0RESCUE06", "title": "Cedar Planter", "category": "Outdoor", "cogs": 9.0, "price": 29.0},
]


def _seed_capture(cur, brand="Cedar & Co"):
    cur.execute(
        "INSERT INTO captured_seeds(name,country,brand_name,sku_count,catalog,source_ref,created_at) "
        "VALUES(%s,%s,%s,%s,%s::json,%s,%s) RETURNING id",
        (f"{brand} · {len(_CATALOG)} SKUs", "US", brand, len(_CATALOG),
         json.dumps(_CATALOG), "9999", "2026-07-17"))
    return cur.fetchone()[0]


def test_captured_seeds_list_endpoint(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    sid = _seed_capture(cur); owner_conn.commit()
    r = client.get("/api/ops/sandbox/captured-seeds", headers=H)
    assert r.status_code == 200
    seeds = r.json()["seeds"]
    row = next((s for s in seeds if s["id"] == sid), None)
    assert row and row["brand_name"] == "Cedar & Co" and row["sku_count"] == 6 and row["country"] == "US"


def test_generate_from_seed_provisions_captured_catalog(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    sid = _seed_capture(cur); owner_conn.commit()
    r = client.post("/api/ops/sandbox/generate-from-seed", headers=H, json={"seed_id": sid})
    assert r.status_code == 200 and r.json()["ok"] and r.json()["redirect"] == "/"
    tid = r.json()["tenant_id"]
    owner_conn.rollback()
    # the provisioned tenant is a reaper-safe sandbox tenant
    cur.execute("SELECT tenant_kind, sandbox, sandbox_scenario FROM tenants WHERE id=%s", (tid,))
    kind, sbx, scen = cur.fetchone()
    assert kind == "sandbox" and sbx and scen == f"captured-{sid}"      # exclusion/reaper convention holds
    # its seller_skus carry the captured ASINs / titles / categories
    cur.execute("SELECT asin, title, category FROM seller_skus WHERE tenant_id=%s ORDER BY asin", (tid,))
    got = {a: (t, c) for a, t, c in cur.fetchall()}
    for row in _CATALOG:
        assert row["asin"] in got, f"{row['asin']} missing from provisioned catalog"
        assert got[row["asin"]] == (row["title"], row["category"])
    # idempotent: a second provision reuses the SAME tenant (no pile-up)
    r2 = client.post("/api/ops/sandbox/generate-from-seed", headers=H, json={"seed_id": sid})
    assert r2.json()["tenant_id"] == tid


def test_hub_renders_captured_seed_pick(agency_client, owner_conn):
    from realify import superlogin
    client, H = agency_client
    cur = owner_conn.cursor()
    _seed_capture(cur, brand="Rescue Brand X"); owner_conn.commit()
    token = superlogin._ser().dumps({"email": "staff@realify.ai"})       # mint the superlogin surface cookie
    client.cookies.set("superlogin_session", token)
    page = client.get("/superlogin/hub").text
    assert "Seed from a real catalog" in page                            # the section renders
    assert "Rescue Brand X" in page and "6 SKUs" in page                 # the rescued catalog is a pick
    assert 'data-seed=' in page                                          # wired to generate-from-seed
