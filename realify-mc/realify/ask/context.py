"""The per-tenant context pack — what a model (stub today, self-hosted later) is grounded on.

Kept small and cheap here: identity + currency + catalog size + a provisioning flag. The narrator uses it
for framing (currency symbol, "you haven't connected data yet"); a real model would receive it as system
context alongside the tool facts. Assembled defensively — a failure yields a minimal pack, never an error.
"""


def build(tenant_id):
    pack = {"tenant_id": tenant_id, "tenant_name": None, "sku_count": 0,
            "symbol": "₹", "currency": "INR", "provisioned": False}
    try:
        from realify import db, country
        from realify.repositories.seller_repo import SellerRepository
        con = db.connect()
        try:
            t = db.get_tenant(con, tenant_id) or {}
            pack["tenant_name"] = t.get("name")
            pack["provisioned"] = bool(t.get("provisioned"))
            pack["sku_count"] = SellerRepository(con).count(tenant_id)
        finally:
            con.close()
        prof = country.tenant_profile(tenant_id) or {}
        pack["symbol"] = prof.get("symbol", pack["symbol"])
        pack["currency"] = prof.get("currency", pack["currency"])
    except Exception:
        pass
    return pack
