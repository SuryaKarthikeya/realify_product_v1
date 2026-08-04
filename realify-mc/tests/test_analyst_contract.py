"""Contract test: the Category Analyst payload shape (/api/category-analyst and /api/v1/...).

Pins the frozen surface the client + future synthesis service build against, and guards the
non-negotiables: tenancy fails closed; provenance is first-class; /api == /api/v1; and — new in
Phase 1 — the per-section DATA-STATE contract (state/field_state) plus the EXPOSURE GATE (a real
tenant never receives fixture numbers). The payload is now assembled from real L1 data
(analyst_live) off the tenant's cards; fixture sections show synthetic content only to the fixture
tenant.
"""
import os, tempfile, sys, json

os.environ["REALIFY_DB"] = os.path.join(tempfile.mkdtemp(prefix="realify_analyst_"), "test.db")
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db                              # noqa: E402
from realify.domain import analyst as A            # noqa: E402
from realify.repositories.seller_repo import SellerRepository  # noqa: E402


def _seed(tid, category="Auto Accessories", account="tester", data_mode=None):
    """Give the tenant one SKU + two cards (competitive + news) so the live sections populate."""
    con = db.connect()
    db.set_account_type(con, tid, account)
    if data_mode:
        con.execute("UPDATE tenants SET data_mode=? WHERE id=?", (data_mode, tid))
    SellerRepository(con).upsert_full(tid, {"internal_sku": "S1", "asin": "AS1", "channel": "amazon",
                                            "category": category, "price": 2000, "cogs": 800, "velocity_day": 3.2,
                                            "title": "Autofy Storm 3-Layer Cover", "net_margin_pct": 42.0,
                                            "margin_floor": 30, "buybox_pct": 72})
    for ct, fam, name, find, sev, rank, elab, eval_, mn, pv in [
        ("C1", "competitive", "Competitor Move", "MotoShield cut the 3-layer cover 12%", "act", 92,
         "Your monthly revenue", "₹2.4L", [["Their price", "₹2,099"]], [["Keepa BSR", "KEEPA"], ["scraped listing", "SCRAPE"]]),
        ("C8", "news", "Recall / Regulatory", "BIS phthalate order tightens PVC limits", "opp", 84,
         "Freed demand", "₹1.8L", [["Affected SKUs", "2"]], [["BIS govt feed", "NEWS"]])]:
        con.execute("""INSERT INTO cards(tenant_id,card_type,family,type_name,category,asin,finding,severity,
            rank_score,exposure_label,exposure_pct,exposure_val,status,is_new,sources,minis,provenance)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (tid, ct, fam, name, category, "AS1", find, sev, rank, elab, 60, eval_, "new", 1,
             json.dumps(["Keepa"]), json.dumps(mn), json.dumps(pv)))
    con.commit(); con.close()


def _client(email="analyst@x.com", account="tester", data_mode=None):
    from run import make_app
    from fastapi.testclient import TestClient
    db.init_db()
    c = TestClient(make_app())
    from realify import auth as _auth
    _auth.signup(email, "password1")                    # /api/signup back door gated (P0.9)
    assert c.post("/api/login", json={"email": email, "password": "password1"}).json()["ok"]
    con = db.connect()
    tid = con.execute("SELECT tenant_id FROM users WHERE email=?", (email,)).fetchone()["tenant_id"]
    con.close()
    _seed(tid, account=account, data_mode=data_mode)
    return c


def _collect_tiers(x, acc):
    if isinstance(x, dict):
        if "tier" in x and "source" in x:
            acc.add(x["tier"])
        for v in x.values():
            _collect_tiers(v, acc)
    elif isinstance(x, list):
        for v in x:
            _collect_tiers(v, acc)


def test_requires_tenant_fail_closed():
    from run import make_app
    from fastapi.testclient import TestClient
    db.init_db()
    assert TestClient(make_app()).get("/api/category-analyst").status_code == 401


def test_analyst_public_contract():
    d = _client().get("/api/category-analyst").json()
    assert set(d.keys()) == A.PUBLIC_KEYS, f"payload keys drifted: {sorted(set(d.keys()) ^ A.PUBLIC_KEYS)}"
    # live sections populated off the seeded cards
    for k in ("signals", "competitive", "market_pulse"):
        assert isinstance(d[k], list) and d[k], f"{k} must be populated (live off cards)"
    assert d["brief"]["moves"], "the Brief must lead with recommended moves"
    assert d["scope"]["position"], "scope bar must carry the brand's own position"
    assert d["moves"]["recommended"] is not None
    assert d["synthesis_source"] in ("live", "live+fixture")
    # numbers are server-formatted strings (L1 owns them; the client never computes)
    m = d["signals"][0]["evidence"][0]
    assert isinstance(m["value"], str) and m["prov"]["tier"] in A.TIERS
    tiers = set(); _collect_tiers(d, tiers)
    assert tiers and tiers <= A.TIERS, f"invalid provenance tier(s): {tiers - A.TIERS}"


def test_per_section_data_state():
    d = _client(email="anstate@x.com").get("/api/category-analyst").json()
    st = d["states"]
    assert set(st.keys()) == {"scope", "brief", "signals", "whitespace", "competitive",
                              "voice", "market_pulse", "moves", "ask"}
    assert st["signals"]["state"] == "live" and st["competitive"]["state"] == "live"
    assert st["market_pulse"]["state"] == "live" and st["brief"]["state"] == "live"
    assert st["scope"]["state"] == "partial" and st["moves"]["state"] == "partial"
    assert st["whitespace"]["state"] == "fixture" and st["voice"]["state"] == "fixture"
    # R15: Share-of-band + Category-rank are now synthesized LIVE (deterministic per world), like velocity
    assert d["scope"]["position"]["share"]["field_state"] == ""         # live (was "coming" pre-R15)
    assert d["scope"]["position"]["rank"]["field_state"] == ""          # live (was "coming" pre-R15)
    assert d["scope"]["position"]["velocity"]["field_state"] == ""      # velocity is live
    # sub-fields that ARE still coming carry field_state="coming" (a placeholder, not a fabricated number)
    assert d["moves"]["attributed_margin"]["field_state"] == "coming"
    # a fixture section for the FIXTURE tenant shows synthetic content + a scraped tier to badge
    assert d["voice"] and any(True for _ in d["whitespace"])
    tiers = set(); _collect_tiers(d, tiers)
    assert A.SCRAPED in tiers, "fixture tenant must expose a scraped·directional figure to badge"


def test_exposure_gate_real_tenant_sees_no_fixture_numbers():
    d = _client(email="realco@x.com", account="customer", data_mode="uploaded").get("/api/category-analyst").json()
    assert d["synthesis_source"] == "live"
    # fixture sections render coming-state with NO items/numbers for a real tenant
    assert d["states"]["whitespace"]["state"] == "fixture" and d["whitespace"] == []
    assert d["states"]["voice"]["state"] == "fixture" and d["voice"] == []
    assert d["states"]["whitespace"]["coming"]                     # honest-empty copy present
    # a real tenant still gets its live sections
    assert d["signals"] and d["competitive"]


def test_brief_assembly_introduces_no_new_number():
    """The Brief is assembly, not a new brain: every impact figure in brief.moves must be a value L1
    already produced on a card (exposure_val or exposure_label). L2 phrasing adds no number."""
    d = _client(email="anbrief@x.com").get("/api/category-analyst").json()
    con = db.connect()
    tid = con.execute("SELECT id FROM tenants ORDER BY id DESC LIMIT 1").fetchone()["id"]
    l1_vals = {r["exposure_val"] for r in con.execute("SELECT exposure_val FROM cards WHERE tenant_id=?", (tid,))}
    l1_labels = {r["exposure_label"] for r in con.execute("SELECT exposure_label FROM cards WHERE tenant_id=?", (tid,))}
    con.close()
    for mv in d["brief"]["moves"]:
        assert (not mv["impact"]) or mv["impact"] in (l1_vals | l1_labels), f"brief move impact not from L1: {mv['impact']}"


def _floor_card(tid, asin, sku_cols, finding="Margin on X has slipped to 48.7%, under the 30% floor you set"):
    con = db.connect()
    SellerRepository(con).upsert_full(tid, {"internal_sku": asin, "asin": asin, "channel": "amazon",
                                            "category": "Auto Accessories", "price": 1000, **sku_cols})
    con.execute("""INSERT INTO cards(tenant_id,card_type,family,type_name,category,asin,finding,severity,
        rank_score,exposure_label,exposure_pct,exposure_val,status,is_new,sources,minis,provenance)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (tid, "margin-vs-floor", "buybox", "Margin vs floor", "Auto Accessories", asin, finding, "act",
         70, "Your monthly revenue", 50, "₹1.2L", "new", 1, "[]", "[]", json.dumps([["net_margin_pct", "OWN"]])))
    con.commit(); con.close()


def test_floor_gate_drops_above_floor_breach_claims():
    """P0-2: a 'margin below floor' card whose SKU is ABOVE floor (48.7% ≥ 30%) must NOT be surfaced —
    the analyst owns the below_floor verdict from L1 seller data."""
    c = _client(email="floor@x.com")
    con = db.connect(); tid = con.execute("SELECT id FROM tenants ORDER BY id DESC LIMIT 1").fetchone()["id"]; con.close()
    _floor_card(tid, "ABOVE1", {"net_margin_pct": 48.7, "margin_floor": 30, "title": "Above-floor SKU"})
    _floor_card(tid, "BELOW1", {"net_margin_pct": 20.0, "margin_floor": 30, "title": "Below-floor SKU"})
    d = c.get("/api/category-analyst").json()
    # scope to the SURFACED items (scope's velocity breakdown legitimately lists every SKU)
    items = json.dumps({"signals": d["signals"], "competitive": d["competitive"]})
    # P0-2 + Fix 4: an above-floor SKU is never a breach anywhere; own-SKU margin findings are NOT
    # feed items (they're Brief context). No margin-below-floor claim in the Signal Feed / Competitive.
    assert "48.7" not in items and "Above-floor SKU" not in items, "above-floor SKU surfaced as a breach"
    assert "below your" not in items and "under the" not in items, "own-SKU floor breach leaked into the feed"
    # own-SKU findings appear only as a Brief context reference (count), never re-listed as items
    assert "own-SKU finding" in d["brief"]["narrative"]


def test_category_all_reads_all_categories_not_none():
    d = _client(email="allcat@x.com").get("/api/category-analyst", params={"category": "All"}).json()
    assert "None" not in d["brief"]["narrative"], "raw None leaked into the memo"
    assert "all categories" in d["brief"]["narrative"]


def test_no_enum_token_or_duplicated_label():
    d = _client(email="tok@x.com").get("/api/category-analyst").json()
    for c in d["competitive"]:
        assert "[" not in c["moved"] and "]" not in c["moved"], "classification enum token leaked into prose"
        assert c["kind_label"] and c["kind"]                        # human label + machine enum kept apart
    for s in d["signals"]:                                          # P1-4: no duplicated label in `why`
        assert "(Your monthly revenue" not in s.get("why", "")


def test_business_numbers_are_structured_with_explain():
    """P1-3: ₹-at-stake / margin / Buy Box are structured metrics with an explain part; the raw
    materiality sort score is NOT surfaced as an explainable metric."""
    d = _client(email="expl@x.com").get("/api/category-analyst").json()
    ev = d["signals"][0]["evidence"]
    assert any(m.get("explain") for m in ev), "no business metric carries an explain object"
    assert not any(m.get("label") == "Materiality" for m in ev), "raw materiality surfaced as a metric"


def test_competitive_rows_carry_provenance():
    d = _client(email="prov@x.com").get("/api/category-analyst").json()
    assert d["competitive"], "need a competitive row"
    for c in d["competitive"]:
        assert c.get("prov") and c["prov"]["tier"] in A.TIERS
    # section source is a real source name, never the raw column
    for src in d["states"]["competitive"]["provenance"]:
        assert src["source"] != "net_margin_pct"


def test_brief_count_matches_feed_and_dedupes():
    d = _client(email="cnt@x.com").get("/api/category-analyst").json()
    import re as _re
    m = _re.search(r"(\d+) live category signal", d["brief"]["narrative"])
    if m:
        assert int(m.group(1)) == len(d["signals"]), "memo count != rendered feed count"
    ids = [mv["id"] for mv in d["brief"]["moves"]]
    assert len(ids) == len(set(ids)), "duplicate moves in the brief"


def test_fix4_signal_feed_is_category_only_no_own_sku_findings():
    """Decision A: the Signal Feed carries only C1–C9 category/competitive change; own-SKU
    P&A/Intelligence findings (margin/Buy Box/ad spend) are NOT re-listed — they inform the Brief."""
    c = _client(email="resrc@x.com")
    con = db.connect(); tid = con.execute("SELECT id FROM tenants ORDER BY id DESC LIMIT 1").fetchone()["id"]; con.close()
    _floor_card(tid, "OWN1", {"net_margin_pct": 22.0, "margin_floor": 30, "title": "Own margin SKU"})
    d = c.get("/api/category-analyst").json()
    # every surfaced signal traces to a C1–C9 card (sig ids are sig-<cardid>); no own-SKU finding present
    feed_txt = json.dumps({"signals": d["signals"], "competitive": d["competitive"], "market_pulse": d["market_pulse"]})
    assert "Own margin SKU" not in feed_txt and "below your" not in feed_txt
    # the own-SKU finding is acknowledged as a Brief input (context), the only place it appears
    assert "own-SKU finding" in d["brief"]["narrative"]


def test_r15_share_and_rank_are_live_and_deterministic():
    """R15: Share-of-band + Category-rank are synthesized LIVE (deterministic per world) from the
    tenant's own catalog + a modeled competitor set — locale-neutral (a % and an integer rank), while
    Whitespace / Voice of Customer stay coming (fixture)."""
    import re as _re
    c = _client(email="r15@x.com")
    d = c.get("/api/category-analyst").json()
    pos = d["scope"]["position"]
    # both flipped coming -> live, with honest provenance and an explain object
    for key in ("share", "rank"):
        assert pos[key]["field_state"] == "", f"{key} must be live"
        assert pos[key]["value"] not in ("—", ""), f"{key} must carry a real value"
        assert pos[key]["explain"], f"{key} must carry an explain part"
        assert "modeled category set" in pos[key]["prov"]["source"]
    # share ∈ (0,1], rendered as a percentage (locale-neutral, no currency)
    share = float(pos["share"]["value"].rstrip("%")) / 100.0
    assert 0.0 < share <= 1.0 and "%" in pos["share"]["value"]
    # rank ∈ 1..N (integer), rendered "#r of N"
    m = _re.match(r"#(\d+) of (\d+)$", pos["rank"]["value"])
    assert m, f"unexpected rank format: {pos['rank']['value']}"
    rank, n = int(m.group(1)), int(m.group(2))
    assert 1 <= rank <= n and 8 <= n <= 40
    # deterministic: same tenant/world ⇒ identical share & rank across calls
    d2 = c.get("/api/category-analyst").json()
    assert d2["scope"]["position"]["share"]["value"] == pos["share"]["value"]
    assert d2["scope"]["position"]["rank"]["value"] == pos["rank"]["value"]
    # Whitespace / Voice stay coming (untouched by R15) for the fixture tenant's section state
    assert d["states"]["whitespace"]["state"] == "fixture"
    assert d["states"]["voice"]["state"] == "fixture"


def test_dual_mount_parity():
    c = _client(email="analyst2@x.com")
    v0 = c.get("/api/category-analyst").json()
    v1 = c.get("/api/v1/category-analyst").json()
    assert set(v0.keys()) == set(v1.keys()) == A.PUBLIC_KEYS
    assert v0["scope"]["category"] == v1["scope"]["category"]
    assert {k: s["state"] for k, s in v0["states"].items()} == {k: s["state"] for k, s in v1["states"].items()}


def test_scope_params_flow_through():
    c = _client(email="analyst3@x.com")
    d = c.get("/api/category-analyst", params={"category": "Auto Accessories",
                                               "price_band": "Value (< ₹1,000)"}).json()
    assert d["scope"]["category"] == "Auto Accessories"


if __name__ == "__main__":
    for fn in (test_requires_tenant_fail_closed, test_analyst_public_contract, test_per_section_data_state,
               test_exposure_gate_real_tenant_sees_no_fixture_numbers, test_brief_assembly_introduces_no_new_number,
               test_r15_share_and_rank_are_live_and_deterministic,
               test_dual_mount_parity, test_scope_params_flow_through):
        fn()
    print("analyst contract OK")
