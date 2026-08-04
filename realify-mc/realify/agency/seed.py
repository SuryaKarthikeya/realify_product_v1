"""Sandbox canary seed (P0.5): 3 agencies x 12 brands = 36 sandbox brand-tenants on the EXISTING
tenants model (agency tables land in P1). Each brand is flagged sandbox=1 and carries a canary string
CANARY_{slug}_{8hex} in ROWS_PER_BRAND of its own seller_skus rows, so the cross-tenant fuzz (T-P1-05)
can scan API response bodies for FOREIGN canaries and catch any leak across the tenant boundary.

Deterministic + idempotent: slugs and canaries derive from a hash, tenants are found-or-created by
their slug-name, and SKU rows upsert by PK (tenant_id, asin) — re-running the seed changes nothing.
"""
import hashlib

from .. import db
from ..repositories.seller_repo import SellerRepository

AGENCIES = 3
BRANDS_PER_AGENCY = 12
ROWS_PER_BRAND = 20
_NAME_PREFIX = "[sandbox] "


def brand_slug(agency_i, brand_i):
    return f"agy{agency_i}-brand{brand_i:02d}"


def canary_for(slug):
    return f"CANARY_{slug}_{hashlib.sha256(slug.encode()).hexdigest()[:8]}"


def all_slugs():
    return [brand_slug(a, b) for a in range(AGENCIES) for b in range(BRANDS_PER_AGENCY)]


def _find_or_create_tenant(con, slug):
    name = _NAME_PREFIX + slug
    row = con.execute("SELECT id FROM tenants WHERE name=? AND sandbox=1", (name,)).fetchone()
    if row:
        return dict(row)["id"], False
    tid = db.create_returning_id(
        con, "INSERT INTO tenants(name,created_at,provisioned,data_mode,sandbox) VALUES(?,?,1,'synthetic',1)",
        (name, db.now_iso()))
    return tid, True


def seed(con):
    """Idempotently seed the 36 sandbox canary brands. Returns a summary dict (agencies, brands,
    created, rows_per_brand, canaries[])."""
    sellers = SellerRepository(con)
    created = 0
    canaries = []
    for a in range(AGENCIES):
        for b in range(BRANDS_PER_AGENCY):
            slug = brand_slug(a, b)
            canary = canary_for(slug)
            canaries.append(canary)
            tid, is_new = _find_or_create_tenant(con, slug)
            created += 1 if is_new else 0
            for i in range(ROWS_PER_BRAND):
                asin = f"{slug}-SKU{i:02d}"
                sellers.upsert_full(tid, {
                    "asin": asin, "internal_sku": asin, "channel": "amazon",
                    "title": f"{canary} sample widget {i:02d}", "category": "Sandbox",
                    "price": 1000, "cogs": 400, "units_month": 10,
                })
    con.commit()
    return {"agencies": AGENCIES, "brands": len(canaries), "created": created,
            "rows_per_brand": ROWS_PER_BRAND, "canaries": canaries}
