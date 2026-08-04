"""R11 (Postgres/agency): the fleet-grid data resolution FIX (grant-independent — the '0 clients' bug),
$-at-stake per brand + health sort, the scope-switcher drill-in with REAL server-side envelope
enforcement (a suggest-only lens can only be proposed, never executed), and the retired queue redirect."""
import datetime
import re
import secrets

from realify import auth as core_auth
from realify.agency import ops, fleet_data, connections, tenancy, fx, sandbox
from realify.agency.actor import resolve_actor
from realify.pdp import ENVELOPES

UTC = datetime.timezone.utc


def _login(client, email=None):
    email = email or f"r11-{secrets.token_hex(4)}@x.com"
    uid, _ = core_auth.signup(email, "password1", "R11 Org")
    assert client.post("/api/login", json={"email": email, "password": "password1"}).status_code == 200
    return uid


def _brand(cur, ag, currency="USD", threshold=1_000_000):
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('BR',now()::text,1) RETURNING id")
    t = cur.fetchone()[0]
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status,maker_checker_threshold_usd_minor,"
                "brand_cosign_threshold_usd_minor) VALUES(%s,%s,'active',%s,0) RETURNING id", (ag, t, threshold))
    return t, cur.fetchone()[0]


def _decision(cur, t, lens, impact_usd, signal, fx_id=None, ccy="USD", impact_minor=None):
    cur.execute("INSERT INTO decisions(tenant_id,lens,kind,impact_minor,impact_currency,fx_rate_id,"
                "impact_usd_minor,confidence,signal,status) VALUES(%s,%s,%s,%s,%s,%s,%s,80,%s,'open')",
                (t, lens, "bid" if lens == "ads" else lens, impact_minor or impact_usd, ccy, fx_id, impact_usd, signal))


# ---------------- the "0 clients" fix: grant-INDEPENDENT resolution ----------------

def test_fleet_data_resolves_brands_grant_independent(owner_conn):
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('FleetAg') RETURNING id"); ag = cur.fetchone()[0]
    tA, _ = _brand(cur, ag); tB, _ = _brand(cur, ag); tC, _ = _brand(cur, ag)
    owner_conn.commit()
    # resolve WITHOUT any grants (agency_ids=[]) via a brand's session tid — the console's old grant-only
    # path returned 0 here; the fix resolves the agency from engagements.
    agency_id, name = fleet_data.resolve_agency(cur, uid=10_000_000, tid=tA, agency_ids=[])
    assert str(agency_id) == str(ag) and name == "FleetAg"
    ids = fleet_data.agency_brand_ids(cur, ag)
    assert set(ids) == {tA, tB, tC}                                  # ALL brands, not grant-scoped


def test_fleet_data_under_rls_app_role(owner_conn, app_conn):
    """The fleet route runs as realify_app (RLS FORCED). agency_brand_ids reads the RLS-forced
    `engagements` table, so it MUST run in the SAME transaction as resolve_actor (which sets the
    app.actor_user_id GUC the selfread policy needs). A rollback in between returns 0 rows — the live
    '0 clients' bug. This exercises the contract under the non-bypass role (owner tests wouldn't catch it)."""
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('RlsAg') RETURNING id"); ag = cur.fetchone()[0]
    tA, engA = _brand(cur, ag); tB, engB = _brand(cur, ag)
    cur.execute("INSERT INTO users(email,created_at) VALUES(%s,now()::text) RETURNING id",
                (f"rls-{secrets.token_hex(3)}@x.com",))
    u = cur.fetchone()[0]
    ops.grant_role(cur, u, engA, tA, u, "account_manager")           # the sandbox operator holds grants on
    ops.grant_role(cur, u, engB, tB, u, "account_manager")           # every brand in its agency (its book)
    owner_conn.commit()
    ac = app_conn.cursor()
    ctx = resolve_actor(ac, u)                                        # sets app.actor_user_id (txn-local)
    agency_id, _ = fleet_data.resolve_agency(ac, u, None, list(ctx.agency_ids))
    ids = fleet_data.agency_brand_ids(ac, agency_id)                  # SAME txn -> GUC live -> brands resolve
    app_conn.rollback()
    assert str(agency_id) == str(ag) and set(ids) == {tA, tB}        # both brands (0 here was the live bug)
    # PROVE the rollback bug: without the actor GUC in scope, RLS returns nothing (the "0 clients" symptom)
    ac2 = app_conn.cursor()
    assert fleet_data.agency_brand_ids(ac2, agency_id) == []          # no resolve_actor first -> 0 rows
    app_conn.rollback()


def test_fresh_member_reads_book_without_grant_under_rls(owner_conn, app_conn):
    """R18.7: a fresh agency admin holds MEMBERSHIP but no per-brand grant. Under the runtime role
    (realify_app, RLS FORCED) the membership-based engagements selfread policy (migration 0037) must let
    them resolve their book — else the fleet is empty and /agency/data-sources 403s the instant they
    onboard a brand. Owner-role tests miss this (bypass), so assert under app_conn. Fail-closed w/o GUC."""
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('MemAg') RETURNING id"); ag = cur.fetchone()[0]
    tA, _ = _brand(cur, ag); tB, _ = _brand(cur, ag)
    cur.execute("INSERT INTO users(email,created_at) VALUES(%s,now()::text) RETURNING id",
                (f"mem-{secrets.token_hex(3)}@x.com",)); u = cur.fetchone()[0]
    cur.execute("INSERT INTO agency_members(agency_id,user_id,role) VALUES(%s,%s,'agency_admin')", (ag, u))
    owner_conn.commit()                                              # membership only — NO grant
    ac = app_conn.cursor()
    resolve_actor(ac, u)                                            # sets app.actor_user_id GUC (no grants exist)
    agency_id, _ = fleet_data.resolve_agency(ac, u, None, [])       # resolves via agency_members
    ids = fleet_data.agency_brand_ids(ac, agency_id)                # visible via the MEMBERSHIP policy
    app_conn.rollback()
    assert str(agency_id) == str(ag) and set(ids) == {tA, tB}, ids  # both brands despite no grant (was [])
    ac2 = app_conn.cursor()
    assert fleet_data.agency_brand_ids(ac2, ag) == []               # no GUC -> fail-closed
    app_conn.rollback()


def test_ensure_demo_brand_attaches_and_fully_populates(agency_client, owner_conn):
    """R19: a REAL agency gets ONE synthesized SAMPLE brand in its fleet, and finalize_world populates
    ALL lenses so it's actually useful — Profit&Ads (ad_performance), the campaign ad-graph
    (ad_entity_perf, mapped → the ƒ modal / RENDERED_OK), and the Intelligence cards. Idempotent; a
    sandbox/preset agency gets none. Uses agency_client so db.connect() (finalize_world) hits the harness PG."""
    from realify.agency import demo, lens_synth
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('DemoCo') RETURNING id"); ag = cur.fetchone()[0]
    owner_conn.commit()
    t, needs = demo.ensure_demo_brand(cur, ag); owner_conn.commit()
    assert t is not None and needs is True
    cur.execute("SELECT tenant_kind, sandbox_scenario FROM tenants WHERE id=%s", (t,)); kind, tag = cur.fetchone()
    assert kind == "sandbox" and tag == f"agency-demo:{ag}"
    cur.execute("SELECT count(*) FROM decisions WHERE tenant_id=%s", (t,)); assert cur.fetchone()[0] > 0
    assert t in fleet_data.agency_brand_ids(cur, ag)                 # in the fleet book
    lens_synth.finalize_world([t])                                   # populate the other lenses (post-commit)
    owner_conn.rollback()                                            # fresh snapshot to see finalize's commits
    cur.execute("SELECT count(*) FROM ad_entity_perf WHERE tenant_id=%s AND internal_sku IS NOT NULL", (t,))
    assert cur.fetchone()[0] > 0                                     # mapped ad-graph → RENDERED_OK → ƒ icons
    cur.execute("SELECT count(*) FROM ad_performance WHERE tenant_id=%s", (t,)); assert cur.fetchone()[0] > 0  # Profit&Ads
    cur.execute("SELECT count(*) FROM cards WHERE tenant_id=%s", (t,)); assert cur.fetchone()[0] > 0            # Intelligence
    t2, needs2 = demo.ensure_demo_brand(cur, ag)                     # idempotent — same tenant, now finalized
    assert t2 == t and needs2 is False
    cur.execute("INSERT INTO agencies(name,sandbox_scenario) VALUES('SbxCo','us_pilot') RETURNING id"); sag = cur.fetchone()[0]
    owner_conn.commit()
    assert demo.ensure_demo_brand(cur, sag) is None                  # sandbox/preset agency: no demo brand


def test_fleet_card_symbol_follows_currency_without_country(owner_conn):
    """R19.1: a brand with INR data but NO country row must still show ₹ on the fleet card — the symbol
    follows the resolved currency, not a hard-defaulted $. (gogodolls: rupee data, missing country → $.)"""
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('CcyAg') RETURNING id"); ag = cur.fetchone()[0]
    t, _ = _brand(cur, ag)                                            # no tenant_settings 'country'
    _decision(cur, t, "ads", 1000, "over breakeven ACoS", ccy="INR", impact_minor=830000)
    owner_conn.commit()
    cards = fleet_data.brand_cards(cur, [t])
    assert cards and cards[0]["currency"] == "INR" and cards[0]["symbol"] == "₹", cards[0]


def test_fleet_cards_stake_health_and_sort(owner_conn):
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('CardAg') RETURNING id"); ag = cur.fetchone()[0]
    tBig, _ = _brand(cur, ag); tSmall, _ = _brand(cur, ag); tPaused, _ = _brand(cur, ag)
    _decision(cur, tBig, "inventory", 300000, "reorder_hero")        # $3,000 at stake
    _decision(cur, tSmall, "ads", 40000, "acos_watch")               # $400 at stake, ads -> watch/gold
    _decision(cur, tPaused, "inventory", 900000, "held")             # paused -> 0 actionable
    tenancy.set_brand_scope(cur, [tPaused])
    connections.upsert_connection(cur, tPaused, "amazon_ads", "expired",
                                  datetime.datetime.now(UTC) - datetime.timedelta(days=1))
    owner_conn.commit()
    cards = fleet_data.brand_cards(cur, [tBig, tSmall, tPaused])
    by = {c["tenant_id"]: c for c in cards}
    assert by[tBig]["stake_usd"] == 3000.0 and by[tBig]["health"] == "sage"
    assert by[tSmall]["health"] == "gold"                            # ads signal -> watch
    assert by[tPaused]["health"] == "terra" and by[tPaused]["paused"]  # expired -> at risk
    # sorted by $-at-stake DESC, paused last (load-bearing triage order)
    assert [c["tenant_id"] for c in cards] == [tBig, tSmall, tPaused]


# ---------------- REAL server-side envelope enforcement in the drill-in ----------------

def test_drilldown_envelope_enforced_server_side(agency_client, owner_conn):
    client, _ = agency_client
    email = f"r11env-{secrets.token_hex(4)}@x.com"
    uid = _login(client, email)
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('EnvAg') RETURNING id"); ag = cur.fetchone()[0]
    t, eng = _brand(cur, ag)                                          # high threshold -> executes when allowed
    ops.grant_role(cur, uid, eng, t, uid, "account_manager")
    ops.publish_envelope(cur, uid, eng, t, ENVELOPES["Operate ex-Pricing"], {})   # pricing = read-only
    owner_conn.commit()

    # R15 Part 0 — the drill-in now scope-switches INTO the real five-lens app (no bespoke wrapper).
    # The envelope rides in the session: /api/scope reports pricing read-only, ads executable — so the
    # real app gates in-lens Approve (ads) vs Propose (pricing).
    r0 = client.get(f"/agency/brand/{t}", follow_redirects=False)
    assert r0.status_code == 303 and r0.headers["location"] == "/"
    scope = client.get("/api/scope").json()["agency_scope"]
    assert scope and scope["caps"]["pricing"] == "read" and scope["caps"]["ads"] == "execute"

    # SERVER-SIDE: a pricing action can only be PROPOSED (never executed) — enforced by the envelope
    r = client.post("/api/agency/queue/propose", json={"tenant_id": t, "lens": "pricing", "kind": "price",
                                                       "signal": "undercut", "impact_usd_minor": 1000})
    assert r.status_code == 200 and r.json()["executed"] is False and r.json()["status"] == "proposed"
    # an ads action (executable under ex-Pricing, below threshold) DOES execute
    r2 = client.post("/api/agency/queue/propose", json={"tenant_id": t, "lens": "ads", "kind": "bid",
                                                        "signal": "acos", "impact_usd_minor": 1000})
    assert r2.status_code == 200 and r2.json()["executed"] is True


def test_drilldown_authz_engagement_based(agency_client, owner_conn):
    """An operator with NO per-brand grant can still drill into their agency's brand (engagement-based)."""
    client, _ = agency_client
    email = f"r11authz-{secrets.token_hex(4)}@x.com"
    uid = _login(client, email)
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('AzAg') RETURNING id"); ag = cur.fetchone()[0]
    t, eng = _brand(cur, ag)
    # membership + agency link via a grant on a DIFFERENT brand so agency_ids resolves, but not on t
    tOther, engO = _brand(cur, ag)
    ops.grant_role(cur, uid, engO, tOther, uid, "account_manager")
    owner_conn.commit()
    r = client.get(f"/agency/brand/{t}", follow_redirects=False)     # engagement-based authz allows it
    assert r.status_code == 303 and r.headers["location"] == "/"     # → real five-lens app (R15 Part 0)
    # a brand of a DIFFERENT agency is refused
    cur.execute("INSERT INTO agencies(name) VALUES('OtherAg') RETURNING id"); other = cur.fetchone()[0]
    tForeign, _ = _brand(cur, other)
    owner_conn.commit()
    assert client.get(f"/agency/brand/{tForeign}", follow_redirects=False).status_code == 403


# ---------------- queue retired ----------------

def test_queue_retired_redirects(agency_client, owner_conn):
    client, _ = agency_client
    _login(client)
    r = client.get("/agency/queue", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == "/agency/console"


# ---------------- reachability: fleet -> brand -> switch (integration) ----------------

def test_reachability_fleet_to_brand(agency_client, owner_conn):
    client, H = agency_client
    sandbox.load_preset(owner_conn.cursor()); owner_conn.commit()
    client.post("/api/ops/sandbox/assume", headers=H, json={"persona": "client_lead"})
    fleet = client.get("/agency/console").text
    ids = re.findall(r"/agency/brand/(\d+)", fleet)
    assert ids                                                        # fleet cards link into the drill-in
    # R15 Part 0 — Open brand → scope-switches INTO the real five-lens app (the retired wrapper is gone).
    r = client.get(f"/agency/brand/{ids[0]}", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"
    app = client.get("/").text
    assert "Per-brand decisions" not in app                          # bespoke wrapper no longer served
    assert "surfaceLabel" in app                                     # real five-lens SPA shell renders
