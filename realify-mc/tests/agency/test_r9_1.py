"""R9.1 (Postgres/agency suite): realistic synthesis where decisions render — sane $ magnitudes,
believable decision-type mix, single-digit paused counts, real names everywhere (no placeholders), the
generator name input, currency↔world sync, and determinism with real names."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realify.agency import sandbox, synth, tenancy, connections

_PLACEHOLDER = re.compile(r"Brand \d+|Direct brand \d+|Agency \(\d+ brands\)|sandbox[-_][a-z0-9_]+@")


def _all_decisions(cur, brand_ids):
    tenancy.set_brand_scope(cur, brand_ids)
    cur.execute("SELECT lens, kind, impact_usd_minor, impact_currency, signal FROM decisions "
                "WHERE tenant_id = ANY(%s)", (brand_ids,))
    return cur.fetchall()


def test_sane_impact_magnitudes(owner_conn):
    cur = owner_conn.cursor()
    st = sandbox.load_preset(cur, "us_pilot"); owner_conn.commit()
    ids = [b["tenant_id"] for b in st["brands"]]
    rows = _all_decisions(cur, ids)
    assert rows, "expected decisions"
    usds = sorted(r[2] / 100 for r in rows)
    max_usd = usds[-1]
    assert max_usd <= 5000, f"single-decision impact too large: ${max_usd:,.0f}"
    at_stake = sum(usds)
    assert at_stake < 500_000, f"portfolio at-stake implausible for {len(ids)} brands: ${at_stake:,.0f}"
    # REAL spread, not a wall of cap-pinned figures: the cap must be a rare outlier, not the norm.
    # (Catches unit-mismatch bugs where every raw impact overflows and clamps to the ceiling.)
    at_cap = sum(1 for v in usds if v >= 5000)
    assert at_cap / len(usds) < 0.25, f"{at_cap}/{len(usds)} decisions pinned at the $5k cap — impacts not realistic"
    assert usds[len(usds) // 2] < 3000, f"median impact ${usds[len(usds)//2]:,.0f} implausibly high"


def test_decision_type_mix(owner_conn):
    cur = owner_conn.cursor()
    st = sandbox.load_preset(cur, "us_pilot"); owner_conn.commit()
    rows = _all_decisions(cur, [b["tenant_id"] for b in st["brands"]])
    by_lens = {}
    for lens, *_ in rows:
        by_lens[lens] = by_lens.get(lens, 0) + 1
    assert len(by_lens) >= 3, f"expected >=3 action types, got {by_lens}"
    top = max(by_lens.values()) / sum(by_lens.values())
    assert top <= 0.60, f"one type dominates ({by_lens})"


def test_planted_moments_generate_their_types(owner_conn):
    cur = owner_conn.cursor()
    for mom, lens in [("stockout", "inventory"), ("acos_over_breakeven", "ads"),
                      ("competitor_undercut", "pricing")]:
        st = synth.generate_world(cur, {"country": "US", "seed": f"mom-{mom}", "brands_per_agency": 2,
                                        "direct_brands": 0, "moments": [mom]}); owner_conn.commit()
        rows = _all_decisions(cur, [b["tenant_id"] for b in st["brands"]])
        lenses = {r[0] for r in rows}
        assert lens in lenses, f"moment {mom} did not generate {lens} (got {lenses})"


def test_sane_paused_counts(owner_conn):
    cur = owner_conn.cursor()
    st = sandbox.load_preset(cur, "us_pilot"); owner_conn.commit()
    for b in st["brands"]:
        if connections.decisions_paused(cur, b["tenant_id"]):
            cur.execute("SELECT count(*) FROM decisions WHERE tenant_id=%s", (b["tenant_id"],))
            n = cur.fetchone()[0]
            assert n <= 12, f"paused brand holds {n} decisions (should be a handful)"


def test_real_names_everywhere_no_placeholders(owner_conn):
    cur = owner_conn.cursor()
    st = sandbox.load_preset(cur, "us_pilot"); owner_conn.commit()
    sst = sandbox.sandbox_state(cur, "us_pilot")
    from realify.agency import team
    blob = " | ".join([sst["agency_name"]] + [b["name"] for b in sst["brands"]]
                      + [d["name"] for d in sst["directs"]]
                      + [m["name"] for m in team.list_members(cur, st["agency_id"])])
    assert not _PLACEHOLDER.search(blob), f"placeholder name leaked: {blob}"
    # decision signals name the product, never 'stockout:SB-004'
    rows = _all_decisions(cur, [b["tenant_id"] for b in st["brands"]])
    assert all(":" not in r[4].split(" ")[0] for r in rows[:20])
    assert not any(_PLACEHOLDER.search(r[4]) for r in rows)


def test_generator_name_input_honored(owner_conn):
    cur = owner_conn.cursor()
    st = synth.generate_world(cur, {"country": "US", "seed": "named", "brands_per_agency": 2,
                                    "direct_brands": 0, "agency_name": "Vanguard Retail Co"})
    owner_conn.commit()
    cur.execute("SELECT name FROM agencies WHERE id=%s", (st["agency_id"],))
    assert cur.fetchone()[0] == "Vanguard Retail Co"
    # blank -> a real bank name (not a placeholder)
    st2 = synth.generate_world(cur, {"country": "IN", "seed": "unnamed", "brands_per_agency": 2,
                                     "direct_brands": 0}); owner_conn.commit()
    cur.execute("SELECT name FROM agencies WHERE id=%s", (st2["agency_id"],))
    assert not _PLACEHOLDER.search(cur.fetchone()[0])


def test_currency_world_sync(owner_conn):
    cur = owner_conn.cursor()
    # India world: every decision is INR
    inn = sandbox.load_preset(cur, "in_pilot"); owner_conn.commit()
    rows = _all_decisions(cur, [b["tenant_id"] for b in inn["brands"]])
    assert rows and all(r[3] == "INR" for r in rows)
    assert sandbox.sandbox_state(cur, "in_pilot")["currency"] == "INR"
    # US world: every decision is USD — zero INR remains
    us = sandbox.load_preset(cur, "us_pilot"); owner_conn.commit()
    rows = _all_decisions(cur, [b["tenant_id"] for b in us["brands"]])
    assert rows and all(r[3] == "USD" for r in rows)
    assert sandbox.sandbox_state(cur, "us_pilot")["currency"] == "USD"


def test_determinism_with_real_names(owner_conn):
    cur = owner_conn.cursor()
    p = {"country": "US", "seed": "det91", "brands_per_agency": 3, "direct_brands": 1,
         "moments": ["stockout", "acos_over_breakeven", "competitor_undercut"]}
    a = synth.generate_world(cur, p); owner_conn.commit()

    def snap(st):
        out = {}
        for b in st["brands"]:
            cur.execute("SELECT asin,title,price,cogs FROM seller_skus WHERE tenant_id=%s ORDER BY asin",
                        (b["tenant_id"],))
            out[b["name"]] = cur.fetchall()
        return out
    s1 = snap(a)
    b = synth.generate_world(cur, p); owner_conn.commit()
    assert s1 == snap(b)                                     # identical incl. real product names
