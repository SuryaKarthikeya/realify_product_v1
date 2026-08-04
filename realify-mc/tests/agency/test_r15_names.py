"""R15 Part B (Postgres/agency): synthesized brand names are CATEGORY-ALIGNED, world-UNIQUE, and
DETERMINISTIC — and a user-supplied name still overrides the category bank.

The old synth `_brand_name` was a category-blind word×suffix cross-product (a Beauty brand could read
"…Kitchen", and two different tenants could collide). Now every tenant (managed AND direct) gets a
primary category and a name drawn from a bank aligned to it, unique across the whole world."""
from realify.agency import synth, locale


def _world_tenants(cur, st):
    """[(tenant_id, name), ...] for EVERY tenant in a world — managed brands then direct brands."""
    out = [(b["tenant_id"], b["name"]) for b in st["brands"]]
    for tid in st.get("direct_brands", []):
        cur.execute("SELECT name FROM tenants WHERE id=%s", (tid,))
        out.append((tid, cur.fetchone()[0]))
    return out


def _dominant_category(cur, tid):
    cur.execute("SELECT category, count(*) FROM seller_skus WHERE tenant_id=%s "
                "GROUP BY category ORDER BY count(*) DESC, category LIMIT 1", (tid,))
    r = cur.fetchone()
    return r[0] if r else None


# (a) every tenant's name category-tag == the dominant category of its catalog (name/catalog/analyst agree)
def _assert_aligned(cur, country, seed):
    st = synth.generate_world(cur, {"country": country, "seed": seed, "brands_per_agency": 6,
                                    "direct_brands": 2})
    for tid, name in _world_tenants(cur, st):
        dom = _dominant_category(cur, tid)
        assert locale.name_category(name) == dom, \
            f"{country} {name!r} tags {locale.name_category(name)!r} but catalog is dominated by {dom!r}"
    return st


def test_name_matches_category_us(owner_conn):
    _assert_aligned(owner_conn.cursor(), "US", "r15names-us"); owner_conn.commit()


def test_name_matches_category_in(owner_conn):
    _assert_aligned(owner_conn.cursor(), "IN", "r15names-in"); owner_conn.commit()


# (b) all display names in a world are DISTINCT (managed + direct)
def test_names_are_unique(owner_conn):
    cur = owner_conn.cursor()
    st = synth.generate_world(cur, {"country": "US", "seed": "r15names-uniq", "brands_per_agency": 7,
                                    "direct_brands": 3}); owner_conn.commit()
    names = [n for _t, n in _world_tenants(cur, st)]
    assert len(names) == len(set(names)), f"duplicate brand names in world: {names}"
    assert len(names) == 10                                    # 7 managed + 3 direct all present


# (c) determinism: two builds of the same seed produce IDENTICAL names on the same tenants
def test_names_are_deterministic(owner_conn):
    cur = owner_conn.cursor()
    p = {"country": "IN", "seed": "r15names-det", "brands_per_agency": 5, "direct_brands": 2}
    a = dict(_world_tenants(cur, synth.generate_world(cur, p))); owner_conn.commit()
    b = dict(_world_tenants(cur, synth.generate_world(cur, p))); owner_conn.commit()
    assert a == b and a                                        # same tenant ids → same names, non-empty


# (d) a custom brand_name / direct_brand_name still OVERRIDES the category bank (R14 B + R15 G.5)
def test_custom_names_override_the_bank(owner_conn):
    cur = owner_conn.cursor()
    st = synth.generate_world(cur, {"country": "US", "seed": "r15names-ovr", "brands_per_agency": 3,
                                    "direct_brands": 1, "brand_name": "Zephyr Goods",
                                    "direct_brand_name": "Solo Direct Co"}); owner_conn.commit()
    assert st["brands"][0]["name"] == "Zephyr Goods"           # managed[0] custom name wins
    tenants = dict(_world_tenants(cur, st))
    assert "Zephyr Goods" in tenants.values() and "Solo Direct Co" in tenants.values()
    # the override brands keep a coherent (bank) primary category even though the NAME is custom
    assert _dominant_category(cur, st["brands"][0]["tenant_id"]) in locale.LOCALES["US"]["categories"]
    # non-overridden brands still draw category-aligned bank names
    assert locale.name_category(st["brands"][1]["name"]) == \
        _dominant_category(cur, st["brands"][1]["tenant_id"])
