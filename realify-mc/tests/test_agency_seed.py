"""T-P0-02: sandbox canary seed is idempotent, counts are correct, and canaries are present."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db                       # noqa: E402
from realify.agency import seed as agency_seed  # noqa: E402


def _sandbox_tenants(con):
    return con.execute("SELECT COUNT(*) c FROM tenants WHERE sandbox=1").fetchone()["c"]


def test_seed_counts_and_canaries_present():
    con = db.connect()
    r = agency_seed.seed(con)
    assert r["agencies"] == 3 and r["brands"] == 36
    assert len(r["canaries"]) == 36 and len(set(r["canaries"])) == 36     # 36 distinct canaries
    assert all(c.startswith("CANARY_") for c in r["canaries"])
    assert _sandbox_tenants(con) == 36
    # every brand carries its canary in >= ROWS_PER_BRAND of its own rows
    for c in r["canaries"]:
        n = con.execute("SELECT COUNT(*) c FROM seller_skus WHERE title LIKE ?", (c + "%",)).fetchone()["c"]
        assert n >= agency_seed.ROWS_PER_BRAND, (c, n)
    con.close()


def test_seed_is_idempotent():
    con = db.connect()
    agency_seed.seed(con)
    tenants_after_first = _sandbox_tenants(con)
    rows_after_first = con.execute("SELECT COUNT(*) c FROM seller_skus").fetchone()["c"]
    r2 = agency_seed.seed(con)                       # second run
    assert r2["created"] == 0                        # nothing new created
    assert _sandbox_tenants(con) == tenants_after_first == 36
    assert con.execute("SELECT COUNT(*) c FROM seller_skus").fetchone()["c"] == rows_after_first
    con.close()
