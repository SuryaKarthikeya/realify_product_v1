"""Contract test: the public card JSON shape that /api/feed (and /api/v1/feed) return.

This is the promise to the partner teams (conversational, front-end, real-time) — their parsers
and renderers build against exactly these fields. The test fails if a promised field disappears
OR an undocumented field leaks, so the shape can't drift without a deliberate update here (and a
version bump). The /api and /api/v1 mounts must return an identical shape.

Internal storage columns (tenant_id, run_id, dedup_key) are present on the row but are NOT part of
the contract — partners must not depend on them. They're allowed as known extras, nothing else is.
"""
import os, tempfile, sys

os.environ["REALIFY_DB"] = os.path.join(tempfile.mkdtemp(prefix="realify_contract_"), "test.db")
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, auth, scheduler                      # noqa: E402
from realify.ingest.synthetic import SyntheticSource         # noqa: E402

# The frozen public contract — 27 fields. Changing this set is a deliberate, reviewed act.
PUBLIC_CONTRACT_FIELDS = {
    "id", "card_type", "family", "type_name", "asin", "category", "finding", "why",
    "severity", "sev_label", "confidence", "conf_label", "exposure_label", "exposure_pct",
    "exposure_val", "action", "sources", "minis", "provenance", "status", "is_new",
    "created_at", "updated_at", "surface", "group", "action_kind", "rank_score",
}
# Present on the row, but explicitly NOT part of the contract.
INTERNAL_FIELDS = {"tenant_id", "run_id", "dedup_key"}


def _provisioned_client():
    from run import make_app
    from fastapi.testclient import TestClient
    db.init_db()
    c = TestClient(make_app())
    from realify import auth as _auth
    _auth.signup("contract@x.com", "password1")         # /api/signup back door gated (P0.9)
    assert c.post("/api/login", json={"email": "contract@x.com", "password": "password1"}).json()["ok"]
    con = db.connect()
    tid = con.execute("SELECT tenant_id FROM users WHERE email='contract@x.com'").fetchone()["tenant_id"]
    db.set_account_type(con, tid, "tester")
    db.set_setting(con, tid, "country", "IN")
    con.commit(); con.close()
    scheduler.provision_tenant(tid, SyntheticSource(seed_skus=None), log=lambda *a, **k: None)
    return c


def test_card_json_public_contract_is_stable():
    c = _provisioned_client()
    feed = c.get("/api/feed").json()
    assert isinstance(feed, list) and feed, "expected a populated feed"
    card = feed[0]
    keys = set(card.keys())

    missing = PUBLIC_CONTRACT_FIELDS - keys
    assert not missing, f"card is missing promised contract fields: {sorted(missing)}"

    undocumented = keys - PUBLIC_CONTRACT_FIELDS - INTERNAL_FIELDS
    assert not undocumented, (
        f"card exposes undocumented field(s): {sorted(undocumented)} — if intended, add to "
        f"PUBLIC_CONTRACT_FIELDS and bump the API version; partners build against this shape"
    )

    # type guarantees partners rely on
    assert isinstance(card["sources"], list)
    assert isinstance(card["minis"], list)
    assert isinstance(card["provenance"], list)
    assert isinstance(card["id"], int)
    assert isinstance(card["exposure_pct"], (int, float))


def test_v1_and_unversioned_feed_have_identical_shape():
    c = _provisioned_client()
    v0 = c.get("/api/feed").json()
    v1 = c.get("/api/v1/feed").json()
    assert v0 and v1, "both mounts must return a populated feed"
    assert set(v0[0].keys()) == set(v1[0].keys()), "/api and /api/v1 must return an identical card shape"
    assert v0[0]["id"] == v1[0]["id"], "both mounts must serve the same tenant's data"


if __name__ == "__main__":
    test_card_json_public_contract_is_stable()
    test_v1_and_unversioned_feed_have_identical_shape()
    print("card contract OK")
