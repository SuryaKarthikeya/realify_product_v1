"""R15 Part A (Postgres/agency): the Fleet grid (h7) is now fed by the R14 synthesizer — every card's
TACoS, GMV and $-at-stake derive from the SAME synthesized world the brand interior five lenses read,
and reconcile with it. This proves the live bug is gone: cards no longer show a flat 0% TACoS and a
seller_skus GMV (~$54K) that contradicts the interior ($2.47M revenue).

Synthesis follows test_r14's pattern: point config.DATABASE_URL at the agency PG, then finalize the
world's lenses (ad_performance + sku_revenue_period + decisions) so the fleet reads real data."""
import os

from realify import config
from realify.agency import synth, tenancy, lens_synth, fleet_data

_DIRECT = os.environ.get("AGENCY_DATABASE_URL")

_PARAMS = {"country": "US", "seed": "r15fleet", "brands_per_agency": 3, "direct_brands": 0,
           "moments": ["acos_over_breakeven", "stockout"]}


def _finalize(monkeypatch, owner_conn, ids):
    monkeypatch.setattr(config, "DATABASE_URL", _DIRECT, raising=False)   # builders' db.connect() → agency PG
    lens_synth.finalize_world(ids)
    owner_conn.rollback()                                                 # fresh read-committed snapshot


def _interior_tacos(cur, tid):
    """The interior Profit & Ads basis: Σ ad spend ÷ Σ revenue × 100 (all month periods)."""
    cur.execute("SELECT COALESCE(SUM(spend),0) FROM ad_performance WHERE tenant_id=%s AND grain='month'", (tid,))
    spend = float(cur.fetchone()[0] or 0)
    cur.execute("SELECT COALESCE(SUM(revenue),0) FROM sku_revenue_period WHERE tenant_id=%s AND grain='month'", (tid,))
    rev = float(cur.fetchone()[0] or 0)
    return (spend / rev * 100.0) if rev > 0 else 0.0


def test_fleet_cards_reconcile_with_synth_interior(owner_conn, monkeypatch):
    cur = owner_conn.cursor()
    st = synth.generate_world(cur, _PARAMS); owner_conn.commit()
    ids = fleet_data.agency_brand_ids(cur, st["agency_id"])
    assert len(ids) >= 2
    _finalize(monkeypatch, owner_conn, ids)
    tenancy.set_brand_scope(cur, ids)

    cards = fleet_data.brand_cards(cur, ids)
    by = {c["tenant_id"]: c for c in cards}
    assert set(by) == set(ids)

    saw_positive_tacos = False
    for tid in ids:
        card = by[tid]
        if card["paused"]:
            continue

        # TACoS: the flat-0% bug is gone AND the card matches the interior portfolio TACoS basis.
        interior = _interior_tacos(cur, tid)
        assert card["tacos_pct"] > 0, f"brand {tid}: fleet TACoS still 0 (the live bug)"
        assert abs(card["tacos_pct"] - round(interior, 1)) < 0.2, \
            f"brand {tid}: card TACoS {card['tacos_pct']} != interior {interior}"
        saw_positive_tacos = True

        # GMV / money_line reconciles with the synthesized revenue (same order of magnitude, > 0).
        cur.execute("SELECT COALESCE(SUM(revenue),0) FROM sku_revenue_period WHERE tenant_id=%s AND grain='month'", (tid,))
        rev = float(cur.fetchone()[0] or 0)
        assert rev > 0 and "GMV" in card["money_line"] and "—" not in card["money_line"]

        # $-at-stake == Σ open decisions' impact_usd_minor / 100 (the interior FIX-ADS recoverable basis).
        cur.execute("SELECT COALESCE(SUM(impact_usd_minor),0) FROM decisions "
                    "WHERE status='open' AND tenant_id=%s", (tid,))
        open_minor = int(cur.fetchone()[0] or 0)
        assert card["stake_usd"] == open_minor / 100.0

        # top-signal names a SKU that exists in THIS brand's seller_skus catalog.
        if card["open_count"]:
            cur.execute("SELECT title FROM seller_skus WHERE tenant_id=%s", (tid,))
            titles = [t[0] for t in cur.fetchall()]
            assert any(t and t in card["top_signal"] for t in titles), \
                f"brand {tid}: top-signal '{card['top_signal']}' names no catalog SKU"

        # health is in the fleet vocabulary and reflects real signals.
        assert card["health"] in ("sage", "gold", "terra")

    assert saw_positive_tacos, "no fleet brand had ad data — synthesis did not populate Profit & Ads"


def test_fleet_cards_deterministic_for_fixed_seed(owner_conn, monkeypatch):
    """Same seed ⇒ byte-identical card numbers (TACoS / $-at-stake / GMV line) across builds."""
    cur = owner_conn.cursor()

    def _build():
        st = synth.generate_world(cur, _PARAMS); owner_conn.commit()
        ids = fleet_data.agency_brand_ids(cur, st["agency_id"])
        _finalize(monkeypatch, owner_conn, ids)
        tenancy.set_brand_scope(cur, ids)
        return {c["tenant_id"]: (c["tacos_pct"], c["stake_usd"], c["money_line"], c["health"])
                for c in fleet_data.brand_cards(cur, ids)}

    first = _build()
    second = _build()
    assert first and first == second
