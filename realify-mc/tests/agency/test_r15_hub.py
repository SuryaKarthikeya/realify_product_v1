"""R15 Part G.5 (Postgres/agency): direct-vs-managed generation is explicit.
 · a Brand name with NO agency ⇒ a DIRECT brand (its own tenant, no agency book/grant)
 · a Brand name WITH an agency ⇒ a MANAGED brand under that agency
The hub layer (routers/agency_sandbox_gen.sb_generate) decides which of `brand_name` / `direct_brand_name`
is set; here we exercise the synth+sandbox primitives those map to.
"""
from realify.agency import synth, sandbox


def test_brand_name_without_agency_creates_a_direct_brand(owner_conn):
    cur = owner_conn.cursor()
    spec = synth.spec_from_params({"country": "US", "seed": "r15g5-direct", "brands_per_agency": 2,
                                   "direct_brands": 0, "direct_brand_name": "Solo Goods"})
    assert spec["direct_brand_name"] == "Solo Goods" and spec["direct_brands"] >= 1   # a direct slot is ensured
    sandbox.load_world(cur, spec, synth.world_key("r15g5-direct")); owner_conn.commit()
    ss = sandbox.sandbox_state(cur, synth.world_key("r15g5-direct"))
    assert any(d["name"] == "Solo Goods" for d in ss.get("directs", []))     # named as a DIRECT brand
    assert all(b["name"] != "Solo Goods" for b in ss.get("brands", []))      # NOT in the managed book


def test_brand_name_with_agency_creates_a_managed_brand(owner_conn):
    cur = owner_conn.cursor()
    spec = synth.spec_from_params({"country": "US", "seed": "r15g5-managed", "brands_per_agency": 2,
                                   "direct_brands": 0, "brand_name": "Book Brand", "agency_name": "Acme Agency"})
    assert spec["brands"][0]["name"] == "Book Brand" and not spec.get("direct_brand_name")
    sandbox.load_world(cur, spec, synth.world_key("r15g5-managed")); owner_conn.commit()
    ss = sandbox.sandbox_state(cur, synth.world_key("r15g5-managed"))
    assert ss["brands"][0]["name"] == "Book Brand"                            # named MANAGED brand
    assert all(d["name"] != "Book Brand" for d in ss.get("directs", []))      # NOT a direct brand
