"""The core invariant: a caught exception is QUERY_ERROR (never a fallback), and entity_rows>0 never
yields fell_back=True. Absence, no-match and failure stay distinct — a silent fallback would re-merge them."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_fbe_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, scheduler                                       # noqa: E402
from realify.ingest.synthetic import SyntheticSource                    # noqa: E402
from realify.repositories.tenant_repo import TenantRepository           # noqa: E402
from realify.domain import ad_resolution as R                           # noqa: E402
from realify.routers import ads                                         # noqa: E402


def test_resolve_rule_unit():
    assert R.resolve(0, 0, None, 0)["reason"] == R.NO_ENTITY_DATA
    assert R.resolve(0, 0, None, 0)["fell_back"] is True                 # the ONLY fallback
    assert R.resolve(5, 5, 90.0, 3)["reason"] == R.RENDERED_OK
    # entity rows exist + mapped, but zero recommendations = a HEALTHY account, not an error/fallback
    hz = R.resolve(5, 5, 90.0, 0)
    assert hz["reason"] == R.RENDERED_OK and hz["fell_back"] is False
    # data exists, nothing mapped -> alarm, not a fallback
    un = R.resolve(5, 0, 0.0, 0)
    assert un["reason"] == R.UNMAPPED and un["fell_back"] is False
    # caught exception -> QUERY_ERROR, never a fallback
    er = R.resolve(5, 5, 90.0, 0, error=True)
    assert er["reason"] == R.QUERY_ERROR and er["fell_back"] is False
    # entity_rows>0 NEVER yields a fallback, in any branch
    for r in (R.resolve(5, 5, 90.0, 0), R.resolve(5, 0, 0.0, 0), R.resolve(5, 5, 90.0, 0, error=True)):
        assert r["fell_back"] is False


def test_query_error_does_not_mask_as_sku_fallback(monkeypatch):
    with db.connect() as con:
        tid = TenantRepository(con).create("Tester"); db.set_account_type(con, tid, "tester"); con.commit()
    scheduler.provision_own_data(tid, SyntheticSource(), log=lambda *a: None)   # entity_rows > 0

    def _boom(con, tid):
        raise RuntimeError("simulated query failure")
    monkeypatch.setattr(ads, "_build_recs", _boom)
    with db.connect() as con:
        res, recs = ads._resolve(con, tid)
    assert res["reason"] == R.QUERY_ERROR and res["fell_back"] is False        # NOT the SKU view
    assert res["entity_rows"] > 0 and recs == []                              # data present; failure surfaced


if __name__ == "__main__":
    test_resolve_rule_unit()
    print("fallback_never_masks_error OK (unit; integration needs pytest)")
