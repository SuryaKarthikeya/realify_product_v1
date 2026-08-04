"""R15.2 (Postgres/agency) — asserted on the ENDPOINT the hub button actually hits (POST
/api/ops/sandbox/generate → poll the job) and the RENDERED surfaces the user sees (/api/ops/sandbox/state
that the picker reads, /agency/console fleet HTML), NOT an internal generator helper in isolation. This
is the fix for the recurring false-green: a helper test passed while the live click-path stayed broken.
"""
import time
from realify.agency import locale


def _generate(client, H, body, wk, tries=90):
    r = client.post("/api/ops/sandbox/generate", headers=H, json=body)
    assert r.status_code == 200 and r.json().get("started"), r.text
    for _ in range(tries):
        j = client.get(f"/api/ops/sandbox/job?world_key={wk}", headers=H).json()
        if j.get("done"):
            assert j.get("state") != "error", j
            return
        time.sleep(1)
    raise AssertionError(f"generate job {wk} did not finish")


def test_hub_generate_blank_agency_is_real_name_everywhere_IN(agency_client, owner_conn):
    client, H = agency_client
    wk = "gen-r152-inblank"
    _generate(client, H, {"country": "IN", "seed": "r152-inblank", "brands_per_agency": 4,
                          "direct_brands": 1, "sku_count": 60, "agency_name": ""}, wk)
    # (1) the endpoint the picker reads
    st = client.get(f"/api/ops/sandbox/state?world_key={wk}", headers=H).json()
    assert "VERIFY" not in st["agency_name"] and st["agency_name"] in locale.AGENCIES["IN"]
    # (2) the fleet HTML the user sees — banner + no VERIFY, Part B ₹, Part C owner variety
    client.post("/api/ops/sandbox/assume", headers=H, json={"persona": "client_lead"})
    fleet = client.get("/agency/console").text
    assert "VERIFY" not in fleet and st["agency_name"] in fleet          # Part A — real agency name in banner
    assert "₹" in fleet and " at stake" in fleet                        # Part B — localized money on cards
    owners_seen = sum(1 for n in locale.PEOPLE["IN"] if n in fleet)
    assert owners_seen >= 2, f"owner names not varied in book (saw {owners_seen})"   # Part C


def test_hub_generate_us_typed_agency_localizes_dollar(agency_client, owner_conn):
    client, H = agency_client
    wk = "gen-r152-us"
    _generate(client, H, {"country": "US", "seed": "r152-us", "brands_per_agency": 3,
                          "direct_brands": 0, "sku_count": 60, "agency_name": "Northbeam Commerce"}, wk)
    st = client.get(f"/api/ops/sandbox/state?world_key={wk}", headers=H).json()
    assert st["agency_name"] == "Northbeam Commerce"                     # typed name round-trips on the hub path
    client.post("/api/ops/sandbox/assume", headers=H, json={"persona": "client_lead"})
    fleet = client.get("/agency/console").text
    assert "Northbeam Commerce" in fleet and "₹" not in fleet           # US → $, no ₹ leak
    assert "$" in fleet and " at stake" in fleet
    owners_seen = sum(1 for n in locale.PEOPLE["US"] if n in fleet)
    assert owners_seen >= 2                                              # Part C — US owner variety


def test_reused_agency_is_renamed_not_stale(agency_client, owner_conn):
    """The real bug: the hub ships a FIXED default seed, so the same world_key is reused; a reused agency
    must be RENAMED to the current world (R14 did this for brands, missed agencies)."""
    client, H = agency_client
    wk = "gen-r152-reuse"
    _generate(client, H, {"country": "US", "seed": "r152-reuse", "brands_per_agency": 2,
                          "direct_brands": 0, "sku_count": 40, "agency_name": "Placeholder Co"}, wk)
    assert client.get(f"/api/ops/sandbox/state?world_key={wk}", headers=H).json()["agency_name"] == "Placeholder Co"
    # regenerate the SAME seed with a BLANK agency → the reused agency is renamed to a real bank name
    _generate(client, H, {"country": "US", "seed": "r152-reuse", "brands_per_agency": 2,
                          "direct_brands": 0, "sku_count": 40, "agency_name": ""}, wk)
    an = client.get(f"/api/ops/sandbox/state?world_key={wk}", headers=H).json()["agency_name"]
    assert an != "Placeholder Co" and "VERIFY" not in an and an in locale.AGENCIES["US"]


def test_reaper_selects_sandbox_agency_without_display_name(owner_conn):
    from realify.agency import synth, sandbox
    cur = owner_conn.cursor()
    spec = synth.spec_from_params({"country": "US", "seed": "r152-reap", "brands_per_agency": 2,
                                   "direct_brands": 0, "agency_name": ""})
    sandbox.load_world(cur, spec, synth.world_key("r152-reap")); owner_conn.commit()
    aid = sandbox._scenario_agency(cur, synth.world_key("r152-reap"))
    cur.execute("SELECT name, sandbox_scenario FROM agencies WHERE id=%s", (aid,))
    nm, scen = cur.fetchone()
    assert "VERIFY" not in nm and scen is not None                       # sandbox identified by TAG, not name
