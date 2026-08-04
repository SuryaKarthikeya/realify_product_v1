"""R11.1 (Postgres/agency): the scope-switched seller app inherits the BRAND's country (currency +
marketplace + realistic fees) — the Alpine Kitchen bug — and the guided-run teleprompter drives the
real surfaces + hops personas across the real world."""
import re

from realify import country
from realify.agency import sandbox, guided, tenancy


# ---------------- G1/G2: brand country setting + realistic fees on scope-switched brands ----------------

def test_us_brand_inherits_us_locale_and_sane_fees(owner_conn):
    cur = owner_conn.cursor()
    st = sandbox.load_preset(cur, "us_pilot"); owner_conn.commit()
    prof = country.profile("US")
    assert prof["symbol"] == "$" and prof["marketplace"] == "amazon.com"   # US profile: $ / US marketplace, no ₹
    for b in st["brands"]:
        tid = b["tenant_id"]
        # brand country setting written to the shared DB so the seller app's /api/me localizes (prod: one RDS)
        cur.execute("SELECT value FROM tenant_settings WHERE tenant_id=%s AND key='country'", (tid,))
        row = cur.fetchone()
        assert row and row[0] == "US"                            # was unset → country.DEFAULT='IN' (the bug)
        tenancy.set_brand_scope(cur, [tid])
        cur.execute("SELECT price,referral_fee,fba_fee,net_margin_pct FROM seller_skus WHERE tenant_id=%s", (tid,))
        rows = cur.fetchall()
        assert rows
        for price, ref, fba, margin in rows:
            assert ref is not None and fba is not None and (ref + fba) < price   # per-unit fees < price
            assert -20 <= margin <= 80, f"implausible margin {margin}% (price {price}, fees {ref}+{fba})"


def test_india_brand_inherits_inr_locale(owner_conn):
    cur = owner_conn.cursor()
    st = sandbox.load_preset(cur, "in_pilot"); owner_conn.commit()
    tid = st["brands"][0]["tenant_id"]
    cur.execute("SELECT value FROM tenant_settings WHERE tenant_id=%s AND key='country'", (tid,))
    assert cur.fetchone()[0] == "IN"
    prof = country.profile("IN")
    assert prof["symbol"] == "₹" and prof["marketplace"] == "amazon.in"


# ---------------- F: guided-run drives the real world ----------------

def test_guided_build_run_real_surfaces_and_persona_flip(owner_conn):
    cur = owner_conn.cursor()
    st = sandbox.load_preset(cur, "us_pilot"); owner_conn.commit()
    b0 = st["brands"][0]["tenant_id"]
    for name in ("customer", "vc"):
        steps = guided.build_run(cur, None, name)
        assert steps and all(s["nav"].startswith("/") for s in steps)     # every step → a real surface
        assert any(s["nav"] == f"/agency/brand/{b0}" for s in steps)      # drills into the real brand's five-lens
        assert len({s["persona"] for s in steps}) >= 2                    # hops personas
    assert any(s["inject"] for s in guided.build_run(cur, None, "customer"))   # injector step fires inline


def test_guided_routes_start_next_exit(agency_client, owner_conn):
    client, H = agency_client
    sandbox.load_preset(owner_conn.cursor(), "us_pilot"); owner_conn.commit()
    # START → lands on step 1's real surface + arms the teleprompter
    r = client.post("/api/ops/sandbox/guided-run/start", headers=H, json={"name": "customer"})
    assert r.status_code == 200 and r.json()["redirect"] == "/agency/console"
    # the bar now rides the real surface
    body = client.get("/agency/console").text
    assert "Guided run" in body and "r9guided" in body and "Next →" in body
    # NEXT → real navigation to the drill-in (URL changes, not same-page state)
    r2 = client.post("/api/ops/sandbox/guided-run/next", headers=H)
    assert r2.status_code == 200 and re.match(r"^/agency/brand/\d+$", r2.json()["redirect"])
    # EXIT → bar cleared, but the surface still serves (stays on the current page)
    assert client.post("/api/ops/sandbox/guided-run/exit", headers=H).json()["ok"] is True
    assert "r9guided" not in client.get("/agency/console").text
