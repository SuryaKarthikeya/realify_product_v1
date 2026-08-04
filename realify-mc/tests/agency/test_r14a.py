"""R14a (Postgres/agency): the custom brand name propagates to the actual tenant + role picker, and a
reused tenant is RENAMED to the current world (no stale name) — Part B. (Part A is hub JS, covered
hermetically in tests/test_r14a.py.)"""
from realify.agency import synth, sandbox


def test_custom_brand_name_becomes_the_tenant_name(owner_conn):
    cur = owner_conn.cursor()
    st = synth.generate_world(cur, {"country": "US", "seed": "r14a-name", "brands_per_agency": 3,
                                    "direct_brands": 0, "brand_name": "Zephyr Goods"})
    owner_conn.commit()
    b0 = st["brands"][0]
    assert b0["name"] == "Zephyr Goods"                          # state (→ role picker) shows the custom name
    cur.execute("SELECT name FROM tenants WHERE id=%s", (b0["tenant_id"],))
    assert cur.fetchone()[0] == "Zephyr Goods"                   # ...and the tenant it points to is actually named X
    # sandbox_state (what fillPickers reads) reflects it too
    ss = sandbox.sandbox_state(cur, synth.world_key("r14a-name"))
    assert ss["brands"][0]["name"] == "Zephyr Goods"


def test_reused_tenant_is_renamed_to_current_world(owner_conn):
    cur = owner_conn.cursor()
    p = {"country": "US", "seed": "r14a-reuse", "brands_per_agency": 3, "direct_brands": 0}
    a = synth.generate_world(cur, {**p, "brand_name": "First Co"}); owner_conn.commit()
    tid = a["brands"][0]["tenant_id"]
    # regenerate the SAME world (reuses the tenant records) with a DIFFERENT first-brand name
    b = synth.generate_world(cur, {**p, "brand_name": "Second Co"}); owner_conn.commit()
    assert b["brands"][0]["tenant_id"] == tid                    # same tenant record reused
    cur.execute("SELECT name FROM tenants WHERE id=%s", (tid,))
    assert cur.fetchone()[0] == "Second Co"                      # renamed to the CURRENT world (not stale "First Co")
