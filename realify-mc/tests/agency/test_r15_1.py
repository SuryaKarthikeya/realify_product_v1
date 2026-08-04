"""R15.1 (Postgres/agency): agency auto-naming (Part A) + hub/picker locale from the world's stored
country (Part B). Both are hub/picker-layer defects — the interior five-lens app was already correct.
"""
from realify.agency import synth, sandbox, locale


def test_blank_agency_gets_real_locale_name_not_verify(owner_conn):
    cur = owner_conn.cursor()
    spec = synth.spec_from_params({"country": "IN", "seed": "r151-agIN", "brands_per_agency": 3,
                                   "direct_brands": 0, "agency_name": ""})
    an = spec["agency_name"]
    assert "VERIFY" not in an and an in locale.AGENCIES["IN"]        # real, India-appropriate bank name
    sandbox.load_world(cur, spec, synth.world_key("r151-agIN")); owner_conn.commit()
    ss = sandbox.sandbox_state(cur, synth.world_key("r151-agIN"))
    assert ss["agency_name"] == an and "VERIFY" not in ss["agency_name"]


def test_entered_agency_name_round_trips(owner_conn):
    cur = owner_conn.cursor()
    spec = synth.spec_from_params({"country": "US", "seed": "r151-agUS", "brands_per_agency": 2,
                                   "direct_brands": 0, "agency_name": "Northbeam Commerce"})
    assert spec["agency_name"] == "Northbeam Commerce"
    sandbox.load_world(cur, spec, synth.world_key("r151-agUS")); owner_conn.commit()
    assert sandbox.sandbox_state(cur, synth.world_key("r151-agUS"))["agency_name"] == "Northbeam Commerce"


def test_reaper_selects_sandbox_agency_without_display_name(owner_conn):
    cur = owner_conn.cursor()
    spec = synth.spec_from_params({"country": "US", "seed": "r151-reap", "brands_per_agency": 2,
                                   "direct_brands": 0, "agency_name": ""})
    sandbox.load_world(cur, spec, synth.world_key("r151-reap")); owner_conn.commit()
    aid = sandbox._scenario_agency(cur, synth.world_key("r151-reap"))
    cur.execute("SELECT name, sandbox_scenario FROM agencies WHERE id=%s", (aid,))
    nm, scen = cur.fetchone()
    assert "VERIFY" not in nm and scen is not None                  # identified as sandbox by the TAG, not the name


def test_names_unique_across_world_incl_agency(owner_conn):
    cur = owner_conn.cursor()
    spec = synth.spec_from_params({"country": "IN", "seed": "r151-uniq", "brands_per_agency": 4,
                                   "direct_brands": 2, "agency_name": ""})
    sandbox.load_world(cur, spec, synth.world_key("r151-uniq")); owner_conn.commit()
    ss = sandbox.sandbox_state(cur, synth.world_key("r151-uniq"))
    names = [ss["agency_name"]] + [b["name"] for b in ss["brands"]] + [d["name"] for d in ss["directs"]]
    assert len(names) == len(set(names))                            # agency + brands + directs all distinct


def test_sandbox_state_locale_from_stored_country(owner_conn):
    cur = owner_conn.cursor()
    spec = synth.spec_from_params({"country": "IN", "seed": "r151-locIN", "brands_per_agency": 3,
                                   "direct_brands": 1, "agency_name": ""})
    sandbox.load_world(cur, spec, synth.world_key("r151-locIN")); owner_conn.commit()
    ss = sandbox.sandbox_state(cur, synth.world_key("r151-locIN"))
    assert ss["country"] == "IN" and ss["currency"] == "INR" and ss["symbol"] == "₹"
    assert ss["brands"] and all(b["symbol"] == "₹" for b in ss["brands"])       # managed picker suffix source
    assert all(d["symbol"] == "₹" for d in ss["directs"])                        # direct picker suffix source
    spec2 = synth.spec_from_params({"country": "US", "seed": "r151-locUS", "brands_per_agency": 2,
                                    "direct_brands": 0, "agency_name": ""})
    sandbox.load_world(cur, spec2, synth.world_key("r151-locUS")); owner_conn.commit()
    ss2 = sandbox.sandbox_state(cur, synth.world_key("r151-locUS"))
    assert ss2["country"] == "US" and ss2["currency"] == "USD" and ss2["symbol"] == "$"
    assert ss2["brands"] and all(b["symbol"] == "$" for b in ss2["brands"])
